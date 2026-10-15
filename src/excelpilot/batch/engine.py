"""Multi-workbook batch consolidation and merging engine."""

from collections.abc import Sequence
from pathlib import Path

import polars as pl
import xlsxwriter

from excelpilot.batch.models import ConsolidationReport, FileContribution
from excelpilot.core.dataset import Dataset
from excelpilot.exceptions.base import WorkbookError
from excelpilot.workbook.reader import OpenpyxlReader


class ConsolidationEngine:
    """Consolidates multiple Excel files into a unified master dataset."""

    def __init__(self, add_source_column: bool = True) -> None:
        self.add_source_column = add_source_column
        self.reader = OpenpyxlReader()

    def consolidate_files(
        self,
        files: Sequence[Path],
        sheet_name: str | None = None,
        output_path: Path | None = None,
    ) -> tuple[Dataset, ConsolidationReport]:
        """Read and concatenate rows from multiple Excel workbooks."""
        if not files:
            raise ValueError("No files provided for consolidation.")

        dataframes: list[pl.DataFrame] = []
        contributions: list[FileContribution] = []
        discrepancies: list[str] = []
        base_columns: set[str] | None = None

        for path in files:
            if not path.is_file():
                continue

            try:
                meta = self.reader.inspect(path)
                target_sheet = sheet_name or meta.sheet_names[0]
                df = self.reader.read_worksheet(path, target_sheet)
            except WorkbookError as err:
                discrepancies.append(f"Failed to read '{path.name}': {err.message}")
                continue

            cols_set = set(df.columns)
            if base_columns is None:
                base_columns = cols_set
            else:
                missing_in_current = base_columns - cols_set
                extra_in_current = cols_set - base_columns
                if missing_in_current:
                    discrepancies.append(
                        f"'{path.name}' is missing columns: {sorted(missing_in_current)}"
                    )
                if extra_in_current:
                    discrepancies.append(
                        f"'{path.name}' introduces extra columns: {sorted(extra_in_current)}"
                    )

            if self.add_source_column:
                df = df.with_columns(pl.lit(path.name).alias("_source_file"))

            dataframes.append(df)
            contributions.append(
                FileContribution(
                    file_path=path,
                    sheet_name=target_sheet,
                    rows_contributed=df.height,
                    column_count=df.width,
                )
            )

        if not dataframes:
            raise ValueError("No valid datasets could be read from the provided files.")

        # Diagonal concatenation handles varying columns smoothly
        merged_df = pl.concat(dataframes, how="diagonal")
        master_dataset = Dataset(merged_df, name="Consolidated_Master")

        report = ConsolidationReport(
            total_files_processed=len(contributions),
            total_rows_consolidated=merged_df.height,
            total_columns=merged_df.width,
            output_path=output_path,
            contributions=contributions,
            schema_discrepancies=discrepancies,
        )

        if output_path:
            self._write_master_workbook(merged_df, output_path)

        return master_dataset, report

    @staticmethod
    def _write_master_workbook(df: pl.DataFrame, output_path: Path) -> None:
        """Write consolidated DataFrame to target Excel workbook."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb = xlsxwriter.Workbook(str(output_path))
        ws = wb.add_worksheet("Consolidated_Data")

        fmt_hdr = wb.add_format(
            {"bold": True, "bg_color": "#1E3A8A", "font_color": "#FFFFFF", "border": 1}
        )
        fmt_txt = wb.add_format({"border": 1, "font_name": "Segoe UI", "font_size": 10})
        fmt_num = wb.add_format(
            {"border": 1, "font_name": "Segoe UI", "font_size": 10, "num_format": "#,##0.00"}
        )

        cols = df.columns
        for c_idx, col in enumerate(cols):
            ws.write(0, c_idx, col, fmt_hdr)

        for r_idx, row in enumerate(df.iter_rows()):
            for c_idx, val in enumerate(row):
                if val is None:
                    ws.write_blank(r_idx + 1, c_idx, None, fmt_txt)
                elif isinstance(val, (int, float)):
                    ws.write_number(r_idx + 1, c_idx, float(val), fmt_num)
                else:
                    ws.write_string(r_idx + 1, c_idx, str(val), fmt_txt)

        ws.autofilter(0, 0, df.height, len(cols) - 1)
        for c_idx, col_name in enumerate(cols):
            ws.set_column(c_idx, c_idx, max(12, min(len(col_name) + 4, 30)))

        wb.close()
