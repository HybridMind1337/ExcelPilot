"""Domain-specific exception hierarchy for ExcelPilot."""

from pathlib import Path


class ExcelPilotError(Exception):
    """Base exception for all domain errors within ExcelPilot."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class WorkbookError(ExcelPilotError):
    """Raised when an Excel workbook cannot be located, opened, or parsed."""

    def __init__(self, path: Path, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Workbook error for '{path}': {reason}")


class WorksheetNotFoundError(WorkbookError):
    """Raised when a requested worksheet does not exist in the workbook."""

    def __init__(self, path: Path, sheet_name: str, available_sheets: list[str]) -> None:
        self.sheet_name = sheet_name
        self.available_sheets = available_sheets
        avail_str = ", ".join(f"'{s}'" for s in available_sheets) if available_sheets else "none"
        super().__init__(
            path=path,
            reason=f"Worksheet '{sheet_name}' was not found. Available worksheets: {avail_str}.",
        )


class ConfigurationError(ExcelPilotError):
    """Raised when a configuration file is missing, invalid, or fails schema validation."""


class AnalysisError(ExcelPilotError):
    """Raised when dataset profiling or metric calculation fails."""


class ExpressionSecurityError(AnalysisError):
    """Raised when an unsafe expression or prohibited token is detected in a metric formula."""


class OutputError(ExcelPilotError):
    """Raised when an output file or dashboard workbook cannot be generated or written."""
