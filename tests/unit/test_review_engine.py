"""Unit tests for the dashboard review engine."""

from pathlib import Path

import openpyxl

from excelpilot.review.engine import DashboardReviewEngine


def test_review_flat_workbook_without_dashboard(tmp_path: Path) -> None:
    path = tmp_path / "raw_dump.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Sheet1"
    ws.append(["A", "B", "Unformatted"])
    # Add raw unformatted float decimals
    for _ in range(10):
        ws.append([1, 2, 12345.678912345])
    wb.save(str(path))
    wb.close()

    engine = DashboardReviewEngine()
    report = engine.review(path)

    assert report.review_score < 90.0
    assert not report.has_dashboard_sheet
    categories = {f.category for f in report.findings}
    assert "SHEET_ARCHITECTURE" in categories
    assert "NUMBER_FORMATTING" in categories


def test_review_generated_dashboard(sales_workbook_path: Path, tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from excelpilot.cli.app import app
    from excelpilot.config.loader import ConfigLoader

    runner = CliRunner()
    cfg_file = tmp_path / "excelpilot.yaml"
    ConfigLoader.create_example_config(cfg_file)
    dash_out = tmp_path / "generated_dash.xlsx"

    runner.invoke(
        app,
        ["build", str(sales_workbook_path), "--config", str(cfg_file), "--output", str(dash_out)],
    )
    assert dash_out.exists()

    engine = DashboardReviewEngine()
    report = engine.review(dash_out)

    assert report.has_dashboard_sheet
    assert report.review_score >= 85.0
