# DocuMind AI — Structured Data Intelligence Engine

## Overview

The Structured Data Intelligence Engine parses, validates, profiles, and visualizes structured configuration and data files across 5 standard formats: JSON, XML, YAML, TOML, and Apache Parquet.

---

## Supported Formats

| Format ID | Format Name | Handled Extensions | Engine Implementation | Core Capabilities |
|:---:|:---:|:---:|:---:|---|
| `json` | JavaScript Object Notation | `.json` | `JSONEngine` | Duplicate key detection, JSON schema inference, candidate key discovery |
| `xml` | Extensible Markup Language | `.xml`, `.xsd`, `.xsl` | `XMLEngine` | DefusedXML entity defense, tag statistics, hierarchy extraction |
| `yaml` | YAML Ain't Markup Language | `.yaml`, `.yml` | `YAMLEngine` | `yaml.safe_load`, anchor/alias density inspection, Billion Laughs defense |
| `toml` | Tom's Obvious Minimal Language | `.toml` | `TOMLEngine` | Python 3.11+ `tomllib`, table breakdown, scalar typing |
| `parquet` | Apache Parquet | `.parquet`, `.pq` | `ParquetEngine` | PyArrow zero-dataframe profiling, column statistics, bounded 50-row batching |

---

## Zero-Dataframe Bounded Profiling

DocuMind AI guarantees memory safety on multi-gigabyte Parquet datasets by leveraging `pyarrow.parquet.ParquetFile`:
- File schema and column types are read directly from Parquet metadata footers.
- Column statistics (`null_count`, `min_value`, `max_value`, `distinct_count`) are aggregated directly from row groups without loading data into RAM.
- Sample previews are extracted via bounded batch streaming (`next(pf.iter_batches(batch_size=50))`), ensuring memory consumption stays under 200 KB regardless of file size.
