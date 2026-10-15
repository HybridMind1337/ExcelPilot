# Contributing to ExcelPilot

Thank you for your interest in contributing to ExcelPilot.

## Development Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12
- `uv` (recommended) or `pip`
- Git

### Initialising the Environment

```bash
git clone https://github.com/HybridMind1337/ExcelPilot.git
cd ExcelPilot
uv venv
uv pip install -e ".[dev]"
```

### Pre-commit Hooks

Install pre-commit hooks to automate formatting and linting:

```bash
uv run pre-commit install
```

## Quality Standards

All pull requests must satisfy the following checks:

1. **Linting and Formatting**:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   ```

2. **Static Type Checking**:
   ```bash
   uv run mypy src
   ```

3. **Automated Tests and Coverage**:
   ```bash
   uv run pytest
   ```
   Code coverage must remain above 80%.

4. **Code Design**:
   - Write strongly typed Python with complete type hints.
   - Do not use arbitrary string-keyed untyped dictionaries when domain models or Pydantic classes are suitable.
   - Never write emojis in CLI output, documentation, or code comments.
   - Keep business logic decoupled from Excel rendering and CLI formatting.
   - Write unit tests for all new calculations and edge cases.

## Commit Guidelines

Use standard conventional commit prefixes:
- `feat:` new user-facing functionality
- `fix:` bug fixes
- `refactor:` code restructuring without changing behaviour
- `test:` adding or updating tests
- `docs:` documentation updates
- `chore:` build, configuration, or dependency updates
