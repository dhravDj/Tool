# DocuMind AI — Code Intelligence Schema Reference

Canonical Pydantic schema: `CodeDocument` (`backend/app/modules/code_intelligence/schemas/code_document.py`).

```typescript
interface CodeDocument {
  document_id: string;
  source_file_id: string;
  language: string;             // "py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"
  encoding: string;
  file_metadata: Record<string, unknown>;
  symbols: CodeSymbol[];
  imports: CodeImport[];
  dependencies: CodeDependency[];
  metrics: CodeMetrics;
  diagnostics: CodeDiagnostic[];
  syntax_validation: SyntaxValidationResult;
  source_references: string[];
  processing_metadata: Record<string, unknown>;
  model_information: CodeModelInfo;
  warnings: string[];
  status: string;
}
```

### Sub-Models

1. **`CodeSymbol`**: Extracted program construct (class, function, method, interface, struct, table).
2. **`CodeImport`**: Module import statement with line number and internal/external classification.
3. **`CodeDependency`**: Identified third-party package or foreign-key table requirement.
4. **`CodeMetrics`**: Lines of code, comment ratio, cyclomatic complexity, nesting depth.
5. **`CodeDiagnostic`**: Linter finding, syntax error, or security alert with remediation advice.
