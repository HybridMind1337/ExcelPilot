"""Data models for workbook batch consolidation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileContribution:
    """Metadata for a single file consolidated into the master dataset."""

    file_path: Path
    sheet_name: str
    rows_contributed: int
    column_count: int


@dataclass(frozen=True)
class ConsolidationReport:
    """Comprehensive audit report for batch workbook consolidation."""

    total_files_processed: int
    total_rows_consolidated: int
    total_columns: int
    output_path: Path | None
    contributions: list[FileContribution]
    schema_discrepancies: list[str]
