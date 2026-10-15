"""Integration tests for ExcelPilot CLI commands and exit codes."""

from pathlib import Path

from typer.testing import CliRunner

from excelpilot.cli.app import app
from excelpilot.cli.exit_codes import ExitCode
from excelpilot.config.loader import ConfigLoader

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == ExitCode.SUCCESS
    assert "ExcelPilot 0.1.0" in result.stdout


def test_cli_inspect(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["inspect", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Sales" in result.stdout


def test_cli_inspect_invalid_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inspect", str(tmp_path / "missing.xlsx")])
    assert result.exit_code == ExitCode.WORKBOOK_ERROR


def test_cli_analyze(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["analyze", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Revenue" in result.stdout
    assert "CURRENCY" in result.stdout


def test_cli_quality(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["quality", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Data Quality Report" in result.stdout
    assert "Overall Quality Score" in result.stdout


def test_cli_init_and_validate(tmp_path: Path) -> None:
    config_file = tmp_path / "excelpilot.yaml"
    init_res = runner.invoke(app, ["init", "--path", str(config_file)])
    assert init_res.exit_code == ExitCode.SUCCESS
    assert config_file.exists()

    val_res = runner.invoke(app, ["validate-config", str(config_file)])
    assert val_res.exit_code == ExitCode.SUCCESS
    assert "Valid configuration" in val_res.stdout


def test_cli_build(sales_workbook_path: Path, tmp_path: Path) -> None:
    config_file = tmp_path / "excelpilot.yaml"
    ConfigLoader.create_example_config(config_file)
    output_dashboard = tmp_path / "sales_report.xlsx"

    build_res = runner.invoke(
        app,
        [
            "build",
            str(sales_workbook_path),
            "--config",
            str(config_file),
            "--output",
            str(output_dashboard),
        ],
    )
    assert build_res.exit_code == ExitCode.SUCCESS
    assert output_dashboard.exists()
    assert output_dashboard.stat().st_size > 0


def test_cli_suggest(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["suggest", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Recommended KPIs" in result.stdout
    assert "Recommended Visualisations" in result.stdout


def test_cli_clean(sales_workbook_path: Path, tmp_path: Path) -> None:
    cleaned_out = tmp_path / "cleaned_sales.xlsx"
    result = runner.invoke(app, ["clean", str(sales_workbook_path), "--output", str(cleaned_out)])
    assert result.exit_code == ExitCode.SUCCESS
    assert cleaned_out.exists()
    assert "Data Cleaning Audit" in result.stdout


def test_cli_compare(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["compare", str(sales_workbook_path), str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Period Variance Analysis" in result.stdout
    assert "Metric Variances" in result.stdout


def test_cli_review(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["review", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Dashboard Review" in result.stdout


def test_cli_anomalies(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["anomalies", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Statistical Anomaly Audit" in result.stdout
    assert "Column Outlier Summaries" in result.stdout


def test_cli_forecast(sales_workbook_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "forecast",
            str(sales_workbook_path),
            "--date-col",
            "OrderDate",
            "--metric",
            "Revenue",
            "--periods",
            "3",
        ],
    )
    assert result.exit_code == ExitCode.SUCCESS
    assert "Time-Series Trend & Forecasting" in result.stdout
    assert "Forward Projection" in result.stdout


def test_cli_export_html(sales_workbook_path: Path, tmp_path: Path) -> None:
    html_out = tmp_path / "dashboard.html"
    result = runner.invoke(
        app,
        ["export-html", str(sales_workbook_path), "--output", str(html_out)],
    )
    assert result.exit_code == ExitCode.SUCCESS
    assert html_out.exists()
    assert html_out.stat().st_size > 0
    assert "Standalone HTML dashboard generated" in result.stdout


def test_cli_query(sales_workbook_path: Path, tmp_path: Path) -> None:
    csv_out = tmp_path / "query_res.csv"
    result = runner.invoke(
        app,
        [
            "query",
            str(sales_workbook_path),
            "SELECT Region, SUM(Revenue) AS TotalRev FROM data GROUP BY Region",
            "--output",
            str(csv_out),
        ],
    )
    assert result.exit_code == ExitCode.SUCCESS
    assert "SQL Query Result" in result.stdout
    assert csv_out.exists()


def test_cli_consolidate(sales_workbook_path: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "consolidated_master.xlsx"
    result = runner.invoke(
        app,
        [
            "consolidate",
            str(sales_workbook_path),
            "--output",
            str(out_file),
        ],
    )
    assert result.exit_code == ExitCode.SUCCESS
    assert "Multi-Workbook Consolidation Audit" in result.stdout
    assert out_file.exists()


def test_cli_catalog(sales_workbook_path: Path, tmp_path: Path) -> None:
    md_out = tmp_path / "dictionary.md"
    result = runner.invoke(
        app,
        [
            "catalog",
            str(sales_workbook_path),
            "--output",
            str(md_out),
        ],
    )
    assert result.exit_code == ExitCode.SUCCESS
    assert "Data Dictionary Catalog" in result.stdout
    assert md_out.exists()


def test_cli_audit_security(sales_workbook_path: Path) -> None:
    result = runner.invoke(app, ["audit-security", str(sales_workbook_path)])
    assert result.exit_code == ExitCode.SUCCESS
    assert "Security & Privacy Audit" in result.stdout
