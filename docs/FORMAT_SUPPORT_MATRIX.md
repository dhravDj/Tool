# Universal Format Support Matrix

DocuMind provides verifiable extraction and universal conversion across 60+ file formats organized into 9 domain categories.

---

## 1. Matrix by Category

| Category | Format | Extensions | Extraction Engine / Library | Supported Output Formats | Supports OCR | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Documents** | PDF | `.pdf` | PyMuPDF + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | Word (Modern) | `.docx` | `python-docx` AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Word (Legacy) | `.doc` | OleFile / Antiword Parser | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | OpenDocument | `.odt` | `odfpy` XML Parser | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Rich Text | `.rtf` | `striprtf` Lexer | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Plain Text | `.txt` | Chardet / UTF-8 Stream | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Markdown | `.md` | Markdown-It-Py AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | eBook | `.epub` | `ebooklib` HTML Parser | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| **Spreadsheets** | Excel (Modern) | `.xlsx` | `openpyxl` / Calamine | `csv`, `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Excel (Legacy) | `.xls` | `xlrd` Binary Parser | `csv`, `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | CSV | `.csv` | Python CSV Stream Reader | `csv`, `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | TSV | `.tsv` | Tab Delimited Reader | `csv`, `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | OpenDocument Calc| `.ods` | `odfpy` / Calamine | `csv`, `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| **Presentations** | PowerPoint (Modern)| `.pptx` | `python-pptx` | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | PowerPoint (Legacy)| `.ppt` | OleFile Parser | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | OpenDocument Impress| `.odp` | `odfpy` Presentation | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| **Images** | PNG | `.png` | Pillow + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | JPEG | `.jpg`, `.jpeg` | Pillow + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | WebP | `.webp` | Pillow + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | TIFF | `.tiff`, `.tif` | Pillow + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | BMP | `.bmp` | Pillow + Tesseract OCR | `txt`, `md`, `json`, `html`, `zip` | Yes | Fully Supported |
| | SVG | `.svg` | `defusedxml` Vector AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| **Audio** | MP3 | `.mp3` | Mutagen / Faster-Whisper / Acoustic | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| | WAV | `.wav` | Wave / Faster-Whisper | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| | M4A | `.m4a` | Mutagen / FFmpeg / STT | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| | AAC | `.aac` | FFmpeg / STT Engine | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| | FLAC | `.flac` | Mutagen / FLAC Stream | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| | OGG | `.ogg` | Vorbis Comment Reader | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | No | Fully Supported |
| **Video** | MP4 | `.mp4` | PyAV / FFmpeg / Scene Cut | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | Yes | Fully Supported |
| | Matroska | `.mkv` | PyAV / EBML Parser | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | Yes | Fully Supported |
| | QuickTime | `.mov` | PyAV / Qt Parser | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | Yes | Fully Supported |
| | AVI | `.avi` | PyAV / RIFF Parser | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | Yes | Fully Supported |
| | WebM | `.webm` | PyAV / VP8/VP9 Decoder | `txt`, `md`, `srt`, `vtt`, `json`, `html`, `zip` | Yes | Fully Supported |
| **Code** | Python | `.py` | `ast` Standard Library | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | JavaScript | `.js`, `.jsx` | Tree-Sitter / RegEx AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | TypeScript | `.ts`, `.tsx` | Tree-Sitter / Type AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | HTML | `.html`, `.htm` | BeautifulSoup4 / lxml | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | CSS | `.css` | TinyCSS2 Parser | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Java | `.java` | Javalang / Regex AST | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | C / C++ | `.c`, `.cpp`, `.h` | Tree-Sitter C/CPP | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Go | `.go` | Tree-Sitter Go | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | Rust | `.rs` | Tree-Sitter Rust | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | PHP | `.php` | PHP Lexer / Regex | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| | SQL | `.sql` | `sqlparse` Formatter | `txt`, `md`, `json`, `html`, `zip` | No | Fully Supported |
| **Structured Data** | JSON | `.json` | `json` / Orjson | `json`, `txt`, `md`, `csv`, `html`, `zip` | No | Fully Supported |
| | XML | `.xml` | `defusedxml` (XXE-safe) | `xml`, `json`, `txt`, `md`, `csv`, `html`, `zip` | No | Fully Supported |
| | YAML | `.yaml`, `.yml` | `ruamel.yaml` (SafeLoader) | `json`, `txt`, `md`, `html`, `zip` | No | Fully Supported |
| | TOML | `.toml` | `tomli` / `tomllib` | `json`, `txt`, `md`, `html`, `zip` | No | Fully Supported |
| | Parquet | `.parquet` | `pyarrow.parquet` | `csv`, `json`, `txt`, `md`, `html`, `zip` | No | Fully Supported |
| **Archives** | ZIP | `.zip` | Safe ZipFile Extractor | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | 7-Zip | `.7z` | `py7zr` Archive Engine | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | Tape Archive | `.tar` | Safe TarFile Inspector | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | Compressed Tar | `.tar.gz`, `.tgz` | Gzip / Tar Engine | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | Bzip2 Tar | `.tar.bz2`, `.tbz2` | Bzip2 / Tar Engine | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | XZ Tar | `.tar.xz`, `.txz` | LZMA / Tar Engine | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |
| | Gzip | `.gz` | Gzip Decompressor | `zip`, `txt`, `md`, `json`, `html` | No | Fully Supported |

---

## 2. Target Output Mapping Rules

- **Spreadsheets to CSV**: Multi-sheet workbooks allow exporting each worksheet separately into individual CSVs (Mode C bundle) or combining all tables into a unified Markdown/TXT representation.
- **Audio/Video to Subtitles**: SRT and VTT outputs are available exclusively for inputs possessing timed speech transcription tracks.
- **Images to Tabular CSV**: Converting an image directly to CSV is disallowed unless OCR detects tabular coordinates and boundaries. The UI dynamically disables non-sensical conversions.
