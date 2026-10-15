"""Rich formatting and table rendering for CLI output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from excelpilot.analysis.anomalies import AnomalyReport
from excelpilot.analysis.forecasting import ForecastResult
from excelpilot.cleaning.models import CleaningReport
from excelpilot.comparison.models import ComparisonReport
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.privacy.detector import PrivacyReport
from excelpilot.profiling.models import DatasetProfile
from excelpilot.quality.models import QualityDimension, QualityReport
from excelpilot.recommendations.models import RecommendedChart, RecommendedKPI
from excelpilot.review.models import ReviewReport
from excelpilot.semantics.models import DatasetSemanticProfile
from excelpilot.workbook.models import WorkbookMetadata


def render_workbook_inspection(metadata: WorkbookMetadata, console: Console) -> None:
    """Render a clean summary table of workbook sheets and dimensions."""
    table = Table(
        title=f"Workbook: {metadata.path.name}", title_style="bold cyan", border_style="dim"
    )
    table.add_column("Sheet Name", style="bold white")
    table.add_column("Rows", justify="right", style="green")
    table.add_column("Columns", justify="right", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Header Preview", style="dim")

    for s in metadata.sheets:
        status = "Empty" if s.is_empty else "Active"
        preview = ", ".join(s.header_preview[:4]) + ("..." if len(s.header_preview) > 4 else "")
        table.add_row(
            s.name,
            f"{s.max_row:,}",
            str(s.max_column),
            status,
            preview or "-",
        )

    console.print(table)


def render_dataset_profile(
    profile: DatasetProfile,
    semantics: DatasetSemanticProfile,
    console: Console,
) -> None:
    """Render comprehensive profiling and semantic classification table."""
    summary_text = (
        f"Rows: [bold green]{profile.row_count:,}[/]  |  "
        f"Columns: [bold green]{profile.column_count}[/]  |  "
        f"Duplicates: [yellow]{profile.duplicate_rows_count:,} ({profile.duplicate_rows_percentage}%)[/]  |  "
        f"Empty Rows: [yellow]{profile.empty_rows_count}[/]"
    )
    console.print(
        Panel(summary_text, title=f"Dataset Profile: {profile.name}", border_style="cyan")
    )

    table = Table(title="Column Schema & Semantics", title_style="bold cyan", border_style="dim")
    table.add_column("Column", style="bold white")
    table.add_column("Physical Type", style="cyan")
    table.add_column("Semantic Type", style="bold magenta")
    table.add_column("Confidence", justify="right", style="green")
    table.add_column("Nulls", justify="right", style="yellow")
    table.add_column("Distinct", justify="right", style="blue")
    table.add_column("Role", style="white")

    for col in profile.columns:
        sem = semantics.get_column(col.name)
        sem_type_str = sem.semantic_type.value if sem else "UNKNOWN"
        conf_str = f"{sem.confidence:.2f}" if sem else "-"
        role = (
            "Metric"
            if sem and sem.is_metric_candidate
            else ("Dimension" if sem and sem.is_dimension_candidate else "-")
        )

        table.add_row(
            col.name,
            col.physical_type,
            sem_type_str,
            conf_str,
            f"{col.null_count} ({col.null_percentage}%)",
            f"{col.distinct_count}",
            role,
        )

    console.print(table)


def render_quality_report(report: QualityReport, console: Console) -> None:
    """Render data quality scores and detected issues."""
    score_style = (
        "green"
        if report.overall_score >= 90.0
        else ("yellow" if report.overall_score >= 70.0 else "red")
    )
    console.print(
        Panel(
            f"Overall Quality Score: [{score_style} bold]{report.overall_score:.1f} / 100[/]\n"
            f"Completeness: {report.dimension_scores.get(QualityDimension.COMPLETENESS, 0.0):.1f}% | "
            f"Validity: {report.dimension_scores.get(QualityDimension.VALIDITY, 0.0):.1f}% | "
            f"Uniqueness: {report.dimension_scores.get(QualityDimension.UNIQUENESS, 0.0):.1f}% | "
            f"Consistency: {report.dimension_scores.get(QualityDimension.CONSISTENCY, 0.0):.1f}%",
            title=f"Data Quality Report: {report.dataset_name}",
            border_style="cyan",
        )
    )

    if not report.issues:
        console.print("[green]No data quality issues identified.[/green]")
        return

    table = Table(
        title="Identified Data Quality Issues", title_style="bold cyan", border_style="dim"
    )
    table.add_column("Severity", style="bold")
    table.add_column("Dimension", style="cyan")
    table.add_column("Column", style="white")
    table.add_column("Description", style="white")
    table.add_column("Affected", justify="right", style="yellow")

    for issue in report.issues:
        sev_color = (
            "red"
            if issue.severity.value == "HIGH"
            else ("yellow" if issue.severity.value == "MEDIUM" else "blue")
        )
        table.add_row(
            f"[{sev_color}]{issue.severity.value}[/]",
            issue.dimension.value.title(),
            issue.column or "(Dataset)",
            issue.description,
            f"{issue.affected_count:,} ({issue.affected_percentage}%)",
        )

    console.print(table)


def render_privacy_warning(privacy: PrivacyReport, console: Console) -> None:
    """Render warning panel when personally identifiable information is detected."""
    if not privacy.has_pii:
        return

    lines = [f"- Column '{risk.column}': {risk.description}" for risk in privacy.risks]
    content = "Potential personal or confidential data detected:\n" + "\n".join(lines)
    console.print(Panel(content, title="Privacy Notice", border_style="red"))


def render_dashboard_plan(spec: DashboardSpecification, console: Console) -> None:
    """Render summary plan of generated dashboard before rendering to disk."""
    console.print(
        Panel(
            f"Title: {spec.title}\nTheme: {spec.theme.title()}\nCurrency: {spec.currency_symbol}",
            title="Dashboard Generation Plan",
            border_style="cyan",
        )
    )

    kpi_table = Table(title="Planned KPI Cards", border_style="dim")
    kpi_table.add_column("KPI", style="bold white")
    kpi_table.add_column("Sample Value", style="green")
    for k in spec.kpis:
        kpi_table.add_row(k.label, k.formatted_value)
    console.print(kpi_table)

    chart_table = Table(title="Planned Charts", border_style="dim")
    chart_table.add_column("Title", style="bold white")
    chart_table.add_column("Type", style="cyan")
    chart_table.add_column("Dimension", style="yellow")
    chart_table.add_column("Metric", style="green")
    for c in spec.charts:
        chart_table.add_row(
            c.title, c.chart_type.value.upper(), c.dimension_column, c.metric_column
        )
    console.print(chart_table)


def render_comparison_report(report: ComparisonReport, console: Console) -> None:
    """Render comparison report between two workbooks or periods."""
    console.print(
        Panel(
            f"Baseline: [bold white]{report.base_name}[/]  vs  Comparison: [bold white]{report.comparison_name}[/]",
            title="Period Variance Analysis",
            border_style="cyan",
        )
    )

    table = Table(title="Metric Variances", border_style="dim")
    table.add_column("Metric", style="bold white")
    table.add_column("Baseline", justify="right", style="dim")
    table.add_column("Comparison", justify="right", style="white")
    table.add_column("Delta %", justify="right", style="bold")

    for delta in report.metric_deltas:
        color = "green" if delta.percentage_change >= 0 else "red"
        sign = "+" if delta.percentage_change > 0 else ""
        table.add_row(
            delta.label,
            delta.formatted_base,
            delta.formatted_comparison,
            f"[{color}]{sign}{delta.percentage_change:.1f}%[/]",
        )
    console.print(table)

    if report.summary_bullet_points:
        console.print("\n[bold cyan]Key Variance Observations:[/]")
        for b in report.summary_bullet_points:
            console.print(f"  - {b}")


def render_review_report(report: ReviewReport, console: Console) -> None:
    """Render dashboard architectural and visual design review report."""
    score_style = (
        "green"
        if report.review_score >= 85.0
        else ("yellow" if report.review_score >= 65.0 else "red")
    )
    console.print(
        Panel(
            f"Dashboard Design Score: [{score_style} bold]{report.review_score:.1f} / 100[/]\n"
            f"Sheets Inspected: {report.sheet_count} | Dedicated Dashboard: {'Yes' if report.has_dashboard_sheet else 'No'}",
            title=f"Dashboard Review: {report.workbook_name}",
            border_style="cyan",
        )
    )

    if not report.findings:
        console.print(
            "[green]Dashboard adheres to recommended design and layout standards.[/green]"
        )
        return

    table = Table(title="Review Findings & Recommendations", border_style="dim")
    table.add_column("Severity", style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Finding", style="white")
    table.add_column("Recommendation", style="yellow")

    for f in report.findings:
        sev_color = (
            "red"
            if f.severity.value == "WARNING"
            else ("yellow" if f.severity.value == "RECOMMENDATION" else "blue")
        )
        table.add_row(
            f"[{sev_color}]{f.severity.value}[/]",
            f.category,
            f.description,
            f.suggested_action or "-",
        )
    console.print(table)


def render_cleaning_report(report: CleaningReport, console: Console) -> None:
    """Render summary of automated cleaning operations."""
    console.print(
        Panel(
            f"Original Dimensions: [bold white]{report.original_row_count:,} rows x {report.original_column_count} cols[/]\n"
            f"Cleaned Dimensions:  [bold green]{report.cleaned_row_count:,} rows x {report.cleaned_column_count} cols[/]\n"
            f"Rows Removed:        [yellow]{report.rows_removed:,}[/]",
            title=f"Data Cleaning Audit: {report.dataset_name}",
            border_style="cyan",
        )
    )

    if report.operations:
        table = Table(title="Executed Transformations", border_style="dim")
        table.add_column("Transformation", style="bold cyan")
        table.add_column("Details", style="white")
        table.add_column("Affected Rows", justify="right", style="green")

        for op in report.operations:
            table.add_row(op.operation_name, op.description, f"{op.affected_rows:,}")
        console.print(table)


def render_recommendations(
    kpis: list[RecommendedKPI], charts: list[RecommendedChart], console: Console
) -> None:
    """Render recommended KPIs and charts."""
    kpi_table = Table(title="Recommended KPIs", border_style="dim")
    kpi_table.add_column("Priority", justify="right", style="yellow")
    kpi_table.add_column("Metric / KPI", style="bold white")
    kpi_table.add_column("Aggregation", style="cyan")
    kpi_table.add_column("Format", style="magenta")
    kpi_table.add_column("Rationale", style="dim")

    for k in kpis:
        agg_val = k.aggregation.value if hasattr(k.aggregation, "value") else str(k.aggregation)
        kpi_table.add_row(str(k.priority), k.label, agg_val.upper(), k.format_type, k.reasoning)
    console.print(kpi_table)

    chart_table = Table(title="Recommended Visualisations", border_style="dim")
    chart_table.add_column("Suitability", justify="right", style="green")
    chart_table.add_column("Chart Title", style="bold white")
    chart_table.add_column("Chart Type", style="cyan")
    chart_table.add_column("Dimension", style="yellow")
    chart_table.add_column("Metric", style="white")
    chart_table.add_column("Rationale", style="dim")

    for c in charts:
        c_type = c.chart_type.value.upper() if hasattr(c.chart_type, "value") else str(c.chart_type)
        chart_table.add_row(
            f"{c.suitability_score:.2f}",
            c.title,
            c_type,
            c.dimension_column,
            c.metric_column,
            c.reasoning,
        )
    console.print(chart_table)


def render_anomaly_report(report: AnomalyReport, console: Console) -> None:
    """Render statistical outlier and anomaly report."""
    console.print(
        Panel(
            f"Analyzed Columns: [bold white]{report.analyzed_columns}[/] | "
            f"Total Anomalies Detected: [bold red]{report.total_outliers_detected:,}[/]",
            title=f"Statistical Anomaly Audit: {report.dataset_name}",
            border_style="cyan",
        )
    )

    table = Table(title="Column Outlier Summaries", border_style="dim")
    table.add_column("Column", style="bold white")
    table.add_column("Method", style="cyan")
    table.add_column("Total Rows", justify="right", style="dim")
    table.add_column("Outliers", justify="right", style="bold red")
    table.add_column("Outlier %", justify="right", style="yellow")
    table.add_column("Expected Bounds", justify="center", style="dim")

    for summary in report.column_summaries:
        table.add_row(
            summary.column_name,
            summary.method.value.upper(),
            f"{summary.total_count:,}",
            str(summary.outlier_count),
            f"{summary.outlier_percentage:.1f}%",
            f"[{summary.lower_bound:,.1f} .. {summary.upper_bound:,.1f}]",
        )
    console.print(table)

    flagged_points = []
    for s in report.column_summaries:
        flagged_points.extend(s.anomalies[:5])

    if flagged_points:
        detail_table = Table(title="Sample Detected Outliers", border_style="dim")
        detail_table.add_column("Row", justify="right", style="dim")
        detail_table.add_column("Column", style="bold white")
        detail_table.add_column("Value", justify="right", style="bold red")
        detail_table.add_column("Deviation", justify="right", style="yellow")
        detail_table.add_column("Reason", style="white")

        for p in flagged_points[:15]:
            detail_table.add_row(
                str(p.row_index + 1),
                p.column_name,
                f"{p.value:,.2f}",
                f"{p.deviation_score:.2f}x",
                p.reason,
            )
        console.print(detail_table)


def render_forecast_report(report: ForecastResult, console: Console) -> None:
    """Render time-series trend and forward projection report."""
    dir_color = (
        "green"
        if report.trend.direction.value == "UPWARD"
        else ("red" if report.trend.direction.value == "DOWNWARD" else "yellow")
    )
    console.print(
        Panel(
            f"Metric: [bold white]{report.metric_name}[/] (by {report.date_column})\n"
            f"Trend Direction: [{dir_color} bold]{report.trend.direction.value}[/] | "
            f"Growth Rate: [{dir_color}]{report.trend.period_growth_rate_pct:+.2f}%/period[/] | "
            f"R-squared: [bold white]{report.trend.r_squared:.2f}[/]",
            title="Time-Series Trend & Forecasting",
            border_style="cyan",
        )
    )

    table = Table(
        title=f"Forward Projection (+{report.periods_projected} Periods)", border_style="dim"
    )
    table.add_column("Period", style="bold cyan")
    table.add_column("Projected Value", justify="right", style="bold white")
    table.add_column("95% Confidence Interval", justify="center", style="dim")

    for pt in report.projected_points:
        table.add_row(
            pt.period_label,
            f"{pt.value:,.2f}",
            f"[{pt.lower_bound:,.2f} .. {pt.upper_bound:,.2f}]",
        )
    console.print(table)

    if report.summary_bullets:
        console.print("\n[bold cyan]Management Forecast Insights:[/]")
        for b in report.summary_bullets:
            console.print(f"  - {b}")
