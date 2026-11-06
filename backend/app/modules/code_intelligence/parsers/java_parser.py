"""Java source code parser and structural extractor."""

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


class JavaParser(BaseLanguageParser):
    """Parser for Java source code extracting packages, imports, classes, interfaces, records, and methods."""

    @property
    def language(self) -> str:
        return "java"

    @property
    def supported_extensions(self) -> list[str]:
        return ["java"]

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
        syntax_validation = SyntaxValidationResult(parser_used="java-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())

        comment_lines = 0
        in_block = False
        code_lines_count = 0

        for line in lines:
            s = line.strip()
            if in_block:
                comment_lines += 1
                if "*/" in s:
                    in_block = False
            elif s.startswith("/*"):
                comment_lines += 1
                if "*/" not in s:
                    in_block = True
            elif s.startswith("//"):
                comment_lines += 1
            elif not s:
                pass
            else:
                code_lines_count += 1

        # 1. Package and Imports
        import_pattern = re.compile(r"""import\s+(?:static\s+)?([A-Za-z0-9_.*]+);""")
        for match in import_pattern.finditer(content):
            import_target = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            is_java_stdlib = import_target.startswith(("java.", "javax."))
            root_pkg = import_target.split(".")[0]

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=import_target,
                    imported_symbols=[import_target.split(".")[-1]],
                    is_relative=False,
                    is_external=not is_java_stdlib,
                    line_number=line_no,
                )
            )
            if not is_java_stdlib:
                parts = import_target.split(".")
                dep_name = ".".join(parts[:2]) if len(parts) >= 2 else root_pkg
                if dep_name not in [d.name for d in dependencies]:
                    dependencies.append(CodeDependency(name=dep_name, dependency_type="external"))

        # 2. Classes, Interfaces, Records, Enums
        type_pattern = re.compile(
            r"""(?:public|protected|private)?\s*(?:static)?\s*(?:final|abstract)?\s*(class|interface|record|enum)\s+(\w+)"""
        )
        for match in type_pattern.finditer(content):
            kind = match.group(1)
            name = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=name,
                    symbol_type=kind,
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Methods: (modifiers) ReturnType name(params) {
        method_pattern = re.compile(
            r"""(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:[A-Za-z0-9_<>\[\],\s]+)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[A-Za-z0-9_,\s]+)?\s*\{"""
        )
        for match in method_pattern.finditer(content):
            m_name = match.group(1)
            if m_name in ("if", "while", "for", "switch", "catch"):
                continue
            raw_params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=m_name,
                    symbol_type="method",
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public",
                    source_reference=f"{m_name}(...)",
                )
            )

        # 4. Diagnostics: Hardcoded secrets and System.exit()
        if "System.exit(" in content:
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="JAVA-SYSTEM-EXIT",
                    severity="warning",
                    message="Direct call to System.exit() halts the JVM immediately.",
                    file_path=filename,
                    start_line=1,
                    end_line=1,
                    column=1,
                    tool_name="java-analyzer",
                    suggested_remediation="Throw an application exception instead of terminating the runtime.",
                )
            )

        func_count = sum(1 for s in symbols if s.symbol_type == "method")
        class_count = sum(1 for s in symbols if s.symbol_type in ("class", "interface", "record", "enum"))
        branch_count = len(re.findall(r"""\b(?:if|else\s+if|case|for|while|catch)\b|\?|&&|\|\|""", content))

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines_count,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=func_count,
            class_count=class_count,
            import_count=len(imports),
            avg_function_length=round(float(code_lines_count / max(1, func_count)), 1) if func_count else 0.0,
            cyclomatic_complexity=float(1 + branch_count),
            nesting_depth=2,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
