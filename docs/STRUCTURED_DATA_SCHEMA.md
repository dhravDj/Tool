# DocuMind AI — Structured Data Schema Reference

Canonical Pydantic schema: `StructuredDataDocument` (`backend/app/modules/structured_data_intelligence/schemas/structured_data_document.py`).

```typescript
interface StructuredDataDocument {
  document_id: string;
  source_file_id: string;
  format: string;               // "json", "xml", "yaml", "toml", "parquet"
  root_type: string;            // "object", "array", "element", "table", "mapping"
  schema_definition: Record<string, unknown>;
  hierarchy: unknown;
  records: Record<string, unknown>[];
  data_profile: DataProfile;
  validation_results: StructuredValidationResult;
  relationships: RelationshipEdge[];
  metadata: Record<string, unknown>;
  processing_metadata: Record<string, unknown>;
  model_information: StructuredModelInfo;
  warnings: string[];
  status: string;
  raw_preview: string;
}
```

### Sub-Models

1. **`DataProfile`**: Total rows, total columns, candidate keys, missing cells ratio.
2. **`ColumnProfile`**: Data type, physical type, null percentage, uniqueness, column statistics.
3. **`ColumnStatistics`**: Min value, max value, null count, distinct count, sample values.
4. **`StructuredValidationResult`**: Syntax validity, duplicate keys, schema errors, security warnings.
5. **`RelationshipEdge`**: Inferred entity relationships or foreign keys.
