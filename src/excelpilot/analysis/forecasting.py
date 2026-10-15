"""Time-series trend analysis and statistical forecasting engine."""

import math
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

import polars as pl

from excelpilot.core.dataset import Dataset


class TrendDirection(str, Enum):
    """Direction of historical metric trajectory."""

    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    STABLE = "STABLE"


@dataclass(frozen=True)
class ForecastPoint:
    """Individual data point within historical series or forward projection."""

    period_index: int
    period_label: str
    value: float
    lower_bound: float
    upper_bound: float
    is_projection: bool


@dataclass(frozen=True)
class TrendMetrics:
    """Statistical summary of the underlying trend."""

    slope: float
    intercept: float
    r_squared: float
    direction: TrendDirection
    mean_value: float
    period_growth_rate_pct: float


@dataclass(frozen=True)
class ForecastResult:
    """Complete time-series trend analysis and future forecast projection."""

    metric_name: str
    date_column: str
    periods_projected: int
    trend: TrendMetrics
    historical_points: list[ForecastPoint]
    projected_points: list[ForecastPoint]
    summary_bullets: list[str]


class ForecastingEngine:
    """Calculates linear trends and forward projections for temporal metrics."""

    def __init__(self, confidence_interval: float = 0.95) -> None:
        self.confidence_multiplier = 1.96 if confidence_interval >= 0.95 else 1.645

    def forecast(
        self,
        dataset: Dataset,
        date_column: str,
        metric_column: str,
        periods: int = 3,
    ) -> ForecastResult:
        """Generate time-series aggregation and forward forecast projection."""
        df = dataset.dataframe
        if date_column not in df.columns or metric_column not in df.columns:
            raise ValueError(f"Columns '{date_column}' or '{metric_column}' not found in dataset.")

        # Drop nulls and select columns
        clean_df = df.select([date_column, metric_column]).drop_nulls().sort(date_column)
        if clean_df.height < 3:
            raise ValueError(
                f"Insufficient historical data ({clean_df.height} rows) to generate a forecast."
            )

        # Aggregate metric by date/period to obtain time series
        grouped = (
            clean_df.group_by(date_column)
            .agg(pl.col(metric_column).sum().alias("metric_sum"))
            .sort(date_column)
        )

        dates_raw = grouped[date_column].to_list()
        y_vals = [float(v) for v in grouped["metric_sum"].to_list()]
        n = len(y_vals)
        x_vals = [float(i) for i in range(n)]

        # Linear regression calculation: y = slope * x + intercept
        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals, strict=False))
        denominator = sum((x - mean_x) ** 2 for x in x_vals)

        if denominator == 0:
            slope = 0.0
            intercept = mean_y
            r_squared = 0.0
        else:
            slope = numerator / denominator
            intercept = mean_y - (slope * mean_x)

            # R-squared computation
            ss_res = sum(
                (y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals, strict=False)
            )
            ss_tot = sum((y - mean_y) ** 2 for y in y_vals)
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Residual standard error
        std_err = math.sqrt(
            sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals, strict=False))
            / n
        )
        margin = self.confidence_multiplier * std_err

        # Direction and growth rate
        if abs(slope) < 0.001 * max(abs(mean_y), 1.0):
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.UPWARD
        else:
            direction = TrendDirection.DOWNWARD

        growth_pct = (slope / mean_y * 100.0) if mean_y != 0 else 0.0

        trend_metrics = TrendMetrics(
            slope=round(slope, 4),
            intercept=round(intercept, 4),
            r_squared=round(max(0.0, min(1.0, r_squared)), 4),
            direction=direction,
            mean_value=round(mean_y, 2),
            period_growth_rate_pct=round(growth_pct, 2),
        )

        # Historical points
        historical: list[ForecastPoint] = []
        for i in range(n):
            dt_label = self._format_date_label(dates_raw[i])
            val = float(y_vals[i])
            historical.append(
                ForecastPoint(
                    period_index=i + 1,
                    period_label=dt_label,
                    value=round(val, 2),
                    lower_bound=round(max(0.0, val - margin), 2),
                    upper_bound=round(val + margin, 2),
                    is_projection=False,
                )
            )

        # Forward projected points
        projected: list[ForecastPoint] = []
        for p in range(1, periods + 1):
            target_x = n + p - 1
            projected_y = slope * target_x + intercept
            # Broaden margin slightly into future
            f_margin = margin * (1.0 + (0.1 * p))
            projected.append(
                ForecastPoint(
                    period_index=n + p,
                    period_label=f"Period +{p}",
                    value=round(max(0.0, projected_y), 2),
                    lower_bound=round(max(0.0, projected_y - f_margin), 2),
                    upper_bound=round(max(0.0, projected_y + f_margin), 2),
                    is_projection=True,
                )
            )

        # Management summary bullets
        bullets: list[str] = [
            f"Underlying trend for '{metric_column}' is {direction.value.lower()} with an average growth rate of {growth_pct:+.1f}% per period.",
            f"Model goodness of fit (R-squared) is {trend_metrics.r_squared:.2f} across {n} historical periods.",
            f"Projected next-period value is {projected[0].value:,.2f} (confidence range: {projected[0].lower_bound:,.2f} - {projected[0].upper_bound:,.2f}).",
        ]
        if periods > 1:
            bullets.append(
                f"Horizon projection (+{periods} periods) estimates {projected[-1].value:,.2f}."
            )

        return ForecastResult(
            metric_name=metric_column,
            date_column=date_column,
            periods_projected=periods,
            trend=trend_metrics,
            historical_points=historical,
            projected_points=projected,
            summary_bullets=bullets,
        )

    @staticmethod
    def _format_date_label(val: Any) -> str:
        """Format datetime/date object or string safely."""
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        return str(val)
