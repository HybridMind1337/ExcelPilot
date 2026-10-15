# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-15

### Added
- Initial project architecture and core domain models.
- Workbook reader protocol supporting openpyxl metadata inspection and streaming sheet ingestion.
- Tabular dataset engine wrapping Polars with DuckDB analytical queries.
- Dataset profiling engine computing cardinality, distribution, null proportions, and quantiles.
- Semantic type classification engine with rule-based heuristics and confidence scoring.
- Four-dimension data quality audit engine (completeness, validity, uniqueness, consistency).
- KPI recommendation and visual chart mapping engine.
- Abstract Syntax Tree (AST) safe mathematical expression evaluator for calculated metrics.
- Multi-sheet executive dashboard renderer generating native Excel charts and KPI scorecards using XlsxWriter.
- Interactive terminal wizard using prompt_toolkit for guided dashboard design.
- CLI commands: `inspect`, `analyze`, `quality`, `wizard`, `build`, `init`, `validate-config`.
- Multi-stage Docker container with non-root security.
