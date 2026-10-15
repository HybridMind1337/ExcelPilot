"""Outlier and anomaly detection for numerical data series."""

from dataclasses import dataclass
from enum import Enum

import polars as pl

from excelpilot.core.dataset import Dataset


class OutlierMethod(str, Enum):
    """Statistical methods for detecting numerical anomalies."""

    IQR = "iqr"
    ZSCORE = "zscore"


@dataclass(frozen=True)
class AnomalyPoint:
    """Detailed metadata for a detected outlier data point."""

    row_index: int
    column_name: str
    value: float
    deviation_score: float
    reason: str


@dataclass(frozen=True)
class ColumnAnomalySummary:
    """Anomaly statistics for a single column."""

    column_name: str
    method: OutlierMethod
    total_count: int
    outlier_count: int
    outlier_percentage: float
    lower_bound: float
    upper_bound: float
    anomalies: list[AnomalyPoint]


@dataclass(frozen=True)
class AnomalyReport:
    """Comprehensive anomaly report across a dataset."""

    dataset_name: str
    analyzed_columns: int
    total_outliers_detected: int
    column_summaries: list[ColumnAnomalySummary]


def _safe_float(val: object) -> float:
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


class AnomalyDetector:
    """Statistical outlier and anomaly detector for tabular datasets."""

    def __init__(
        self,
        method: OutlierMethod = OutlierMethod.IQR,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ) -> None:
        self.method = method
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier

    def detect_column(
        self,
        df: pl.DataFrame,
        column_name: str,
    ) -> ColumnAnomalySummary:
        """Detect outliers in a specific numerical column."""
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in dataframe.")

        series = df[column_name].drop_nulls()
        if not series.dtype.is_numeric() or series.is_empty():
            return ColumnAnomalySummary(
                column_name=column_name,
                method=self.method,
                total_count=df.height,
                outlier_count=0,
                outlier_percentage=0.0,
                lower_bound=0.0,
                upper_bound=0.0,
                anomalies=[],
            )

        total_count = series.len()
        if total_count < 4:
            min_v = _safe_float(series.min()) if total_count > 0 else 0.0
            max_v = _safe_float(series.max()) if total_count > 0 else 0.0
            return ColumnAnomalySummary(
                column_name=column_name,
                method=self.method,
                total_count=total_count,
                outlier_count=0,
                outlier_percentage=0.0,
                lower_bound=min_v,
                upper_bound=max_v,
                anomalies=[],
            )

        anomalies: list[AnomalyPoint] = []
        if self.method == OutlierMethod.IQR:
            q25_val = series.quantile(0.25)
            q75_val = series.quantile(0.75)
            q25 = float(q25_val) if q25_val is not None else 0.0
            q75 = float(q75_val) if q75_val is not None else 0.0
            iqr = q75 - q25
            lower_bound = q25 - (self.iqr_multiplier * iqr)
            upper_bound = q75 + (self.iqr_multiplier * iqr)

            for idx, val in enumerate(df[column_name].to_list()):
                if val is not None and isinstance(val, (int, float)):
                    f_val = float(val)
                    if f_val < lower_bound or f_val > upper_bound:
                        diff = abs(f_val - (q75 if f_val > upper_bound else q25))
                        score = diff / iqr if iqr > 0 else 1.0
                        reason = (
                            f"Value {f_val:,.2f} exceeds upper threshold {upper_bound:,.2f}"
                            if f_val > upper_bound
                            else f"Value {f_val:,.2f} falls below lower threshold {lower_bound:,.2f}"
                        )
                        anomalies.append(
                            AnomalyPoint(
                                row_index=idx,
                                column_name=column_name,
                                value=f_val,
                                deviation_score=round(score, 2),
                                reason=reason,
                            )
                        )
        else:
            mean = _safe_float(series.mean())
            std = _safe_float(series.std())
            lower_bound = mean - (self.z_threshold * std)
            upper_bound = mean + (self.z_threshold * std)

            for idx, val in enumerate(df[column_name].to_list()):
                if val is not None and isinstance(val, (int, float)):
                    f_val = float(val)
                    if std > 0:
                        z = abs(f_val - mean) / std
                        if z > self.z_threshold:
                            reason = f"Z-score {z:.2f} exceeds threshold {self.z_threshold:.1f}"
                            anomalies.append(
                                AnomalyPoint(
                                    row_index=idx,
                                    column_name=column_name,
                                    value=f_val,
                                    deviation_score=round(z, 2),
                                    reason=reason,
                                )
                            )

        outlier_count = len(anomalies)
        pct = (outlier_count / total_count * 100.0) if total_count > 0 else 0.0

        return ColumnAnomalySummary(
            column_name=column_name,
            method=self.method,
            total_count=total_count,
            outlier_count=outlier_count,
            outlier_percentage=round(pct, 2),
            lower_bound=round(lower_bound, 2),
            upper_bound=round(upper_bound, 2),
            anomalies=anomalies,
        )

    def detect_dataset(
        self,
        dataset: Dataset,
        target_columns: list[str] | None = None,
    ) -> AnomalyReport:
        """Scan all or selected numerical columns in a dataset for anomalies."""
        df = dataset.dataframe
        if target_columns is None:
            target_columns = [col for col in df.columns if df[col].dtype.is_numeric()]

        summaries: list[ColumnAnomalySummary] = []
        total_outliers = 0

        for col in target_columns:
            summary = self.detect_column(df, col)
            summaries.append(summary)
            total_outliers += summary.outlier_count

        return AnomalyReport(
            dataset_name=dataset.name,
            analyzed_columns=len(summaries),
            total_outliers_detected=total_outliers,
            column_summaries=summaries,
        )
