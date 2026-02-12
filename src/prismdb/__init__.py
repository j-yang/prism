"""
PRISM-DB: Clinical Trial Data Warehouse
"""

__version__ = "3.0.0"

# Core modules
from .database import Database, init_database, get_connection
from .metadata import MetadataManager

# Bronze layer
from .parse_als_v2 import parse_als_to_db, parse_als
from .classify_forms_v2 import classify_forms
from .init_bronze import (
    load_sas_to_bronze,
    load_study_data,
    load_sas_file,
    load_csv_file,
    convert_sas_date,
    convert_sas_datetime
)

# Legacy modules (to be refactored) - commented out temporarily
# from .parse_als import parse_als
# from .classify_forms import classify_forms, generate_data_catalog
# from .generate_schema import generate_raw_layer_ddl
# from .init_raw_layer import init_raw_layer

__all__ = [
    # Core
    'Database',
    'init_database',
    'get_connection',
    'MetadataManager',
    # Bronze
    'parse_als_to_db',
    'parse_als',
    'classify_forms',
    'load_sas_to_bronze',
    'load_study_data',
    'load_sas_file',
    'load_csv_file',
    'convert_sas_date',
    'convert_sas_datetime',
    # Legacy - commented out
    # 'parse_als',
    # 'classify_forms',
    # 'generate_data_catalog', 
    # 'generate_raw_layer_ddl',
    # 'init_raw_layer'
]


