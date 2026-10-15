"""Unit tests for the Dataset wrapper and DuckDB analytical queries."""

import polars as pl

from excelpilot.core.dataset import Dataset


def test_dataset_properties() -> None:
    df = pl.DataFrame(
        {
            "id": [1, 2, 3],
            "val": [10.5, 20.0, 35.5],
        }
    )
    dataset = Dataset(df, name="test_data")

    assert dataset.name == "test_data"
    assert dataset.row_count == 3
    assert dataset.column_count == 2
    assert dataset.columns == ["id", "val"]
    assert not dataset.is_empty()


def test_dataset_sample() -> None:
    df = pl.DataFrame({"x": list(range(100))})
    dataset = Dataset(df)
    sampled = dataset.sample(n=10)

    assert sampled.height == 10


def test_dataset_duckdb_sql_query() -> None:
    df = pl.DataFrame(
        {
            "category": ["A", "A", "B", "B", "B"],
            "amount": [10.0, 20.0, 5.0, 15.0, 30.0],
        }
    )
    dataset = Dataset(df, name="sales")

    query = """
    SELECT category, SUM(amount) AS total_amount, COUNT(*) AS count
    FROM sales
    GROUP BY category
    ORDER BY category
    """
    result = dataset.query_sql(query)

    assert result.height == 2
    assert result["category"].to_list() == ["A", "B"]
    assert result["total_amount"].to_list() == [30.0, 50.0]
    assert result["count"].to_list() == [2, 3]
