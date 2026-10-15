"""Unit tests for privacy scanner, summary generation, and CLI formatters."""

from pathlib import Path

import polars as pl
from rich.console import Console

from excelpilot.analysis.summary import ManagementSummaryGenerator
from excelpilot.cli.formatters import (
    render_dashboard_plan,
    render_workbook_inspection,
)
from excelpilot.core.dataset import Dataset
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.dashboards.themes import get_theme
from excelpilot.metrics.models import MetricResult
from excelpilot.privacy.detector import PrivacyDetector
from excelpilot.recommendations.models import ChartType, RecommendedChart
from excelpilot.semantics.classifier import SemanticClassifier
from excelpilot.workbook.models import WorkbookMetadata, WorksheetMetadata


def test_privacy_detector_detects_pii() -> None:
    df = pl.DataFrame(
        {
            "customer_name": ["Alice Smith", "Bob Jones"],
            "CustomerEmail": ["alice@corp.com", "bob@corp.com"],
            "Phone": ["+44 7700 90001", "+44 7700 90002"],
            "ssn": ["123-45-6789", "987-65-4321"],
            "card_number": ["4111222233334444", "5500111122223333"],
        }
    )
    dataset = Dataset(df, name="sensitive")
    classifier = SemanticClassifier()
    semantics = classifier.classify_dataset(dataset)

    detector = PrivacyDetector()
    report = detector.scan(semantics)

    assert report.has_pii
    assert len(report.risks) >= 3
    risk_types = {r.risk_type for r in report.risks}
    assert "EMAIL" in risk_types
    assert "PERSONAL_NAME" in risk_types or "GOVERNMENT_ID" in risk_types


def test_management_summary_generator() -> None:
    generator = ManagementSummaryGenerator()
    kpis = [
        MetricResult(
            name="total_revenue",
            label="Total Revenue",
            raw_value=50000.0,
            formatted_value="£50,000.00",
            format_type="currency",
        ),
        MetricResult(
            name="total_orders",
            label="Total Orders",
            raw_value=250.0,
            formatted_value="250",
            format_type="integer",
        ),
        MetricResult(
            name="avg_order_value",
            label="Average Order Value",
            raw_value=200.0,
            formatted_value="£200.00",
            format_type="currency",
        ),
        MetricResult(
            name="gross_profit",
            label="Gross Profit",
            raw_value=15000.0,
            formatted_value="£15,000.00",
            format_type="currency",
        ),
        MetricResult(
            name="gross_margin",
            label="Gross Margin",
            raw_value=30.0,
            formatted_value="30.0%",
            format_type="percentage",
        ),
    ]
    bullets = generator.generate(kpis)

    assert len(bullets) >= 2
    assert any("Total Revenue" in b for b in bullets)
    assert any("Average Order Value" in b for b in bullets)


def test_theme_retrieval() -> None:
    exec_theme = get_theme("executive")
    assert exec_theme.name == "executive"
    assert exec_theme.font_name == "Segoe UI"

    fin_theme = get_theme("financial")
    assert fin_theme.name == "financial"
    assert fin_theme.colors.primary == "#064E3B"

    op_theme = get_theme("operational")
    assert op_theme.name == "operational"

    min_theme = get_theme("minimal")
    assert min_theme.name == "minimal"

    unknown_theme = get_theme("non_existent")
    assert unknown_theme.name == "executive"


def test_cli_formatters_rendering() -> None:
    console = Console(record=True)
    meta = WorkbookMetadata(
        path=Path("dummy.xlsx"),
        file_size_bytes=1024,
        sheet_names=["Sheet1"],
        sheets=[
            WorksheetMetadata(
                name="Sheet1", max_row=10, max_column=2, is_empty=False, header_preview=["A", "B"]
            )
        ],
    )
    render_workbook_inspection(meta, console)
    out = console.export_text()
    assert "dummy.xlsx" in out
    assert "Sheet1" in out

    spec = DashboardSpecification(
        title="Test Dash",
        theme="executive",
        kpis=[
            MetricResult(
                name="m", label="Metric", raw_value=1.0, formatted_value="1", format_type="number"
            )
        ],
        charts=[
            RecommendedChart(
                title="C1",
                chart_type=ChartType.LINE,
                dimension_column="D",
                metric_column="M",
                suitability_score=0.9,
                reasoning="test",
            )
        ],
    )
    render_dashboard_plan(spec, console)
    plan_out = console.export_text()
    assert "Test Dash" in plan_out
