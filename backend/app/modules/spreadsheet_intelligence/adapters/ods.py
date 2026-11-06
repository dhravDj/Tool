"""OpenDocument Spreadsheet (ODS) Adapter using safe XML and ZIP container parsing."""

import logging
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.modules.spreadsheet_intelligence.adapters.base import (
    BaseSpreadsheetAdapter,
    SpreadsheetLimitsExceededError,
)
from app.modules.spreadsheet_intelligence.profiling.profiler import DataUnderstandingProfiler
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    CellData,
    CellDataType,
    ColumnData,
    RowData,
    SheetVisibility,
    SpreadsheetDocument,
    WorkbookMetadata,
    WorksheetData,
)

logger = logging.getLogger(__name__)


class ODSAdapter(BaseSpreadsheetAdapter):
    """High-performance extraction adapter for OpenDocument Spreadsheet (.ods) files."""

    format_id = "ods"
    engine_name = "ods_adapter"
    version = "1.0.0"

    # OpenDocument XML namespaces
    NS = {
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def extract_workbook(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> SpreadsheetDocument:
        doc_id = str(uuid.uuid4())
        file_id = options.get("file_id", doc_id) if options else doc_id
        warnings: list[str] = []

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # 1. Parse meta.xml for workbook properties
                creator = None
                created_at = None
                if "meta.xml" in zf.namelist():
                    try:
                        meta_root = ET.fromstring(zf.read("meta.xml"))
                        creator_elem = meta_root.find(".//dc:creator", self.NS)
                        if creator_elem is not None:
                            creator = creator_elem.text
                        created_elem = meta_root.find(".//meta:creation-date", self.NS)
                        if created_elem is not None:
                            created_at = created_elem.text
                    except Exception:
                        pass

                # 2. Parse content.xml for tables and cells
                content_xml = zf.read("content.xml")
                root = ET.fromstring(content_xml)

                tables = root.findall(".//table:table", self.NS)
                worksheets: list[WorksheetData] = []

                for sheet_idx, tbl in enumerate(tables):
                    sheet_name = tbl.attrib.get(f"{{{self.NS['table']}}}name", f"Sheet{sheet_idx + 1}")
                    grid_rows: list[list[Any]] = []
                    canonical_rows: list[RowData] = []
                    col_headers: list[str] = []
                    max_cols = 0

                    rows = tbl.findall(".//table:table-row", self.NS)
                    r_idx = 1

                    for row_elem in rows:
                        row_repeat = int(row_elem.attrib.get(f"{{{self.NS['table']}}}number-rows-repeated", "1"))
                        # Defensive cap on empty repeated rows at end of sheet
                        if row_repeat > 5000:
                            row_repeat = 1

                        cells = row_elem.findall(".//table:table-cell", self.NS)
                        row_vals: list[Any] = []
                        sparse_cells: list[CellData] = []
                        c_idx = 1

                        for cell_elem in cells:
                            col_repeat = int(cell_elem.attrib.get(f"{{{self.NS['table']}}}number-columns-repeated", "1"))
                            if col_repeat > 1024:
                                col_repeat = 1

                            val_type = cell_elem.attrib.get(f"{{{self.NS['office']}}}value-type")
                            formula_raw = cell_elem.attrib.get(f"{{{self.NS['table']}}}formula")
                            val: Any = None
                            data_type = CellDataType.STRING

                            # Extract text paragraph
                            text_p = cell_elem.findall(".//text:p", self.NS)
                            text_content = " ".join(p.text or "" for p in text_p).strip()

                            if val_type == "float" or val_type == "currency" or val_type == "percentage":
                                raw_num = cell_elem.attrib.get(f"{{{self.NS['office']}}}value")
                                try:
                                    val = float(raw_num) if raw_num else float(text_content)
                                    data_type = CellDataType.NUMBER
                                except (ValueError, TypeError):
                                    val = text_content
                            elif val_type == "boolean":
                                raw_b = cell_elem.attrib.get(f"{{{self.NS['office']}}}boolean-value")
                                val = (raw_b.lower() == "true") if raw_b else (text_content.lower() == "true")
                                data_type = CellDataType.BOOLEAN
                            elif val_type == "date":
                                val = cell_elem.attrib.get(f"{{{self.NS['office']}}}date-value") or text_content
                                data_type = CellDataType.DATE
                            elif text_content:
                                val = text_content
                                data_type = CellDataType.STRING
                            else:
                                val = None
                                data_type = CellDataType.EMPTY

                            # Format formula if present (ODF formulas often look like 'of:=SUM([.A1:.A10])')
                            clean_formula = None
                            if formula_raw:
                                clean_formula = formula_raw.replace("of:=", "=").replace("[.", "").replace("]", "")
                                data_type = CellDataType.FORMULA

                            for _ in range(col_repeat):
                                row_vals.append(val)
                                if val is not None or clean_formula:
                                    col_letter = DataUnderstandingProfiler._get_column_letter(c_idx)
                                    sparse_cells.append(
                                        CellData(
                                            address=f"{col_letter}{r_idx}",
                                            row=r_idx,
                                            column=c_idx,
                                            raw_value=val,
                                            formatted_value=str(val) if val is not None else "",
                                            data_type=data_type,
                                            formula=clean_formula,
                                        )
                                    )
                                c_idx += 1

                        if c_idx - 1 > max_cols:
                            max_cols = c_idx - 1

                        if r_idx == 1:
                            col_headers = [str(v or f"Col_{i+1}") for i, v in enumerate(row_vals)]

                        for _ in range(row_repeat):
                            grid_rows.append(row_vals)
                            if sparse_cells:
                                canonical_rows.append(
                                    RowData(
                                        row_index=r_idx,
                                        cells=sparse_cells,
                                    )
                                )
                            r_idx += 1

                    total_rows = len(grid_rows)
                    self.check_limits(total_rows, max_cols)

                    columns: list[ColumnData] = []
                    for c_idx in range(1, max_cols + 1):
                        letter = DataUnderstandingProfiler._get_column_letter(c_idx)
                        name = col_headers[c_idx - 1] if c_idx - 1 < len(col_headers) else f"Column {letter}"
                        columns.append(
                            ColumnData(
                                column_index=c_idx,
                                column_letter=letter,
                                name=name,
                            )
                        )

                    profiling = DataUnderstandingProfiler.profile_worksheet(
                        grid_data=grid_rows,
                        column_names=col_headers,
                    )

                    for col, prof in zip(columns, profiling.column_profiles, strict=False):
                        col.profiling = prof

                    worksheets.append(
                        WorksheetData(
                            sheet_id=f"sheet_{sheet_idx + 1}",
                            name=sheet_name,
                            position=sheet_idx + 1,
                            visibility=SheetVisibility.VISIBLE,
                            dimensions=f"A1:{DataUnderstandingProfiler._get_column_letter(max(1, max_cols))}{max(1, total_rows)}",
                            total_rows=total_rows,
                            total_columns=max_cols,
                            columns=columns,
                            rows=canonical_rows,
                            profiling=profiling,
                        )
                    )

                wb_meta = WorkbookMetadata(
                    filename=original_filename or file_path.name,
                    format="ods",
                    creator=creator,
                    created_at=created_at,
                    sheet_count=len(worksheets),
                )

                return SpreadsheetDocument(
                    document_id=doc_id,
                    file_id=file_id,
                    workbook_metadata=wb_meta,
                    worksheets=worksheets,
                    warnings=warnings,
                    extraction_metadata={
                        "engine": self.engine_name,
                        "version": self.version,
                        "extracted_at": datetime.now(UTC).isoformat(),
                    },
                )

        except SpreadsheetLimitsExceededError:
            raise
        except Exception as exc:
            logger.error(f"Failed to extract ODS spreadsheet '{file_path}': {exc}")
            raise
