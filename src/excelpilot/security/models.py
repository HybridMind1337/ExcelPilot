"""Models for workbook security, formula injection, and privacy auditing."""

from dataclasses import dataclass
from enum import Enum


class SecuritySeverity(str, Enum):
    """Severity levels for detected security findings."""

    INFO = "INFO"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ThreatCategory(str, Enum):
    """Categorisation of security threats within spreadsheets."""

    FORMULA_INJECTION = "FORMULA_INJECTION"
    HIDDEN_SHEET = "HIDDEN_SHEET"
    EXTERNAL_LINK = "EXTERNAL_LINK"
    PII_EXPOSURE = "PII_EXPOSURE"
    MACRO_VBA = "MACRO_VBA"


@dataclass(frozen=True)
class SecurityFinding:
    """Individual security or privacy finding in a workbook."""

    severity: SecuritySeverity
    category: ThreatCategory
    location: str  # e.g., "Sheet1!B12" or "Workbook"
    description: str
    sample_content: str | None = None


@dataclass(frozen=True)
class SecurityReport:
    """Comprehensive security audit report for an Excel workbook."""

    workbook_name: str
    is_macro_enabled: bool
    hidden_sheets_count: int
    findings: list[SecurityFinding]
    security_score: float  # 0.0 - 100.0
    risk_level: str  # SAFE, LOW, MODERATE, HIGH
