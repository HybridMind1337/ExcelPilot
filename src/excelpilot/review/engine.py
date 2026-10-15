"""Dashboard review engine auditing layout, chart density, and formatting."""

from pathlib import Path

import openpyxl

from excelpilot.exceptions.base import WorkbookError
from excelpilot.review.models import ReviewFinding, ReviewReport, ReviewSeverity
from excelpilot.workbook.reader import OpenpyxlReader


class DashboardReviewEngine:
    """Audits Excel workbooks for dashboard design, number formatting, and visual density."""

    def __init__(self) -> None:
        self.reader = OpenpyxlReader()

    def review(self, workbook_path: Path) -> ReviewReport:
        """Perform a comprehensive design review on an existing Excel workbook."""
        metadata = self.reader.inspect(workbook_path)
        sheets = metadata.sheet_names
        findings: list[ReviewFinding] = []

        has_dashboard = any("dash" in s.lower() for s in sheets)
        if not has_dashboard:
            findings.append(
                ReviewFinding(
                    severity=ReviewSeverity.WARNING,
                    category="SHEET_ARCHITECTURE",
                    description="No dedicated 'Dashboard' sheet detected. Report appears to be a raw data dump.",
                    suggested_action="Create a dedicated front-page Dashboard sheet with high-level KPI cards and charts.",
                )
            )

        # Inspect cell formatting and structure using openpyxl
        try:
            wb = openpyxl.load_workbook(str(workbook_path), data_only=False)
        except Exception as err:
            raise WorkbookError(
                path=workbook_path, reason=f"Failed to load workbook: {err}"
            ) from err

        try:
            # 1. Check for Analysis or supporting aggregate sheet
            has_analysis = any("analysis" in s.lower() or "summary" in s.lower() for s in sheets)
            if not has_analysis and has_dashboard:
                findings.append(
                    ReviewFinding(
                        severity=ReviewSeverity.RECOMMENDATION,
                        category="DATA_SEPARATION",
                        description="Dashboard lacks a separate 'Analysis' sheet for chart reference data.",
                        suggested_action="Isolate chart aggregation tables on a separate Analysis sheet.",
                    )
                )

            # 2. Check for Data Quality sheet
            has_quality = any("quality" in s.lower() for s in sheets)
            if not has_quality:
                findings.append(
                    ReviewFinding(
                        severity=ReviewSeverity.INFO,
                        category="DATA_GOVERNANCE",
                        description="No data quality audit sheet identified.",
                        suggested_action="Include an automated Data_Quality audit tab to verify completeness and integrity.",
                    )
                )

            # 3. Inspect charts and category overload in sheets
            for s_name in sheets:
                ws = wb[s_name]
                chart_count = len(getattr(ws, "_charts", []))
                if chart_count > 6:
                    findings.append(
                        ReviewFinding(
                            severity=ReviewSeverity.WARNING,
                            category="VISUAL_DENSITY",
                            description=f"Sheet '{s_name}' contains {chart_count} charts, exceeding recommended visual density.",
                            suggested_action="Limit dashboard charts to 4-6 primary visuals to avoid cognitive overload.",
                        )
                    )

                # Inspect first 100 rows for raw unformatted floating point decimals
                unformatted_floats = 0
                for row in ws.iter_rows(max_row=100, values_only=False):
                    for cell in row:
                        if isinstance(cell.value, float) and cell.number_format in (
                            "General",
                            None,
                        ):
                            # Check if it has many decimal places
                            str_val = str(cell.value)
                            if "." in str_val and len(str_val.split(".")[1]) > 3:
                                unformatted_floats += 1
                                if unformatted_floats >= 5:
                                    break
                    if unformatted_floats >= 5:
                        break

                if unformatted_floats >= 5:
                    findings.append(
                        ReviewFinding(
                            severity=ReviewSeverity.WARNING,
                            category="NUMBER_FORMATTING",
                            description=f"Sheet '{s_name}' contains raw unformatted decimal numbers.",
                            suggested_action="Apply consistent currency (£#,##0.00), percentage (0.0%), or integer formats.",
                        )
                    )

            # Deduct points: WARNING = -12, RECOMMENDATION = -6, INFO = -2
            score = 100.0
            for f in findings:
                if f.severity == ReviewSeverity.WARNING:
                    score -= 12.0
                elif f.severity == ReviewSeverity.RECOMMENDATION:
                    score -= 6.0
                elif f.severity == ReviewSeverity.INFO:
                    score -= 2.0

            final_score = max(0.0, min(100.0, round(score, 1)))

            return ReviewReport(
                workbook_name=workbook_path.name,
                review_score=final_score,
                sheet_count=len(sheets),
                has_dashboard_sheet=has_dashboard,
                findings=findings,
            )
        finally:
            wb.close()
