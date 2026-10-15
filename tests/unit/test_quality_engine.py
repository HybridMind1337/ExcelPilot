"""Unit tests for data quality audit engine."""

from pathlib import Path

from excelpilot.core.dataset import Dataset
from excelpilot.quality.engine import QualityEngine
from excelpilot.quality.models import (
    ColumnRule,
    QualityDimension,
    QualityRulesConfig,
    QualitySeverity,
)
from excelpilot.workbook.reader import OpenpyxlReader


def test_clean_dataset_quality_score(sales_dataset: Dataset) -> None:
    engine = QualityEngine()
    report = engine.audit(sales_dataset)

    assert report.total_rows == 150
    assert report.total_columns == 12
    assert report.overall_score >= 90.0
    assert report.high_severity_count == 0


def test_quality_defects_detection(quality_workbook_path: Path) -> None:
    reader = OpenpyxlReader()
    df = reader.read_worksheet(quality_workbook_path, "Transactions")
    dataset = Dataset(df, name="Transactions")

    config = QualityRulesConfig(
        rules={
            "Quantity": ColumnRule(nullable=False, minimum=0.0),
            "CustomerID": ColumnRule(nullable=False),
        }
    )
    engine = QualityEngine(rules_config=config)
    report = engine.audit(dataset)

    assert report.overall_score < 90.0

    # Assert defect categories
    dims_with_issues = {i.dimension for i in report.issues}
    assert QualityDimension.VALIDITY in dims_with_issues
    assert QualityDimension.COMPLETENESS in dims_with_issues
    assert QualityDimension.UNIQUENESS in dims_with_issues
    assert QualityDimension.CONSISTENCY in dims_with_issues

    # Assert high severity issues
    high_issues = [i for i in report.issues if i.severity == QualitySeverity.HIGH]
    assert len(high_issues) >= 1
