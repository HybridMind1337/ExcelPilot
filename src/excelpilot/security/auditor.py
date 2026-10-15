"""Comprehensive Excel security, formula injection, and privacy auditor."""

import re
from pathlib import Path

import openpyxl

from excelpilot.exceptions.base import WorkbookError
from excelpilot.security.models import (
    SecurityFinding,
    SecurityReport,
    SecuritySeverity,
    ThreatCategory,
)

# Regex patterns for formula injection and privacy detection
DANGEROUS_FORMULA_PATTERN = re.compile(
    r"^[\=\+\-\@\t\r].*(cmd|powershell|cscript|wscript|dde|shell|exec|regsvr32|mshta)",
    re.IGNORECASE,
)
EXTERNAL_REF_PATTERN = re.compile(r"\[.*\.xls[xm]?\]", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


class SecurityAuditor:
    """Audits Excel files for formula injection, concealed sheets, and PII leakage."""

    def audit_workbook(self, workbook_path: Path) -> SecurityReport:
        """Perform comprehensive security inspection on an Excel workbook."""
        if not workbook_path.is_file():
            raise WorkbookError(workbook_path, f"Workbook not found at '{workbook_path}'.")

        findings: list[SecurityFinding] = []
        is_macro = workbook_path.suffix.lower() in [".xlsm", ".xltm"]

        if is_macro:
            findings.append(
                SecurityFinding(
                    severity=SecuritySeverity.HIGH,
                    category=ThreatCategory.MACRO_VBA,
                    location="Workbook",
                    description="Macro-enabled workbook format (.xlsm) contains executable VBA code.",
                )
            )

        try:
            wb = openpyxl.load_workbook(
                str(workbook_path), read_only=False, data_only=False, keep_vba=is_macro
            )
        except Exception as err:
            raise WorkbookError(
                workbook_path, f"Failed to open workbook for security audit: {err}"
            ) from err

        hidden_sheets = 0
        try:
            # 1. Audit worksheets visibility and structure
            for sheet in wb.worksheets:
                if sheet.sheet_state in ("hidden", "veryHidden"):
                    hidden_sheets += 1
                    findings.append(
                        SecurityFinding(
                            severity=SecuritySeverity.MEDIUM,
                            category=ThreatCategory.HIDDEN_SHEET,
                            location=sheet.title,
                            description=f"Concealed worksheet detected (state: '{sheet.sheet_state}').",
                        )
                    )

                # 2. Inspect cells for formula injection, external links, and PII
                for row in sheet.iter_rows(values_only=False):
                    for cell in row:
                        val = cell.value
                        if val is None:
                            continue

                        val_str = str(val).strip()
                        cell_ref = f"{sheet.title}!{cell.coordinate}"

                        # Formula injection check
                        if DANGEROUS_FORMULA_PATTERN.search(val_str):
                            findings.append(
                                SecurityFinding(
                                    severity=SecuritySeverity.CRITICAL,
                                    category=ThreatCategory.FORMULA_INJECTION,
                                    location=cell_ref,
                                    description="Dangerous dynamic command or formula injection payload detected.",
                                    sample_content=val_str[:50],
                                )
                            )

                        # External link check
                        if EXTERNAL_REF_PATTERN.search(val_str):
                            findings.append(
                                SecurityFinding(
                                    severity=SecuritySeverity.MEDIUM,
                                    category=ThreatCategory.EXTERNAL_LINK,
                                    location=cell_ref,
                                    description="External workbook reference identified in formula.",
                                    sample_content=val_str[:50],
                                )
                            )

                        # PII Checks (Emails, Phones, Cards)
                        if EMAIL_PATTERN.search(val_str):
                            findings.append(
                                SecurityFinding(
                                    severity=SecuritySeverity.INFO,
                                    category=ThreatCategory.PII_EXPOSURE,
                                    location=cell_ref,
                                    description="Potential electronic mail address (PII) identified.",
                                    sample_content=val_str[:40],
                                )
                            )

                        if CARD_PATTERN.search(val_str):
                            findings.append(
                                SecurityFinding(
                                    severity=SecuritySeverity.HIGH,
                                    category=ThreatCategory.PII_EXPOSURE,
                                    location=cell_ref,
                                    description="Potential payment card number pattern (PII) detected.",
                                    sample_content="****-****-****-****",
                                )
                            )
        finally:
            wb.close()

        # Calculate security score
        score = 100.0
        for f in findings:
            if f.severity == SecuritySeverity.CRITICAL:
                score -= 35.0
            elif f.severity == SecuritySeverity.HIGH:
                score -= 20.0
            elif f.severity == SecuritySeverity.MEDIUM:
                score -= 10.0
            elif f.severity == SecuritySeverity.INFO:
                score -= 2.0

        score = max(0.0, score)
        if score >= 90.0:
            risk = "SAFE"
        elif score >= 75.0:
            risk = "LOW"
        elif score >= 50.0:
            risk = "MODERATE"
        else:
            risk = "HIGH"

        return SecurityReport(
            workbook_name=workbook_path.name,
            is_macro_enabled=is_macro,
            hidden_sheets_count=hidden_sheets,
            findings=findings,
            security_score=round(score, 1),
            risk_level=risk,
        )
