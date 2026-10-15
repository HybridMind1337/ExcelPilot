"""Unit tests for Dataset parquet serialization and deserialization."""

from pathlib import Path

import polars as pl

from excelpilot.core.dataset import Dataset


def test_dataset_to_and_from_parquet(tmp_path: Path) -> None:
    df = pl.DataFrame({"ID": [1, 2, 3], "Score": [88.5, 92.0, 79.5]})
    dataset = Dataset(df, name="scores")

    parquet_file = tmp_path / "cache.parquet"
    dataset.to_parquet(parquet_file)
    assert parquet_file.exists()

    loaded = Dataset.from_parquet(parquet_file, name="loaded_scores")
    assert loaded.name == "loaded_scores"
    assert loaded.row_count == 3
    assert loaded.column_count == 2
    assert loaded.dataframe["Score"].to_list() == [88.5, 92.0, 79.5]
