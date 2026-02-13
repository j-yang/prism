"""
PRISM-DB Gold Layer

Generate Python analysis scripts for Silver → Gold aggregation.
"""

from .engine import GoldEngine
from .stats import (
    desc_stats_continuous,
    desc_stats_categorical,
    format_stat,
    compute_table_stats,
    compute_total_stats,
)

__all__ = [
    "GoldEngine",
    "desc_stats_continuous",
    "desc_stats_categorical",
    "format_stat",
    "compute_table_stats",
    "compute_total_stats",
]
