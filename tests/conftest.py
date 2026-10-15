"""Global pytest fixtures and test configuration."""

from pathlib import Path

import pytest

from excelpilot.core.dataset import Dataset
from excelpilot.workbook.reader import OpenpyxlReader
from tests.fixtures.synthetic_workbooks import (
    create_empty_worksheet_workbook,
    create_synthetic_quality_issue_workbook,
    create_synthetic_sales_workbook,
)


@pytest.fixture
def sales_workbook_path(tmp_path: Path) -> Path:
    """Fixture providing a realistic sales workbook."""
    return create_synthetic_sales_workbook(tmp_path / "sales.xlsx")


@pytest.fixture
def quality_workbook_path(tmp_path: Path) -> Path:
    """Fixture providing a workbook with deliberate data quality anomalies."""
    return create_synthetic_quality_issue_workbook(tmp_path / "quality_issues.xlsx")


@pytest.fixture
def empty_workbook_path(tmp_path: Path) -> Path:
    """Fixture providing a workbook with an empty sheet."""
    return create_empty_worksheet_workbook(tmp_path / "empty.xlsx")


@pytest.fixture
def corrupt_workbook_path(tmp_path: Path) -> Path:
    """Fixture providing a corrupted non-zip file with an .xlsx extension."""
    file_path = tmp_path / "corrupt.xlsx"
    file_path.write_bytes(b"NOT_A_VALID_ZIP_OR_EXCEL_STREAM")
    return file_path


@pytest.fixture
def sales_dataset(sales_workbook_path: Path) -> Dataset:
    """Fixture providing an ingested sales Dataset instance."""
    reader = OpenpyxlReader()
    df = reader.read_worksheet(sales_workbook_path, "Sales")
    return Dataset(df, name="Sales")
