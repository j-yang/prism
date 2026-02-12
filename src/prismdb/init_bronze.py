"""
Bronze Layer Data Loader
从SAS/CSV/Excel文件导入数据到Bronze层

Note: 使用pandas读取SAS文件（内置支持，无需额外依赖）
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging

from .database import Database
from .metadata import MetadataManager

logger = logging.getLogger(__name__)


# ============================================================================
# SAS Date/Time Conversion
# ============================================================================

def convert_sas_date(sas_value: Union[float, int]) -> Optional[datetime]:
    """
    转换SAS日期到Python datetime
    
    SAS日期基准: 1960-01-01
    Python日期基准: 1970-01-01
    
    Args:
        sas_value: SAS日期数值（距1960-01-01的天数）
    
    Returns:
        Python datetime对象，如果是缺失值返回None
    """
    if pd.isna(sas_value):
        return None
    
    try:
        sas_epoch = datetime(1960, 1, 1)
        return sas_epoch + timedelta(days=float(sas_value))
    except (ValueError, OverflowError) as e:
        logger.warning(f"Invalid SAS date value: {sas_value}, error: {e}")
        return None


def convert_sas_datetime(sas_value: Union[float, int]) -> Optional[datetime]:
    """
    转换SAS datetime到Python datetime
    
    SAS datetime基准: 1960-01-01 00:00:00
    单位: 秒
    
    Args:
        sas_value: SAS datetime数值（距1960-01-01的秒数）
    
    Returns:
        Python datetime对象
    """
    if pd.isna(sas_value):
        return None
    
    try:
        sas_epoch = datetime(1960, 1, 1)
        return sas_epoch + timedelta(seconds=float(sas_value))
    except (ValueError, OverflowError) as e:
        logger.warning(f"Invalid SAS datetime value: {sas_value}, error: {e}")
        return None


def identify_date_columns(df: pd.DataFrame, metadata: Dict = None) -> Dict[str, str]:
    """
    识别DataFrame中的日期列
    
    Args:
        df: 数据DataFrame
        metadata: metadata字典（如果使用pandas读取SAS，此参数功能有限）
    
    Returns:
        {column_name: date_type}，date_type为'date'或'datetime'
    """
    date_columns = {}
    
    # 方法1: 从列名推断
    for col in df.columns:
        col_upper = col.upper()
        if any(x in col_upper for x in ['DAT', 'DATE', 'DT']) and 'TIM' not in col_upper:
            date_columns[col] = 'date'
        elif any(x in col_upper for x in ['DTTM', 'DATETIME', 'TIM']):
            date_columns[col] = 'datetime'
    
    # 方法2: 检查数据类型和值范围
    for col in df.columns:
        if col not in date_columns:
            # 如果是数值型且值在合理的SAS日期范围内（1960-2100）
            if pd.api.types.is_numeric_dtype(df[col]):
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    min_val, max_val = non_null.min(), non_null.max()
                    # SAS日期范围: 0 (1960-01-01) 到 51000 (约2099年)
                    if 0 <= min_val < 51000 and 0 <= max_val < 51000:
                        if 'DAT' in col.upper() or 'DT' in col.upper():
                            date_columns[col] = 'date'
    
    return date_columns


# ============================================================================
# Data Validation
# ============================================================================

def validate_bronze_data(df: pd.DataFrame, form_oid: str, 
                        required_columns: List[str] = None) -> List[str]:
    """
    验证Bronze层数据质量
    
    Args:
        df: 待验证的DataFrame
        form_oid: Form OID
        required_columns: 必填列列表
    
    Returns:
        错误消息列表，空列表表示验证通过
    """
    errors = []
    
    # 检查必填列
    if required_columns is None:
        required_columns = ['usubjid']  # 默认必填
    
    for col in required_columns:
        if col.lower() not in [c.lower() for c in df.columns]:
            errors.append(f"Missing required column: {col}")
        else:
            # 找到实际列名（可能大小写不同）
            actual_col = next(c for c in df.columns if c.lower() == col.lower())
            missing_count = df[actual_col].isna().sum()
            if missing_count > 0:
                errors.append(f"Column '{actual_col}' has {missing_count} missing values")
    
    # 检查是否为空
    if len(df) == 0:
        errors.append(f"DataFrame is empty for form {form_oid}")
    
    # 检查重复记录（基于usubjid）
    if 'usubjid' in [c.lower() for c in df.columns]:
        usubjid_col = next(c for c in df.columns if c.lower() == 'usubjid')
        if df[usubjid_col].duplicated().any():
            dup_count = df[usubjid_col].duplicated().sum()
            logger.warning(f"Found {dup_count} duplicate usubjid values in {form_oid}")
    
    return errors


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_sas_file(sas_path: str, encoding: str = 'latin1') -> tuple[pd.DataFrame, Dict]:
    """
    读取SAS文件（使用pandas内置功能）
    
    Args:
        sas_path: SAS文件路径
        encoding: 文件编码（默认latin1）
    
    Returns:
        (DataFrame, metadata_dict)
        
    Note:
        pandas读取SAS的功能有限，但足以完成基本导入
        如需完整metadata（变量标签、格式等），建议安装pyreadstat
    """
    sas_path = Path(sas_path)
    
    if not sas_path.exists():
        raise FileNotFoundError(f"SAS file not found: {sas_path}")
    
    logger.info(f"Reading SAS file: {sas_path.name}")
    
    try:
        # pandas可以直接读取sas7bdat
        df = pd.read_sas(str(sas_path), encoding=encoding)
        
        # 简化的metadata（pandas不提供完整metadata）
        meta = {
            'columns': list(df.columns),
            'row_count': len(df),
            'dtypes': df.dtypes.to_dict()
        }
        
        logger.info(f"Loaded {len(df)} records, {len(df.columns)} columns")
        return df, meta
        
    except Exception as e:
        logger.error(f"Failed to read SAS file {sas_path}: {e}")
        logger.info("Tip: For better SAS support, install pyreadstat: pip install pyreadstat")
        raise


def load_csv_file(csv_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
    """
    读取CSV文件
    
    Args:
        csv_path: CSV文件路径
        encoding: 文件编码
    
    Returns:
        DataFrame
    """
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger.info(f"Reading CSV file: {csv_path.name}")
    
    try:
        df = pd.read_csv(csv_path, encoding=encoding)
        logger.info(f"Loaded {len(df)} records, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV file {csv_path}: {e}")
        raise


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化列名（转小写）
    
    Args:
        df: 原始DataFrame
    
    Returns:
        列名标准化后的DataFrame
    """
    df.columns = [col.lower() for col in df.columns]
    return df


def convert_dates_in_dataframe(df: pd.DataFrame, date_columns: Dict[str, str]) -> pd.DataFrame:
    """
    批量转换DataFrame中的日期列
    
    Args:
        df: DataFrame
        date_columns: {column_name: date_type}
    
    Returns:
        日期转换后的DataFrame
    """
    df = df.copy()
    
    for col, date_type in date_columns.items():
        if col not in df.columns:
            continue
        
        logger.info(f"Converting column '{col}' as {date_type}")
        
        if date_type == 'date':
            df[col] = df[col].apply(convert_sas_date)
        elif date_type == 'datetime':
            df[col] = df[col].apply(convert_sas_datetime)
    
    return df


def insert_to_bronze(df: pd.DataFrame, table_name: str, db: Database,
                    mode: str = 'append') -> int:
    """
    插入数据到Bronze表
    
    Args:
        df: 待插入的DataFrame
        table_name: Bronze表名（不含schema前缀）
        db: Database实例
        mode: 'append' 或 'replace'
    
    Returns:
        插入的记录数
    """
    full_table = f"bronze.{table_name}"
    
    # 检查表是否存在
    if not db.table_exists(table_name, 'bronze'):
        raise ValueError(f"Bronze table does not exist: {full_table}")
    
    # 获取表结构
    schema_df = db.query_df(f"DESCRIBE {full_table}")
    expected_columns = schema_df['column_name'].str.lower().tolist()
    
    # 检查列是否匹配
    df_columns = [col.lower() for col in df.columns]
    missing_in_df = set(expected_columns) - set(df_columns)
    extra_in_df = set(df_columns) - set(expected_columns)
    
    if missing_in_df:
        logger.warning(f"Columns in table but not in data: {missing_in_df}")
    
    if extra_in_df:
        logger.warning(f"Columns in data but not in table: {extra_in_df}")
        # 只保留表中存在的列
        df = df[[col for col in df.columns if col.lower() in expected_columns]]
    
    # 使用DuckDB的INSERT FROM SELECT
    temp_view = f"temp_{table_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        # 注册DataFrame为临时view
        conn = db.connect()  # 使用公开的connect方法
        conn.register(temp_view, df)
        
        # 执行INSERT
        if mode == 'replace':
            db.execute(f"DELETE FROM {full_table}")
        
        insert_sql = f"INSERT INTO {full_table} SELECT * FROM {temp_view}"
        db.execute(insert_sql)
        
        # 清理临时view
        conn.unregister(temp_view)
        
        record_count = len(df)
        logger.info(f"Inserted {record_count} records into {full_table}")
        
        return record_count
        
    except Exception as e:
        logger.error(f"Failed to insert data into {full_table}: {e}")
        # 清理临时view
        try:
            conn.unregister(temp_view)
        except:
            pass
        raise


# ============================================================================
# High-Level API
# ============================================================================

def load_sas_to_bronze(
    sas_path: str,
    form_oid: str,
    db: Database,
    validate: bool = True,
    convert_dates: bool = True,
    mode: str = 'append'
) -> Dict[str, Any]:
    """
    从SAS文件加载数据到Bronze层（高级API）
    
    Args:
        sas_path: SAS文件路径
        form_oid: 对应的Form OID（Bronze表名）
        db: Database实例
        validate: 是否验证数据
        convert_dates: 是否自动转换日期
        mode: 'append' 或 'replace'
    
    Returns:
        加载统计信息字典
    """
    start_time = datetime.now()
    
    logger.info(f"Loading SAS file to bronze.{form_oid.lower()}")
    
    # 1. 读取SAS文件
    df, meta = load_sas_file(sas_path)
    original_count = len(df)
    
    # 2. 标准化列名
    df = standardize_column_names(df)
    
    # 3. 识别并转换日期列
    if convert_dates:
        date_columns = identify_date_columns(df, meta)
        if date_columns:
            logger.info(f"Identified date columns: {list(date_columns.keys())}")
            df = convert_dates_in_dataframe(df, date_columns)
    
    # 4. 验证数据
    if validate:
        errors = validate_bronze_data(df, form_oid)
        if errors:
            error_msg = "; ".join(errors)
            raise ValueError(f"Data validation failed: {error_msg}")
    
    # 5. 插入数据库
    table_name = form_oid.lower()
    inserted_count = insert_to_bronze(df, table_name, db, mode=mode)
    
    # 6. 返回统计信息
    elapsed = (datetime.now() - start_time).total_seconds()
    
    result = {
        'form_oid': form_oid,
        'table_name': f'bronze.{table_name}',
        'source_file': str(sas_path),
        'original_records': original_count,
        'inserted_records': inserted_count,
        'columns': len(df.columns),
        'elapsed_seconds': elapsed,
        'mode': mode,
        'success': True
    }
    
    logger.info(f"Successfully loaded {inserted_count} records in {elapsed:.2f}s")
    
    return result


def load_study_data(
    data_dir: str,
    db: Database,
    file_pattern: str = "*.sas7bdat",
    form_mapping: Dict[str, str] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    批量加载研究数据
    
    Args:
        data_dir: 数据文件目录
        db: Database实例
        file_pattern: 文件匹配模式
        form_mapping: {文件名: form_oid} 映射，如果None则使用文件名
        validate: 是否验证数据
    
    Returns:
        批量加载统计信息
    """
    data_dir = Path(data_dir)
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # 查找所有数据文件
    data_files = list(data_dir.glob(file_pattern))
    
    if not data_files:
        raise ValueError(f"No data files found matching '{file_pattern}' in {data_dir}")
    
    logger.info(f"Found {len(data_files)} data files to load")
    
    # 加载每个文件
    results = []
    errors = []
    
    for file_path in data_files:
        file_stem = file_path.stem  # 文件名（不含扩展名）
        
        # 确定对应的form_oid
        if form_mapping and file_stem.upper() in form_mapping:
            form_oid = form_mapping[file_stem.upper()]
        else:
            form_oid = file_stem.upper()
        
        try:
            result = load_sas_to_bronze(
                sas_path=str(file_path),
                form_oid=form_oid,
                db=db,
                validate=validate
            )
            results.append(result)
            
        except Exception as e:
            error_info = {
                'file': str(file_path),
                'form_oid': form_oid,
                'error': str(e)
            }
            errors.append(error_info)
            logger.error(f"Failed to load {file_path}: {e}")
    
    # 汇总统计
    summary = {
        'total_files': len(data_files),
        'successful': len(results),
        'failed': len(errors),
        'total_records': sum(r['inserted_records'] for r in results),
        'results': results,
        'errors': errors
    }
    
    logger.info(f"Batch load complete: {summary['successful']}/{summary['total_files']} successful, "
                f"{summary['total_records']} total records")
    
    return summary
