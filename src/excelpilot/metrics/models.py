"""Models for metric definitions, calculated values, and aggregations."""

from pydantic import BaseModel, Field

from excelpilot.core.types import AggregationType


class MetricDefinition(BaseModel):
    """Specification of a business metric to calculate."""

    name: str
    label: str
    column: str | None = None
    aggregation: AggregationType = AggregationType.SUM
    formula: str | None = None
    format_type: str = Field(default="number")  # currency, percentage, integer, number
    description: str | None = None


class MetricResult(BaseModel):
    """Evaluated scalar metric result."""

    name: str
    label: str
    raw_value: float
    formatted_value: str
    format_type: str
    period_comparison_delta: float | None = None
    period_comparison_label: str | None = None
