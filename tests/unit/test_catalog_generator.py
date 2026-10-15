"""Unit tests for CatalogGenerator."""

from pathlib import Path

import polars as pl

from excelpilot.catalog.generator import CatalogGenerator
from excelpilot.core.dataset import Dataset
from excelpilot.semantics.models import SemanticType


def test_catalog_generator_basic(tmp_path: Path) -> None:
    df = pl.DataFrame(
        {
            "OrderID": [101, 102, 103],
            "CustomerEmail": ["alice@example.com", "bob@example.com", "carol@example.com"],
            "Revenue": [120.50, 450.00, 78.25],
            "Status": ["active", "pending", "closed"],
            "Category": ["A", "B", "A"],
        }
    )
    dataset = Dataset(df, name="Orders")
    generator = CatalogGenerator()

    catalog = generator.generate_catalog(dataset)
    assert catalog.dataset_name == "Orders"
    assert catalog.total_rows == 3
    assert catalog.total_columns == 5
    assert len(catalog.entries) == 5

    # Check descriptions and types
    email_entry = next(e for e in catalog.entries if e.name == "CustomerEmail")
    assert email_entry.semantic_type == SemanticType.EMAIL

    # Export to markdown
    md_file = tmp_path / "catalog.md"
    generator.export_markdown(catalog, md_file)
    assert md_file.is_file()
    content = md_file.read_text(encoding="utf-8")
    assert "# Data Dictionary: Orders" in content
    assert "CustomerEmail" in content

    # Export to excel
    xlsx_file = tmp_path / "catalog.xlsx"
    generator.export_excel(catalog, xlsx_file)
    assert xlsx_file.is_file()
    assert xlsx_file.stat().st_size > 0


def test_infer_business_description() -> None:
    gen = CatalogGenerator()
    assert "Monetary" in gen._infer_business_description("Price", SemanticType.CURRENCY)
    assert "identifier" in gen._infer_business_description("ID", SemanticType.IDENTIFIER).lower()
    assert "mail" in gen._infer_business_description("Email", SemanticType.EMAIL).lower()
    assert "telephone" in gen._infer_business_description("Phone", SemanticType.PHONE).lower()
    assert "ratio" in gen._infer_business_description("Rate", SemanticType.PERCENTAGE).lower()
    assert (
        "lifecycle"
        in gen._infer_business_description("order_status", SemanticType.CATEGORICAL).lower()
    )
    assert (
        "classification"
        in gen._infer_business_description("product_category", SemanticType.CATEGORICAL).lower()
    )
