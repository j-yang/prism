"""Transform Registry.

Register and retrieve Python transformation functions.
"""

import logging
from typing import Callable, Dict, List, Optional

import polars as pl

logger = logging.getLogger(__name__)

TransformFunc = Callable[[pl.DataFrame], pl.DataFrame]

_REGISTRY: Dict[str, TransformFunc] = {}


def register_transform(name: str) -> Callable:
    """Decorator to register a transformation function.

    Usage:
        @register_transform("teae_flg")
        def derive_teae_flag(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([
                pl.when(pl.col("ae_start_date") >= pl.col("infusion_date"))
                .then(pl.lit("Y"))
                .otherwise(pl.lit("N"))
                .alias("teae_flg")
            ])
    """

    def decorator(func: TransformFunc) -> TransformFunc:
        _REGISTRY[name] = func
        logger.debug(f"Registered transform: {name}")
        return func

    return decorator


def get_transform(name: str) -> Optional[TransformFunc]:
    """Get a registered transformation by name."""
    return _REGISTRY.get(name)


def list_transforms() -> List[str]:
    """List all registered transformation names."""
    return list(_REGISTRY.keys())


def apply_transform(df: pl.DataFrame, name: str) -> pl.DataFrame:
    """Apply a transformation to a DataFrame.

    Args:
        df: Input DataFrame
        name: Name of registered transform

    Returns:
        Transformed DataFrame

    Raises:
        ValueError: If transform not found
    """
    transform = get_transform(name)
    if transform is None:
        raise ValueError(f"Transform not found: {name}")
    return transform(df)


def apply_transforms(df: pl.DataFrame, names: List[str]) -> pl.DataFrame:
    """Apply multiple transformations sequentially.

    Args:
        df: Input DataFrame
        names: List of transform names

    Returns:
        Transformed DataFrame
    """
    result = df
    for name in names:
        result = apply_transform(result, name)
    return result
