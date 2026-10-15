"""Core type definitions and semantic constants."""

from enum import Enum


class SemanticType(str, Enum):
    """Semantic data types inferred from column names, data types, and value patterns."""

    TEMPORAL = "TEMPORAL"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"
    CATEGORICAL = "CATEGORICAL"
    IDENTIFIER = "IDENTIFIER"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    URL = "URL"
    GEO = "GEO"
    UNKNOWN = "UNKNOWN"


class AggregationType(str, Enum):
    """Supported aggregation functions for metrics and chart dimensions."""

    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    MIN = "min"
    MAX = "max"
