"""Gold Transformations.

Statistical functions for gold layer aggregations.
"""

from typing import Any, Dict

import polars as pl


def count(df: pl.DataFrame, column: str = None) -> int:
    """Count non-null values in column or total rows."""
    if column:
        return df.select(pl.col(column).drop_nulls()).height
    return df.height


def n_subj(df: pl.DataFrame, subject_col: str = "USUBJID") -> int:
    """Count unique subjects."""
    return df.select(subject_col).n_unique()


def n_events(df: pl.DataFrame) -> int:
    """Count total events (rows)."""
    return df.height


def mean_sd(df: pl.DataFrame, value_col: str, group_col: str = None) -> Dict[str, Any]:
    """Calculate mean and standard deviation.

    Args:
        df: Input DataFrame
        value_col: Column with values
        group_col: Optional grouping column

    Returns:
        Dict with mean, sd, median, min, max
    """
    result = {}

    if group_col:
        for group in df.select(group_col).unique():
            subset = df.filter(pl.col(group_col) == group)
            vals = subset.select(value_col).drop_nulls()
            if vals.height > 0:
                result[group] = {
                    "n": vals.height,
                    "mean": vals.select(value_col).mean(),
                    "sd": vals.select(value_col).std(),
                    "median": vals.select(value_col).median(),
                    "min": vals.select(value_col).min(),
                    "max": vals.select(value_col).max(),
                }
    else:
        vals = df.select(value_col).drop_nulls()
        if vals.height > 0:
            result["_overall"] = {
                "n": vals.height,
                "mean": vals.select(value_col).mean(),
                "sd": vals.select(value_col).std(),
                "median": vals.select(value_col).median(),
                "min": vals.select(value_col).min(),
                "max": vals.select(value_col).max(),
            }

    return result


def freq_pct(
    df: pl.DataFrame, category_col: str, group_col: str = None
) -> Dict[str, Dict[str, Any]]:
    """Calculate frequency and percentage.

    Args:
        df: Input DataFrame
        category_col: Column with categories
        group_col: Optional grouping column

    Returns:
        Dict with n and pct for"""
    result = {}

    if group_col:
        for group in df.select(group_col).unique():
            subset = df.filter(pl.col(group_col) == group)
            total = subset.height
            freq = subset.group_by(category_col).agg(pl.len().alias("n"))
            for row in freq.iter_rows(named=True):
                result[f"{group}_{row[category_col]}"] = {
                    "n": row["n"],
                    "pct": round(row["n"] / total * 100, 1) if total > 0 else 0,
                }
    else:
        total = df.height
        freq = df.group_by(category_col).agg(pl.len().alias("n"))
        for row in freq.iter_rows(named=True):
            result[row[category_col]] = {
                "n": row["n"],
                "pct": round(row["n"] / total * 100, 1) if total > 0 else 0,
            }

    return result
