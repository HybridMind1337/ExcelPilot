"""Protocols for reading and inspecting Excel workbooks."""

from pathlib import Path
from typing import Protocol

import polars as pl

from excelpilot.workbook.models import WorkbookMetadata, WorksheetMetadata


class WorkbookReader(Protocol):
    """Protocol defining the contract for inspecting and reading Excel workbooks."""

    def inspect(self, path: Path) -> WorkbookMetadata:
        """Inspect the workbook metadata without loading all cell records into memory."""
        ...

    def inspect_worksheet(self, path: Path, sheet_name: str) -> WorksheetMetadata:
        """Inspect structural properties of a single worksheet."""
        ...

    def read_worksheet(
        self,
        path: Path,
        sheet_name: str,
        max_rows: int | None = None,
    ) -> pl.DataFrame:
        """Read a worksheet into a Polars DataFrame."""
        ...
