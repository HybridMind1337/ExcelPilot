# ExcelPilot Architecture

ExcelPilot is designed as a modular, decoupled command-line application and Python library for spreadsheet intelligence and reporting automation.

## Core Design Principles

- **Separation of Concerns**: Workbook reading, statistical profiling, semantic inference, quality auditing, metric calculations, and workbook generation are isolated behind typed protocols.
- **Pure Domain Operations**: Analysis engines operate on immutable domain models without coupling to terminal output or physical files.
- **Polars Data Engine**: High-performance columnar processing leveraging Rust kernels and Apache Arrow.
- **DuckDB Analytical SQL**: Embedded columnar relational engine used for complex grouping and period-over-period delta computations.
- **Safe Evaluation**: Custom formula expressions are parsed into an Abstract Syntax Tree (AST) whitelist to prevent arbitrary Python code execution.
- **Non-Destructive Workflows**: Original source workbooks are never modified. Generated reports are written to new destination files.

## Subsystems

### 1. Workbook Ingestion (`excelpilot.workbook`)
- `WorkbookReader` protocol defines inspection and extraction contracts.
- `OpenpyxlReader` implements read-only streaming to discover sheets, dimensions, and extract tabular datasets without loading unneeded cell formats.

### 2. Dataset Abstraction (`excelpilot.core`)
- Wraps `polars.DataFrame` with zero-copy Arrow interchange.
- Provides embedded DuckDB query execution.

### 3. Profiling & Semantics (`excelpilot.profiling`, `excelpilot.semantics`)
- Single-pass statistical profiling.
- Heuristic and pattern-based semantic classifier determining column roles (`CURRENCY`, `TEMPORAL`, `IDENTIFIER`, `CATEGORICAL`, etc.) with calibrated confidence scores.

### 4. Data Quality Engine (`excelpilot.quality`)
- Multi-dimensional quality scoring across Completeness, Validity, Uniqueness, and Consistency.

### 5. Metric & Recommendation Engines (`excelpilot.metrics`, `excelpilot.recommendations`)
- AST mathematical parser for user-defined calculated metrics (`Revenue - Cost`).
- Rule-based KPI and visual chart recommender mapping data cardinality and temporal semantics to appropriate visual charts.

### 6. Excel Exporter (`excelpilot.exporters`)
- Built on `xlsxwriter` for fast, deterministic workbook emission.
- Emits multi-sheet deliverables (`Dashboard`, `Analysis`, `Data_Quality`, `Cleaned_Data`, `Raw_Data`, `Metadata`).
- Hardened against CSV/Excel formula injection (DDE attacks).

### 7. CLI & Wizard (`excelpilot.cli`)
- Built on `typer`, `rich`, and `prompt_toolkit`.
- Strict standard exit codes (`0` to `6`).
