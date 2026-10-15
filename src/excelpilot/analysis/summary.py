"""Rule-based management summary generator."""

from excelpilot.metrics.models import MetricResult
from excelpilot.quality.models import QualityReport


class ManagementSummaryGenerator:
    """Generates concise, factual executive summary statements grounded strictly in computed metrics."""

    def generate(
        self,
        kpi_results: list[MetricResult],
        quality_report: QualityReport | None = None,
    ) -> list[str]:
        """Produce factual observation bullet points from calculated KPIs and quality audit."""
        bullets: list[str] = []

        # Find key metrics
        revenue_kpi = next(
            (k for k in kpi_results if "revenue" in k.name.lower() or "sales" in k.name.lower()),
            None,
        )
        trans_kpi = next(
            (
                k
                for k in kpi_results
                if "trans" in k.name.lower()
                or "order" in k.name.lower()
                or "record" in k.name.lower()
            ),
            None,
        )
        avg_kpi = next(
            (k for k in kpi_results if "avg" in k.name.lower() or "mean" in k.name.lower()), None
        )
        profit_kpi = next((k for k in kpi_results if "profit" in k.name.lower()), None)
        margin_kpi = next((k for k in kpi_results if "margin" in k.name.lower()), None)

        if revenue_kpi and trans_kpi:
            bullets.append(
                f"{revenue_kpi.label} reached {revenue_kpi.formatted_value} across {trans_kpi.formatted_value} recorded activities."
            )
        elif revenue_kpi:
            bullets.append(f"{revenue_kpi.label} reached {revenue_kpi.formatted_value}.")

        if avg_kpi:
            bullets.append(f"{avg_kpi.label} was {avg_kpi.formatted_value} per unit.")

        if profit_kpi and margin_kpi:
            bullets.append(
                f"{profit_kpi.label} totalled {profit_kpi.formatted_value}, delivering a {margin_kpi.formatted_value} operating margin."
            )

        if quality_report is not None:
            high_count = quality_report.high_severity_count
            if high_count == 0:
                bullets.append(
                    f"Data quality audit completed with an overall score of {quality_report.overall_score:.1f}/100 and zero high-severity integrity issues."
                )
            else:
                bullets.append(
                    f"Data quality audit scored {quality_report.overall_score:.1f}/100; {high_count} high-priority issues require attention."
                )

        if not bullets:
            bullets.append("Dataset successfully ingested and indexed for analytical reporting.")

        return bullets
