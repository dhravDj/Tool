#!/usr/bin/env python3
"""DocuMind - Universal Document Processor & File Converter CLI.

Powered by Universal-Converter engine (https://github.com/junaidbusy-cell/Universal-Converter).
Supports PDF, Word (DOCX/DOC), PowerPoint (PPTX/PPT), Excel (XLSX/XLS/CSV), EPUB,
Images (PNG/JPG/WEBP/TIFF/SVG with OCR), HTML, Live Webpages, Academic DOIs, Code, Text & Data files.
"""

import sys
from pathlib import Path

# Add converter_engine directory to sys.path so submodules can import each other directly
_root_dir = Path(__file__).resolve().parent
_engine_dir = _root_dir / "converter_engine"
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir))

from main import main

if __name__ == "__main__":
    main()
