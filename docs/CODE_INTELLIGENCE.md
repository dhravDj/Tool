# DocuMind AI — Code Intelligence Engine

## Overview

The Code Intelligence Engine provides multi-language static code parsing, symbol extraction, import dependency analysis, static diagnostics, code complexity metrics, and multi-format exports across 14 programming languages.

---

## Supported Programming Languages

| Format ID | Language | Standard Extensions | Parser Implementation | Capabilities |
|:---:|:---:|:---:|:---:|---|
| `py` | Python | `.py`, `.pyi` | `PythonParser` (`ast`) | AST parsing, docstrings, classes, functions, typing, bare except, secrets |
| `js` | JavaScript | `.js`, `.mjs`, `.cjs` | `JavaScriptTypeScriptParser` | Classes, functions, arrow functions, CommonJS/ESM, debugger detection |
| `ts` | TypeScript | `.ts`, `.mts`, `.cts` | `JavaScriptTypeScriptParser` | Interfaces, types, enums, classes, decorators, imports |
| `jsx` | React JSX | `.jsx` | `JavaScriptTypeScriptParser` | React components, JSX nodes, hooks |
| `tsx` | React TSX | `.tsx` | `JavaScriptTypeScriptParser` | Typed React components, props interfaces |
| `html` | HTML5 | `.html`, `.htm` | `HTMLParser` | Document structure, tags, scripts, stylesheets, inline script warnings |
| `css` | CSS3 | `.css` | `CSSParser` | Rules, selectors, media queries, keyframe animations |
| `java` | Java | `.java` | `JavaParser` | Packages, imports, classes, interfaces, records, methods |
| `c` | C | `.c`, `.h` | `CCppParser` | Includes (system vs local), structs, functions, legacy unsafe C functions |
| `cpp` | C++ | `.cpp`, `.hpp`, `.cc`, `.cxx` | `CCppParser` | Classes, namespaces, templates, methods |
| `go` | Go | `.go` | `GoParser` | Packages, imports, structs, interfaces, methods, functions |
| `rs` | Rust | `.rs` | `RustParser` | Modules, use crates, structs, enums, traits, unsafe blocks |
| `php` | PHP | `.php`, `.phtml` | `PHPParser` | Namespaces, classes, functions, dangerous function alerts |
| `sql` | SQL | `.sql` | `SQLParser` (`sqlglot`) | DDL tables, column types, foreign key relationships, queries |

---

## Architectural Components

1. **`BaseLanguageParser` (`backend/app/modules/code_intelligence/parsers/base.py`):**
   Standard contract implemented by all language parsers.
2. **`LanguageParserRegistry` (`backend/app/modules/code_intelligence/parsers/registry.py`):**
   Dispatches files by language ID or filename extension.
3. **`CodeIntelligencePipeline` (`backend/app/modules/code_intelligence/pipeline.py`):**
   Orchestrates parsing, database persistence into `CodeAnalysisRecord`, and storage artifact generation.
4. **Export Generators (`backend/app/modules/code_intelligence/generators/`):**
   - `CodeJSONGenerator`: Canonical JSON document serialization.
   - `CodeMarkdownGenerator`: Detailed human-readable intelligence report.
   - `CodePlainTextGenerator`: Compact plain-text terminal summary.
