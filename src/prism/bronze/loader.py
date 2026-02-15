import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging

from prism.core.database import Database

logger = logging.getLogger(__name__)


def convert_sas_date(sas_value: Union[float, int]) -> Optional[datetime]:
    if pd.isna(sas_value):
        return None
    try:
        sas_epoch = datetime(1960, 1, 1)
        return sas_epoch + timedelta(days=float(sas_value))
    except (ValueError, OverflowError) as e:
        logger.warning(f"Invalid SAS date value: {sas_value}, error: {e}")
        return None


def convert_sas_datetime(sas_value: Union[float, int]) -> Optional[datetime]:
    if pd.isna(sas_value):
        return None
    try:
        sas_epoch = datetime(1960, 1, 1)
        return sas_epoch + timedelta(seconds=float(sas_value))
    except (ValueError, OverflowError) as e:
        logger.warning(f"Invalid SAS datetime value: {sas_value}, error: {e}")
        return None


def load_sas_file(sas_path: str, encoding: str = "latin1") -> tuple[pd.DataFrame, Dict]:
    sas_path = Path(sas_path)

    if not sas_path.exists():
        raise FileNotFoundError(f"SAS file not found: {sas_path}")

    logger.info(f"Reading SAS file: {sas_path.name}")

    try:
        df = pd.read_sas(str(sas_path), encoding=encoding)

        meta = {
            "columns": list(df.columns),
            "row_count": len(df),
            "dtypes": df.dtypes.to_dict(),
        }

        logger.info(f"Loaded {len(df)} records, {len(df.columns)} columns")
        return df, meta

    except Exception as e:
        logger.error(f"Failed to read SAS file {sas_path}: {e}")
        raise


def load_csv_file(csv_path: str, **kwargs) -> tuple[pd.DataFrame, Dict]:
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    logger.info(f"Reading CSV file: {csv_path.name}")

    df = pd.read_csv(csv_path, **kwargs)

    meta = {
        "columns": list(df.columns),
        "row_count": len(df),
        "dtypes": df.dtypes.to_dict(),
    }

    logger.info(f"Loaded {len(df)} records, {len(df.columns)} columns")
    return df, meta


def load_sas_to_bronze(
    db: Database,
    sas_path: str,
    table_name: str,
    schema: str = "bronze",
    encoding: str = "latin1",
) -> int:
    df, meta = load_sas_file(sas_path, encoding)

    df.columns = [c.lower() for c in df.columns]

    full_table_name = f"{schema}.{table_name}"

    db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    db.execute(f"DROP TABLE IF EXISTS {full_table_name}")

    conn = db.connect()
    conn.execute(f"CREATE TABLE {full_table_name} AS SELECT * FROM df")

    logger.info(f"Loaded {len(df)} rows into {full_table_name}")
    return len(df)


def load_study_data(
    db: Database,
    data_dir: str,
    file_pattern: str = "*.sas7bdat",
    schema: str = "bronze",
) -> Dict[str, int]:
    data_dir = Path(data_dir)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    results = {}

    for file_path in data_dir.glob(file_pattern):
        table_name = file_path.stem.lower()

        try:
            row_count = load_sas_to_bronze(db, str(file_path), table_name, schema)
            results[table_name] = row_count
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            results[table_name] = -1

    return results
