"""Comparison engine calculating variances and period-over-period deltas."""

from excelpilot.comparison.models import (
    ComparisonReport,
    DimensionSliceDelta,
    MetricDelta,
)
from excelpilot.core.dataset import Dataset
from excelpilot.core.types import AggregationType
from excelpilot.metrics.engine import MetricEngine
from excelpilot.metrics.models import MetricDefinition
from excelpilot.profiling.engine import Profiler
from excelpilot.semantics.classifier import SemanticClassifier


class ComparisonEngine:
    """Compares two datasets to compute metric variances and dimensional trends."""

    def __init__(self, currency_symbol: str = "£") -> None:
        self.metric_engine = MetricEngine(currency_symbol=currency_symbol)
        self.profiler = Profiler()
        self.classifier = SemanticClassifier()

    def compare(
        self,
        base_dataset: Dataset,
        comparison_dataset: Dataset,
    ) -> ComparisonReport:
        """Evaluate variances between a baseline and comparison dataset."""
        # Classify semantics for both
        base_prof = self.profiler.profile(base_dataset)
        base_sem = self.classifier.classify_dataset(base_dataset, base_prof)

        comp_prof = self.profiler.profile(comparison_dataset)
        comp_sem = self.classifier.classify_dataset(comparison_dataset, comp_prof)

        # Identify common numeric metric columns
        common_metrics = [c for c in base_sem.metric_candidates if c in comp_sem.metric_candidates]

        metric_deltas: list[MetricDelta] = []
        for m_col in common_metrics[:5]:
            m_def = MetricDefinition(
                name=m_col.lower(),
                label=m_col.replace("_", " ").title(),
                column=m_col,
                aggregation=AggregationType.SUM,
                format_type="currency"
                if "revenue" in m_col.lower() or "cost" in m_col.lower()
                else "number",
            )
            base_res = self.metric_engine.calculate_metric(base_dataset, m_def)
            comp_res = self.metric_engine.calculate_metric(comparison_dataset, m_def)

            b_val = base_res.raw_value
            c_val = comp_res.raw_value
            abs_change = c_val - b_val
            pct_change = ((c_val - b_val) / abs(b_val) * 100.0) if b_val != 0.0 else 0.0

            metric_deltas.append(
                MetricDelta(
                    metric_name=m_col,
                    label=m_def.label,
                    base_value=b_val,
                    comparison_value=c_val,
                    absolute_change=abs_change,
                    percentage_change=round(pct_change, 2),
                    formatted_base=base_res.formatted_value,
                    formatted_comparison=comp_res.formatted_value,
                )
            )

        # Dimensional breakdown analysis (e.g., Region, Category)
        common_dims = [
            c
            for c in base_sem.dimension_candidates
            if c in comp_sem.dimension_candidates and c not in base_sem.temporal_columns
        ]

        slice_deltas: list[DimensionSliceDelta] = []
        if common_metrics and common_dims:
            primary_metric = common_metrics[0]
            primary_dim = common_dims[0]

            base_agg = self.metric_engine.aggregate_by_dimension(
                base_dataset, dimension_col=primary_dim, metric_col=primary_metric
            )
            comp_agg = self.metric_engine.aggregate_by_dimension(
                comparison_dataset, dimension_col=primary_dim, metric_col=primary_metric
            )

            # Map values by category
            base_map = {str(row[0]): float(row[1]) for row in base_agg.iter_rows()}
            comp_map = {str(row[0]): float(row[1]) for row in comp_agg.iter_rows()}

            for cat, c_val in comp_map.items():
                if cat in base_map:
                    b_val = base_map[cat]
                    if b_val > 0.0:
                        pct = ((c_val - b_val) / b_val) * 100.0
                        slice_deltas.append(
                            DimensionSliceDelta(
                                dimension=primary_dim,
                                category=cat,
                                base_value=b_val,
                                comparison_value=c_val,
                                percentage_change=round(pct, 2),
                            )
                        )

        largest_growth = (
            max(slice_deltas, key=lambda s: s.percentage_change) if slice_deltas else None
        )
        largest_decline = (
            min(slice_deltas, key=lambda s: s.percentage_change) if slice_deltas else None
        )

        # Build summary observation bullets
        bullets: list[str] = []
        for delta in metric_deltas[:3]:
            direction = "increased" if delta.percentage_change >= 0 else "decreased"
            bullets.append(
                f"{delta.label} {direction} by {abs(delta.percentage_change):.1f}% "
                f"({delta.formatted_base} -> {delta.formatted_comparison})."
            )

        if largest_growth and largest_growth.percentage_change > 0:
            bullets.append(
                f"Strongest segment growth: {largest_growth.category} "
                f"(+{largest_growth.percentage_change:.1f}% in {largest_growth.dimension})."
            )

        if largest_decline and largest_decline.percentage_change < 0:
            bullets.append(
                f"Largest segment decline: {largest_decline.category} "
                f"({largest_decline.percentage_change:.1f}% in {largest_decline.dimension})."
            )

        return ComparisonReport(
            base_name=base_dataset.name,
            comparison_name=comparison_dataset.name,
            metric_deltas=metric_deltas,
            largest_growth=largest_growth,
            largest_decline=largest_decline,
            summary_bullet_points=bullets,
        )
