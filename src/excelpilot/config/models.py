"""Configuration models for project specification files (excelpilot.yaml)."""

from pathlib import Path

from pydantic import BaseModel, Field

from excelpilot.core.types import AggregationType
from excelpilot.quality.models import ColumnRule


class MetricConfig(BaseModel):
    """Configuration for a business metric."""

    label: str | None = None
    column: str | None = None
    aggregation: AggregationType = AggregationType.SUM
    formula: str | None = None
    format_type: str = "number"


class TimeConfig(BaseModel):
    """Configuration for temporal analysis."""

    column: str
    granularity: str = "month"


class DashboardConfig(BaseModel):
    """Configuration for dashboard styling and presentation."""

    title: str = "Executive Dashboard"
    theme: str = "executive"
    currency: str = "GBP"


class SourceConfig(BaseModel):
    """Configuration identifying source dataset workbook and worksheet."""

    path: Path | None = None
    worksheet: str | None = None


class OutputConfig(BaseModel):
    """Configuration for rendered output destination."""

    path: Path = Path("reports/dashboard.xlsx")


class ProjectConfig(BaseModel):
    """Metadata describing the reporting project."""

    name: str = "excelpilot-project"
    version: str = "1.0"


class ExcelPilotConfig(BaseModel):
    """Root configuration model representing excelpilot.yaml."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    source: SourceConfig = Field(default_factory=SourceConfig)
    metrics: dict[str, MetricConfig] = Field(default_factory=dict)
    dimensions: list[str] = Field(default_factory=list)
    time: TimeConfig | None = None
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    quality: dict[str, ColumnRule] = Field(default_factory=dict)
    output: OutputConfig = Field(default_factory=OutputConfig)
