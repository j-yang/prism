"""Silver Transformations.

Python functions for silver layer data transformations.
"""

import polars as pl

from prism.transforms.registry import register_transform


@register_transform("age")
def derive_age(df: pl.DataFrame) -> pl.DataFrame:
    """Direct mapping from DM.AGE."""
    return df.with_columns([pl.col("DM_AGE").alias("age")])


@register_transform("sex")
def derive_sex(df: pl.DataFrame) -> pl.DataFrame:
    """Direct mapping from DM.SEX."""
    return df.with_columns([pl.col("DM_SEX").alias("sex")])


@register_transform("age_group")
def derive_age_group(df: pl.DataFrame) -> pl.DataFrame:
    """Age grouping: <18, 18-64, >=65."""
    return df.with_columns(
        [
            pl.when(pl.col("age") < 18)
            .then(pl.lit("<18"))
            .when(pl.col("age") < 65)
            .then(pl.lit("18-64"))
            .otherwise(pl.lit(">=65"))
            .alias("age_group")
        ]
    )


@register_transform("disease_duration_years")
def derive_disease_duration(df: pl.DataFrame) -> pl.DataFrame:
    """Disease duration in years from diagnosis date."""
    return df.with_columns(
        [
            (
                (pl.col("reference_date") - pl.col("diagnosis_date")).dt.total_days()
                / 365.25
            )
            .cast(pl.Int32)
            .alias("disease_duration_years")
        ]
    )


@register_transform("follow_up_duration_months")
def derive_follow_up_duration(df: pl.DataFrame) -> pl.DataFrame:
    """Follow-up duration in months."""
    return df.with_columns(
        [
            (
                (pl.col("last_visit_date") - pl.col("infusion_date")).dt.total_days()
                / 30.4375
            )
            .cast(pl.Int32)
            .alias("follow_up_duration_months")
        ]
    )
