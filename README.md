# ExcelPilot

[![CI](https://github.com/HybridMind1337/ExcelPilot/actions/workflows/ci.yml/badge.svg)](https://github.com/HybridMind1337/ExcelPilot/actions/workflows/ci.yml)
[![Release](https://github.com/HybridMind1337/ExcelPilot/actions/workflows/release.yml/badge.svg)](https://github.com/HybridMind1337/ExcelPilot/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/excelpilot/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://github.com/python/mypy)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker)](https://github.com/HybridMind1337/ExcelPilot/pkgs/container/excelpilot)

Analyse Excel data and build professional dashboards from the command line.

ExcelPilot is a command-line tool and Python library for profiling Excel workbooks, auditing data quality, calculating business metrics, recommending visualisations, and generating formatted Excel dashboards.

## Features

- **Workbook Inspection**: Discovers worksheets, dimensions, defined names, and cell types without modifying source files.
- **Dataset Profiling**: Calculates column statistics, cardinality, null proportions, value distributions, and quantiles.
- **Semantic Type Classification**: Infers semantic types (Currency, Percentage, Identifier, Categorical, Temporal, Email, Phone, URL) using rule-based heuristics and value distributions.
- **Data Quality Auditing**: Assesses completeness, validity, uniqueness, and consistency, assigning an overall quality score and categorising issues by severity.
- **Statistical Anomaly Detection**: Identifies numerical outliers using Interquartile Range (IQR) and Z-score statistical bounds.
- **Time-Series Forecasting**: Evaluates linear regression trends, compound growth rates, and projects forward confidence intervals.
- **Automated Data Cleaning**: Trims whitespace, deduplicates rows, normalises column names, and applies deterministic null-handling strategies.
- **Period & Workbook Comparison**: Variance analysis computing baseline vs comparison deltas and dimensional changes.
- **Dashboard Review Engine**: Evaluates existing workbooks against corporate BI layout guidelines, rating visual density and sheet structure.
- **Excel & HTML Dashboard Generation**: Emits structured `.xlsx` workbooks with native charts and standalone, responsive `.html` dashboards with vector SVG visualisations.
- **Interactive Wizard**: Terminal wizard for exploratory inspection and guided dashboard design.
- **Docker-Ready**: Multi-stage Docker container supporting non-root execution and interactive terminal operation.

## Installation

### Using uv

```bash
uv pip install excelpilot
```

Or install as a standalone CLI tool:

```bash
uv tool install excelpilot
```

### From Source

```bash
git clone https://github.com/HybridMind1337/ExcelPilot.git
cd ExcelPilot
uv venv
uv pip install -e ".[dev]"
```

## Quick Start

### 1. Inspect a Workbook

Inspect sheet structure and column counts without loading entire datasets into memory:

```bash
excelpilot inspect data/sales.xlsx
```

### 2. Audit Data Quality

Generate a quality report checking completeness, validity, uniqueness, and consistency:

```bash
excelpilot quality data/sales.xlsx --sheet Sales
```

### 3. Interactive Wizard

Launch the guided wizard to profile data, select KPIs and dimensions, and generate a dashboard:

```bash
excelpilot wizard data/sales.xlsx
```

### 4. Detect Statistical Anomalies

Identify numerical outliers and distribution anomalies using IQR or Z-score:

```bash
excelpilot anomalies data/sales.xlsx --sheet Sales --method iqr
```

### 5. Time-Series Forecasting

Evaluate trend direction, growth rate, and project forward confidence intervals:

```bash
excelpilot forecast data/sales.xlsx --date-col OrderDate --metric Revenue --periods 3
```

### 6. Clean Dataset

Strip whitespace, drop duplicates, and normalise column names:

```bash
excelpilot clean data/sales.xlsx --output data/sales-clean.xlsx
```

### 7. Export Standalone HTML Dashboard

Generate a responsive, dependency-free HTML dashboard with embedded SVG visualisations:

```bash
excelpilot export-html data/sales.xlsx --output reports/sales-dashboard.html
```

### 8. Compare Workbooks & Reporting Periods

Calculate metric variances and dimensional breakdown deltas between two workbooks:

```bash
excelpilot compare data/sales_q1.xlsx data/sales_q2.xlsx
```

### 9. Review Dashboard Quality

Audit an existing Excel dashboard against corporate BI layout guidelines:

```bash
excelpilot review reports/sales-dashboard.xlsx
```

### 10. Build from Configuration

Build a dashboard non-interactively using a declarative YAML configuration:

```bash
excelpilot build data/sales.xlsx --config excelpilot.yaml --output reports/sales-dashboard.xlsx
```

### Shell Autocompletion

Enable tab completion for bash, zsh, fish, or PowerShell:

```bash
excelpilot --install-completion
```

## Docker Usage

ExcelPilot provides a lightweight, non-root Docker container.

### Build the Image

```bash
docker build -t excelpilot .
```

### Run Commands

```bash
docker run --rm \
    -v "$(pwd)/data:/data" \
    excelpilot quality /data/sales.xlsx
```

### Run the Interactive Wizard

```bash
docker run --rm -it \
    -v "$(pwd)/data:/data" \
    excelpilot wizard /data/sales.xlsx
```

## Project Configuration

ExcelPilot projects can be automated using an `excelpilot.yaml` configuration file:

```yaml
project:
  name: northstar-retail
  version: "1.0"

source:
  worksheet: Orders

metrics:
  total_revenue:
    column: Revenue
    aggregation: sum
  order_count:
    column: OrderID
    aggregation: count_distinct
  profit_margin:
    formula: (Revenue - Cost) / Revenue * 100

dimensions:
  - Region
  - Channel
  - Category

time:
  column: OrderDate
  granularity: month

dashboard:
  title: Retail Performance Dashboard
  theme: executive
  currency: GBP

output:
  path: reports/retail-dashboard.xlsx
```

## Exit Codes

ExcelPilot uses standard exit codes for automated environments:

- `0`: Success
- `1`: General application error
- `2`: Invalid command-line arguments
- `3`: Configuration error
- `4`: Workbook read error
- `5`: Analysis error
- `6`: Output write error

## Development

Run tests, linting, and type checking:

```bash
# Run test suite
uv run pytest

# Check code formatting and linting
uv run ruff check .
uv run ruff format --check .

# Type checking
uv run mypy src
```

## Licence

ExcelPilot is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
