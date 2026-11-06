# DocuMind AI — Code Intelligence REST API Reference

Base URL prefix: `/api/v1`

## Endpoints

### 1. `GET /code-intelligence/capabilities`
Returns list of supported languages, installed parsers, and features.

### 2. `POST /files/{file_id}/analyze-code`
Triggers code parsing, AST symbol extraction, metrics calculation, and security audits.
- Request body: Optional configuration dictionary.
- Response: Status manifest with `symbol_count`, `metrics`, and `language`.

### 3. `GET /files/{file_id}/code-analysis`
Retrieves historical summary record from PostgreSQL database.

### 4. `GET /files/{file_id}/code-analysis/result`
Retrieves full canonical `CodeDocument`.

### 5. `GET /files/{file_id}/code-analysis/symbols`
Returns array of `CodeSymbol` objects.

### 6. `GET /files/{file_id}/code-analysis/dependencies`
Returns array of imports and identified third-party dependencies.

### 7. `GET /files/{file_id}/code-analysis/diagnostics`
Returns static code diagnostics and security vulnerability alerts.

### 8. `GET /files/{file_id}/code-analysis/metrics`
Returns code metrics (lines, comments, complexity, nesting).

### 9. `GET /files/{file_id}/code-analysis/source`
Returns raw source code text (`text/plain`).

### 10. `GET /files/{file_id}/code-analysis/export/{format}`
Exports report as `json`, `markdown`, or `txt`.
