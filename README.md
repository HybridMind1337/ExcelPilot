# ExcelPilot

Analyse Excel data and build professional dashboards from the command line.

ExcelPilot is a command-line tool and Python library for profiling Excel workbooks, auditing data quality, calculating business metrics, recommending visualisations, and generating formatted Excel dashboards.

## Features

- **Workbook Inspection**: Discovers worksheets, dimensions, defined names, and cell types without modifying source files.
- **Dataset Profiling**: Calculates column statistics, cardinality, null proportions, value distributions, and quantiles.
- **Semantic Type Classification**: Infers semantic types (Currency, Percentage, Identifier, Categorical, Temporal, Email, Phone, URL) using rule-based heuristics and value distributions.
- **Data Quality Auditing**: Assesses completeness, validity, uniqueness, and consistency, assigning an overall quality score and categorising issues by severity.
- **KPI and Visualisation Recommendation**: Evaluates schema attributes to suggest meaningful metrics and suitable chart representations.
- **Dashboard Generation**: Emits structured `.xlsx` workbooks featuring KPI summary cards, native charts, reference tables, data quality audits, and cleaned datasets.
- **Interactive Wizard**: Terminal wizard for exploratory inspection and guided dashboard design.
- **Safe Evaluation**: Metric calculations use an Abstract Syntax Tree (AST) mathematical evaluator to prevent unsafe code execution.
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

### 4. Build from Configuration

Build a dashboard using a declarative YAML configuration:

```bash
excelpilot build data/sales.xlsx --config excelpilot.yaml --output reports/sales-dashboard.xlsx
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
