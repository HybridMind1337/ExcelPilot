"""Metric calculation engine supporting aggregations and calculated expressions."""

import logging
from typing import Any

import polars as pl

from excelpilot.core.dataset import Dataset
from excelpilot.core.types import AggregationType
from excelpilot.exceptions.base import AnalysisError
from excelpilot.metrics.models import MetricDefinition, MetricResult
from excelpilot.metrics.parser import SafeExpressionEvaluator

logger = logging.getLogger(__name__)


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


class MetricEngine:
    """Calculates scalar metrics and dimension breakdowns over datasets."""

    def __init__(self, currency_symbol: str = "£") -> None:
        self.currency_symbol = currency_symbol
        self.evaluator = SafeExpressionEvaluator()

    def calculate_metric(self, dataset: Dataset, metric: MetricDefinition) -> MetricResult:
        """Calculate a single scalar metric value."""
        df = dataset.dataframe
        if df.is_empty():
            return MetricResult(
                name=metric.name,
                label=metric.label,
                raw_value=0.0,
                formatted_value="0",
                format_type=metric.format_type,
            )

        # 1. Calculated formula
        if metric.formula:
            try:
                expr = self.evaluator.parse_to_polars_expr(metric.formula)
                computed_df = df.select(expr.alias("__result__"))
                # Aggregate formula column by mean or sum
                val = _safe_float(computed_df["__result__"].cast(pl.Float64).mean())
            except Exception as err:
                raise AnalysisError(
                    f"Failed to evaluate metric formula '{metric.formula}': {err}"
                ) from err

        # 2. Column aggregation
        elif metric.column:
            col_name = metric.column
            if col_name not in df.columns:
                raise AnalysisError(
                    f"Column '{col_name}' required for metric '{metric.name}' not found."
                )

            agg = metric.aggregation
            if agg == AggregationType.COUNT:
                val = float(df[col_name].len())
            elif agg == AggregationType.COUNT_DISTINCT:
                val = float(df[col_name].n_unique())
            else:
                num_s = df[col_name].cast(pl.Float64)
                if agg == AggregationType.SUM:
                    val = _safe_float(num_s.sum())
                elif agg == AggregationType.MEAN:
                    val = _safe_float(num_s.mean())
                elif agg == AggregationType.MEDIAN:
                    val = _safe_float(num_s.median())
                elif agg == AggregationType.MIN:
                    val = _safe_float(num_s.min())
                elif agg == AggregationType.MAX:
                    val = _safe_float(num_s.max())
                else:
                    val = _safe_float(num_s.sum())
        else:
            # Default count rows
            val = float(df.height)

        formatted = self.format_value(val, metric.format_type)

        return MetricResult(
            name=metric.name,
            label=metric.label,
            raw_value=val,
            formatted_value=formatted,
            format_type=metric.format_type,
        )

    def aggregate_by_dimension(
        self,
        dataset: Dataset,
        dimension_col: str,
        metric_col: str,
        aggregation: AggregationType = AggregationType.SUM,
        top_n: int | None = None,
    ) -> pl.DataFrame:
        """Aggregate a metric across category dimension groups."""
        df = dataset.dataframe
        if dimension_col not in df.columns or metric_col not in df.columns:
            raise AnalysisError(
                f"Columns '{dimension_col}' or '{metric_col}' not present in dataset."
            )

        # Polars group_by
        col_expr = pl.col(metric_col)
        if aggregation == AggregationType.SUM:
            agg_expr = col_expr.sum().alias("value")
        elif aggregation == AggregationType.MEAN:
            agg_expr = col_expr.mean().alias("value")
        elif aggregation == AggregationType.COUNT_DISTINCT:
            agg_expr = col_expr.n_unique().alias("value")
        else:
            agg_expr = col_expr.count().alias("value")

        grouped = (
            df.filter(pl.col(dimension_col).is_not_null())
            .group_by(dimension_col)
            .agg(agg_expr)
            .sort("value", descending=True)
        )

        if top_n is not None and grouped.height > top_n:
            top_records = grouped.head(top_n)
            other_val = grouped.slice(top_n)["value"].sum()
            other_df = pl.DataFrame(
                {
                    dimension_col: ["Other"],
                    "value": [other_val],
                },
                schema=grouped.schema,
            )
            grouped = pl.concat([top_records, other_df])

        return grouped

    def format_value(self, val: float, format_type: str) -> str:
        """Format numbers according to business conventions without rounding artifacts."""
        if format_type == "currency":
            return f"{self.currency_symbol}{val:,.2f}"
        if format_type == "percentage":
            return f"{val:.1f}%"
        if format_type == "integer":
            return f"{round(val):,}"
        # standard number
        if abs(val) >= 1000:
            return f"{val:,.2f}" if val % 1 != 0 else f"{int(val):,}"
        return f"{val:.2f}" if val % 1 != 0 else str(int(val))
