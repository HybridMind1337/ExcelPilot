"""Unit tests for WorkbookReader and OpenpyxlReader."""

from pathlib import Path

import pytest

from excelpilot.exceptions.base import WorkbookError, WorksheetNotFoundError
from excelpilot.workbook.reader import OpenpyxlReader


def test_inspect_valid_workbook(sales_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    metadata = reader.inspect(sales_workbook_path)

    assert metadata.path.name == "sales.xlsx"
    assert "Sales" in metadata.sheet_names
    assert len(metadata.sheets) == 1
    assert metadata.sheets[0].name == "Sales"
    assert metadata.sheets[0].max_row >= 150
    assert metadata.sheets[0].max_column == 12
    assert not metadata.sheets[0].is_empty


def test_inspect_nonexistent_workbook(tmp_path: Path) -> None:
    reader = OpenpyxlReader()
    with pytest.raises(WorkbookError, match="does not exist"):
        reader.inspect(tmp_path / "does_not_exist.xlsx")


def test_inspect_corrupted_workbook(corrupt_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    with pytest.raises(WorkbookError, match="corrupted or not a valid Excel"):
        reader.inspect(corrupt_workbook_path)


def test_read_valid_worksheet(sales_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    df = reader.read_worksheet(sales_workbook_path, "Sales")

    assert df.height == 150
    assert df.width == 12
    assert "Revenue" in df.columns
    assert "OrderID" in df.columns


def test_read_nonexistent_worksheet(sales_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    with pytest.raises(WorksheetNotFoundError, match="Worksheet 'NonExistent' was not found"):
        reader.read_worksheet(sales_workbook_path, "NonExistent")


def test_read_empty_worksheet(empty_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    df = reader.read_worksheet(empty_workbook_path, "EmptySheet")
    assert df.is_empty()
