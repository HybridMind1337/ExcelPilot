"""Unit tests for time-series trend analysis and forecasting engine."""

from datetime import date

import polars as pl
import pytest

from excelpilot.analysis.forecasting import ForecastingEngine, TrendDirection
from excelpilot.core.dataset import Dataset


def test_linear_trend_forecasting() -> None:
    # 5 consecutive months with steadily growing revenue (+100/month)
    dates = [
        date(2025, 1, 1),
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
    ]
    revenues = [100.0, 200.0, 300.0, 400.0, 500.0]

    df = pl.DataFrame({"OrderDate": dates, "Revenue": revenues})
    dataset = Dataset(df, name="growth_series")

    engine = ForecastingEngine()
    result = engine.forecast(dataset, date_column="OrderDate", metric_column="Revenue", periods=3)

    assert result.trend.direction == TrendDirection.UPWARD
    assert result.trend.slope == pytest.approx(100.0, rel=1e-2)
    assert result.trend.r_squared == pytest.approx(1.0, rel=1e-2)

    # Historical verification
    assert len(result.historical_points) == 5
    assert result.historical_points[-1].value == 500.0

    # Projected verification (+3 periods: should be 600, 700, 800)
    assert len(result.projected_points) == 3
    assert result.projected_points[0].value == pytest.approx(600.0, rel=1e-2)
    assert result.projected_points[1].value == pytest.approx(700.0, rel=1e-2)
    assert result.projected_points[2].value == pytest.approx(800.0, rel=1e-2)
    assert len(result.summary_bullets) >= 3


def test_insufficient_history_raises_error() -> None:
    df = pl.DataFrame({"OrderDate": [date(2025, 1, 1), date(2025, 2, 1)], "Revenue": [10.0, 20.0]})
    dataset = Dataset(df, name="short_series")
    engine = ForecastingEngine()

    with pytest.raises(ValueError, match="Insufficient historical data"):
        engine.forecast(dataset, date_column="OrderDate", metric_column="Revenue")
