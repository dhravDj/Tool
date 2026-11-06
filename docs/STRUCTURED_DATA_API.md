# DocuMind AI — Structured Data Intelligence REST API Reference

Base URL prefix: `/api/v1`

## Endpoints

### 1. `GET /structured-data-intelligence/capabilities`
Returns list of supported structured data formats, installed engines, and features.

### 2. `POST /files/{file_id}/analyze-structured-data`
Triggers structured data parsing, schema extraction, and column profiling.
- Request body: Optional configuration dictionary.
- Response: Status manifest with row count, column count, and candidate keys.

### 3. `GET /files/{file_id}/structured-data-analysis`
Retrieves historical summary record from PostgreSQL database.

### 4. `GET /files/{file_id}/structured-data-analysis/result`
Retrieves full canonical `StructuredDataDocument`.

### 5. `GET /files/{file_id}/structured-data-analysis/schema`
Returns inferred JSON Schema or Parquet schema definition.

### 6. `GET /files/{file_id}/structured-data-analysis/profile`
Returns `DataProfile` object with column-level metrics and candidate keys.

### 7. `GET /files/{file_id}/structured-data-analysis/relationships`
Returns array of inferred entity relationships or foreign keys.

### 8. `GET /files/{file_id}/structured-data-analysis/records`
Returns bounded sample of records (up to 50 rows).

### 9. `GET /files/{file_id}/structured-data-analysis/export/{format}`
Exports report as `json`, `markdown`, or `csv`.
