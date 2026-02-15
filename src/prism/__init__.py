"""
PRISM - Clinical Trial Data Pipeline

A Medallion-architecture data warehouse with AI-powered code generation.
"""

__version__ = "1.0.0"

from prism.core.database import Database, init_database, get_connection
from prism.core.schema import (
    StudyInfo,
    Variable,
    Derivation,
    Output,
    Parameter,
    Flag,
    Visit,
    Function,
    Dependency,
)

from prism.meta import MetadataManager, parse_als_to_db
from prism.bronze import (
    load_sas_file,
    load_csv_file,
    load_sas_to_bronze,
    load_study_data,
)
from prism.silver import SilverGenerator
from prism.gold import GoldEngine, desc_stats_continuous, desc_stats_categorical
from prism.platinum import render_output

__all__ = [
    "Database",
    "init_database",
    "get_connection",
    "StudyInfo",
    "Variable",
    "Derivation",
    "Output",
    "Parameter",
    "Flag",
    "Visit",
    "Function",
    "Dependency",
    "MetadataManager",
    "parse_als_to_db",
    "load_sas_file",
    "load_csv_file",
    "load_sas_to_bronze",
    "load_study_data",
    "SilverGenerator",
    "GoldEngine",
    "desc_stats_continuous",
    "desc_stats_categorical",
    "render_output",
]
