"""Silver Occurrence Transformations.

Python functions for occurrence domain transformations.
"""

import polars as pl

from olympus.transforms.registry import register_transform


@register_transform("teae_flg")
def derive_teae_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Treatment Emergent Adverse Event Flag.

    AE starting on or after infusion date.
    """
    return df.with_columns(
        [
            pl.when(pl.col("ae_start_date") >= pl.col("infusion_date"))
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("teae_flg")
        ]
    )


@register_transform("sae_flg")
def derive_sae_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Serious Adverse Event Flag."""
    return df.with_columns(
        [
            pl.when(pl.col("AE_AESER") == "Y")
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("sae_flg")
        ]
    )


@register_transform("ae_related_flg")
def derive_ae_related_flag(df: pl.DataFrame) -> pl.DataFrame:
    """AE related to treatment flag."""
    return df.with_columns(
        [
            pl.when(
                pl.col("AE_AEREL").is_in(
                    [
                        "Related",
                        "Possibly Related",
                        "Probably Related",
                    ]
                )
            )
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("ae_related_flg")
        ]
    )


@register_transform("ae_grade_3_4_flg")
def derive_ae_grade_3_4_flag(df: pl.DataFrame) -> pl.DataFrame:
    """AE grade 3 or 4 flag."""
    return df.with_columns(
        [
            pl.when(pl.col("AE_AETOXGR").is_in(["3", "4"]))
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("ae_grade_3_4_flg")
        ]
    )


@register_transform("ae_related_grade_3_4_flg")
def derive_ae_related_grade_3_4_flag(df: pl.DataFrame) -> pl.DataFrame:
    """AE related and grade 3-4 flag."""
    return df.with_columns(
        [
            pl.when(
                (
                    pl.col("AE_AEREL").is_in(
                        ["Related", "Possibly Related", "Probably Related"]
                    )
                )
                & (pl.col("AE_AETOXGR").is_in(["3", "4"]))
            )
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("ae_related_grade_3_4_flg")
        ]
    )


@register_transform("sae_death_flg")
def derive_sae_death_flag(df: pl.DataFrame) -> pl.DataFrame:
    """SAE with outcome death flag."""
    return df.with_columns(
        [
            pl.when(pl.col("AE_AESDTH") == "Y")
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("sae_death_flg")
        ]
    )


@register_transform("ae_interrupt_cart_flg")
def derive_ae_interrupt_flag(df: pl.DataFrame) -> pl.DataFrame:
    """AE leading to interruption of CART therapy."""
    return df.with_columns(
        [
            pl.when(pl.col("AE_AEACN").is_in(["Drug interrupted", "Dose Interrupted"]))
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("ae_interrupt_cart_flg")
        ]
    )


@register_transform("ae_withdrawal_flg")
def derive_ae_withdrawal_flag(df: pl.DataFrame) -> pl.DataFrame:
    """AE leading to study withdrawal."""
    return df.with_columns(
        [
            pl.when(pl.col("AE_AEWD") == "Y")
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("ae_withdrawal_flg")
        ]
    )


@register_transform("crs_flg")
def derive_crs_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Cytokine Release Syndrome flag."""
    return df.with_columns(
        [
            pl.when(
                pl.col("AE_AEDECOD")
                .str.to_lowercase()
                .str.contains("cytokine release syndrome")
            )
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("crs_flg")
        ]
    )


@register_transform("icans_flg")
def derive_icans_flag(df: pl.DataFrame) -> pl.DataFrame:
    """ICANS (neurotoxicity) flag."""
    return df.with_columns(
        [
            pl.when(
                pl.col("AE_AEDECOD").str.to_lowercase().str.contains("neurotoxicity")
                | pl.col("AE_AEBODSYS")
                .str.to_lowercase()
                .str.contains("nervous system")
            )
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("icans_flg")
        ]
    )


@register_transform("ae_duration_days")
def derive_ae_duration(df: pl.DataFrame) -> pl.DataFrame:
    """AE duration in days."""
    return df.with_columns(
        [
            (pl.col("AE_AEENDTC") - pl.col("AE_AESTDTC"))
            .dt.total_days()
            .cast(pl.Int32)
            .alias("ae_duration_days")
        ]
    )


@register_transform("received_infusion_flg")
def derive_received_infusion_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Received infusion flag."""
    return df.with_columns(
        [
            pl.when(pl.col("EX_EXSTDTC").is_not_null())
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("received_infusion_flg")
        ]
    )


@register_transform("has_safety_eval_flg")
def derive_has_safety_eval_flag(df: pl.DataFrame) -> pl.DataFrame:
    """Has safety evaluation flag."""
    return df.with_columns(
        [
            pl.when(pl.col("SAFFL") == "Y")
            .then(pl.lit("Y"))
            .otherwise(pl.lit("N"))
            .alias("has_safety_eval_flg")
        ]
    )
