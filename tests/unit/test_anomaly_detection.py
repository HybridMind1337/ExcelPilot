"""Unit tests for statistical anomaly and outlier detection engine."""

import polars as pl

from excelpilot.analysis.anomalies import AnomalyDetector, OutlierMethod
from excelpilot.core.dataset import Dataset


def test_iqr_outlier_detection() -> None:
    # 20 typical values around 100, plus one obvious high outlier (10,000)
    data = [100.0, 102.0, 98.0, 101.0, 99.0, 105.0, 95.0, 100.0, 103.0, 97.0] * 2
    data.append(10_000.0)

    df = pl.DataFrame({"Revenue": data})
    dataset = Dataset(df, name="test_iqr")
    detector = AnomalyDetector(method=OutlierMethod.IQR)

    report = detector.detect_dataset(dataset)
    assert report.analyzed_columns == 1
    assert report.total_outliers_detected == 1

    summary = report.column_summaries[0]
    assert summary.column_name == "Revenue"
    assert summary.outlier_count == 1
    assert summary.anomalies[0].value == 10_000.0
    assert summary.anomalies[0].row_index == 20


def test_zscore_outlier_detection() -> None:
    data = [50.0, 52.0, 48.0, 51.0, 49.0, 53.0, 47.0] * 3
    data.append(2500.0)

    df = pl.DataFrame({"Cost": data})
    dataset = Dataset(df, name="test_zscore")
    detector = AnomalyDetector(method=OutlierMethod.ZSCORE, z_threshold=3.0)

    report = detector.detect_dataset(dataset)
    assert report.total_outliers_detected >= 1
    assert report.column_summaries[0].outlier_count >= 1


def test_empty_or_small_column_handling() -> None:
    df = pl.DataFrame({"EmptyCol": [1.0, 2.0]})
    dataset = Dataset(df, name="small")
    detector = AnomalyDetector()

    report = detector.detect_dataset(dataset)
    assert report.total_outliers_detected == 0
