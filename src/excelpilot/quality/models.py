"""Data models for data quality metrics, rules, and reports."""

from enum import Enum

from pydantic import BaseModel, Field


class QualityDimension(str, Enum):
    """Core dimensions of data quality."""

    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    CONSISTENCY = "consistency"


class QualitySeverity(str, Enum):
    """Severity classification of a detected data quality issue."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class QualityIssue(BaseModel):
    """An individual data quality violation detected during inspection."""

    dimension: QualityDimension
    severity: QualitySeverity
    column: str | None = None
    description: str
    affected_count: int = Field(ge=0)
    affected_percentage: float = Field(ge=0.0, le=100.0)


class QualityDimensionScore(BaseModel):
    """Audit score for an individual quality dimension."""

    dimension: QualityDimension
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(default=0.25, ge=0.0, le=1.0)


class QualityReport(BaseModel):
    """Comprehensive data quality audit report."""

    dataset_name: str
    total_rows: int = Field(ge=0)
    total_columns: int = Field(ge=0)
    overall_score: float = Field(ge=0.0, le=100.0)
    dimension_scores: dict[QualityDimension, float]
    issues: list[QualityIssue]

    @property
    def high_severity_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualitySeverity.HIGH)

    @property
    def medium_severity_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualitySeverity.MEDIUM)

    @property
    def low_severity_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualitySeverity.LOW)


class ColumnRule(BaseModel):
    """Validation constraints for a single column."""

    nullable: bool = True
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: list[str] | None = None
    regex_pattern: str | None = None
    expected_type: str | None = None


class QualityRulesConfig(BaseModel):
    """Configured rules for explicit data quality auditing."""

    rules: dict[str, ColumnRule] = Field(default_factory=dict)
