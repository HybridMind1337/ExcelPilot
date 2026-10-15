"""Interactive CLI wizard for guided workbook analysis and dashboard creation."""

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from excelpilot.analysis.summary import ManagementSummaryGenerator
from excelpilot.cli.exit_codes import ExitCode
from excelpilot.cli.formatters import (
    render_dashboard_plan,
    render_dataset_profile,
    render_privacy_warning,
    render_quality_report,
)
from excelpilot.core.dataset import Dataset
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.exporters.excel import XlsxWriterDashboardExporter
from excelpilot.metrics.engine import MetricEngine
from excelpilot.metrics.models import MetricDefinition, MetricResult
from excelpilot.privacy.detector import PrivacyDetector
from excelpilot.profiling.engine import Profiler
from excelpilot.quality.engine import QualityEngine
from excelpilot.recommendations.charts import ChartRecommender
from excelpilot.recommendations.kpi import KPIRecommender
from excelpilot.semantics.classifier import SemanticClassifier
from excelpilot.workbook.reader import OpenpyxlReader


class WizardController:
    """Orchestrates the interactive 17-step guided dashboard design workflow."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.reader = OpenpyxlReader()
        self.profiler = Profiler()
        self.classifier = SemanticClassifier()
        self.quality_engine = QualityEngine()
        self.kpi_recommender = KPIRecommender()
        self.chart_recommender = ChartRecommender()
        self.privacy_detector = PrivacyDetector()
        self.exporter = XlsxWriterDashboardExporter()

    def run(self, workbook_path: Path, output_path: Path | None = None) -> int:
        """Execute the interactive wizard."""
        self.console.print("[bold cyan]ExcelPilot Interactive Dashboard Wizard[/bold cyan]\n")

        # Step 1: Open workbook
        if not workbook_path.exists():
            self.console.print(f"[red]Error: File '{workbook_path}' does not exist.[/red]")
            return ExitCode.WORKBOOK_ERROR

        metadata = self.reader.inspect(workbook_path)
        self.console.print(f"Source Workbook: [bold white]{workbook_path.name}[/bold white]")

        # Step 2 & 3: Detect and select worksheet
        sheets = metadata.sheet_names
        if not sheets:
            self.console.print("[red]Error: Workbook contains no worksheets.[/red]")
            return ExitCode.WORKBOOK_ERROR

        if len(sheets) == 1:
            selected_sheet = sheets[0]
            self.console.print(f"Using worksheet: [bold green]{selected_sheet}[/bold green]\n")
        else:
            self.console.print("\nWorksheets detected:")
            for idx, s in enumerate(sheets, 1):
                self.console.print(f"  {idx}. {s}")

            choice_str = Prompt.ask(
                "Select worksheet number",
                default="1",
                choices=[str(i) for i in range(1, len(sheets) + 1)],
            )
            selected_sheet = sheets[int(choice_str) - 1]
            self.console.print(f"Selected: [bold green]{selected_sheet}[/bold green]\n")

        # Load worksheet data
        with self.console.status("Loading dataset..."):
            raw_df = self.reader.read_worksheet(workbook_path, selected_sheet)
            if raw_df.is_empty():
                self.console.print("[red]Error: Selected worksheet is empty.[/red]")
                return ExitCode.ANALYSIS_ERROR
            dataset = Dataset(raw_df, name=selected_sheet)

        # Step 4, 5, 6: Profile, Semantics, Quality, Privacy
        with self.console.status("Analysing dataset profile, semantics, and data quality..."):
            profile = self.profiler.profile(dataset)
            semantics = self.classifier.classify_dataset(dataset, profile)
            quality_report = self.quality_engine.audit(dataset, profile, semantics)
            privacy_report = self.privacy_detector.scan(semantics)

        # Render inspection findings
        render_dataset_profile(profile, semantics, self.console)
        render_quality_report(quality_report, self.console)
        render_privacy_warning(privacy_report, self.console)

        # Step 7: Dataset Purpose
        self.console.print("\nWhat is the primary purpose of this dataset?")
        purposes = [
            "Sales and revenue",
            "Finance",
            "Inventory",
            "Customer analysis",
            "Marketing",
            "Operations",
            "General analysis",
        ]
        for idx, p in enumerate(purposes, 1):
            self.console.print(f"  {idx}. {p}")
        purpose_idx = Prompt.ask(
            "Select purpose",
            default="1",
            choices=[str(i) for i in range(1, len(purposes) + 1)],
        )
        selected_purpose = purposes[int(purpose_idx) - 1]

        # Step 8: Metric Selection
        metric_candidates = semantics.metric_candidates
        if not metric_candidates:
            # Fallback to all numeric columns or default
            metric_candidates = [
                c.name
                for c in profile.columns
                if "int" in c.physical_type or "float" in c.physical_type
            ]

        if not metric_candidates:
            primary_metric = profile.columns[0].name
        elif len(metric_candidates) == 1:
            primary_metric = metric_candidates[0]
        else:
            self.console.print("\nSelect the primary metric:")
            for idx, m in enumerate(metric_candidates, 1):
                self.console.print(f"  {idx}. {m}")
            m_idx = Prompt.ask(
                "Select metric",
                default="1",
                choices=[str(i) for i in range(1, len(metric_candidates) + 1)],
            )
            primary_metric = metric_candidates[int(m_idx) - 1]

        # Step 9: Dimension Selection
        dim_candidates = [
            c for c in semantics.columns if c.is_dimension_candidate and c.name != primary_metric
        ]
        available_dims = [c.name for c in dim_candidates]

        self.console.print(
            f"\nIdentified category dimensions: {', '.join(available_dims) if available_dims else 'None'}"
        )

        # Step 10: Time Field
        temporal_cols = semantics.temporal_columns
        time_field: str | None = None
        if temporal_cols:
            self.console.print(f"\nDetected date/time fields: {', '.join(temporal_cols)}")
            time_field = temporal_cols[0]

        # Step 11: Recommend KPIs
        recommended_kpi_defs = self.kpi_recommender.recommend_kpis(profile, semantics)
        metric_engine = MetricEngine(currency_symbol="£")
        kpi_results: list[MetricResult] = []

        for kpi_def in recommended_kpi_defs[:4]:
            m_def = MetricDefinition(
                name=kpi_def.name,
                label=kpi_def.label,
                column=kpi_def.column,
                aggregation=kpi_def.aggregation,
                formula=kpi_def.formula,
                format_type=kpi_def.format_type,
            )
            res = metric_engine.calculate_metric(dataset, m_def)
            kpi_results.append(res)

        # Step 12: Recommend Charts
        recommended_charts = self.chart_recommender.recommend_charts(
            profile,
            semantics,
            primary_metric_col=primary_metric,
        )

        # Generate summary bullets
        summary_gen = ManagementSummaryGenerator()
        bullets = summary_gen.generate(kpi_results, quality_report)

        # Step 13: Dashboard Plan
        target_output = output_path or workbook_path.parent / f"{workbook_path.stem}-dashboard.xlsx"
        spec = DashboardSpecification(
            title=f"{selected_sheet} Performance Dashboard",
            reporting_period=f"Time Dimension: {time_field}" if time_field else None,
            theme="executive",
            currency_symbol="£",
            kpis=kpi_results,
            charts=recommended_charts[:4],
            quality_report=quality_report,
            executive_summary_bullets=bullets,
            metadata_info={
                "Purpose": selected_purpose,
                "Source Workbook": workbook_path.name,
                "Source Worksheet": selected_sheet,
            },
        )

        self.console.print("\n")
        render_dashboard_plan(spec, self.console)

        # Step 14: Confirmation
        confirm = Confirm.ask(
            f"\nGenerate Excel dashboard at '[bold white]{target_output}[/bold white]'?",
            default=True,
        )
        if not confirm:
            self.console.print("[yellow]Dashboard generation cancelled.[/yellow]")
            return ExitCode.SUCCESS

        # Step 15 & 16: Excel Generation & Validation
        with self.console.status(f"Generating dashboard at '{target_output}'..."):
            out_file = self.exporter.export(
                specification=spec,
                raw_dataframe=raw_df,
                cleaned_dataframe=raw_df,  # in v0.1 cleaned matches raw
                output_path=target_output,
            )

        # Step 17: Show output path
        self.console.print("\n[bold green]Success:[/] Dashboard successfully generated at:")
        self.console.print(f"  [bold white]{out_file}[/bold white]\n")

        return ExitCode.SUCCESS
