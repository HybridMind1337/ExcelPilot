"""High-performance dataset profiling engine using Polars."""

import logging
from typing import Any

import polars as pl

from excelpilot.core.dataset import Dataset
from excelpilot.profiling.models import (
    CategoryFrequency,
    ColumnProfile,
    DatasetProfile,
    NumericStats,
)

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class Profiler:
    """Profiles datasets to extract structural, statistical, and cardinality properties."""

    def __init__(self, max_categories: int = 10, sample_size_for_stats: int = 100_000) -> None:
        self.max_categories = max_categories
        self.sample_size_for_stats = sample_size_for_stats

    def profile(self, dataset: Dataset) -> DatasetProfile:
        """Execute a comprehensive statistical audit across all columns of the dataset."""
        df = dataset.dataframe
        row_count = df.height
        column_count = df.width

        if row_count == 0 or column_count == 0:
            return DatasetProfile(
                name=dataset.name,
                row_count=row_count,
                column_count=column_count,
                duplicate_rows_count=0,
                duplicate_rows_percentage=0.0,
                empty_rows_count=0,
                columns=[],
                numeric_column_count=0,
                categorical_column_count=0,
                temporal_column_count=0,
            )

        # Duplicate row calculation
        try:
            duplicate_count = int(df.is_duplicated().sum())
        except Exception:
            duplicate_count = 0
        duplicate_pct = (float(duplicate_count) / row_count) * 100.0 if row_count > 0 else 0.0

        # Empty rows: all nulls across all columns
        null_mask = df.select([pl.all().is_null()]).to_series(0) if df.width == 1 else None
        if null_mask is not None:
            empty_rows = int(null_mask.sum())
        else:
            # Multi-column: row is empty if all columns are null
            try:
                empty_rows = int(df.filter(pl.all_horizontal(pl.all().is_null())).height)
            except Exception:
                empty_rows = 0

        columns_profile: list[ColumnProfile] = []
        num_count = 0
        cat_count = 0
        temp_count = 0

        for col_name in df.columns:
            series = df[col_name]
            dtype = series.dtype

            null_count = int(series.null_count())
            null_pct = (null_count / row_count) * 100.0 if row_count > 0 else 0.0

            distinct_count = int(series.n_unique())
            distinct_pct = (distinct_count / row_count) * 100.0 if row_count > 0 else 0.0
            is_unique = distinct_count == row_count and null_count == 0
            is_constant = distinct_count == 1

            # Extract non-null sample values for inspection preview
            non_null_series = series.drop_nulls()
            sample_values = [str(v) for v in non_null_series.head(5).to_list()]

            numeric_stats: NumericStats | None = None
            top_categories: list[CategoryFrequency] = []

            # Check if numeric
            if dtype.is_numeric():
                num_count += 1
                try:
                    # Drop nulls and cast to Float64 for consistent statistics
                    clean_s = non_null_series.cast(pl.Float64)
                    if clean_s.len() > 0:
                        numeric_stats = NumericStats(
                            min_value=_to_float(clean_s.min()),
                            max_value=_to_float(clean_s.max()),
                            mean=_to_float(clean_s.mean()),
                            median=_to_float(clean_s.median()),
                            std_dev=_to_float(clean_s.std()),
                            quantile_25=_to_float(clean_s.quantile(0.25)),
                            quantile_75=_to_float(clean_s.quantile(0.75)),
                        )
                except Exception as err:
                    logger.debug("Failed computing numeric stats on '%s': %s", col_name, err)

            elif dtype.is_temporal():
                temp_count += 1
            else:
                cat_count += 1
                # Calculate category frequencies for low-medium cardinality
                if distinct_count <= 1000 and non_null_series.len() > 0:
                    try:
                        counts_df = (
                            non_null_series.to_frame()
                            .group_by(col_name)
                            .len()
                            .sort("len", descending=True)
                            .head(self.max_categories)
                        )
                        for row in counts_df.iter_rows():
                            val_str = str(row[0])
                            cnt = int(row[1])
                            top_categories.append(
                                CategoryFrequency(
                                    value=val_str,
                                    count=cnt,
                                    percentage=(cnt / row_count) * 100.0,
                                )
                            )
                    except Exception as err:
                        logger.debug("Failed category distribution on '%s': %s", col_name, err)

            columns_profile.append(
                ColumnProfile(
                    name=col_name,
                    physical_type=str(dtype),
                    total_count=row_count,
                    null_count=null_count,
                    null_percentage=round(null_pct, 2),
                    distinct_count=distinct_count,
                    distinct_percentage=round(distinct_pct, 2),
                    is_unique=is_unique,
                    is_constant=is_constant,
                    numeric_stats=numeric_stats,
                    top_categories=top_categories,
                    sample_values=sample_values,
                )
            )

        return DatasetProfile(
            name=dataset.name,
            row_count=row_count,
            column_count=column_count,
            duplicate_rows_count=duplicate_count,
            duplicate_rows_percentage=round(duplicate_pct, 2),
            empty_rows_count=empty_rows,
            columns=columns_profile,
            numeric_column_count=num_count,
            categorical_column_count=cat_count,
            temporal_column_count=temp_count,
        )
