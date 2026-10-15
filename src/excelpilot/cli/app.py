"""Main command-line interface entrypoint for ExcelPilot."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from excelpilot import __version__
from excelpilot.analysis.anomalies import AnomalyDetector, OutlierMethod
from excelpilot.analysis.forecasting import ForecastingEngine
from excelpilot.analysis.summary import ManagementSummaryGenerator
from excelpilot.cleaning import CleaningConfig, CleaningEngine, NullHandlingStrategy
from excelpilot.cli.exit_codes import ExitCode
from excelpilot.cli.formatters import (
    render_anomaly_report,
    render_cleaning_report,
    render_comparison_report,
    render_dataset_profile,
    render_forecast_report,
    render_privacy_warning,
    render_quality_report,
    render_recommendations,
    render_review_report,
    render_workbook_inspection,
)
from excelpilot.cli.wizard import WizardController
from excelpilot.comparison import ComparisonEngine
from excelpilot.config.loader import ConfigLoader
from excelpilot.core.dataset import Dataset
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.exceptions.base import ConfigurationError, WorkbookError
from excelpilot.exporters.excel import XlsxWriterDashboardExporter
from excelpilot.exporters.html import HtmlDashboardExporter
from excelpilot.logging.setup import configure_logging
from excelpilot.metrics.engine import MetricEngine
from excelpilot.metrics.models import MetricDefinition, MetricResult
from excelpilot.privacy.detector import PrivacyDetector
from excelpilot.profiling.engine import Profiler
from excelpilot.quality.engine import QualityEngine
from excelpilot.recommendations.charts import ChartRecommender
from excelpilot.recommendations.kpi import KPIRecommender
from excelpilot.review import DashboardReviewEngine
from excelpilot.semantics.classifier import SemanticClassifier
from excelpilot.workbook.reader import OpenpyxlReader

app = typer.Typer(
    name="excelpilot",
    help="Analyse Excel data and build professional dashboards from the command line.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"ExcelPilot {__version__}")
        raise typer.Exit(code=ExitCode.SUCCESS)


@app.callback()
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Display application version.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Enable verbose technical diagnostic logging."),
    ] = False,
) -> None:
    """ExcelPilot command-line tool."""
    _ = version
    configure_logging(verbose=verbose)


@app.command(name="version")
def show_version() -> None:
    """Display the ExcelPilot version."""
    console.print(f"ExcelPilot {__version__}")


@app.command(name="inspect")
def inspect_workbook(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
) -> None:
    """Inspect workbook metadata, worksheet names, and cell dimensions."""
    reader = OpenpyxlReader()
    try:
        metadata = reader.inspect(workbook)
    except WorkbookError as err:
        console.print(f"[red]Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    render_workbook_inspection(metadata, console)


@app.command(name="analyze")
def analyze_dataset(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", "-s", help="Worksheet name to analyse.")
    ] = None,
) -> None:
    """Profile dataset distributions, cardinality, and infer semantic column types."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or (meta.sheet_names[0] if meta.sheet_names else "")
        if not target_sheet:
            console.print("[red]Error:[/] Workbook contains no worksheets.")
            raise typer.Exit(code=ExitCode.WORKBOOK_ERROR)

        raw_df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(raw_df, name=target_sheet)
    profiler = Profiler()
    classifier = SemanticClassifier()
    privacy_detector = PrivacyDetector()

    with console.status("Profiling dataset..."):
        profile = profiler.profile(dataset)
        semantics = classifier.classify_dataset(dataset, profile)
        privacy = privacy_detector.scan(semantics)

    render_dataset_profile(profile, semantics, console)
    render_privacy_warning(privacy, console)


@app.command(name="quality")
def quality_audit(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", "-s", help="Worksheet name to audit.")
    ] = None,
) -> None:
    """Audit data quality across completeness, validity, uniqueness, and consistency."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or (meta.sheet_names[0] if meta.sheet_names else "")
        raw_df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(raw_df, name=target_sheet)
    quality_engine = QualityEngine()

    with console.status("Executing data quality audit..."):
        report = quality_engine.audit(dataset)

    render_quality_report(report, console)


@app.command(name="wizard")
def interactive_wizard(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Target path for generated dashboard.")
    ] = None,
) -> None:
    """Launch the interactive terminal wizard to design and build an Excel dashboard."""
    controller = WizardController(console=console)
    exit_code = controller.run(workbook_path=workbook, output_path=output)
    if exit_code != ExitCode.SUCCESS:
        raise typer.Exit(code=exit_code)


@app.command(name="build")
def build_dashboard(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    config: Annotated[
        Path, typer.Option("--config", "-c", help="Path to excelpilot.yaml configuration.")
    ],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Optional output override path.")
    ] = None,
) -> None:
    """Build an Excel dashboard non-interactively using an excelpilot.yaml configuration file."""
    try:
        cfg = ConfigLoader.load(config)
    except ConfigurationError as err:
        console.print(f"[red]Configuration Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.CONFIGURATION_ERROR) from err

    reader = OpenpyxlReader()
    target_sheet = cfg.source.worksheet
    try:
        if not target_sheet:
            meta = reader.inspect(workbook)
            target_sheet = meta.sheet_names[0]
        raw_df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(raw_df, name=target_sheet)
    profiler = Profiler()
    classifier = SemanticClassifier()
    quality_engine = QualityEngine()
    chart_recommender = ChartRecommender()
    exporter = XlsxWriterDashboardExporter()

    with console.status("Generating dashboard from configuration..."):
        profile = profiler.profile(dataset)
        semantics = classifier.classify_dataset(dataset, profile)
        quality_report = quality_engine.audit(dataset, profile, semantics)

        metric_engine = MetricEngine(
            currency_symbol="£" if cfg.dashboard.currency == "GBP" else "$"
        )
        kpis: list[MetricResult] = []

        if cfg.metrics:
            for m_key, m_val in cfg.metrics.items():
                m_def = MetricDefinition(
                    name=m_key,
                    label=m_val.label or m_key.replace("_", " ").title(),
                    column=m_val.column,
                    aggregation=m_val.aggregation,
                    formula=m_val.formula,
                    format_type=m_val.format_type,
                )
                kpis.append(metric_engine.calculate_metric(dataset, m_def))
        else:
            kpi_recs = KPIRecommender().recommend_kpis(profile, semantics)
            for rec in kpi_recs[:4]:
                m_def = MetricDefinition(
                    name=rec.name,
                    label=rec.label,
                    column=rec.column,
                    aggregation=rec.aggregation,
                    formula=rec.formula,
                    format_type=rec.format_type,
                )
                kpis.append(metric_engine.calculate_metric(dataset, m_def))

        charts = chart_recommender.recommend_charts(profile, semantics)
        summary_gen = ManagementSummaryGenerator()
        bullets = summary_gen.generate(kpis, quality_report)

        target_out = output or cfg.output.path
        spec = DashboardSpecification(
            title=cfg.dashboard.title,
            theme=cfg.dashboard.theme,
            currency_symbol="£" if cfg.dashboard.currency == "GBP" else "$",
            kpis=kpis,
            charts=charts[:4],
            quality_report=quality_report,
            executive_summary_bullets=bullets,
            metadata_info={"Configuration": config.name, "Sheet": target_sheet},
        )

        out_path = exporter.export(
            specification=spec,
            raw_dataframe=raw_df,
            cleaned_dataframe=raw_df,
            output_path=target_out,
        )

    console.print(
        f"[bold green]Success:[/] Dashboard written to [bold white]{out_path}[/bold white]"
    )


@app.command(name="init")
def init_project(
    path: Annotated[
        Path, typer.Option("--path", "-p", help="Directory or file path to initialize.")
    ] = Path(),
) -> None:
    """Initialize a starter excelpilot.yaml configuration file."""
    target = path / "excelpilot.yaml" if path.is_dir() else path
    if target.exists():
        console.print(f"[yellow]Notice:[/] File already exists at '{target}'.")
        return

    ConfigLoader.create_example_config(target)
    console.print(
        f"[bold green]Success:[/] Created configuration template at [bold white]{target}[/bold white]"
    )


@app.command(name="validate-config")
def validate_config(
    config: Annotated[Path, typer.Argument(help="Path to excelpilot.yaml file to validate.")],
) -> None:
    """Validate syntax and schema of an excelpilot.yaml configuration file."""
    try:
        cfg = ConfigLoader.load(config)
        console.print(f"[bold green]Valid configuration:[/] Project '{cfg.project.name}' is valid.")
    except ConfigurationError as err:
        console.print(f"[red]Invalid Configuration:[/]\n{err.message}")
        raise typer.Exit(code=ExitCode.CONFIGURATION_ERROR) from err


@app.command(name="suggest")
def suggest_insights(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", "-s", help="Worksheet name to evaluate.")
    ] = None,
) -> None:
    """Recommend candidate KPIs, business metrics, and suitable visualisations."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or (meta.sheet_names[0] if meta.sheet_names else "")
        raw_df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(raw_df, name=target_sheet)
    profiler = Profiler()
    classifier = SemanticClassifier()
    kpi_recommender = KPIRecommender()
    chart_recommender = ChartRecommender()

    with console.status("Evaluating recommendation heuristics..."):
        profile = profiler.profile(dataset)
        semantics = classifier.classify_dataset(dataset, profile)
        kpis = kpi_recommender.recommend_kpis(profile, semantics)
        charts = chart_recommender.recommend_charts(profile, semantics)

    render_recommendations(kpis, charts, console)


@app.command(name="clean")
def clean_dataset(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel (.xlsx) workbook.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", "-s", help="Worksheet name to clean.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Target output Excel file path.")
    ] = None,
    drop_nulls: Annotated[
        bool, typer.Option("--drop-nulls", help="Drop rows with null values.")
    ] = False,
    fill_zero: Annotated[
        bool, typer.Option("--fill-zero", help="Impute missing numbers with zero.")
    ] = False,
) -> None:
    """Clean dataset by stripping whitespace, deduplicating rows, and normalising column names."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or (meta.sheet_names[0] if meta.sheet_names else "")
        raw_df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(raw_df, name=target_sheet)
    null_strategy = (
        NullHandlingStrategy.DROP_ROWS
        if drop_nulls
        else (NullHandlingStrategy.FILL_ZERO if fill_zero else NullHandlingStrategy.PRESERVE)
    )
    config = CleaningConfig(null_strategy=null_strategy)
    cleaner = CleaningEngine(config=config)

    with console.status("Executing cleaning transformations..."):
        cleaned_df, report = cleaner.clean(dataset)

    render_cleaning_report(report, console)

    target_path = output or workbook.parent / f"{workbook.stem}-cleaned.xlsx"
    # Write cleaned data to Excel
    cleaned_df.write_excel(str(target_path))
    console.print(
        f"[bold green]Success:[/] Cleaned dataset written to [bold white]{target_path}[/bold white]"
    )


@app.command(name="compare")
def compare_workbooks(
    first: Annotated[Path, typer.Argument(help="Baseline Excel workbook path.")],
    second: Annotated[Path, typer.Argument(help="Comparison Excel workbook path.")],
    sheet1: Annotated[
        str | None, typer.Option("--sheet1", help="Worksheet name in baseline workbook.")
    ] = None,
    sheet2: Annotated[
        str | None, typer.Option("--sheet2", help="Worksheet name in comparison workbook.")
    ] = None,
) -> None:
    """Compare two workbooks to evaluate period-over-period metric deltas and dimensional variances."""
    reader = OpenpyxlReader()
    try:
        meta1 = reader.inspect(first)
        meta2 = reader.inspect(second)
        target_s1 = sheet1 or meta1.sheet_names[0]
        target_s2 = sheet2 or meta2.sheet_names[0]

        df1 = reader.read_worksheet(first, target_s1)
        df2 = reader.read_worksheet(second, target_s2)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    base_ds = Dataset(df1, name=f"{first.name} ({target_s1})")
    comp_ds = Dataset(df2, name=f"{second.name} ({target_s2})")

    engine = ComparisonEngine()
    with console.status("Computing period variances and dimensional trends..."):
        report = engine.compare(base_ds, comp_ds)

    render_comparison_report(report, console)


@app.command(name="review")
def review_dashboard(
    dashboard: Annotated[
        Path, typer.Argument(help="Path to an Excel dashboard workbook to review.")
    ],
) -> None:
    """Audit an existing Excel dashboard for visual density, number formatting, and layout standards."""
    engine = DashboardReviewEngine()
    try:
        with console.status("Reviewing dashboard layout and design rules..."):
            report = engine.review(dashboard)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    render_review_report(report, console)


@app.command(name="anomalies")
def detect_anomalies(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel workbook to inspect.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", "-s", help="Worksheet name to inspect.")
    ] = None,
    column: Annotated[
        str | None, typer.Option("--column", "-c", help="Specific numerical column to test.")
    ] = None,
    method: Annotated[
        OutlierMethod,
        typer.Option("--method", "-m", help="Outlier detection method: 'iqr' or 'zscore'."),
    ] = OutlierMethod.IQR,
    threshold: Annotated[
        float,
        typer.Option(
            "--threshold",
            "-t",
            help="Z-score threshold (default 3.0) or IQR multiplier (default 1.5).",
        ),
    ] = 1.5,
) -> None:
    """Detect statistical outliers and anomalies in numerical dataset columns."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or meta.sheet_names[0]
        df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(df, name=f"{workbook.name} ({target_sheet})")
    iqr_mult = threshold if method == OutlierMethod.IQR else 1.5
    z_thresh = threshold if method == OutlierMethod.ZSCORE else 3.0
    detector = AnomalyDetector(method=method, z_threshold=z_thresh, iqr_multiplier=iqr_mult)

    target_cols = [column] if column else None
    with console.status("Scanning numerical distributions for statistical anomalies..."):
        report = detector.detect_dataset(dataset, target_columns=target_cols)

    render_anomaly_report(report, console)


@app.command(name="forecast")
def forecast_metric(
    workbook: Annotated[Path, typer.Argument(help="Path to the Excel workbook.")],
    date_col: Annotated[
        str, typer.Option("--date-col", "-d", help="Date or temporal dimension column.")
    ],
    metric: Annotated[
        str, typer.Option("--metric", "-m", help="Numerical metric column to forecast.")
    ],
    sheet: Annotated[str | None, typer.Option("--sheet", "-s", help="Worksheet name.")] = None,
    periods: Annotated[
        int, typer.Option("--periods", "-p", help="Number of forward periods to project.")
    ] = 3,
) -> None:
    """Calculate time-series trends, growth rates, and forward projections."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or meta.sheet_names[0]
        df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(df, name=f"{workbook.name} ({target_sheet})")
    engine = ForecastingEngine()

    try:
        with console.status(
            "Calculating linear regression trend and forward confidence intervals..."
        ):
            result = engine.forecast(
                dataset, date_column=date_col, metric_column=metric, periods=periods
            )
    except ValueError as err:
        console.print(f"[red]Forecast Error:[/] {err}")
        raise typer.Exit(code=ExitCode.ANALYSIS_ERROR) from err

    render_forecast_report(result, console)


@app.command(name="export-html")
def export_html_dashboard(
    workbook: Annotated[Path, typer.Argument(help="Path to the source Excel workbook.")],
    sheet: Annotated[str | None, typer.Option("--sheet", "-s", help="Worksheet name.")] = None,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Destination path for HTML report.")
    ] = None,
    theme: Annotated[
        str,
        typer.Option("--theme", "-t", help="Theme: executive, financial, operational, minimal."),
    ] = "executive",
    title: Annotated[
        str, typer.Option("--title", help="Dashboard title.")
    ] = "Executive Business Dashboard",
) -> None:
    """Generate a standalone, responsive HTML executive dashboard with embedded SVG charts."""
    reader = OpenpyxlReader()
    try:
        meta = reader.inspect(workbook)
        target_sheet = sheet or meta.sheet_names[0]
        df = reader.read_worksheet(workbook, target_sheet)
    except WorkbookError as err:
        console.print(f"[red]Workbook Error:[/] {err.message}")
        raise typer.Exit(code=ExitCode.WORKBOOK_ERROR) from err

    dataset = Dataset(df, name=f"{workbook.name} ({target_sheet})")
    profiler = Profiler()
    classifier = SemanticClassifier()
    kpi_rec = KPIRecommender()
    chart_rec = ChartRecommender()
    metric_engine = MetricEngine(currency_symbol="£")

    profile = profiler.profile(dataset)
    semantic_profile = classifier.classify_dataset(dataset, profile)
    recommended_kpis = kpi_rec.recommend_kpis(profile, semantic_profile)[:4]
    charts = chart_rec.recommend_charts(profile, semantic_profile)[:2]

    kpi_results = []
    for k in recommended_kpis:
        m_def = MetricDefinition(
            name=k.name,
            label=k.label,
            column=k.column,
            aggregation=k.aggregation,
            formula=k.formula,
            format_type=k.format_type,
        )
        kpi_results.append(metric_engine.calculate_metric(dataset, m_def))

    spec = DashboardSpecification(
        title=title,
        reporting_period=f"Generated from {workbook.name} ({target_sheet})",
        theme=theme,
        currency_symbol="£",
        kpis=kpi_results,
        charts=charts,
    )

    dest_path = output or Path("reports") / f"{workbook.stem}-dashboard.html"
    exporter = HtmlDashboardExporter(currency_symbol="£")
    with console.status("Generating standalone HTML dashboard..."):
        rendered_path = exporter.export(spec, df, dest_path)

    console.print(
        f"[green]Success:[/] Standalone HTML dashboard generated at [bold white]{rendered_path}[/]"
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
