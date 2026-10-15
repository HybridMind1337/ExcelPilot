"""Core dataset abstraction wrapping Polars and DuckDB."""

from typing import Any

import duckdb
import polars as pl


class Dataset:
    """Wrapper around a Polars DataFrame providing memory-efficient analytical operations."""

    def __init__(self, data: pl.DataFrame, name: str = "dataset") -> None:
        self._df = data
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def dataframe(self) -> pl.DataFrame:
        """Access the underlying Polars DataFrame."""
        return self._df

    @property
    def row_count(self) -> int:
        return self._df.height

    @property
    def column_count(self) -> int:
        return self._df.width

    @property
    def columns(self) -> list[str]:
        return self._df.columns

    @property
    def schema(self) -> dict[str, pl.DataType]:
        return dict(self._df.schema)

    def is_empty(self) -> bool:
        return self._df.is_empty()

    def sample(self, n: int = 1000, seed: int = 42) -> pl.DataFrame:
        """Return a deterministic sample of rows for rapid heuristic evaluation."""
        if self._df.height <= n:
            return self._df
        return self._df.sample(n=n, seed=seed)

    def query_sql(self, query: str) -> pl.DataFrame:
        """Execute an analytical SQL query against the dataset using DuckDB."""
        # DuckDB can register and query Arrow tables or Polars DataFrames directly without serialization
        con = duckdb.connect(database=":memory:")
        try:
            arrow_table = self._df.to_arrow()
            con.register(self._name, arrow_table)
            res = con.execute(query).arrow()
            return pl.from_arrow(res)  # type: ignore[return-value]
        finally:
            con.close()

    def head(self, n: int = 5) -> list[dict[str, Any]]:
        """Return the first n records as a list of dictionaries."""
        return self._df.head(n).to_dicts()
