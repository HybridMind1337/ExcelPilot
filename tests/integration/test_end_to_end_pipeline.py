"""Integration test verifying end-to-end dashboard generation and output validation."""

from pathlib import Path

from excelpilot.analysis.summary import ManagementSummaryGenerator
from excelpilot.core.dataset import Dataset
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.exporters.excel import XlsxWriterDashboardExporter
from excelpilot.metrics.engine import MetricEngine
from excelpilot.metrics.models import MetricDefinition, MetricResult
from excelpilot.profiling.engine import Profiler
from excelpilot.quality.engine import QualityEngine
from excelpilot.recommendations.charts import ChartRecommender
from excelpilot.recommendations.kpi import KPIRecommender
from excelpilot.semantics.classifier import SemanticClassifier
from excelpilot.workbook.reader import OpenpyxlReader


def test_end_to_end_dashboard_generation(sales_dataset: Dataset, tmp_path: Path) -> None:
    # 1. Profile and classify
    profiler = Profiler()
    classifier = SemanticClassifier()
    quality_engine = QualityEngine()
    kpi_recommender = KPIRecommender()
    chart_recommender = ChartRecommender()
    summary_gen = ManagementSummaryGenerator()
    exporter = XlsxWriterDashboardExporter()

    profile = profiler.profile(sales_dataset)
    semantics = classifier.classify_dataset(sales_dataset, profile)
    quality_report = quality_engine.audit(sales_dataset, profile, semantics)

    # 2. Recommendations
    kpi_defs = kpi_recommender.recommend_kpis(profile, semantics)
    charts = chart_recommender.recommend_charts(profile, semantics)

    # 3. Calculate metrics
    metric_engine = MetricEngine(currency_symbol="£")
    kpis: list[MetricResult] = []
    for k_def in kpi_defs[:4]:
        m_def = MetricDefinition(
            name=k_def.name,
            label=k_def.label,
            column=k_def.column,
            aggregation=k_def.aggregation,
            formula=k_def.formula,
            format_type=k_def.format_type,
        )
        kpis.append(metric_engine.calculate_metric(sales_dataset, m_def))

    bullets = summary_gen.generate(kpis, quality_report)

    # 4. Create Dashboard Specification
    spec = DashboardSpecification(
        title="Executive Performance Dashboard",
        reporting_period="Q1 2025",
        theme="executive",
        currency_symbol="£",
        kpis=kpis,
        charts=charts[:4],
        quality_report=quality_report,
        executive_summary_bullets=bullets,
        metadata_info={"Dataset": sales_dataset.name, "Pipeline": "Automated Integration Test"},
    )

    # 5. Render workbook
    output_path = tmp_path / "final_dashboard.xlsx"
    rendered = exporter.export(
        specification=spec,
        raw_dataframe=sales_dataset.dataframe,
        cleaned_dataframe=sales_dataset.dataframe,
        output_path=output_path,
    )

    assert rendered.exists()
    assert rendered.stat().st_size > 0

    # 6. Validate generated workbook using reader
    reader = OpenpyxlReader()
    meta = reader.inspect(rendered)

    expected_sheets = {
        "Dashboard",
        "Analysis",
        "Data_Quality",
        "Cleaned_Data",
        "Raw_Data",
        "Metadata",
    }
    actual_sheets = set(meta.sheet_names)
    assert expected_sheets.issubset(actual_sheets)
