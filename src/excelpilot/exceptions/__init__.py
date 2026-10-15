"""Exception classes for ExcelPilot."""

from excelpilot.exceptions.base import (
    AnalysisError,
    ConfigurationError,
    ExcelPilotError,
    ExpressionSecurityError,
    OutputError,
    WorkbookError,
    WorksheetNotFoundError,
)

__all__ = [
    "AnalysisError",
    "ConfigurationError",
    "ExcelPilotError",
    "ExpressionSecurityError",
    "OutputError",
    "WorkbookError",
    "WorksheetNotFoundError",
]
