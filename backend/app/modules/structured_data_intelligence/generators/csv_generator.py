"""CSV export generator for structured data sample records."""

import csv
import io

from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)


class StructuredCSVGenerator:
    """Generates standard CSV representation of sampled records."""

    def generate(self, doc: StructuredDataDocument) -> str:
        if not doc.records:
            return ""

        output = io.StringIO()
        fieldnames = sorted(doc.records[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in doc.records:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
        return output.getvalue()
