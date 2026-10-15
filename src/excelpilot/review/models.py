"""Models for auditing and reviewing generated Excel dashboards."""

from enum import Enum

from pydantic import BaseModel, Field


class ReviewSeverity(str, Enum):
    """Classification of review findings."""

    INFO = "INFO"
    RECOMMENDATION = "RECOMMENDATION"
    WARNING = "WARNING"


class ReviewFinding(BaseModel):
    """An individual design, visual, or layout finding identified in a dashboard."""

    severity: ReviewSeverity
    category: str
    description: str
    suggested_action: str | None = None


class ReviewReport(BaseModel):
    """Comprehensive design and layout review report for an Excel dashboard."""

    workbook_name: str
    review_score: float = Field(ge=0.0, le=100.0)
    sheet_count: int
    has_dashboard_sheet: bool
    findings: list[ReviewFinding] = Field(default_factory=list)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.WARNING)

    @property
    def recommendation_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.RECOMMENDATION)
