"""Python language parser using standard ast and tokenize modules."""

import ast
import re
import sys
import uuid
from typing import Any

from app.modules.code_intelligence.parsers.base import BaseLanguageParser
from app.modules.code_intelligence.schemas.code_document import (
    CodeDependency,
    CodeDiagnostic,
    CodeImport,
    CodeMetrics,
    CodeSymbol,
    SyntaxValidationResult,
)


class PythonParser(BaseLanguageParser):
    """Deep structural and semantic parser for Python source code using standard Python AST."""

    @property
    def language(self) -> str:
        return "py"

    @property
    def supported_extensions(self) -> list[str]:
        return ["py", "pyw"]

    def parse(
        self,
        content: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> tuple[
        list[CodeSymbol],
        list[CodeImport],
        list[CodeDependency],
        CodeMetrics,
        list[CodeDiagnostic],
        SyntaxValidationResult,
    ]:
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        dependencies: list[CodeDependency] = []
        diagnostics: list[CodeDiagnostic] = []
        syntax_validation = SyntaxValidationResult(parser_used="python-ast")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        code_lines = total_lines - blank_lines - comment_lines

        # 1. Syntax Validation & AST Parsing
        try:
            tree = ast.parse(content, filename=filename or "<input>")
        except SyntaxError as e:
            syntax_validation.is_valid = False
            err_msg = f"SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}"
            syntax_validation.errors.append(err_msg)
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="PY-SYNTAX-ERROR",
                    severity="error",
                    message=e.msg or "Syntax error",
                    file_path=filename,
                    start_line=e.lineno or 1,
                    end_line=e.lineno or 1,
                    column=e.offset or 1,
                    tool_name="python-ast",
                    evidence=e.text.strip() if e.text else None,
                    suggested_remediation="Fix syntax error at the indicated position.",
                )
            )
            # Return partial metrics on syntax error
            metrics = CodeMetrics(
                total_lines=total_lines,
                code_lines=max(0, code_lines),
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                cyclomatic_complexity=1.0,
            )
            return symbols, imports, dependencies, metrics, diagnostics, syntax_validation

        # 2. Extract Symbols & Imports via AST Visitor
        used_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)

        # Helper to extract parameter names and annotations
        def get_params(args: ast.arguments) -> list[str]:
            params: list[str] = []
            for arg in args.posonlyargs + args.args:
                ann = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
                params.append(f"{arg.arg}{ann}")
            if args.vararg:
                params.append(f"*{args.vararg.arg}")
            for arg in args.kwonlyargs:
                ann = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
                params.append(f"{arg.arg}{ann}")
            if args.kwarg:
                params.append(f"**{args.kwarg.arg}")
            return params

        # Top-level and nested symbol collector
        function_lengths: list[int] = []

        class SymbolCollector(ast.NodeVisitor):
            def __init__(self) -> None:
                self.parent_stack: list[str] = []

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                sym_id = f"sym_{uuid.uuid4().hex[:8]}"
                parent = self.parent_stack[-1] if self.parent_stack else None
                doc = ast.get_docstring(node)
                symbols.append(
                    CodeSymbol(
                        symbol_id=sym_id,
                        name=node.name,
                        symbol_type="class",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        parent_symbol=parent,
                        visibility="private" if node.name.startswith("_") else "public",
                        documentation=doc,
                        source_reference=f"class {node.name}:",
                    )
                )
                self.parent_stack.append(sym_id)
                self.generic_visit(node)
                self.parent_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._handle_func(node, is_async=False)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._handle_func(node, is_async=True)

            def _handle_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
                sym_id = f"sym_{uuid.uuid4().hex[:8]}"
                parent = self.parent_stack[-1] if self.parent_stack else None
                sym_type = "method" if parent is not None else "function"
                doc = ast.get_docstring(node)
                ret_type = ast.unparse(node.returns) if node.returns else None
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                function_lengths.append(length)

                symbols.append(
                    CodeSymbol(
                        symbol_id=sym_id,
                        name=node.name,
                        symbol_type=sym_type,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        parent_symbol=parent,
                        visibility="private" if node.name.startswith("_") else "public",
                        parameters=get_params(node.args),
                        return_type=ret_type,
                        documentation=doc,
                        source_reference=f"{'async def' if is_async else 'def'} {node.name}(...)",
                    )
                )
                self.parent_stack.append(sym_id)
                self.generic_visit(node)
                self.parent_stack.pop()

            def visit_Assign(self, node: ast.Assign) -> None:
                if not self.parent_stack:  # Module-level assignments
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            symbols.append(
                                CodeSymbol(
                                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                                    name=target.id,
                                    symbol_type="constant",
                                    start_line=node.lineno,
                                    end_line=node.end_lineno or node.lineno,
                                    source_reference=f"{target.id} = ...",
                                )
                            )
                self.generic_visit(node)

        collector = SymbolCollector()
        collector.visit(tree)

        # 3. Extract Imports & External Dependencies
        imported_symbols_map: dict[str, int] = {}
        stdlib_names: set[str] = set(getattr(sys, "stdlib_module_names", set()))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    is_ext = root_pkg not in stdlib_names and root_pkg != "__future__"
                    bound_name = alias.asname or alias.name
                    imported_symbols_map[bound_name] = node.lineno
                    imports.append(
                        CodeImport(
                            statement=f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""),
                            module_name=alias.name,
                            imported_symbols=[bound_name],
                            is_relative=False,
                            is_external=is_ext,
                            alias=alias.asname,
                            line_number=node.lineno,
                        )
                    )
                    if is_ext and root_pkg not in [d.name for d in dependencies]:
                        dependencies.append(CodeDependency(name=root_pkg, dependency_type="external"))

            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                root_pkg = mod.split(".")[0] if mod else ""
                is_ext = bool(root_pkg and root_pkg not in stdlib_names and node.level == 0)
                symbols_imported = [alias.name for alias in node.names]
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    imported_symbols_map[bound_name] = node.lineno

                imports.append(
                    CodeImport(
                        statement=f"from {'.' * node.level}{mod} import {', '.join(symbols_imported)}",
                        module_name=mod or f"{'.' * node.level}",
                        imported_symbols=symbols_imported,
                        is_relative=node.level > 0,
                        is_external=is_ext,
                        line_number=node.lineno,
                    )
                )
                if is_ext and root_pkg not in [d.name for d in dependencies]:
                    dependencies.append(CodeDependency(name=root_pkg, dependency_type="external"))

        # 4. Static Code Diagnostics (Security & Quality Checks)
        # Check 4.1: Unused imports
        for bound_name, line_no in imported_symbols_map.items():
            if bound_name == "*":
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id="PY-WILDCARD-IMPORT",
                        severity="warning",
                        message="Wildcard import detected ('from ... import *'). Pollutes module namespace.",
                        file_path=filename,
                        start_line=line_no,
                        end_line=line_no,
                        column=1,
                        tool_name="python-linter",
                        suggested_remediation="Import specific required symbols explicitly.",
                    )
                )
            elif bound_name not in used_names:
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id="PY-UNUSED-IMPORT",
                        severity="info",
                        message=f"Import '{bound_name}' is declared but never referenced in module.",
                        file_path=filename,
                        start_line=line_no,
                        end_line=line_no,
                        column=1,
                        tool_name="python-linter",
                        suggested_remediation=f"Remove unused import '{bound_name}'.",
                    )
                )

        # Check 4.2: AST walk for unsafe patterns
        for node in ast.walk(tree):
            # Dangerous calls (eval, exec, os.system)
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"

                if func_name in ("eval", "exec"):
                    diagnostics.append(
                        CodeDiagnostic(
                            diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                            rule_id="SEC-DANGEROUS-EXEC",
                            severity="error",
                            message=f"Potentially unsafe dynamic code execution via '{func_name}()'.",
                            file_path=filename,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            column=node.col_offset,
                            tool_name="security-auditor",
                            evidence=ast.unparse(node),
                            suggested_remediation="Avoid eval/exec; use safe parsing (e.g. ast.literal_eval or json.loads).",
                        )
                    )
                elif func_name in ("os.system", "subprocess.call", "subprocess.Popen"):
                    # Check for shell=True
                    has_shell_true = any(
                        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                        for kw in node.keywords
                    )
                    if func_name == "os.system" or has_shell_true:
                        diagnostics.append(
                            CodeDiagnostic(
                                diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                                rule_id="SEC-SHELL-INJECTION",
                                severity="warning",
                                message=f"Subprocess call with shell execution risk: '{func_name}'.",
                                file_path=filename,
                                start_line=node.lineno,
                                end_line=node.end_lineno or node.lineno,
                                column=node.col_offset,
                                tool_name="security-auditor",
                                evidence=ast.unparse(node),
                                suggested_remediation="Pass command arguments as a list without shell=True to avoid injection.",
                            )
                        )

            # Bare except clause
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    diagnostics.append(
                        CodeDiagnostic(
                            diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                            rule_id="PY-BARE-EXCEPT",
                            severity="warning",
                            message="Bare 'except:' handler catches all exceptions including SystemExit and KeyboardInterrupt.",
                            file_path=filename,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            column=node.col_offset,
                            tool_name="python-linter",
                            suggested_remediation="Catch specific exceptions or at minimum 'except Exception:'.",
                        )
                    )

        # Check 4.3: Hardcoded credentials regex check
        secret_regex = re.compile(
            r"""(?i)(password|secret|api[_-]?key|access[_-]?token|private[_-]?key)\s*=\s*['"]([A-Za-z0-9_\-\.]{8,})['"]"""
        )
        for idx, line in enumerate(lines, start=1):
            if secret_regex.search(line) and not line.strip().startswith("#"):
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id="SEC-HARDCODED-SECRET",
                        severity="error",
                        message="Potential hardcoded secret or API credential detected in source code.",
                        file_path=filename,
                        start_line=idx,
                        end_line=idx,
                        column=1,
                        tool_name="security-auditor",
                        suggested_remediation="Store credentials in environment variables or a secure secret manager.",
                    )
                )

        # 5. Calculate Metrics & Cyclomatic Complexity
        complexity = 1.0
        max_depth = 1

        def calculate_depth(node: ast.AST, current_depth: int) -> int:
            depth = current_depth
            compound_nodes = (
                ast.If,
                ast.While,
                ast.For,
                ast.AsyncFor,
                ast.Try,
                ast.With,
                ast.AsyncWith,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            )
            for child in ast.iter_child_nodes(node):
                child_depth = current_depth + (1 if isinstance(child, compound_nodes) else 0)
                sub_depth = calculate_depth(child, child_depth)
                if sub_depth > depth:
                    depth = sub_depth
            return depth

        max_depth = calculate_depth(tree, 1)

        # McCabe Complexity
        for node in ast.walk(tree):
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                    ast.With,
                    ast.AsyncWith,
                    ast.Assert,
                    ast.comprehension,
                ),
            ):
                complexity += 1.0
            elif isinstance(node, ast.BoolOp):
                complexity += max(0, len(node.values) - 1)

        func_count = sum(1 for s in symbols if s.symbol_type in ("function", "method"))
        class_count = sum(1 for s in symbols if s.symbol_type == "class")
        avg_func_len = float(sum(function_lengths) / len(function_lengths)) if function_lengths else 0.0
        max_func_len = max(function_lengths) if function_lengths else 0

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=max(0, code_lines),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=func_count,
            class_count=class_count,
            import_count=len(imports),
            avg_function_length=round(avg_func_len, 1),
            max_function_length=max_func_len,
            cyclomatic_complexity=round(complexity, 1),
            nesting_depth=max_depth,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
