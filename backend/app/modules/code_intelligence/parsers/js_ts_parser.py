"""JavaScript, TypeScript, JSX, and TSX code parser with structural analysis."""

import re
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


class JavaScriptTypeScriptParser(BaseLanguageParser):
    """Structural parser for JavaScript, TypeScript, JSX, and TSX files."""

    @property
    def language(self) -> str:
        return "js"

    @property
    def supported_extensions(self) -> list[str]:
        return ["js", "mjs", "cjs", "jsx", "ts", "mts", "cts", "tsx"]

    def can_parse(self, filename: str, content: str = "") -> bool:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        return ext in self.supported_extensions

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
        syntax_validation = SyntaxValidationResult(parser_used="js-ts-structural-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())

        # Count comments (line comments // and block comments /* */)
        comment_lines = 0
        in_block_comment = False
        code_lines_count = 0

        for line in lines:
            stripped = line.strip()
            if in_block_comment:
                comment_lines += 1
                if "*/" in stripped:
                    in_block_comment = False
            elif stripped.startswith("/*"):
                comment_lines += 1
                if "*/" not in stripped:
                    in_block_comment = True
            elif stripped.startswith("//"):
                comment_lines += 1
            elif not stripped:
                pass
            else:
                code_lines_count += 1

        # 1. Imports and Dependencies
        # Matches: import ... from 'pkg' OR import 'pkg' OR const ... = require('pkg')
        import_stmt_pattern = re.compile(
            r"""(?m)^(?:export\s+)?import\s+(?:(?:(\*\s+as\s+\w+|[\w\s{},]+)\s+from\s+)?['"]([^'"]+)['"]|['"]([^'"]+)['"]);?"""
        )
        require_stmt_pattern = re.compile(
            r"""(?:const|let|var)\s+(?:(\{[^}]+\}|\w+))\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)"""
        )

        for match in import_stmt_pattern.finditer(content):
            imported_clause = match.group(1) or ""
            target_pkg = match.group(2) or match.group(3) or ""
            line_no = content[: match.start()].count("\n") + 1
            is_relative = target_pkg.startswith(".")
            symbols_imported = [
                s.strip()
                for s in re.sub(r"[\{\}\*as]", "", imported_clause).split(",")
                if s.strip()
            ]

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=target_pkg,
                    imported_symbols=symbols_imported,
                    is_relative=is_relative,
                    is_external=not is_relative,
                    line_number=line_no,
                )
            )
            if not is_relative:
                pkg_name = target_pkg.split("/")[0]
                if target_pkg.startswith("@") and "/" in target_pkg:
                    parts = target_pkg.split("/")
                    pkg_name = f"{parts[0]}/{parts[1]}"
                if pkg_name not in [d.name for d in dependencies]:
                    dependencies.append(CodeDependency(name=pkg_name, dependency_type="external"))

        for match in require_stmt_pattern.finditer(content):
            imported_clause = match.group(1) or ""
            target_pkg = match.group(2) or ""
            line_no = content[: match.start()].count("\n") + 1
            is_relative = target_pkg.startswith(".")
            symbols_imported = [
                s.strip()
                for s in re.sub(r"[\{\}]", "", imported_clause).split(",")
                if s.strip()
            ]

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=target_pkg,
                    imported_symbols=symbols_imported,
                    is_relative=is_relative,
                    is_external=not is_relative,
                    line_number=line_no,
                )
            )
            if not is_relative:
                pkg_name = target_pkg.split("/")[0]
                if pkg_name not in [d.name for d in dependencies]:
                    dependencies.append(CodeDependency(name=pkg_name, dependency_type="external"))

        # 2. Extract Symbols: Functions, Classes, Interfaces, Types, Enums
        # Classes: class Name [extends ...]
        class_pattern = re.compile(r"""(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?""")
        for match in class_pattern.finditer(content):
            c_name = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=c_name,
                    symbol_type="class",
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # Interfaces & Types (TypeScript)
        interface_pattern = re.compile(r"""(?:export\s+)?interface\s+(\w+)""")
        for match in interface_pattern.finditer(content):
            i_name = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=i_name,
                    symbol_type="interface",
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        type_pattern = re.compile(r"""(?:export\s+)?type\s+(\w+)\s*=""")
        for match in type_pattern.finditer(content):
            t_name = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=t_name,
                    symbol_type="type_alias",
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        enum_pattern = re.compile(r"""(?:export\s+)?enum\s+(\w+)""")
        for match in enum_pattern.finditer(content):
            e_name = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=e_name,
                    symbol_type="enum",
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # Functions & Arrow Functions
        # function name(...)
        func_decl_pattern = re.compile(r"""(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)""")
        for match in func_decl_pattern.finditer(content):
            f_name = match.group(1)
            raw_params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=f_name,
                    symbol_type="function",
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # const name = (...) => ... OR const name = async (...) => ...
        arrow_func_pattern = re.compile(
            r"""(?:export\s+)?const\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?::\s*[^=]+)?\s*=>"""
        )
        for match in arrow_func_pattern.finditer(content):
            f_name = match.group(1)
            raw_params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=f_name,
                    symbol_type="function",
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Diagnostics & Security Warnings
        # Check 3.1: Dangerous calls (eval, Function constructor, document.write)
        dangerous_patterns = [
            (r"""\beval\s*\(""", "SEC-EVAL-USAGE", "error", "Direct execution of arbitrary code via eval()."),
            (r"""\bnew\s+Function\s*\(""", "SEC-NEW-FUNCTION", "error", "Dynamic code construction via new Function()."),
            (r"""\bdocument\.write(?:ln)?\s*\(""", "SEC-DOCUMENT-WRITE", "warning", "document.write() is vulnerable to Cross-Site Scripting (XSS)."),
            (r"""\bdebugger\s*;""", "JS-DEBUGGER-STMT", "info", "Extraneous 'debugger' statement left in production code."),
        ]

        for pat, rule_id, sev, msg in dangerous_patterns:
            for match in re.finditer(pat, content):
                line_no = content[: match.start()].count("\n") + 1
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id=rule_id,
                        severity=sev,
                        message=msg,
                        file_path=filename,
                        start_line=line_no,
                        end_line=line_no,
                        column=1,
                        tool_name="js-ts-security-scanner",
                        evidence=match.group(0).strip(),
                        suggested_remediation="Refactor to safe alternatives without dynamic execution.",
                    )
                )

        # Check 3.2: Hardcoded secrets
        secret_regex = re.compile(
            r"""(?i)(const|let|var)\s+(password|secret|api[_-]?key|access[_-]?token|auth_token)\s*=\s*['"]([A-Za-z0-9_\-\.]{8,})['"]"""
        )
        for match in secret_regex.finditer(content):
            line_no = content[: match.start()].count("\n") + 1
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="SEC-HARDCODED-SECRET",
                    severity="error",
                    message="Hardcoded API secret or credential detected.",
                    file_path=filename,
                    start_line=line_no,
                    end_line=line_no,
                    column=1,
                    tool_name="js-ts-security-scanner",
                    suggested_remediation="Store secrets in process.env or secret manager.",
                )
            )

        # 4. Metrics & Complexity Estimation
        # Heuristic cyclomatic complexity (branches: if, else if, case, for, while, catch, &&, ||, ?)
        branch_matches = len(re.findall(r"""\b(?:if|else\s+if|case|for|while|catch)\b|\?|&&|\|\|""", content))
        complexity = float(1 + branch_matches)

        # Nesting depth via curly braces
        max_depth = 1
        curr_depth = 0
        for char in content:
            if char == "{":
                curr_depth += 1
                if curr_depth > max_depth:
                    max_depth = curr_depth
            elif char == "}":
                curr_depth = max(0, curr_depth - 1)

        func_count = sum(1 for s in symbols if s.symbol_type == "function")
        class_count = sum(1 for s in symbols if s.symbol_type in ("class", "interface"))

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines_count,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=func_count,
            class_count=class_count,
            import_count=len(imports),
            avg_function_length=round(float(code_lines_count / max(1, func_count)), 1) if func_count else 0.0,
            max_function_length=code_lines_count if func_count == 1 else (code_lines_count // 2 if func_count > 1 else 0),
            cyclomatic_complexity=round(complexity, 1),
            nesting_depth=max_depth,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
