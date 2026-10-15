"""Rule-based KPI recommendation engine grounded in schema and semantics."""

from excelpilot.core.types import AggregationType, SemanticType
from excelpilot.profiling.models import DatasetProfile
from excelpilot.recommendations.models import RecommendedKPI
from excelpilot.semantics.models import DatasetSemanticProfile


class KPIRecommender:
    """Evaluates column semantics and statistical profiles to recommend relevant business KPIs."""

    def recommend_kpis(
        self,
        profile: DatasetProfile,
        semantics: DatasetSemanticProfile,
    ) -> list[RecommendedKPI]:
        """Generate a prioritised list of recommended business KPIs."""
        kpis: list[RecommendedKPI] = []

        # Find columns by semantic types
        currency_cols = [
            c.name for c in semantics.columns if c.semantic_type == SemanticType.CURRENCY
        ]
        id_cols = [c.name for c in semantics.columns if c.semantic_type == SemanticType.IDENTIFIER]
        int_cols = [c.name for c in semantics.columns if c.semantic_type == SemanticType.INTEGER]

        # 1. Primary monetary metric (e.g., Revenue, Sales, Total)
        primary_revenue = next(
            (
                c
                for c in currency_cols
                if any(k in c.lower() for k in ("revenue", "sales", "total"))
            ),
            currency_cols[0] if currency_cols else None,
        )

        if primary_revenue:
            kpis.append(
                RecommendedKPI(
                    name=f"total_{primary_revenue.lower()}",
                    label=f"Total {primary_revenue.replace('_', ' ').title()}",
                    column=primary_revenue,
                    aggregation=AggregationType.SUM,
                    format_type="currency",
                    reasoning=f"Identified '{primary_revenue}' as key monetary column suitable for aggregation.",
                    priority=1,
                )
            )

        # 2. Transaction / Order volume
        order_id = next(
            (
                c
                for c in id_cols
                if any(k in c.lower() for k in ("order", "trans", "invoice", "sale"))
            ),
            id_cols[0] if id_cols else None,
        )

        if order_id:
            kpis.append(
                RecommendedKPI(
                    name=f"total_{order_id.lower()}",
                    label="Total Transactions",
                    column=order_id,
                    aggregation=AggregationType.COUNT_DISTINCT,
                    format_type="integer",
                    reasoning=f"Identified '{order_id}' as distinct transaction identifier.",
                    priority=2,
                )
            )
        else:
            # Fallback to total row count
            kpis.append(
                RecommendedKPI(
                    name="total_records",
                    label="Total Volume",
                    column=None,
                    aggregation=AggregationType.COUNT,
                    format_type="integer",
                    reasoning=f"Total record volume across {profile.row_count:,} rows.",
                    priority=2,
                )
            )

        # 3. Average value per transaction
        if primary_revenue:
            kpis.append(
                RecommendedKPI(
                    name=f"avg_{primary_revenue.lower()}",
                    label=f"Average {primary_revenue.replace('_', ' ').title()}",
                    column=primary_revenue,
                    aggregation=AggregationType.MEAN,
                    format_type="currency",
                    reasoning=f"Calculates mean ticket size or unit value across '{primary_revenue}'.",
                    priority=3,
                )
            )

        # 4. Units / Quantity sold
        qty_col = next(
            (
                c
                for c in int_cols
                if any(k in c.lower() for k in ("qty", "quantity", "units", "items", "count"))
            ),
            None,
        )
        if qty_col:
            kpis.append(
                RecommendedKPI(
                    name=f"total_{qty_col.lower()}",
                    label="Total Units Sold",
                    column=qty_col,
                    aggregation=AggregationType.SUM,
                    format_type="integer",
                    reasoning=f"Identified '{qty_col}' as quantity measurement.",
                    priority=4,
                )
            )

        # 5. Customer base count
        cust_id = next(
            (
                c
                for c in id_cols
                if any(k in c.lower() for k in ("cust", "user", "client", "member"))
            ),
            None,
        )
        if cust_id:
            kpis.append(
                RecommendedKPI(
                    name="active_customers",
                    label="Customer Count",
                    column=cust_id,
                    aggregation=AggregationType.COUNT_DISTINCT,
                    format_type="integer",
                    reasoning=f"Identified '{cust_id}' as unique customer identifier.",
                    priority=4,
                )
            )

        # 6. Profit and Gross Margin if both revenue and cost exist
        cost_col = next(
            (c for c in currency_cols if any(k in c.lower() for k in ("cost", "expense"))), None
        )
        if primary_revenue and cost_col:
            kpis.append(
                RecommendedKPI(
                    name="total_profit",
                    label="Gross Profit",
                    column=None,
                    formula=f"{primary_revenue} - {cost_col}",
                    format_type="currency",
                    reasoning=f"Calculated from detected revenue ('{primary_revenue}') and cost ('{cost_col}') columns.",
                    priority=2,
                )
            )
            kpis.append(
                RecommendedKPI(
                    name="gross_margin_pct",
                    label="Gross Margin",
                    column=None,
                    formula=f"({primary_revenue} - {cost_col}) / {primary_revenue} * 100",
                    format_type="percentage",
                    reasoning="Calculated margin percentage derived from revenue and cost.",
                    priority=3,
                )
            )

        return sorted(kpis, key=lambda k: k.priority)
