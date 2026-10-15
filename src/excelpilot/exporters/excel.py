"""Production Excel dashboard renderer using XlsxWriter."""

import datetime
from pathlib import Path
from typing import Any

import polars as pl
import xlsxwriter

from excelpilot.core.dataset import Dataset
from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.dashboards.themes import DashboardTheme, get_theme
from excelpilot.exceptions.base import OutputError
from excelpilot.exporters.protocol import DashboardExporter
from excelpilot.metrics.engine import MetricEngine


class XlsxWriterDashboardExporter(DashboardExporter):
    """Generates multi-sheet Excel workbooks with native charts and KPI cards."""

    def export(
        self,
        specification: DashboardSpecification,
        raw_dataframe: pl.DataFrame,
        cleaned_dataframe: pl.DataFrame,
        output_path: Path,
    ) -> Path:
        """Render complete workbook structure based on specification and datasets."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            wb = xlsxwriter.Workbook(str(output_path))
        except Exception as err:
            raise OutputError(
                f"Failed to initialise destination workbook at '{output_path}': {err}"
            ) from err

        theme = get_theme(specification.theme)

        try:
            # 1. Create worksheets
            ws_dash = wb.add_worksheet("Dashboard")
            ws_analysis = wb.add_worksheet("Analysis")
            ws_quality = wb.add_worksheet("Data_Quality")
            ws_clean = wb.add_worksheet("Cleaned_Data")
            ws_raw = wb.add_worksheet("Raw_Data")
            ws_meta = wb.add_worksheet("Metadata")

            # Enable gridlines on Dashboard
            ws_dash.hide_gridlines(0)

            # Common format styles
            fmt_title = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.title_size,
                    "bold": True,
                    "font_color": theme.colors.primary,
                }
            )
            fmt_subtitle = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.body_size,
                    "font_color": "#6B7280",
                }
            )
            fmt_bullet = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.body_size,
                    "font_color": theme.colors.neutral_dark,
                }
            )
            fmt_kpi_label = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.kpi_label_size,
                    "font_color": "#6B7280",
                    "bold": True,
                    "align": "center",
                    "valign": "vcenter",
                    "bg_color": theme.colors.neutral_light,
                    "top": 1,
                    "left": 1,
                    "right": 1,
                    "border_color": theme.colors.card_border,
                }
            )
            fmt_kpi_val = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.kpi_value_size,
                    "font_color": theme.colors.primary,
                    "bold": True,
                    "align": "center",
                    "valign": "vcenter",
                    "bg_color": theme.colors.neutral_light,
                    "bottom": 1,
                    "left": 1,
                    "right": 1,
                    "border_color": theme.colors.card_border,
                }
            )
            fmt_tbl_header = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.body_size,
                    "font_color": "#FFFFFF",
                    "bg_color": theme.colors.primary,
                    "bold": True,
                    "align": "left",
                    "border": 1,
                    "border_color": theme.colors.primary,
                }
            )
            fmt_cell_text = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.body_size,
                    "border": 1,
                    "border_color": "#E5E7EB",
                }
            )
            fmt_cell_number = wb.add_format(
                {
                    "font_name": theme.font_name,
                    "font_size": theme.body_size,
                    "num_format": "#,##0.00",
                    "border": 1,
                    "border_color": "#E5E7EB",
                }
            )

            # ----------------------------------------------------
            # SHEET 1: DASHBOARD
            # ----------------------------------------------------
            # Header Title & Period
            ws_dash.set_column("A:A", 3)
            ws_dash.set_column("B:E", 18)
            ws_dash.set_column("F:F", 4)
            ws_dash.set_column("G:J", 18)

            ws_dash.write("B2", specification.title, fmt_title)
            period_str = (
                f"Reporting Period: {specification.reporting_period}"
                if specification.reporting_period
                else "Generated by ExcelPilot"
            )
            ws_dash.write("B3", period_str, fmt_subtitle)

            # Executive Summary Bullets
            curr_row = 4
            if specification.executive_summary_bullets:
                for bullet in specification.executive_summary_bullets[:3]:
                    ws_dash.write(curr_row, 1, f"-  {bullet}", fmt_bullet)
                    curr_row += 1
                curr_row += 1
            else:
                curr_row = 5

            # KPI Scorecards
            kpi_start_col = 1  # Column B
            for idx, kpi in enumerate(specification.kpis[:4]):
                card_col = kpi_start_col + (idx * 2)
                # Label row
                ws_dash.write(curr_row, card_col, kpi.label.upper(), fmt_kpi_label)
                ws_dash.write(curr_row, card_col + 1, "", fmt_kpi_label)
                ws_dash.merge_range(
                    curr_row, card_col, curr_row, card_col + 1, kpi.label.upper(), fmt_kpi_label
                )
                # Value row
                ws_dash.write(curr_row + 1, card_col, kpi.formatted_value, fmt_kpi_val)
                ws_dash.write(curr_row + 1, card_col + 1, "", fmt_kpi_val)
                ws_dash.merge_range(
                    curr_row + 1,
                    card_col,
                    curr_row + 1,
                    card_col + 1,
                    kpi.formatted_value,
                    fmt_kpi_val,
                )

            ws_dash.set_row(curr_row, 18)
            ws_dash.set_row(curr_row + 1, 32)

            # ----------------------------------------------------
            # SHEET 2: ANALYSIS & CHARTS
            # ----------------------------------------------------
            analysis_row = 1
            metric_engine = MetricEngine(currency_symbol=specification.currency_symbol)

            chart_positions = [
                (curr_row + 4, 1),  # Row below KPIs, Col B
                (curr_row + 4, 6),  # Row below KPIs, Col G
                (curr_row + 21, 1),  # Second row, Col B
                (curr_row + 21, 6),  # Second row, Col G
            ]

            for chart_idx, chart_spec in enumerate(specification.charts[:4]):
                # Aggregate data for chart
                try:
                    agg_df = metric_engine.aggregate_by_dimension(
                        dataset=Dataset(cleaned_dataframe, name="Cleaned_Data"),
                        dimension_col=chart_spec.dimension_column,
                        metric_col=chart_spec.metric_column,
                        aggregation=chart_spec.aggregation,
                        top_n=chart_spec.top_n or 10,
                    )
                except Exception:
                    continue

                if agg_df.is_empty():
                    continue

                # Write aggregate table on Analysis sheet
                ws_analysis.write(
                    analysis_row, 1, f"Table {chart_idx + 1}: {chart_spec.title}", fmt_title
                )
                ws_analysis.write(analysis_row + 1, 1, chart_spec.dimension_column, fmt_tbl_header)
                ws_analysis.write(analysis_row + 1, 2, chart_spec.metric_column, fmt_tbl_header)

                data_start_row = analysis_row + 2
                for r_idx, row_tuple in enumerate(agg_df.iter_rows()):
                    dim_val = str(row_tuple[0])
                    num_val = float(row_tuple[1])
                    ws_analysis.write_string(
                        data_start_row + r_idx, 1, self._escape_string(dim_val), fmt_cell_text
                    )
                    ws_analysis.write_number(data_start_row + r_idx, 2, num_val, fmt_cell_number)

                data_end_row = data_start_row + agg_df.height - 1

                # Construct Chart
                xlsx_chart_type = self._map_chart_type(chart_spec.chart_type.value)
                chart = wb.add_chart({"type": xlsx_chart_type})
                chart.set_title(
                    {
                        "name": chart_spec.title,
                        "name_font": {"name": theme.font_name, "size": 11, "bold": True},
                    }
                )
                chart.set_legend({"font": {"name": theme.font_name, "size": 9}})
                chart.set_size({"width": 460, "height": 300})

                chart.add_series(
                    {
                        "name": chart_spec.title,
                        "categories": ["Analysis", data_start_row, 1, data_end_row, 1],
                        "values": ["Analysis", data_start_row, 2, data_end_row, 2],
                        "fill": {
                            "color": theme.colors.chart_palette[
                                chart_idx % len(theme.colors.chart_palette)
                            ]
                        },
                    }
                )

                if chart_spec.chart_type.value not in ("donut", "pie"):
                    chart.set_x_axis(
                        {
                            "name_font": {"name": theme.font_name, "size": 9},
                            "num_font": {"name": theme.font_name, "size": 8},
                        }
                    )
                    chart.set_y_axis(
                        {
                            "name_font": {"name": theme.font_name, "size": 9},
                            "num_font": {"name": theme.font_name, "size": 8},
                        }
                    )

                # Insert chart on Dashboard
                if chart_idx < len(chart_positions):
                    c_row, c_col = chart_positions[chart_idx]
                    ws_dash.insert_chart(c_row, c_col, chart)

                analysis_row = data_end_row + 4

            # Auto-fit Analysis columns
            ws_analysis.set_column("A:A", 3)
            ws_analysis.set_column("B:C", 25)

            # ----------------------------------------------------
            # SHEET 3: DATA QUALITY AUDIT
            # ----------------------------------------------------
            self._render_quality_sheet(ws_quality, wb, specification, theme)

            # ----------------------------------------------------
            # SHEET 4 & 5: CLEANED DATA & RAW DATA
            # ----------------------------------------------------
            self._render_table_sheet(
                ws_clean, cleaned_dataframe, fmt_tbl_header, fmt_cell_text, fmt_cell_number
            )
            self._render_table_sheet(
                ws_raw, raw_dataframe, fmt_tbl_header, fmt_cell_text, fmt_cell_number
            )

            # ----------------------------------------------------
            # SHEET 6: METADATA
            # ----------------------------------------------------
            self._render_metadata_sheet(
                ws_meta, specification, raw_dataframe, fmt_title, fmt_tbl_header, fmt_cell_text
            )

        finally:
            wb.close()

        return output_path.resolve()

    def _render_quality_sheet(
        self,
        ws: Any,
        wb: xlsxwriter.Workbook,
        spec: DashboardSpecification,
        theme: DashboardTheme,
    ) -> None:
        """Render data quality scores and detected issues."""
        fmt_title = wb.add_format(
            {
                "font_name": theme.font_name,
                "font_size": 14,
                "bold": True,
                "font_color": theme.colors.primary,
            }
        )
        fmt_hdr = wb.add_format(
            {
                "font_name": theme.font_name,
                "font_size": 10,
                "bold": True,
                "bg_color": theme.colors.primary,
                "font_color": "#FFFFFF",
                "border": 1,
            }
        )
        fmt_txt = wb.add_format({"font_name": theme.font_name, "font_size": 10, "border": 1})
        fmt_num = wb.add_format(
            {"font_name": theme.font_name, "font_size": 10, "num_format": "0.0", "border": 1}
        )
        fmt_high = wb.add_format(
            {
                "font_name": theme.font_name,
                "font_size": 10,
                "bg_color": "#FEE2E2",
                "font_color": "#991B1B",
                "bold": True,
                "border": 1,
            }
        )
        fmt_med = wb.add_format(
            {
                "font_name": theme.font_name,
                "font_size": 10,
                "bg_color": "#FEF3C7",
                "font_color": "#92400E",
                "bold": True,
                "border": 1,
            }
        )
        fmt_low = wb.add_format(
            {
                "font_name": theme.font_name,
                "font_size": 10,
                "bg_color": "#E0F2FE",
                "font_color": "#075985",
                "border": 1,
            }
        )

        ws.set_column("A:A", 3)
        ws.set_column("B:B", 20)
        ws.set_column("C:C", 14)
        ws.set_column("D:D", 18)
        ws.set_column("E:E", 50)
        ws.set_column("F:F", 14)

        ws.write("B2", "Data Quality Audit Report", fmt_title)

        q_report = spec.quality_report
        if q_report is None:
            ws.write("B4", "No data quality audit data available.", fmt_txt)
            return

        ws.write("B4", "Dimension", fmt_hdr)
        ws.write("C4", "Score (/100)", fmt_hdr)

        dim_row = 5
        for dim, score in q_report.dimension_scores.items():
            ws.write(dim_row, 1, dim.value.title(), fmt_txt)
            ws.write(dim_row, 2, score, fmt_num)
            dim_row += 1

        ws.write(dim_row, 1, "Overall Score", fmt_hdr)
        ws.write(dim_row, 2, q_report.overall_score, fmt_hdr)

        # Issues table
        issues_start_row = dim_row + 3
        ws.write(issues_start_row, 1, "Severity", fmt_hdr)
        ws.write(issues_start_row, 2, "Dimension", fmt_hdr)
        ws.write(issues_start_row, 3, "Column", fmt_hdr)
        ws.write(issues_start_row, 4, "Description", fmt_hdr)
        ws.write(issues_start_row, 5, "Records Affected", fmt_hdr)

        if not q_report.issues:
            ws.write(issues_start_row + 1, 1, "NONE", fmt_low)
            ws.write(issues_start_row + 1, 2, "-", fmt_txt)
            ws.write(issues_start_row + 1, 3, "-", fmt_txt)
            ws.write(issues_start_row + 1, 4, "No quality issues detected.", fmt_txt)
            ws.write(issues_start_row + 1, 5, 0, fmt_txt)
        else:
            for idx, issue in enumerate(q_report.issues):
                row = issues_start_row + 1 + idx
                sev_fmt = (
                    fmt_high
                    if issue.severity.value == "HIGH"
                    else (fmt_med if issue.severity.value == "MEDIUM" else fmt_low)
                )
                ws.write(row, 1, issue.severity.value, sev_fmt)
                ws.write(row, 2, issue.dimension.value.title(), fmt_txt)
                ws.write(row, 3, issue.column or "(Dataset)", fmt_txt)
                ws.write(row, 4, issue.description, fmt_txt)
                ws.write(row, 5, issue.affected_count, fmt_txt)

    def _render_table_sheet(
        self,
        ws: Any,
        df: pl.DataFrame,
        fmt_hdr: Any,
        fmt_txt: Any,
        fmt_num: Any,
    ) -> None:
        """Write raw or cleaned DataFrame with formatted headers and auto-filters."""
        if df.is_empty():
            ws.write(0, 0, "No records in dataset.")
            return

        cols = df.columns
        for c_idx, col_name in enumerate(cols):
            ws.write(0, c_idx, col_name, fmt_hdr)

        max_rows_to_write = min(df.height, 50_000)
        for r_idx in range(max_rows_to_write):
            row_vals = df.row(r_idx)
            for c_idx, val in enumerate(row_vals):
                if val is None:
                    ws.write_blank(r_idx + 1, c_idx, None, fmt_txt)
                elif isinstance(val, (int, float)):
                    ws.write_number(r_idx + 1, c_idx, float(val), fmt_num)
                else:
                    ws.write_string(r_idx + 1, c_idx, self._escape_string(str(val)), fmt_txt)

        ws.autofilter(0, 0, max_rows_to_write, len(cols) - 1)
        for c_idx, col_name in enumerate(cols):
            ws.set_column(c_idx, c_idx, max(12, min(len(col_name) + 4, 35)))

    def _render_metadata_sheet(
        self,
        ws: Any,
        spec: DashboardSpecification,
        df: pl.DataFrame,
        fmt_title: Any,
        fmt_hdr: Any,
        fmt_txt: Any,
    ) -> None:
        """Write audit metadata, timestamps, and schema summary."""
        ws.set_column("A:A", 3)
        ws.set_column("B:B", 25)
        ws.set_column("C:C", 40)

        ws.write("B2", "Workbook Metadata", fmt_title)
        ws.write("B4", "Property", fmt_hdr)
        ws.write("C4", "Value", fmt_hdr)

        props = [
            (
                "Generated At",
                datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            ),
            ("Generator", "ExcelPilot v0.1.0"),
            ("Theme", spec.theme.title()),
            ("Total Rows Inspected", str(df.height)),
            ("Total Columns", str(df.width)),
        ]
        props.extend(list(spec.metadata_info.items()))

        for idx, (prop, val) in enumerate(props):
            ws.write(5 + idx, 1, prop, fmt_txt)
            ws.write(5 + idx, 2, self._escape_string(val), fmt_txt)

    def _map_chart_type(self, chart_type: str) -> str:
        """Translate domain chart type to native Excel chart type string."""
        if chart_type == "donut":
            return "doughnut"
        if chart_type == "bar":
            return "bar"
        if chart_type == "line":
            return "line"
        return "column"

    def _escape_string(self, text: str) -> str:
        """Sanitise text against CSV/Excel Formula Injection (DDE attack vectors)."""
        if text and text[0] in ("=", "+", "-", "@"):
            return "'" + text
        return text
