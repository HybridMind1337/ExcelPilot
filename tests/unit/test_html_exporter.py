"""Unit tests for standalone HTML executive dashboard exporter."""

from pathlib import Path

import polars as pl

from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.exporters.html import HtmlDashboardExporter
from excelpilot.metrics.models import MetricResult
from excelpilot.recommendations.models import ChartType, RecommendedChart


def test_html_dashboard_export(tmp_path: Path) -> None:
    df = pl.DataFrame(
        {
            "Region": ["North", "South", "East", "West"],
            "Revenue": [1000.0, 2000.0, 1500.0, 3000.0],
            "Units": [10, 20, 15, 30],
        }
    )

    kpi = MetricResult(
        name="total_rev",
        label="Total Revenue",
        raw_value=7500.0,
        formatted_value="£7,500.00",
        format_type="currency",
    )
    chart = RecommendedChart(
        chart_type=ChartType.BAR,
        dimension_column="Region",
        metric_column="Revenue",
        title="Revenue by Region",
        suitability_score=0.95,
        reasoning="High clarity",
    )

    spec = DashboardSpecification(
        title="Executive Performance",
        reporting_period="Q1 Summary",
        theme="executive",
        currency_symbol="£",
        kpis=[kpi],
        charts=[chart],
    )

    out_file = tmp_path / "dashboard.html"
    exporter = HtmlDashboardExporter(currency_symbol="£")
    exported_path = exporter.export(spec, df, out_file)

    assert exported_path.exists()
    content = exported_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Executive Performance" in content
    assert "Revenue by Region" in content
    assert "Total Revenue" in content
    assert "<svg" in content
