"""Unit tests for AST safe expression parser."""

import polars as pl
import pytest

from excelpilot.exceptions.base import ExpressionSecurityError
from excelpilot.metrics.parser import SafeExpressionEvaluator


def test_safe_arithmetic_parsing() -> None:
    evaluator = SafeExpressionEvaluator()
    expr = evaluator.parse_to_polars_expr("(Revenue - Cost) / Revenue * 100")

    df = pl.DataFrame(
        {
            "Revenue": [100.0, 200.0],
            "Cost": [60.0, 150.0],
        }
    )
    res = df.select(expr.alias("margin"))
    assert res["margin"].to_list() == [40.0, 25.0]


def test_prohibited_function_call() -> None:
    evaluator = SafeExpressionEvaluator()
    with pytest.raises(ExpressionSecurityError, match="is prohibited"):
        evaluator.parse_to_polars_expr("__import__('os').system('echo pwned')")


def test_prohibited_attribute_access() -> None:
    evaluator = SafeExpressionEvaluator()
    with pytest.raises(ExpressionSecurityError, match="is prohibited"):
        evaluator.parse_to_polars_expr("Revenue.__class__")


def test_empty_expression() -> None:
    evaluator = SafeExpressionEvaluator()
    with pytest.raises(ExpressionSecurityError, match="cannot be empty"):
        evaluator.parse_to_polars_expr("   ")
