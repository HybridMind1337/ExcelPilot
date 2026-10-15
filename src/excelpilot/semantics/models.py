"""Models for semantic data typing and classification."""

from pydantic import BaseModel, Field

from excelpilot.core.types import SemanticType


class ColumnSemanticProfile(BaseModel):
    """Semantic classification metadata for an individual column."""

    name: str
    physical_type: str
    semantic_type: SemanticType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    is_metric_candidate: bool = False
    is_dimension_candidate: bool = False
    sample_values: list[str] = Field(default_factory=list)


class DatasetSemanticProfile(BaseModel):
    """Comprehensive semantic classification report for a dataset."""

    columns: list[ColumnSemanticProfile]

    def get_column(self, name: str) -> ColumnSemanticProfile | None:
        """Find a column profile by name (case-insensitive)."""
        lower = name.lower()
        for col in self.columns:
            if col.name.lower() == lower:
                return col
        return None

    @property
    def metric_candidates(self) -> list[str]:
        return [c.name for c in self.columns if c.is_metric_candidate]

    @property
    def dimension_candidates(self) -> list[str]:
        return [c.name for c in self.columns if c.is_dimension_candidate]

    @property
    def temporal_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.semantic_type == SemanticType.TEMPORAL]
