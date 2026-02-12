"""
Schema Generator
根据data_catalog生成Raw Layer的DDL
"""
from typing import Dict, List, Any
import json


def generate_raw_layer_ddl(data_catalog: List[Dict]) -> str:
    """
    生成完整的Raw Layer DDL
    
    包含:
    - Metadata tables (studies, data_catalog)
    - raw_static
    - raw_longitudinal  
    - raw_occurrence
    """
    ddl_parts = []
    
    # 1. Metadata tables
    ddl_parts.append(_generate_metadata_tables())
    
    # 2. raw_static - 动态列根据catalog生成
    static_fields = [f for f in data_catalog if f['structure'] == 'static']
    ddl_parts.append(_generate_raw_static(static_fields))
    
    # 3. raw_longitudinal - 固定结构
    ddl_parts.append(_generate_raw_longitudinal())
    
    # 4. raw_occurrence - 核心列固定 + 动态列
    occurrence_fields = [f for f in data_catalog if f['structure'] == 'occurrence']
    ddl_parts.append(_generate_raw_occurrence(occurrence_fields))
    
    # 5. Indexes
    ddl_parts.append(_generate_indexes())
    
    return '\n\n'.join(ddl_parts)


def _generate_metadata_tables() -> str:
    return '''-- ============================================
-- Metadata Tables
-- ============================================

CREATE TABLE IF NOT EXISTS studies (
    study_code TEXT PRIMARY KEY,
    study_name TEXT,
    indication TEXT,
    phase TEXT,
    status TEXT DEFAULT 'active',
    edc_schema_file TEXT,
    raw_data_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_code TEXT,
    var_name TEXT NOT NULL,
    structure TEXT NOT NULL CHECK (structure IN ('static', 'longitudinal', 'occurrence')),
    label TEXT,
    data_type TEXT,
    source_form TEXT,
    source_field TEXT,
    codelist TEXT,
    is_derived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_code, var_name, structure),
    FOREIGN KEY (study_code) REFERENCES studies(study_code)
);'''


def _generate_raw_static(static_fields: List[Dict]) -> str:
    """生成raw_static表DDL，包含动态列"""
    
    # 收集唯一的变量名
    var_names = {}
    for f in static_fields:
        var = f['var_name']
        if var not in var_names:
            var_names[var] = f['data_type']
    
    # 生成列定义
    columns = [
        'usubjid TEXT PRIMARY KEY',
        'study_code TEXT',
    ]
    
    for var_name, data_type in var_names.items():
        if var_name.lower() not in ('usubjid', 'study_code'):
            columns.append(f'{var_name} {data_type}')
    
    columns.append('import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    return f'''-- ============================================
-- Raw Layer: Static (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_static (
    {(',' + chr(10) + '    ').join(columns)}
);'''


def _generate_raw_longitudinal() -> str:
    """生成raw_longitudinal表DDL - 固定结构"""
    return '''-- ============================================
-- Raw Layer: Longitudinal (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_longitudinal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    domain TEXT,
    paramcd TEXT NOT NULL,
    param TEXT,
    visit TEXT,
    visitnum INTEGER,
    adt TEXT,
    aval REAL,
    avalc TEXT,
    ablfl TEXT,
    source_form TEXT,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, paramcd, visit)
);'''


def _generate_raw_occurrence(occurrence_fields: List[Dict]) -> str:
    """生成raw_occurrence表DDL"""
    
    # 收集occurrence特有的变量
    var_names = {}
    core_vars = {'usubjid', 'study_code', 'domain', 'seq', 'term', 'decod', 
                 'cat', 'scat', 'astdt', 'aendt', 'source_form', 'import_timestamp'}
    
    for f in occurrence_fields:
        var = f['var_name']
        if var not in var_names and var.lower() not in core_vars:
            var_names[var] = f['data_type']
    
    # 生成额外列
    extra_columns = []
    for var_name, data_type in list(var_names.items())[:50]:  # 限制列数
        extra_columns.append(f'{var_name} {data_type}')
    
    extra_sql = ''
    if extra_columns:
        extra_sql = ',\n    ' + ',\n    '.join(extra_columns)
    
    return f'''-- ============================================
-- Raw Layer: Occurrence (Bronze)
-- ============================================

CREATE TABLE IF NOT EXISTS raw_occurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usubjid TEXT NOT NULL,
    study_code TEXT,
    domain TEXT NOT NULL,
    seq INTEGER,
    term TEXT,
    decod TEXT,
    cat TEXT,
    scat TEXT,
    astdt TEXT,
    aendt TEXT,
    source_form TEXT{extra_sql},
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usubjid, domain, seq)
);'''


def _generate_indexes() -> str:
    return '''-- ============================================
-- Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_raw_static_study ON raw_static(study_code);
CREATE INDEX IF NOT EXISTS idx_raw_long_usubjid ON raw_longitudinal(usubjid);
CREATE INDEX IF NOT EXISTS idx_raw_long_paramcd ON raw_longitudinal(paramcd);
CREATE INDEX IF NOT EXISTS idx_raw_long_visit ON raw_longitudinal(visit);
CREATE INDEX IF NOT EXISTS idx_raw_long_domain ON raw_longitudinal(domain);
CREATE INDEX IF NOT EXISTS idx_raw_occur_usubjid ON raw_occurrence(usubjid);
CREATE INDEX IF NOT EXISTS idx_raw_occur_domain ON raw_occurrence(domain);'''


if __name__ == '__main__':
    # 示例用法
    sample_catalog = [
        {'var_name': 'age', 'structure': 'static', 'data_type': 'INTEGER'},
        {'var_name': 'sex', 'structure': 'static', 'data_type': 'TEXT'},
    ]
    print(generate_raw_layer_ddl(sample_catalog))
