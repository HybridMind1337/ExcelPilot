"""Unit tests for metric calculations, KPI recommendations, and chart recommendations."""

from excelpilot.core.dataset import Dataset
from excelpilot.core.types import AggregationType
from excelpilot.metrics.engine import MetricEngine
from excelpilot.metrics.models import MetricDefinition
from excelpilot.profiling.engine import Profiler
from excelpilot.recommendations.charts import ChartRecommender
from excelpilot.recommendations.kpi import KPIRecommender
from excelpilot.recommendations.models import ChartType
from excelpilot.semantics.classifier import SemanticClassifier


def test_metric_calculation(sales_dataset: Dataset) -> None:
    engine = MetricEngine(currency_symbol="£")
    metric = MetricDefinition(
        name="total_revenue",
        label="Total Revenue",
        column="Revenue",
        aggregation=AggregationType.SUM,
        format_type="currency",
    )
    res = engine.calculate_metric(sales_dataset, metric)

    assert res.name == "total_revenue"
    assert res.raw_value > 0.0
    assert res.formatted_value.startswith("£")


def test_kpi_and_chart_recommendation(sales_dataset: Dataset) -> None:
    profiler = Profiler()
    classifier = SemanticClassifier()
    kpi_recommender = KPIRecommender()
    chart_recommender = ChartRecommender()

    profile = profiler.profile(sales_dataset)
    semantics = classifier.classify_dataset(sales_dataset, profile)

    # Assert KPI recommendations
    kpis = kpi_recommender.recommend_kpis(profile, semantics)
    assert len(kpis) >= 3
    kpi_names = [k.name for k in kpis]
    assert any("revenue" in n for n in kpi_names)

    # Assert Chart recommendations
    charts = chart_recommender.recommend_charts(profile, semantics)
    assert len(charts) >= 2

    # Expect line chart for temporal dimension
    chart_types = {c.chart_type for c in charts}
    assert ChartType.LINE in chart_types
