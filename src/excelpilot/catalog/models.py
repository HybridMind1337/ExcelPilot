"""Models representing data dictionaries and schema catalogs."""

from dataclasses import dataclass

from excelpilot.core.types import SemanticType


@dataclass(frozen=True)
class ColumnCatalogEntry:
    """Detailed catalog entry and data dictionary attributes for a single column."""

    name: str
    physical_type: str
    semantic_type: SemanticType
    confidence: float
    null_count: int
    null_percentage: float
    distinct_count: int
    min_value: str
    max_value: str
    sample_values: list[str]
    description: str


@dataclass(frozen=True)
class DataCatalog:
    """Complete data dictionary and schema documentation for a dataset."""

    dataset_name: str
    total_rows: int
    total_columns: int
    entries: list[ColumnCatalogEntry]
