"""Privacy and personally identifiable information (PII) detection engine."""

from pydantic import BaseModel, Field

from excelpilot.core.types import SemanticType
from excelpilot.semantics.models import DatasetSemanticProfile


class PrivacyRisk(BaseModel):
    """Identified privacy or sensitive data risk."""

    column: str
    risk_type: str
    description: str


class PrivacyReport(BaseModel):
    """Assessment of sensitive and personal data columns."""

    has_pii: bool
    risks: list[PrivacyRisk] = Field(default_factory=list)


class PrivacyDetector:
    """Scans dataset columns for potentially sensitive or personally identifiable information."""

    def scan(self, semantics: DatasetSemanticProfile) -> PrivacyReport:
        """Scan semantic column profiles and flag personal or confidential data attributes."""
        risks: list[PrivacyRisk] = []

        for col in semantics.columns:
            name_lower = col.name.lower()
            sem_type = col.semantic_type

            if sem_type == SemanticType.EMAIL:
                risks.append(
                    PrivacyRisk(
                        column=col.name,
                        risk_type="EMAIL",
                        description="Column contains electronic mail addresses.",
                    )
                )
            elif sem_type == SemanticType.PHONE:
                risks.append(
                    PrivacyRisk(
                        column=col.name,
                        risk_type="PHONE",
                        description="Column contains telephone or mobile numbers.",
                    )
                )
            elif any(
                k in name_lower for k in ("ssn", "national_id", "passport", "tax_id", "ni_number")
            ):
                risks.append(
                    PrivacyRisk(
                        column=col.name,
                        risk_type="GOVERNMENT_ID",
                        description="Column name indicates government-issued identity or tax numbers.",
                    )
                )
            elif any(k in name_lower for k in ("credit_card", "card_number", "iban", "cvv")):
                risks.append(
                    PrivacyRisk(
                        column=col.name,
                        risk_type="FINANCIAL_ACCOUNT",
                        description="Column name indicates payment card or banking account details.",
                    )
                )
            elif any(
                k in name_lower
                for k in ("customer_name", "first_name", "last_name", "full_name", "surname")
            ):
                risks.append(
                    PrivacyRisk(
                        column=col.name,
                        risk_type="PERSONAL_NAME",
                        description="Column contains individual human names.",
                    )
                )

        return PrivacyReport(has_pii=len(risks) > 0, risks=risks)
