"""Automated data cleaning engine for tabular datasets."""

import polars as pl

from excelpilot.cleaning.models import (
    CleaningConfig,
    CleaningOperation,
    CleaningReport,
    NullHandlingStrategy,
)
from excelpilot.core.dataset import Dataset


class CleaningEngine:
    """Performs deterministic cleaning, normalisation, and null handling on datasets."""

    def __init__(self, config: CleaningConfig | None = None) -> None:
        self.config = config or CleaningConfig()

    def clean(self, dataset: Dataset) -> tuple[pl.DataFrame, CleaningReport]:
        """Apply configured transformations and return the cleaned DataFrame with an audit report."""
        df = dataset.dataframe
        orig_rows = df.height
        orig_cols = df.width
        operations: list[CleaningOperation] = []

        if df.is_empty():
            return df, CleaningReport(
                dataset_name=dataset.name,
                original_row_count=0,
                cleaned_row_count=0,
                original_column_count=0,
                cleaned_column_count=0,
                operations=[],
            )

        # 1. Normalise column names
        if self.config.normalize_column_names:
            rename_map = {}
            renamed_count = 0
            for col in df.columns:
                cleaned_name = col.strip().replace(" ", "_")
                if cleaned_name != col:
                    rename_map[col] = cleaned_name
                    renamed_count += 1
            if rename_map:
                df = df.rename(rename_map)
                operations.append(
                    CleaningOperation(
                        operation_name="NORMALIZE_COLUMNS",
                        column=None,
                        description=f"Normalised formatting for {renamed_count} column header(s).",
                        affected_rows=0,
                    )
                )

        # 2. Trim string whitespace
        if self.config.trim_strings:
            exprs = []
            for col in df.columns:
                if df[col].dtype == pl.String:
                    exprs.append(pl.col(col).str.strip_chars().alias(col))
            if exprs:
                df = df.with_columns(exprs)
                operations.append(
                    CleaningOperation(
                        operation_name="TRIM_WHITESPACE",
                        column=None,
                        description=f"Stripped leading and trailing whitespace across {len(exprs)} text column(s).",
                        affected_rows=df.height,
                    )
                )

        # 3. Deduplicate rows
        if self.config.drop_duplicates:
            dupes = int(df.is_duplicated().sum())
            if dupes > 0:
                df = df.unique(maintain_order=True)
                operations.append(
                    CleaningOperation(
                        operation_name="DROP_DUPLICATES",
                        column=None,
                        description=f"Removed {dupes:,} duplicate row(s).",
                        affected_rows=dupes,
                    )
                )

        # 4. Null handling strategy
        if self.config.null_strategy == NullHandlingStrategy.DROP_ROWS:
            before_drop = df.height
            df = df.drop_nulls()
            dropped_rows = before_drop - df.height
            if dropped_rows > 0:
                operations.append(
                    CleaningOperation(
                        operation_name="DROP_NULL_ROWS",
                        column=None,
                        description=f"Dropped {dropped_rows:,} row(s) containing missing values.",
                        affected_rows=dropped_rows,
                    )
                )
        elif self.config.null_strategy == NullHandlingStrategy.FILL_ZERO:
            exprs = []
            for col in df.columns:
                if df[col].dtype.is_numeric() and df[col].null_count() > 0:
                    exprs.append(pl.col(col).fill_null(0).alias(col))
            if exprs:
                df = df.with_columns(exprs)
                operations.append(
                    CleaningOperation(
                        operation_name="FILL_NULL_ZERO",
                        column=None,
                        description=f"Replaced nulls with zero across {len(exprs)} numeric column(s).",
                        affected_rows=df.height,
                    )
                )
        elif self.config.null_strategy == NullHandlingStrategy.FILL_UNKNOWN:
            exprs = []
            for col in df.columns:
                if df[col].dtype == pl.String and df[col].null_count() > 0:
                    exprs.append(pl.col(col).fill_null("Unknown").alias(col))
            if exprs:
                df = df.with_columns(exprs)
                operations.append(
                    CleaningOperation(
                        operation_name="FILL_NULL_UNKNOWN",
                        column=None,
                        description=f"Replaced nulls with 'Unknown' across {len(exprs)} string column(s).",
                        affected_rows=df.height,
                    )
                )

        report = CleaningReport(
            dataset_name=dataset.name,
            original_row_count=orig_rows,
            cleaned_row_count=df.height,
            original_column_count=orig_cols,
            cleaned_column_count=df.width,
            operations=operations,
        )

        return df, report
