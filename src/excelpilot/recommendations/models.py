"""Models for KPI and visual chart recommendations."""

from enum import Enum

from pydantic import BaseModel, Field

from excelpilot.core.types import AggregationType


class ChartType(str, Enum):
    """Supported Excel chart types."""

    LINE = "line"
    COLUMN = "column"
    BAR = "bar"
    SCATTER = "scatter"
    DONUT = "donut"
    AREA = "area"


class RecommendedKPI(BaseModel):
    """A recommended business KPI derived from schema and semantics."""

    name: str
    label: str
    column: str | None = None
    aggregation: AggregationType = AggregationType.SUM
    formula: str | None = None
    format_type: str = "number"  # currency, percentage, integer, number
    reasoning: str
    priority: int = Field(default=1, ge=1, le=5)


class RecommendedChart(BaseModel):
    """A recommended visual chart specification."""

    title: str
    chart_type: ChartType
    dimension_column: str
    metric_column: str
    aggregation: AggregationType = AggregationType.SUM
    top_n: int | None = None
    reasoning: str
    suitability_score: float = Field(ge=0.0, le=1.0)
