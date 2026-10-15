"""Models representing complete declarative dashboard specifications."""

from pydantic import BaseModel, Field

from excelpilot.metrics.models import MetricResult
from excelpilot.quality.models import QualityReport
from excelpilot.recommendations.models import RecommendedChart


class DashboardSpecification(BaseModel):
    """Complete declarative specification for generating a multi-sheet Excel dashboard."""

    title: str = "Executive Dashboard"
    reporting_period: str | None = None
    theme: str = "executive"
    currency_symbol: str = "£"
    kpis: list[MetricResult] = Field(default_factory=list)
    charts: list[RecommendedChart] = Field(default_factory=list)
    quality_report: QualityReport | None = None
    executive_summary_bullets: list[str] = Field(default_factory=list)
    raw_sheet_name: str = "Raw_Data"
    metadata_info: dict[str, str] = Field(default_factory=dict)
