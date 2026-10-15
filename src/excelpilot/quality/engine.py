"""Data quality auditing engine implementing multi-dimensional evaluation."""

import polars as pl

from excelpilot.core.dataset import Dataset
from excelpilot.profiling.engine import Profiler
from excelpilot.profiling.models import DatasetProfile
from excelpilot.quality.models import (
    ColumnRule,
    QualityDimension,
    QualityIssue,
    QualityReport,
    QualityRulesConfig,
    QualitySeverity,
)
from excelpilot.semantics.classifier import SemanticClassifier
from excelpilot.semantics.models import DatasetSemanticProfile


class QualityEngine:
    """Evaluates datasets against completeness, validity, uniqueness, and consistency dimensions."""

    def __init__(self, rules_config: QualityRulesConfig | None = None) -> None:
        self.rules_config = rules_config or QualityRulesConfig()

    def audit(
        self,
        dataset: Dataset,
        profile: DatasetProfile | None = None,
        semantics: DatasetSemanticProfile | None = None,
    ) -> QualityReport:
        """Run an automated audit across the dataset and return a structured QualityReport."""
        df = dataset.dataframe
        total_rows = df.height
        total_cols = df.width

        if total_rows == 0 or total_cols == 0:
            return QualityReport(
                dataset_name=dataset.name,
                total_rows=0,
                total_columns=0,
                overall_score=100.0,
                dimension_scores={
                    QualityDimension.COMPLETENESS: 100.0,
                    QualityDimension.VALIDITY: 100.0,
                    QualityDimension.UNIQUENESS: 100.0,
                    QualityDimension.CONSISTENCY: 100.0,
                },
                issues=[],
            )

        if profile is None:
            profile = Profiler().profile(dataset)
        if semantics is None:
            semantics = SemanticClassifier().classify_dataset(dataset, profile)

        issues: list[QualityIssue] = []

        # ----------------------------------------------------
        # 1. COMPLETENESS EVALUATION
        # ----------------------------------------------------
        total_cells = total_rows * total_cols
        total_null_cells = sum(col.null_count for col in profile.columns)
        completeness_score = max(0.0, 100.0 - ((total_null_cells / total_cells) * 100.0))

        for col in profile.columns:
            rule: ColumnRule | None = self.rules_config.rules.get(col.name)
            sem = semantics.get_column(col.name)
            is_mandatory = (
                rule.nullable is False
                if rule
                else (sem is not None and sem.semantic_type.value == "IDENTIFIER")
            )

            if col.null_count > 0:
                severity = (
                    QualitySeverity.HIGH
                    if is_mandatory
                    else (
                        QualitySeverity.MEDIUM
                        if col.null_percentage > 25.0
                        else QualitySeverity.LOW
                    )
                )
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.COMPLETENESS,
                        severity=severity,
                        column=col.name,
                        description=f"Column has {col.null_count:,} missing values ({col.null_percentage}% null).",
                        affected_count=col.null_count,
                        affected_percentage=col.null_percentage,
                    )
                )

        # ----------------------------------------------------
        # 2. UNIQUENESS EVALUATION
        # ----------------------------------------------------
        uniqueness_score = max(0.0, 100.0 - profile.duplicate_rows_percentage)
        if profile.duplicate_rows_count > 0:
            severity = (
                QualitySeverity.HIGH
                if profile.duplicate_rows_percentage > 10.0
                else QualitySeverity.MEDIUM
                if profile.duplicate_rows_percentage > 1.0
                else QualitySeverity.LOW
            )
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.UNIQUENESS,
                    severity=severity,
                    column=None,
                    description=f"{profile.duplicate_rows_count:,} duplicate rows identified in dataset.",
                    affected_count=profile.duplicate_rows_count,
                    affected_percentage=profile.duplicate_rows_percentage,
                )
            )

        # Identifier column uniqueness check
        for sem in semantics.columns:
            if sem.semantic_type.value == "IDENTIFIER":
                col_prof = next((c for c in profile.columns if c.name == sem.name), None)
                if col_prof and not col_prof.is_unique:
                    dupe_keys = total_rows - col_prof.distinct_count
                    pct = round((dupe_keys / total_rows) * 100.0, 2)
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.UNIQUENESS,
                            severity=QualitySeverity.HIGH,
                            column=sem.name,
                            description=f"Identifier column '{sem.name}' contains {dupe_keys:,} duplicate values.",
                            affected_count=dupe_keys,
                            affected_percentage=pct,
                        )
                    )

        # ----------------------------------------------------
        # 3. VALIDITY EVALUATION
        # ----------------------------------------------------
        validity_deductions = 0.0

        for col_name in df.columns:
            series = df[col_name]
            rule = self.rules_config.rules.get(col_name)
            sem = semantics.get_column(col_name)

            # Check negative numbers in columns that should be non-negative
            is_currency_or_quantity = (
                sem is not None and sem.semantic_type.value == "CURRENCY"
            ) or any(k in col_name.lower() for k in ("quantity", "units", "items", "count", "qty"))

            if series.dtype.is_numeric() and (
                (rule and rule.minimum is not None) or is_currency_or_quantity
            ):
                min_threshold = rule.minimum if (rule and rule.minimum is not None) else 0.0
                # Don't forbid negative profit, but forbid negative price/quantity/sales
                if not any(k in col_name.lower() for k in ("profit", "margin", "delta", "growth")):
                    try:
                        neg_count = int(df.filter(pl.col(col_name) < min_threshold).height)
                        if neg_count > 0:
                            pct = round((neg_count / total_rows) * 100.0, 2)
                            validity_deductions += min(15.0, pct)
                            issues.append(
                                QualityIssue(
                                    dimension=QualityDimension.VALIDITY,
                                    severity=QualitySeverity.HIGH,
                                    column=col_name,
                                    description=f"{neg_count:,} records have values below minimum threshold ({min_threshold}).",
                                    affected_count=neg_count,
                                    affected_percentage=pct,
                                )
                            )
                    except Exception:
                        pass

            # Maximum check from rule
            if rule and rule.maximum is not None and series.dtype.is_numeric():
                try:
                    over_max = int(df.filter(pl.col(col_name) > rule.maximum).height)
                    if over_max > 0:
                        pct = round((over_max / total_rows) * 100.0, 2)
                        validity_deductions += min(10.0, pct)
                        issues.append(
                            QualityIssue(
                                dimension=QualityDimension.VALIDITY,
                                severity=QualitySeverity.MEDIUM,
                                column=col_name,
                                description=f"{over_max:,} records exceed maximum allowed value ({rule.maximum}).",
                                affected_count=over_max,
                                affected_percentage=pct,
                            )
                        )
                except Exception:
                    pass

            # Allowed values check
            if rule and rule.allowed_values is not None:
                try:
                    invalid_cnt = int(
                        df.filter(
                            pl.col(col_name).is_not_null()
                            & ~pl.col(col_name).cast(pl.String).is_in(rule.allowed_values)
                        ).height
                    )
                    if invalid_cnt > 0:
                        pct = round((invalid_cnt / total_rows) * 100.0, 2)
                        validity_deductions += min(15.0, pct)
                        issues.append(
                            QualityIssue(
                                dimension=QualityDimension.VALIDITY,
                                severity=QualitySeverity.HIGH,
                                column=col_name,
                                description=f"{invalid_cnt:,} records contain values outside allowed set.",
                                affected_count=invalid_cnt,
                                affected_percentage=pct,
                            )
                        )
                except Exception:
                    pass

        validity_score = max(0.0, round(100.0 - validity_deductions, 2))

        # ----------------------------------------------------
        # 4. CONSISTENCY EVALUATION
        # ----------------------------------------------------
        consistency_deductions = 0.0

        for col_name in df.columns:
            series = df[col_name]
            # Check string columns for trailing or leading whitespace inconsistency
            if series.dtype == pl.String or str(series.dtype).startswith("str"):
                non_null_str = series.drop_nulls()
                if non_null_str.len() > 0:
                    try:
                        trimmed = non_null_str.str.strip_chars()
                        whitespace_diff = int((non_null_str != trimmed).sum())
                        if whitespace_diff > 0:
                            pct = round((whitespace_diff / total_rows) * 100.0, 2)
                            consistency_deductions += min(5.0, pct * 0.5)
                            issues.append(
                                QualityIssue(
                                    dimension=QualityDimension.CONSISTENCY,
                                    severity=QualitySeverity.LOW,
                                    column=col_name,
                                    description=f"{whitespace_diff:,} records have untrimmed leading or trailing whitespace.",
                                    affected_count=whitespace_diff,
                                    affected_percentage=pct,
                                )
                            )
                    except Exception:
                        pass

        consistency_score = max(0.0, round(100.0 - consistency_deductions, 2))

        # Overall weighted composite score
        # Completeness: 30%, Validity: 30%, Uniqueness: 20%, Consistency: 20%
        overall = (
            (0.30 * completeness_score)
            + (0.30 * validity_score)
            + (0.20 * uniqueness_score)
            + (0.20 * consistency_score)
        )

        return QualityReport(
            dataset_name=dataset.name,
            total_rows=total_rows,
            total_columns=total_cols,
            overall_score=round(overall, 1),
            dimension_scores={
                QualityDimension.COMPLETENESS: round(completeness_score, 1),
                QualityDimension.VALIDITY: round(validity_score, 1),
                QualityDimension.UNIQUENESS: round(uniqueness_score, 1),
                QualityDimension.CONSISTENCY: round(consistency_score, 1),
            },
            issues=issues,
        )
