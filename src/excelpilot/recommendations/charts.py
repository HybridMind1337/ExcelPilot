"""Rule-based visual chart recommendation engine."""

from excelpilot.core.types import AggregationType, SemanticType
from excelpilot.profiling.models import DatasetProfile
from excelpilot.recommendations.models import ChartType, RecommendedChart
from excelpilot.semantics.models import DatasetSemanticProfile


class ChartRecommender:
    """Recommends appropriate chart types based on semantic data types and cardinality."""

    def recommend_charts(
        self,
        profile: DatasetProfile,
        semantics: DatasetSemanticProfile,
        primary_metric_col: str | None = None,
    ) -> list[RecommendedChart]:
        """Generate a prioritised list of chart recommendations."""
        charts: list[RecommendedChart] = []

        # Find primary metric column if not specified
        if not primary_metric_col:
            metric_candidates = semantics.metric_candidates
            primary_metric_col = metric_candidates[0] if metric_candidates else None

        if not primary_metric_col:
            # No metric found to plot
            return []

        col_profiles = {c.name: c for c in profile.columns}

        # 1. Temporal breakdown (Line Chart)
        temporal_cols = semantics.temporal_columns
        for t_col in temporal_cols:
            charts.append(
                RecommendedChart(
                    title=f"{primary_metric_col.replace('_', ' ').title()} Over Time",
                    chart_type=ChartType.LINE,
                    dimension_column=t_col,
                    metric_column=primary_metric_col,
                    aggregation=AggregationType.SUM,
                    reasoning=f"Temporal dimension '{t_col}' with continuous metric '{primary_metric_col}'.",
                    suitability_score=0.98,
                )
            )

        # 2. Categorical breakdowns
        dimension_candidates = [
            c
            for c in semantics.columns
            if c.is_dimension_candidate and c.semantic_type != SemanticType.TEMPORAL
        ]

        for dim in dimension_candidates:
            c_prof = col_profiles.get(dim.name)
            cardinality = c_prof.distinct_count if c_prof else 10

            # Donut chart for very low cardinality (2 to 5 distinct categories)
            if 2 <= cardinality <= 5:
                charts.append(
                    RecommendedChart(
                        title=f"{primary_metric_col.replace('_', ' ').title()} by {dim.name.replace('_', ' ').title()}",
                        chart_type=ChartType.DONUT,
                        dimension_column=dim.name,
                        metric_column=primary_metric_col,
                        aggregation=AggregationType.SUM,
                        reasoning=f"Low cardinality ({cardinality} categories) provides clear part-to-whole view.",
                        suitability_score=0.91,
                    )
                )

            # Column chart for moderate cardinality (4 to 12 categories)
            elif 4 <= cardinality <= 12:
                charts.append(
                    RecommendedChart(
                        title=f"{primary_metric_col.replace('_', ' ').title()} by {dim.name.replace('_', ' ').title()}",
                        chart_type=ChartType.COLUMN,
                        dimension_column=dim.name,
                        metric_column=primary_metric_col,
                        aggregation=AggregationType.SUM,
                        reasoning=f"Standard column chart for comparing {cardinality} categories.",
                        suitability_score=0.94,
                    )
                )

            # High cardinality (> 12 categories): Top 10 horizontal bar chart
            elif cardinality > 12:
                charts.append(
                    RecommendedChart(
                        title=f"Top 10 {dim.name.replace('_', ' ').title()} by {primary_metric_col.replace('_', ' ').title()}",
                        chart_type=ChartType.BAR,
                        dimension_column=dim.name,
                        metric_column=primary_metric_col,
                        aggregation=AggregationType.SUM,
                        top_n=10,
                        reasoning=f"High cardinality ({cardinality} categories); restricted to Top 10 to avoid clutter.",
                        suitability_score=0.92,
                    )
                )

        # Sort recommendations by suitability score descending
        return sorted(charts, key=lambda c: c.suitability_score, reverse=True)
