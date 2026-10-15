"""Unit tests for the variance comparison engine."""

import polars as pl

from excelpilot.comparison.engine import ComparisonEngine
from excelpilot.core.dataset import Dataset


def test_comparison_metric_and_dimension_deltas() -> None:
    base_df = pl.DataFrame(
        {
            "Region": ["North", "South"],
            "Revenue": [1000.0, 2000.0],
        }
    )
    comp_df = pl.DataFrame(
        {
            "Region": ["North", "South"],
            "Revenue": [1200.0, 1800.0],
        }
    )

    base_ds = Dataset(base_df, name="Jan")
    comp_ds = Dataset(comp_df, name="Feb")

    engine = ComparisonEngine(currency_symbol="£")
    report = engine.compare(base_ds, comp_ds)

    assert report.base_name == "Jan"
    assert report.comparison_name == "Feb"
    assert len(report.metric_deltas) == 1

    rev_delta = report.metric_deltas[0]
    assert rev_delta.base_value == 3000.0
    assert rev_delta.comparison_value == 3000.0
    assert rev_delta.percentage_change == 0.0

    # North grew from 1000 to 1200 (+20%)
    # South declined from 2000 to 1800 (-10%)
    assert report.largest_growth is not None
    assert report.largest_growth.category == "North"
    assert report.largest_growth.percentage_change == 20.0

    assert report.largest_decline is not None
    assert report.largest_decline.category == "South"
    assert report.largest_decline.percentage_change == -10.0
