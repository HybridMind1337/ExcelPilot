"""Classifier that determines semantic data types and business roles."""

from excelpilot.core.dataset import Dataset
from excelpilot.core.types import SemanticType
from excelpilot.profiling.engine import Profiler
from excelpilot.profiling.models import ColumnProfile, DatasetProfile
from excelpilot.semantics.models import ColumnSemanticProfile, DatasetSemanticProfile
from excelpilot.semantics.rules import (
    BOOLEAN_KEYWORDS,
    CURRENCY_KEYWORDS,
    CURRENCY_SYMBOLS,
    DATE_REGEX,
    EMAIL_REGEX,
    GEO_KEYWORDS,
    IDENTIFIER_KEYWORDS,
    PERCENTAGE_KEYWORDS,
    PHONE_REGEX,
    TEMPORAL_KEYWORDS,
    URL_REGEX,
)


class SemanticClassifier:
    """Classifies dataset columns into semantic data types with calibrated confidence scores."""

    def classify_dataset(
        self,
        dataset: Dataset,
        profile: DatasetProfile | None = None,
    ) -> DatasetSemanticProfile:
        """Classify all columns in a dataset using statistical profile and heuristic rules."""
        if profile is None:
            profile = Profiler().profile(dataset)

        results: list[ColumnSemanticProfile] = []
        for col_profile in profile.columns:
            classified = self.classify_column(col_profile)
            results.append(classified)

        return DatasetSemanticProfile(columns=results)

    def classify_column(self, col: ColumnProfile) -> ColumnSemanticProfile:
        """Evaluate a single column profile and return its semantic classification."""
        name_lower = col.name.lower().replace("-", "_").replace(" ", "_")
        samples = col.sample_values
        phys = col.physical_type.lower()

        # 1. Physical Temporal check
        if any(t in phys for t in ("date", "time", "datetime")):
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.TEMPORAL,
                confidence=0.99,
                reasoning="Physical column data type is temporal.",
                is_dimension_candidate=True,
                sample_values=samples,
            )

        # 2. String sample checks for Email, URL, Phone, Date
        if samples and ("str" in phys or "object" in phys):
            # Email check
            if any(EMAIL_REGEX.match(s.strip()) for s in samples):
                matched_ratio = sum(1 for s in samples if EMAIL_REGEX.match(s.strip())) / len(
                    samples
                )
                if matched_ratio > 0.5:
                    return ColumnSemanticProfile(
                        name=col.name,
                        physical_type=col.physical_type,
                        semantic_type=SemanticType.EMAIL,
                        confidence=round(0.85 + 0.14 * matched_ratio, 2),
                        reasoning="Values match standard email format.",
                        sample_values=samples,
                    )

            # URL check
            if any(URL_REGEX.match(s.strip()) for s in samples):
                matched_ratio = sum(1 for s in samples if URL_REGEX.match(s.strip())) / len(samples)
                if matched_ratio > 0.5:
                    return ColumnSemanticProfile(
                        name=col.name,
                        physical_type=col.physical_type,
                        semantic_type=SemanticType.URL,
                        confidence=round(0.85 + 0.14 * matched_ratio, 2),
                        reasoning="Values match URL format.",
                        sample_values=samples,
                    )

            # Phone check
            if "phone" in name_lower or "mobile" in name_lower or "tel" in name_lower:
                matched_ratio = sum(1 for s in samples if PHONE_REGEX.match(s.strip())) / len(
                    samples
                )
                if matched_ratio > 0.3:
                    return ColumnSemanticProfile(
                        name=col.name,
                        physical_type=col.physical_type,
                        semantic_type=SemanticType.PHONE,
                        confidence=0.92,
                        reasoning="Column name and values match telephone number patterns.",
                        sample_values=samples,
                    )

            # Date string pattern match
            matched_date_ratio = sum(1 for s in samples if DATE_REGEX.match(s.strip())) / len(
                samples
            )
            if matched_date_ratio > 0.6 or (
                any(k in name_lower for k in TEMPORAL_KEYWORDS) and matched_date_ratio > 0.4
            ):
                return ColumnSemanticProfile(
                    name=col.name,
                    physical_type=col.physical_type,
                    semantic_type=SemanticType.TEMPORAL,
                    confidence=0.91,
                    reasoning="Text values follow standard calendar date format.",
                    is_dimension_candidate=True,
                    sample_values=samples,
                )

        # 3. Boolean check
        if "bool" in phys or (
            col.distinct_count == 2 and any(k in name_lower for k in BOOLEAN_KEYWORDS)
        ):
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.BOOLEAN,
                confidence=0.98 if "bool" in phys else 0.88,
                reasoning="Binary distinct values with boolean indicator.",
                is_dimension_candidate=True,
                sample_values=samples,
            )

        # 4. Identifier check
        name_parts = set(name_lower.split("_"))
        is_id_name = bool(name_parts.intersection(IDENTIFIER_KEYWORDS)) or name_lower.endswith("id")
        if is_id_name and (col.distinct_percentage > 80.0 or col.is_unique):
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.IDENTIFIER,
                confidence=0.96,
                reasoning="High cardinality column matching identifier naming convention.",
                is_dimension_candidate=False,
                is_metric_candidate=False,
                sample_values=samples,
            )

        # 5. Numeric classification (Currency, Percentage, Decimal, Integer)
        is_numeric = any(t in phys for t in ("int", "float", "decimal", "numeric"))
        if is_numeric:
            # Currency check
            has_curr_symbol = any(
                any(sym in s.lower() for sym in CURRENCY_SYMBOLS) for s in samples
            )
            has_curr_name = any(k in name_lower for k in CURRENCY_KEYWORDS)
            if has_curr_symbol or has_curr_name:
                return ColumnSemanticProfile(
                    name=col.name,
                    physical_type=col.physical_type,
                    semantic_type=SemanticType.CURRENCY,
                    confidence=0.95 if has_curr_symbol and has_curr_name else 0.88,
                    reasoning="Numeric field with monetary terminology or currency formatting.",
                    is_metric_candidate=True,
                    sample_values=samples,
                )

            # Percentage check
            has_pct_name = any(k in name_lower for k in PERCENTAGE_KEYWORDS)
            has_pct_symbol = any("%" in s for s in samples)
            if has_pct_name or has_pct_symbol:
                return ColumnSemanticProfile(
                    name=col.name,
                    physical_type=col.physical_type,
                    semantic_type=SemanticType.PERCENTAGE,
                    confidence=0.92,
                    reasoning="Numeric field representing ratio, rate, or percentage.",
                    is_metric_candidate=True,
                    sample_values=samples,
                )

            # Integer vs Decimal
            if "int" in phys:
                return ColumnSemanticProfile(
                    name=col.name,
                    physical_type=col.physical_type,
                    semantic_type=SemanticType.INTEGER,
                    confidence=0.90,
                    reasoning="Integer quantitative measurement.",
                    is_metric_candidate=True,
                    sample_values=samples,
                )
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.DECIMAL,
                confidence=0.88,
                reasoning="Continuous floating-point measurement.",
                is_metric_candidate=True,
                sample_values=samples,
            )

        # 6. Geographic check
        if any(k in name_parts for k in GEO_KEYWORDS):
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.GEO,
                confidence=0.87,
                reasoning="Column name denotes geographic dimension.",
                is_dimension_candidate=True,
                sample_values=samples,
            )

        # 7. Categorical vs Free Text
        if col.distinct_count <= 250 or col.distinct_percentage < 20.0:
            return ColumnSemanticProfile(
                name=col.name,
                physical_type=col.physical_type,
                semantic_type=SemanticType.CATEGORICAL,
                confidence=0.85,
                reasoning="Low to moderate cardinality distinct category values.",
                is_dimension_candidate=True,
                sample_values=samples,
            )

        # Default fallback to Text or Unknown
        return ColumnSemanticProfile(
            name=col.name,
            physical_type=col.physical_type,
            semantic_type=SemanticType.TEXT,
            confidence=0.70,
            reasoning="High-cardinality unstructured textual data.",
            is_dimension_candidate=False,
            is_metric_candidate=False,
            sample_values=samples,
        )
