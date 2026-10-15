"""Concrete implementation of WorkbookReader using openpyxl and Polars."""

import logging
import zipfile
from pathlib import Path
from typing import Any

import openpyxl
import polars as pl
from openpyxl.utils.exceptions import InvalidFileException

from excelpilot.exceptions.base import WorkbookError, WorksheetNotFoundError
from excelpilot.workbook.models import WorkbookMetadata, WorksheetMetadata
from excelpilot.workbook.protocol import WorkbookReader

logger = logging.getLogger(__name__)


class OpenpyxlReader(WorkbookReader):
    """Excel workbook reader backed by openpyxl with read-only streaming."""

    def inspect(self, path: Path) -> WorkbookMetadata:
        """Inspect workbook structure and sheet properties."""
        if not path.exists():
            raise WorkbookError(path=path, reason="File does not exist.")
        if not path.is_file():
            raise WorkbookError(path=path, reason="Path is not a regular file.")

        file_size = path.stat().st_size
        try:
            wb = openpyxl.load_workbook(filename=str(path), read_only=True, data_only=True)
        except (InvalidFileException, zipfile.BadZipFile) as err:
            raise WorkbookError(
                path=path,
                reason="The file is corrupted or not a valid Excel (.xlsx) workbook.",
            ) from err
        except Exception as err:
            raise WorkbookError(path=path, reason=f"Failed to open workbook: {err}") from err

        try:
            sheet_names = wb.sheetnames
            sheets: list[WorksheetMetadata] = []
            active_name = wb.active.title if wb.active is not None else None

            for name in sheet_names:
                ws = wb[name]
                max_r = ws.max_row or 0
                max_c = ws.max_column or 0
                is_empty = max_r == 0 or max_c == 0

                header_preview: list[str] = []
                if not is_empty:
                    # Read the first non-empty row as header preview
                    for row in ws.iter_rows(max_row=5, values_only=True):
                        non_null = [str(c).strip() for c in row if c is not None and str(c).strip()]
                        if non_null:
                            header_preview = non_null
                            break

                sheets.append(
                    WorksheetMetadata(
                        name=name,
                        max_row=max_r,
                        max_column=max_c,
                        is_empty=is_empty or len(header_preview) == 0,
                        header_preview=header_preview,
                    )
                )

            return WorkbookMetadata(
                path=path.resolve(),
                file_size_bytes=file_size,
                sheet_names=sheet_names,
                sheets=sheets,
                active_sheet_name=active_name,
            )
        finally:
            wb.close()

    def inspect_worksheet(self, path: Path, sheet_name: str) -> WorksheetMetadata:
        """Inspect a single sheet from a workbook."""
        meta = self.inspect(path)
        for s in meta.sheets:
            if s.name == sheet_name:
                return s
        raise WorksheetNotFoundError(
            path=path, sheet_name=sheet_name, available_sheets=meta.sheet_names
        )

    def read_worksheet(
        self,
        path: Path,
        sheet_name: str,
        max_rows: int | None = None,
    ) -> pl.DataFrame:
        """Read a worksheet into a Polars DataFrame with cleaned headers and typed rows."""
        if not path.exists():
            raise WorkbookError(path=path, reason="File does not exist.")

        try:
            wb = openpyxl.load_workbook(filename=str(path), read_only=True, data_only=True)
        except (InvalidFileException, zipfile.BadZipFile) as err:
            raise WorkbookError(
                path=path,
                reason="The file is corrupted or not a valid Excel (.xlsx) workbook.",
            ) from err
        except Exception as err:
            raise WorkbookError(path=path, reason=f"Failed to open workbook: {err}") from err

        try:
            if sheet_name not in wb.sheetnames:
                raise WorksheetNotFoundError(
                    path=path,
                    sheet_name=sheet_name,
                    available_sheets=wb.sheetnames,
                )

            ws = wb[sheet_name]
            row_iter = ws.iter_rows(values_only=True)

            # Find first non-empty row for header
            header_row: tuple[Any, ...] | None = None
            for row in row_iter:
                if any(cell is not None and str(cell).strip() != "" for cell in row):
                    header_row = row
                    break

            if header_row is None:
                # Completely empty worksheet
                return pl.DataFrame()

            # Determine column names and effective width
            raw_columns = list(header_row)
            # Find the last column index that has a non-null header or data
            last_idx = len(raw_columns) - 1
            while last_idx >= 0 and (
                raw_columns[last_idx] is None or str(raw_columns[last_idx]).strip() == ""
            ):
                last_idx -= 1

            if last_idx < 0:
                return pl.DataFrame()

            width = last_idx + 1
            column_names: list[str] = []
            seen_names: dict[str, int] = {}

            for idx in range(width):
                val = raw_columns[idx]
                col_name = (
                    str(val).strip()
                    if val is not None and str(val).strip()
                    else f"Column_{idx + 1}"
                )
                if col_name in seen_names:
                    seen_names[col_name] += 1
                    col_name = f"{col_name}_{seen_names[col_name]}"
                else:
                    seen_names[col_name] = 1
                column_names.append(col_name)

            data_rows: list[list[Any]] = []
            row_count = 0

            for row in row_iter:
                # Check if row has any non-blank value
                sliced = (
                    list(row[:width])
                    if len(row) >= width
                    else list(row) + [None] * (width - len(row))
                )
                if any(c is not None and str(c).strip() != "" for c in sliced):
                    data_rows.append(sliced)
                    row_count += 1
                    if max_rows is not None and row_count >= max_rows:
                        break

            if not data_rows:
                # Only header was found, return empty DataFrame with schema
                return pl.DataFrame(schema=column_names)

            # Build polars DataFrame
            # Construct a dictionary of lists for columnar construction
            col_data: dict[str, list[Any]] = {name: [] for name in column_names}
            for r in data_rows:
                for idx, name in enumerate(column_names):
                    col_data[name].append(r[idx])

            df = pl.DataFrame(col_data, strict=False)
            return df
        finally:
            wb.close()
