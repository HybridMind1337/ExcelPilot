"""Unit tests for dataset profiling engine."""

import polars as pl

from excelpilot.core.dataset import Dataset
from excelpilot.profiling.engine import Profiler


def test_profiler_statistics() -> None:
    df = pl.DataFrame(
        {
            "numbers": [10.0, 20.0, 30.0, 40.0, 50.0],
            "categories": ["A", "B", "A", "B", "A"],
            "with_nulls": [1.0, None, 3.0, None, 5.0],
        }
    )
    dataset = Dataset(df, name="test_profile")
    profiler = Profiler()
    profile = profiler.profile(dataset)

    assert profile.row_count == 5
    assert profile.column_count == 3
    assert profile.duplicate_rows_count == 0

    num_col = next(c for c in profile.columns if c.name == "numbers")
    assert num_col.numeric_stats is not None
    assert num_col.numeric_stats.min_value == 10.0
    assert num_col.numeric_stats.max_value == 50.0
    assert num_col.numeric_stats.mean == 30.0
    assert num_col.numeric_stats.median == 30.0

    cat_col = next(c for c in profile.columns if c.name == "categories")
    assert cat_col.distinct_count == 2
    assert len(cat_col.top_categories) == 2
    assert cat_col.top_categories[0].value == "A"
    assert cat_col.top_categories[0].count == 3

    null_col = next(c for c in profile.columns if c.name == "with_nulls")
    assert null_col.null_count == 2
    assert null_col.null_percentage == 40.0


def test_profiler_empty_dataset() -> None:
    dataset = Dataset(pl.DataFrame(), name="empty")
    profiler = Profiler()
    profile = profiler.profile(dataset)

    assert profile.row_count == 0
    assert profile.column_count == 0
    assert len(profile.columns) == 0
