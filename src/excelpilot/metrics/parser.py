"""Abstract Syntax Tree (AST) safe mathematical expression parser."""

import ast
import operator
from collections.abc import Callable
from typing import Any

import polars as pl

from excelpilot.exceptions.base import ExpressionSecurityError

# Whitelist safe arithmetic operators
_OPERATORS: dict[type[ast.AST], Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class SafeExpressionEvaluator:
    """Safely evaluates algebraic expressions over Polars columns without Python eval()."""

    def parse_to_polars_expr(self, expression_str: str) -> pl.Expr:
        """Parse an expression like '(Revenue - Cost) / Revenue * 100' into a Polars expression."""
        clean_expr = expression_str.strip()
        if not clean_expr:
            raise ExpressionSecurityError("Expression string cannot be empty.")

        try:
            tree = ast.parse(clean_expr, mode="eval")
        except SyntaxError as err:
            raise ExpressionSecurityError(
                f"Syntax error in expression '{clean_expr}': {err}"
            ) from err

        return self._evaluate_node_to_expr(tree.body)

    def _evaluate_node_to_expr(self, node: ast.AST) -> pl.Expr:
        """Recursively convert an AST node to a Polars expression with strict security checks."""
        # Variable name (representing a column name)
        if isinstance(node, ast.Name):
            return pl.col(node.id)

        # Constant numbers (e.g. 100, 0.5)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return pl.lit(node.value)
            raise ExpressionSecurityError(
                f"Constant of type '{type(node.value).__name__}' is not permitted in arithmetic formulas."
            )

        # Binary operation (e.g. A + B, A - B, A * B, A / B)
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ExpressionSecurityError(
                    f"Binary operator '{op_type.__name__}' is not permitted."
                )

            left_expr = self._evaluate_node_to_expr(node.left)
            right_expr = self._evaluate_node_to_expr(node.right)

            if op_type is ast.Add:
                return left_expr + right_expr
            if op_type is ast.Sub:
                return left_expr - right_expr
            if op_type is ast.Mult:
                return left_expr * right_expr
            if op_type is ast.Div:
                return left_expr / right_expr

        # Unary operation (e.g. -A)
        if isinstance(node, ast.UnaryOp):
            uop_type = type(node.op)
            if uop_type not in (ast.USub, ast.UAdd):
                raise ExpressionSecurityError(
                    f"Unary operator '{uop_type.__name__}' is not permitted."
                )
            operand_expr = self._evaluate_node_to_expr(node.operand)
            return -operand_expr if uop_type is ast.USub else operand_expr

        # Prohibited nodes
        raise ExpressionSecurityError(
            f"AST element '{type(node).__name__}' is prohibited. Only arithmetic expressions with column names and numbers are allowed."
        )
