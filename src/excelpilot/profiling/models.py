"""Pydantic models for column and dataset statistical profiles."""

from pydantic import BaseModel, Field


class NumericStats(BaseModel):
    """Statistical summary for numeric columns."""

    min_value: float | None = None
    max_value: float | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    quantile_25: float | None = None
    quantile_75: float | None = None


class CategoryFrequency(BaseModel):
    """Category value frequency pair."""

    value: str
    count: int
    percentage: float


class ColumnProfile(BaseModel):
    """Detailed profile of an individual dataset column."""

    name: str
    physical_type: str
    total_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    null_percentage: float = Field(ge=0.0, le=100.0)
    distinct_count: int = Field(ge=0)
    distinct_percentage: float = Field(ge=0.0, le=100.0)
    is_unique: bool = False
    is_constant: bool = False
    numeric_stats: NumericStats | None = None
    top_categories: list[CategoryFrequency] = Field(default_factory=list)
    sample_values: list[str] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    """Comprehensive statistical profile for a tabular dataset."""

    name: str
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    duplicate_rows_count: int = Field(ge=0)
    duplicate_rows_percentage: float = Field(ge=0.0, le=100.0)
    empty_rows_count: int = Field(ge=0)
    columns: list[ColumnProfile]
    numeric_column_count: int = Field(ge=0)
    categorical_column_count: int = Field(ge=0)
    temporal_column_count: int = Field(ge=0)
