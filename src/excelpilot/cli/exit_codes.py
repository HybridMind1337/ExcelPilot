"""Standard exit codes for ExcelPilot CLI."""

from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_INPUT = 2
    CONFIGURATION_ERROR = 3
    WORKBOOK_ERROR = 4
    ANALYSIS_ERROR = 5
    OUTPUT_ERROR = 6
