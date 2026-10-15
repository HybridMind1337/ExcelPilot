"""Data dictionary and schema catalog generator."""

from pathlib import Path

import xlsxwriter

from excelpilot.catalog.models import ColumnCatalogEntry, DataCatalog
from excelpilot.core.dataset import Dataset
from excelpilot.core.types import SemanticType
from excelpilot.profiling.engine import Profiler
from excelpilot.semantics.classifier import SemanticClassifier


class CatalogGenerator:
    """Generates comprehensive data dictionaries and technical schema catalogs."""

    def __init__(self) -> None:
        self.profiler = Profiler()
        self.classifier = SemanticClassifier()

    def generate_catalog(self, dataset: Dataset) -> DataCatalog:
        """Inspect and document schema, types, distribution bounds, and business definitions."""
        profile = self.profiler.profile(dataset)
        semantics = self.classifier.classify_dataset(dataset, profile)

        entries: list[ColumnCatalogEntry] = []
        df = dataset.dataframe
        total_rows = df.height

        for col_name in df.columns:
            series = df[col_name]
            col_prof = next((c for c in profile.columns if c.name == col_name), None)
            sem_col = next((c for c in semantics.columns if c.name == col_name), None)

            sem_type = sem_col.semantic_type if sem_col else SemanticType.UNKNOWN
            confidence = sem_col.confidence if sem_col else 0.0

            null_cnt = col_prof.null_count if col_prof else 0
            null_pct = col_prof.null_percentage if col_prof else 0.0
            distinct_cnt = col_prof.distinct_count if col_prof else 0

            # Compute min and max safely
            min_str, max_str = "-", "-"
            non_nulls = series.drop_nulls()
            if not non_nulls.is_empty():
                try:
                    min_val = non_nulls.min()
                    max_val = non_nulls.max()
                    min_str = f"{min_val:,.2f}" if isinstance(min_val, float) else str(min_val)
                    max_str = f"{max_val:,.2f}" if isinstance(max_val, float) else str(max_val)
                except Exception:
                    pass

            # Samples
            sample_vals = [str(v) for v in non_nulls.unique().head(4).to_list() if v is not None]

            desc = self._infer_business_description(col_name, sem_type)

            entries.append(
                ColumnCatalogEntry(
                    name=col_name,
                    physical_type=str(series.dtype),
                    semantic_type=sem_type,
                    confidence=round(confidence, 2),
                    null_count=null_cnt,
                    null_percentage=round(null_pct, 1),
                    distinct_count=distinct_cnt,
                    min_value=min_str,
                    max_value=max_str,
                    sample_values=sample_vals,
                    description=desc,
                )
            )

        return DataCatalog(
            dataset_name=dataset.name,
            total_rows=total_rows,
            total_columns=len(entries),
            entries=entries,
        )

    def export_markdown(self, catalog: DataCatalog, output_path: Path) -> Path:
        """Export data catalog as a structured Markdown document."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Data Dictionary: {catalog.dataset_name}",
            "",
            f"**Total Records:** {catalog.total_rows:,} | **Total Attributes:** {catalog.total_columns}",
            "",
            "| Column Name | Physical Type | Semantic Type | Nulls (%) | Distinct | Bounds [Min .. Max] | Sample Values | Description |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |",
        ]

        for e in catalog.entries:
            samples = ", ".join(e.sample_values[:3]) or "-"
            bounds = f"[{e.min_value} .. {e.max_value}]" if e.min_value != "-" else "-"
            lines.append(
                f"| `{e.name}` | {e.physical_type} | `{e.semantic_type.value}` ({int(e.confidence * 100)}%) | {e.null_percentage}% | {e.distinct_count:,} | {bounds} | {samples} | {e.description} |"
            )

        lines.append("")
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def export_excel(self, catalog: DataCatalog, output_path: Path) -> Path:
        """Export data catalog as a formatted Excel workbook."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb = xlsxwriter.Workbook(str(output_path))
        ws = wb.add_worksheet("Data_Dictionary")

        fmt_hdr = wb.add_format(
            {"bold": True, "bg_color": "#1E3A8A", "font_color": "#FFFFFF", "border": 1}
        )
        fmt_txt = wb.add_format({"border": 1, "font_name": "Segoe UI", "font_size": 10})
        fmt_code = wb.add_format(
            {"border": 1, "font_name": "Consolas", "font_size": 9, "bg_color": "#F8FAFC"}
        )

        headers = [
            "Column Name",
            "Physical Type",
            "Semantic Type",
            "Confidence",
            "Null Count",
            "Null %",
            "Distinct Count",
            "Min Value",
            "Max Value",
            "Sample Values",
            "Business Description",
        ]

        for c_idx, h in enumerate(headers):
            ws.write(0, c_idx, h, fmt_hdr)

        for r_idx, e in enumerate(catalog.entries):
            ws.write(r_idx + 1, 0, e.name, fmt_code)
            ws.write(r_idx + 1, 1, e.physical_type, fmt_txt)
            ws.write(r_idx + 1, 2, e.semantic_type.value.upper(), fmt_txt)
            ws.write(r_idx + 1, 3, f"{e.confidence * 100:.0f}%", fmt_txt)
            ws.write(r_idx + 1, 4, e.null_count, fmt_txt)
            ws.write(r_idx + 1, 5, f"{e.null_percentage:.1f}%", fmt_txt)
            ws.write(r_idx + 1, 6, e.distinct_count, fmt_txt)
            ws.write(r_idx + 1, 7, e.min_value, fmt_txt)
            ws.write(r_idx + 1, 8, e.max_value, fmt_txt)
            ws.write(r_idx + 1, 9, ", ".join(e.sample_values), fmt_txt)
            ws.write(r_idx + 1, 10, e.description, fmt_txt)

        ws.autofilter(0, 0, len(catalog.entries), len(headers) - 1)
        for c_idx in range(len(headers)):
            ws.set_column(c_idx, c_idx, 18)
        ws.set_column(10, 10, 35)

        wb.close()
        return output_path

    @staticmethod
    def _infer_business_description(name: str, sem_type: SemanticType) -> str:
        """Generate intuitive business definition placeholder based on semantics and naming."""
        low = name.lower()
        if sem_type == SemanticType.CURRENCY:
            return f"Monetary amount or transaction measure for {name}."
        if sem_type == SemanticType.IDENTIFIER:
            return f"Unique identifier or reference key for {name}."
        if sem_type == SemanticType.TEMPORAL:
            return f"Timestamp or calendar reference date for {name}."
        if sem_type == SemanticType.PERCENTAGE:
            return f"Ratio or percentage calculation ({name})."
        if sem_type == SemanticType.EMAIL:
            return "Contact electronic mail address."
        if sem_type == SemanticType.PHONE:
            return "Telephone contact number."
        if sem_type == SemanticType.GEO:
            return f"Geographical region, location, or territory designation ({name})."
        if "status" in low or "stage" in low:
            return "Lifecycle state or workflow status indicator."
        if "category" in low or "type" in low:
            return f"Classification category for {name}."
        return f"Operational attribute: {name}."
