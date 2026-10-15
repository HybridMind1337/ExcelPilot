"""Unit tests for ConsolidationEngine."""

from pathlib import Path

import openpyxl
import pytest

from excelpilot.batch.engine import ConsolidationEngine


def _create_sample_file(path: Path, sheet_name: str, rows: list[list]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = sheet_name
    for r in rows:
        ws.append(r)
    wb.save(str(path))
    wb.close()
    return path


def test_consolidation_matching_schemas(tmp_path: Path) -> None:
    f1 = _create_sample_file(
        tmp_path / "north.xlsx",
        "Data",
        [["ID", "Region", "Amount"], [1, "North", 100], [2, "North", 150]],
    )
    f2 = _create_sample_file(
        tmp_path / "south.xlsx",
        "Data",
        [["ID", "Region", "Amount"], [3, "South", 200], [4, "South", 250]],
    )

    engine = ConsolidationEngine(add_source_column=True)
    out_file = tmp_path / "consolidated.xlsx"
    dataset, report = engine.consolidate_files([f1, f2], sheet_name="Data", output_path=out_file)

    assert report.total_files_processed == 2
    assert report.total_rows_consolidated == 4
    assert "_source_file" in dataset.dataframe.columns
    assert len(report.schema_discrepancies) == 0
    assert out_file.is_file()


def test_consolidation_schema_discrepancy(tmp_path: Path) -> None:
    f1 = _create_sample_file(
        tmp_path / "file1.xlsx",
        "Sheet1",
        [["ID", "Name"], [1, "Alice"]],
    )
    f2 = _create_sample_file(
        tmp_path / "file2.xlsx",
        "Sheet1",
        [["ID", "Age", "Country"], [2, 30, "UK"]],
    )

    engine = ConsolidationEngine(add_source_column=False)
    dataset, report = engine.consolidate_files([f1, f2])

    assert report.total_files_processed == 2
    assert report.total_rows_consolidated == 2
    assert len(report.schema_discrepancies) > 0
    assert "_source_file" not in dataset.dataframe.columns
    assert "Age" in dataset.dataframe.columns
    assert "Name" in dataset.dataframe.columns


def test_consolidation_empty_file_list() -> None:
    engine = ConsolidationEngine()
    with pytest.raises(ValueError, match="No files provided"):
        engine.consolidate_files([])


def test_consolidation_all_invalid_files(tmp_path: Path) -> None:
    engine = ConsolidationEngine()
    non_existent = tmp_path / "does_not_exist.xlsx"
    with pytest.raises(ValueError, match="No valid datasets"):
        engine.consolidate_files([non_existent])
