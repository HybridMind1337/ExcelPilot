"""Unit tests for semantic type classification."""

import polars as pl

from excelpilot.core.dataset import Dataset
from excelpilot.core.types import SemanticType
from excelpilot.semantics.classifier import SemanticClassifier


def test_semantic_classification() -> None:
    df = pl.DataFrame(
        {
            "OrderID": ["ORD-101", "ORD-102", "ORD-103", "ORD-104", "ORD-105"],
            "Revenue": [120.50, 450.00, 32.99, 1500.00, 89.90],
            "OrderDate": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"],
            "CustomerEmail": [
                "alice@example.com",
                "bob@example.com",
                "carol@example.com",
                "dave@example.com",
                "eve@example.com",
            ],
            "Region": ["North", "South", "North", "West", "South"],
        }
    )
    dataset = Dataset(df, name="test_semantics")
    classifier = SemanticClassifier()
    profile = classifier.classify_dataset(dataset)

    order_id = profile.get_column("OrderID")
    assert order_id is not None
    assert order_id.semantic_type == SemanticType.IDENTIFIER
    assert order_id.confidence >= 0.85

    revenue = profile.get_column("Revenue")
    assert revenue is not None
    assert revenue.semantic_type == SemanticType.CURRENCY
    assert revenue.is_metric_candidate

    order_date = profile.get_column("OrderDate")
    assert order_date is not None
    assert order_date.semantic_type == SemanticType.TEMPORAL
    assert order_date.is_dimension_candidate

    email = profile.get_column("CustomerEmail")
    assert email is not None
    assert email.semantic_type == SemanticType.EMAIL

    region = profile.get_column("Region")
    assert region is not None
    assert region.semantic_type == SemanticType.CATEGORICAL
    assert region.is_dimension_candidate
