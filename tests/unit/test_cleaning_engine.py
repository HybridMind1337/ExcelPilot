"""Unit tests for the data cleaning engine."""

import polars as pl

from excelpilot.cleaning.engine import CleaningEngine
from excelpilot.cleaning.models import CleaningConfig, NullHandlingStrategy
from excelpilot.core.dataset import Dataset


def test_clean_trims_and_deduplicates() -> None:
    df = pl.DataFrame(
        {
            "  Category  ": ["  Hardware  ", "Software", "Software"],
            "Value": [10.0, 20.0, 20.0],
        }
    )
    dataset = Dataset(df, name="dirty")
    cleaner = CleaningEngine()
    cleaned_df, report = cleaner.clean(dataset)

    assert "Category" in cleaned_df.columns
    assert cleaned_df["Category"].to_list() == ["Hardware", "Software"]
    assert cleaned_df.height == 2
    assert report.rows_removed == 1
    assert len(report.operations) >= 2


def test_clean_null_drop_strategy() -> None:
    df = pl.DataFrame(
        {
            "ID": [1, 2, 3],
            "Score": [10.0, None, 30.0],
        }
    )
    dataset = Dataset(df)
    config = CleaningConfig(null_strategy=NullHandlingStrategy.DROP_ROWS)
    cleaner = CleaningEngine(config=config)
    cleaned_df, report = cleaner.clean(dataset)

    assert cleaned_df.height == 2
    assert report.rows_removed == 1


def test_clean_null_fill_zero_strategy() -> None:
    df = pl.DataFrame(
        {
            "Score": [10.0, None, 30.0],
        }
    )
    dataset = Dataset(df)
    config = CleaningConfig(null_strategy=NullHandlingStrategy.FILL_ZERO)
    cleaner = CleaningEngine(config=config)
    cleaned_df, _ = cleaner.clean(dataset)

    assert cleaned_df["Score"].to_list() == [10.0, 0.0, 30.0]
