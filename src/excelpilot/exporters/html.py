"""Standalone, dependency-free interactive HTML executive dashboard exporter."""

import datetime
from pathlib import Path
from typing import Any

import polars as pl

from excelpilot.dashboards.models import DashboardSpecification
from excelpilot.dashboards.themes import get_theme
from excelpilot.metrics.engine import MetricEngine


class HtmlDashboardExporter:
    """Renders standalone, responsive HTML dashboards with embedded SVG visualisations."""

    def __init__(self, currency_symbol: str = "£") -> None:
        self.metric_engine = MetricEngine(currency_symbol=currency_symbol)

    def export(
        self,
        specification: DashboardSpecification,
        dataframe: pl.DataFrame,
        output_path: Path,
    ) -> Path:
        """Render complete standalone HTML dashboard to output_path."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        theme = get_theme(specification.theme)
        primary_hex = theme.colors.primary.lstrip("#")
        secondary_hex = theme.colors.secondary.lstrip("#")
        accent_hex = theme.colors.accent.lstrip("#")

        # 1. Compute KPI values
        kpi_cards_html = self._render_kpi_cards(specification)

        # 2. Render SVG Charts
        charts_html = self._render_charts(specification, dataframe, theme)

        # 3. Render Sample Table
        table_html = self._render_data_preview(dataframe, limit=10)

        # 4. Generate Full Document
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        reporting_sub = specification.reporting_period or "Executive Performance Report"
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{specification.title} - ExcelPilot</title>
  <style>
    :root {{
      --bg-main: #0B0F19;
      --bg-card: #151D30;
      --bg-card-hover: #1E2942;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --border-color: #26334D;
      --accent-primary: #{primary_hex};
      --accent-secondary: #{secondary_hex};
      --accent-kpi: #{accent_hex};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }}
    .header-title h1 {{ font-size: 1.75rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.02em; }}
    .header-title p {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }}
    .header-meta {{ text-align: right; font-size: 0.8rem; color: var(--text-muted); }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      font-weight: 600;
      color: var(--accent-primary);
      margin-bottom: 0.25rem;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      border-top: 4px solid var(--accent-primary);
      transition: transform 0.15s ease, background-color 0.15s ease;
    }}
    .kpi-card:hover {{ transform: translateY(-2px); background-color: var(--bg-card-hover); }}
    .kpi-label {{ font-size: 0.825rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }}
    .kpi-value {{ font-size: 1.85rem; font-weight: 700; margin: 0.4rem 0; color: #FFFFFF; }}
    .kpi-footer {{ font-size: 0.75rem; color: var(--text-muted); }}
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1.5rem;
    }}
    .chart-title {{ font-size: 1.05rem; font-weight: 600; margin-bottom: 1rem; color: #FFFFFF; }}
    .chart-body {{ display: flex; justify-content: center; align-items: center; min-height: 240px; }}
    svg {{ max-width: 100%; height: auto; }}
    .table-section {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 2rem;
      overflow-x: auto;
    }}
    .section-title {{ font-size: 1.05rem; font-weight: 600; margin-bottom: 1rem; color: #FFFFFF; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    th {{
      text-align: left;
      padding: 0.65rem 0.75rem;
      border-bottom: 2px solid var(--border-color);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
    }}
    td {{
      padding: 0.65rem 0.75rem;
      border-bottom: 1px solid var(--border-color);
      color: #E2E8F0;
    }}
    tr:nth-child(even) td {{ background-color: rgba(255, 255, 255, 0.015); }}
    footer {{
      text-align: center;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border-color);
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-title">
        <span class="badge">Executive Dashboard</span>
        <h1>{specification.title}</h1>
        <p>{reporting_sub}</p>
      </div>
      <div class="header-meta">
        <div>Theme: <strong>{specification.theme.title()}</strong></div>
        <div>Total Rows: <strong>{dataframe.height:,}</strong></div>
        <div>Generated: <strong>{timestamp}</strong></div>
      </div>
    </header>

    <main>
      <div class="kpi-grid">
        {kpi_cards_html}
      </div>

      <div class="charts-grid">
        {charts_html}
      </div>

      <div class="table-section">
        <div class="section-title">Data Sample (Top 10 Records)</div>
        {table_html}
      </div>
    </main>

    <footer>
      Produced by ExcelPilot - Open source Excel analysis and dashboard generation.
    </footer>
  </div>
</body>
</html>
"""
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    def _render_kpi_cards(
        self,
        spec: DashboardSpecification,
    ) -> str:
        """Format KPIs into HTML cards using MetricResult values."""
        cards = []
        for kpi in spec.kpis:
            cards.append(f"""
        <div class="kpi-card">
          <div class="kpi-label">{kpi.label}</div>
          <div class="kpi-value">{kpi.formatted_value}</div>
          <div class="kpi-footer">Metric: {kpi.name}</div>
        </div>
            """)
        return "\n".join(cards)

    def _render_charts(
        self,
        spec: DashboardSpecification,
        df: pl.DataFrame,
        theme: Any,
    ) -> str:
        """Render pure SVG charts for specified visualisations."""
        rendered = []
        for chart in spec.charts:
            chart_html = ""
            c_type = chart.chart_type.value.lower()
            dim = chart.dimension_column
            met = chart.metric_column

            if dim in df.columns and met in df.columns:
                grouped = (
                    df.group_by(dim)
                    .agg(pl.col(met).sum().alias("total"))
                    .sort("total", descending=True)
                    .head(chart.top_n or 8)
                )

                labels = [str(x) for x in grouped[dim].to_list()]
                values = [float(x) for x in grouped["total"].to_list()]

                if c_type in ["pie", "donut"]:
                    chart_svg = self._generate_donut_svg(labels, values, theme)
                elif c_type == "line":
                    chart_svg = self._generate_line_svg(labels, values, theme)
                else:
                    chart_svg = self._generate_bar_svg(labels, values, theme)

                chart_html = f"""
        <div class="chart-card">
          <div class="chart-title">{chart.title}</div>
          <div class="chart-body">
            {chart_svg}
          </div>
        </div>
                """
                rendered.append(chart_html)

        return "\n".join(rendered)

    def _generate_bar_svg(self, labels: list[str], values: list[float], theme: Any) -> str:
        """Generate responsive SVG horizontal bar chart."""
        if not values or max(values) == 0:
            return "<p style='color:#94A3B8'>No data</p>"

        max_val = max(values)
        w, row_h = 460, 32
        h = max(160, len(labels) * row_h + 30)
        svg_bars = []

        for i, (lbl, val) in enumerate(zip(labels, values, strict=False)):
            bar_w = (val / max_val) * 260
            y = 20 + (i * row_h)
            lbl_short = lbl[:18] + ("..." if len(lbl) > 18 else "")
            svg_bars.append(f"""
              <text x="5" y="{y + 14}" fill="#94A3B8" font-size="11" font-family="sans-serif">{lbl_short}</text>
              <rect x="130" y="{y}" width="{bar_w:.1f}" height="18" rx="3" fill="{theme.colors.primary}"/>
              <text x="{140 + bar_w:.1f}" y="{y + 14}" fill="#F8FAFC" font-size="11" font-weight="600">{val:,.0f}</text>
            """)

        return f"""
          <svg viewBox="0 0 {w} {h}" width="100%" height="{h}">
            {"".join(svg_bars)}
          </svg>
        """

    def _generate_donut_svg(self, labels: list[str], values: list[float], theme: Any) -> str:
        """Generate SVG donut chart with legend."""
        total = sum(values)
        if total == 0:
            return "<p style='color:#94A3B8'>No data</p>"

        palette = theme.colors.chart_palette

        # Generate donut slices using stroke-dasharray
        circumference = 2 * 3.14159 * 50  # radius = 50
        svg_slices = []
        svg_legend = []
        accumulated_pct = 0.0

        for i, (lbl, val) in enumerate(zip(labels, values, strict=False)):
            pct = val / total
            stroke_dash = pct * circumference
            stroke_offset = -accumulated_pct * circumference
            color = palette[i % len(palette)]

            svg_slices.append(f"""
              <circle cx="90" cy="90" r="50" fill="transparent" stroke="{color}" stroke-width="26"
                      stroke-dasharray="{stroke_dash:.2f} {circumference:.2f}"
                      stroke-dashoffset="{stroke_offset:.2f}" />
            """)

            lbl_clean = lbl[:14] + ("..." if len(lbl) > 14 else "")
            legend_y = 30 + (i * 20)
            svg_legend.append(f"""
              <rect x="190" y="{legend_y - 10}" width="10" height="10" rx="2" fill="{color}"/>
              <text x="210" y="{legend_y}" fill="#94A3B8" font-size="11">{lbl_clean} ({pct * 100:.1f}%)</text>
            """)
            accumulated_pct += pct

        return f"""
          <svg viewBox="0 0 380 180" width="100%" height="180">
            <g transform="rotate(-90 90 90)">
              {"".join(svg_slices)}
            </g>
            {"".join(svg_legend)}
          </svg>
        """

    def _generate_line_svg(self, labels: list[str], values: list[float], theme: Any) -> str:
        """Generate responsive SVG line trend chart."""
        if len(values) < 2 or max(values) == 0:
            return self._generate_bar_svg(labels, values, theme)

        w, h = 460, 200
        pad_x, pad_y = 40, 25
        chart_w = w - (pad_x * 2)
        chart_h = h - (pad_y * 2)

        min_val, max_val = min(values), max(values)
        val_range = (max_val - min_val) if max_val != min_val else 1.0

        pts = []
        for i, val in enumerate(values):
            x = pad_x + (i / (len(values) - 1)) * chart_w
            y = h - pad_y - ((val - min_val) / val_range) * chart_h
            pts.append((x, y, val, labels[i]))

        polyline_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts)
        circles_svg = []
        for x, y, _val, _lbl in pts:
            circles_svg.append(f"""
              <circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{theme.colors.primary}" stroke="#0B0F19" stroke-width="2"/>
            """)

        return f"""
          <svg viewBox="0 0 {w} {h}" width="100%" height="{h}">
            <line x1="{pad_x}" y1="{h - pad_y}" x2="{w - pad_x}" y2="{h - pad_y}" stroke="#26334D" stroke-width="1"/>
            <polyline fill="none" stroke="{theme.colors.primary}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{polyline_pts}"/>
            {"".join(circles_svg)}
          </svg>
        """

    def _render_data_preview(self, df: pl.DataFrame, limit: int = 10) -> str:
        """Render responsive HTML table preview."""
        cols = df.columns
        sample = df.head(limit)

        headers = "".join(f"<th>{col}</th>" for col in cols)
        rows = []
        for row in sample.iter_rows():
            cells = []
            for val in row:
                if val is None:
                    cells.append("<td style='color:#64748B'>-</td>")
                elif isinstance(val, float):
                    cells.append(f"<td>{val:,.2f}</td>")
                elif isinstance(val, int):
                    cells.append(f"<td>{val:,}</td>")
                else:
                    cells.append(f"<td>{val!s}</td>")
            rows.append(f"<tr>{''.join(cells)}</tr>")

        return f"""
          <table>
            <thead><tr>{headers}</tr></thead>
            <tbody>{"".join(rows)}</tbody>
          </table>
        """
