"""Models and configuration for dataset cleaning workflows."""

from enum import Enum

from pydantic import BaseModel, Field


class NullHandlingStrategy(str, Enum):
    """Strategy for addressing missing or null values."""

    PRESERVE = "preserve"
    DROP_ROWS = "drop_rows"
    FILL_ZERO = "fill_zero"
    FILL_MEAN = "fill_mean"
    FILL_MEDIAN = "fill_median"
    FILL_UNKNOWN = "fill_unknown"


class CleaningConfig(BaseModel):
    """Configuration options for automated dataset cleaning."""

    trim_strings: bool = True
    drop_duplicates: bool = True
    normalize_column_names: bool = True
    null_strategy: NullHandlingStrategy = NullHandlingStrategy.PRESERVE
    specific_null_fill: dict[str, str | float] = Field(default_factory=dict)


class CleaningOperation(BaseModel):
    """Record of a single cleaning transformation executed on the dataset."""

    operation_name: str
    column: str | None = None
    description: str
    affected_rows: int = Field(ge=0)


class CleaningReport(BaseModel):
    """Summary of operations performed and row count delta."""

    dataset_name: str
    original_row_count: int = Field(ge=0)
    cleaned_row_count: int = Field(ge=0)
    original_column_count: int = Field(ge=0)
    cleaned_column_count: int = Field(ge=0)
    operations: list[CleaningOperation] = Field(default_factory=list)

    @property
    def rows_removed(self) -> int:
        return max(0, self.original_row_count - self.cleaned_row_count)
