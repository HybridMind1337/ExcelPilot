"""Data models representing workbook structure and metadata."""

from pathlib import Path

from pydantic import BaseModel, Field


class WorksheetMetadata(BaseModel):
    """Metadata for an individual worksheet within an Excel workbook."""

    name: str
    max_row: int = Field(default=0, ge=0)
    max_column: int = Field(default=0, ge=0)
    is_empty: bool = False
    header_preview: list[str] = Field(default_factory=list)


class WorkbookMetadata(BaseModel):
    """High-level inspection metadata for an entire workbook."""

    path: Path
    file_size_bytes: int
    sheet_names: list[str]
    sheets: list[WorksheetMetadata]
    active_sheet_name: str | None = None
