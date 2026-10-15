"""Unit tests for QueryEngine and SQL execution over datasets."""

import polars as pl
import pytest

from excelpilot.core.dataset import Dataset
from excelpilot.exceptions.base import AnalysisError
from excelpilot.query.engine import QueryEngine


def test_query_engine_single_table() -> None:
    df = pl.DataFrame(
        {
            "Region": ["EMEA", "EMEA", "APAC", "APAC", "AMER"],
            "Revenue": [100.0, 150.0, 200.0, 50.0, 300.0],
        }
    )
    dataset = Dataset(df, name="Sales")
    engine = QueryEngine()

    sql = "SELECT Region, SUM(Revenue) AS TotalRev FROM data GROUP BY Region ORDER BY TotalRev DESC"
    res = engine.execute_query(dataset, sql)

    assert res.row_count == 3
    assert res.column_count == 2
    assert res.execution_time_ms >= 0.0

    regions = res.dataframe["Region"].to_list()
    assert regions[0] == "AMER"
    assert res.dataframe["TotalRev"].to_list()[0] == 300.0


def test_query_engine_invalid_sql() -> None:
    df = pl.DataFrame({"A": [1, 2, 3]})
    dataset = Dataset(df, name="test")
    engine = QueryEngine()

    with pytest.raises(AnalysisError, match="SQL execution failed"):
        engine.execute_query(dataset, "SELECT NON_EXISTENT FROM data")


def test_query_engine_multi_sheet() -> None:
    customers = pl.DataFrame({"CustID": [1, 2], "Name": ["Alice", "Bob"]})
    orders = pl.DataFrame({"CustID": [1, 1, 2], "Amount": [10.0, 20.0, 50.0]})

    ds_map = {
        "Customers": Dataset(customers, name="Customers"),
        "Orders": Dataset(orders, name="Orders"),
    }
    engine = QueryEngine()
    sql = """
        SELECT c.Name, SUM(o.Amount) AS TotalSpent
        FROM Customers c
        JOIN Orders o ON c.CustID = o.CustID
        GROUP BY c.Name
        ORDER BY TotalSpent DESC
    """
    res = engine.execute_multi_sheet_query(ds_map, sql)
    assert res.row_count == 2
    assert res.dataframe["Name"].to_list() == ["Bob", "Alice"]
