"""Models for period-over-period and cross-workbook comparisons."""

from pydantic import BaseModel, Field


class MetricDelta(BaseModel):
    """Comparative variance for a single metric between two periods."""

    metric_name: str
    label: str
    base_value: float
    comparison_value: float
    absolute_change: float
    percentage_change: float = Field(description="Relative change in percentage.")
    formatted_base: str
    formatted_comparison: str


class DimensionSliceDelta(BaseModel):
    """Variance for a specific slice within a category dimension."""

    dimension: str
    category: str
    base_value: float
    comparison_value: float
    percentage_change: float


class ComparisonReport(BaseModel):
    """Comprehensive comparative evaluation between two workbooks or periods."""

    base_name: str
    comparison_name: str
    metric_deltas: list[MetricDelta]
    largest_growth: DimensionSliceDelta | None = None
    largest_decline: DimensionSliceDelta | None = None
    summary_bullet_points: list[str] = Field(default_factory=list)
