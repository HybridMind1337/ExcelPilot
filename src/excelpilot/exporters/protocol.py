"""Protocol for rendering dashboard specifications to physical output files."""

from pathlib import Path
from typing import Protocol

import polars as pl

from excelpilot.dashboards.models import DashboardSpecification


class DashboardExporter(Protocol):
    """Protocol for exporting a DashboardSpecification and underlying dataset to disk."""

    def export(
        self,
        specification: DashboardSpecification,
        raw_dataframe: pl.DataFrame,
        cleaned_dataframe: pl.DataFrame,
        output_path: Path,
    ) -> Path:
        """Render the dashboard specification and data tables to the specified destination path."""
        ...
