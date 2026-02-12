"""
ALS (EDC Schema) Parser v2.0
解析Medidata Rave ALS文件并自动填充DuckDB metadata
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import logging

from .database import Database
from .metadata import MetadataManager
from .classify_forms_v2 import classify_forms

logger = logging.getLogger(__name__)


def parse_als_to_db(als_path: str, db: Database, study_code: str = '') -> Dict[str, Any]:
    """
    解析ALS文件并填充到DuckDB
    
    Args:
        als_path: ALS文件路径
        db: Database实例
        study_code: 研究代码 (默认''表示cross-study)
    
    Returns:
        包含解析结果和统计信息的字典
    """
    logger.info(f"Parsing ALS: {als_path}")
    als_path = Path(als_path)
    
    # 1. 解析ALS文件
    als_data = _parse_als_file(als_path)
    
    # 2. 分类forms
    form_classification = classify_forms(
        forms=als_data['forms'],
        fields=als_data['fields'],
        matrices=als_data['matrices'],
        matrix_details=als_data['matrix_details']
    )
    
    # 3. 生成Bronze DDL
    ddl_statements = _generate_bronze_ddl(als_data, form_classification)
    
    # 4. 创建Bronze表
    db.create_schema('bronze')
    for form_oid, ddl in ddl_statements.items():
        logger.info(f"Creating Bronze table: bronze.{form_oid.lower()}")
        db.execute(ddl)
    
    # 5. 填充metadata
    meta = MetadataManager(db)
    _populate_schema_docs(meta, als_data, form_classification, study_code)
    _populate_data_catalog(meta, als_data, form_classification, study_code)
    
    # 6. 返回统计信息
    result = {
        'study_code': study_code,
        'forms_total': len(als_data['forms']),
        'forms_by_type': {
            'baseline': len(form_classification['baseline']),
            'longitudinal': len(form_classification['longitudinal']),
            'occurrence': len(form_classification['occurrence'])
        },
        'fields_total': len(als_data['fields']),
        'codelists_total': len(als_data['codelists']),
        'bronze_tables_created': len(ddl_statements),
        'classification': form_classification
    }
    
    logger.info(f"ALS parsing complete: {result['forms_total']} forms, "
                f"{result['fields_total']} fields, "
                f"{result['bronze_tables_created']} Bronze tables")
    
    return result


def _parse_als_file(als_path: Path) -> Dict[str, Any]:
    """解析ALS文件，返回结构化数据"""
    # 读取主要sheets
    forms_df = pd.read_excel(als_path, sheet_name='Forms')
    fields_df = pd.read_excel(als_path, sheet_name='Fields')
    matrices_df = pd.read_excel(als_path, sheet_name='Matrices')
    
    # 解析codelists
    codelists = _parse_codelists(als_path)
    
    # 读取所有Matrix detail sheets
    xl = pd.ExcelFile(als_path)
    matrix_sheets = [s for s in xl.sheet_names if s.startswith('Matrix') and '#' in s]
    matrix_details = {}
    for sheet in matrix_sheets:
        matrix_details[sheet] = pd.read_excel(als_path, sheet_name=sheet)
    
    # 解析forms
    forms = []
    for _, row in forms_df.iterrows():
        forms.append({
            'oid': row['OID'],
            'name': row['DraftFormName'],
            'active': row['DraftFormActive']
        })
    
    # 解析fields
    fields = []
    for _, row in fields_df.iterrows():
        field = {
            'form_oid': row['FormOID'],
            'field_oid': row['FieldOID'],
            'variable_oid': row['VariableOID'],
            'data_format': row['DataFormat'],
            'label': row['SASLabel'] if pd.notna(row['SASLabel']) else row['FieldOID'],
            'codelist_name': row['DataDictionaryName'] if pd.notna(row['DataDictionaryName']) else None
        }
        # 附加codelist
        if field['codelist_name'] and field['codelist_name'] in codelists:
            field['codelist'] = codelists[field['codelist_name']]
        fields.append(field)
    
    # 解析matrices
    matrices = []
    for _, row in matrices_df.iterrows():
        matrices.append({
            'oid': row['OID'],
            'name': row['MatrixName'],
            'addable': row['Addable']
        })
    
    return {
        'forms': forms,
        'fields': fields,
        'matrices': matrices,
        'matrix_details': matrix_details,
        'codelists': codelists
    }


def _parse_codelists(als_path: Path) -> Dict[str, Dict[str, str]]:
    """解析DataDictionaries和DataDictionaryEntries"""
    try:
        dict_df = pd.read_excel(als_path, sheet_name='DataDictionaries')
        entries_df = pd.read_excel(als_path, sheet_name='DataDictionaryEntries')
    except Exception:
        return {}
    
    codelists = {}
    for _, row in dict_df.iterrows():
        dict_name = row['Name'] if 'Name' in dict_df.columns else row.get('OID', '')
        codelists[dict_name] = {}
    
    for _, row in entries_df.iterrows():
        dict_name = row.get('DataDictionaryName', row.get('DataDictionaryOID', ''))
        if dict_name in codelists:
            coded = str(row.get('CodedData', row.get('CodedValue', '')))
            decode = str(row.get('UserDataString', row.get('Decode', '')))
            codelists[dict_name][coded] = decode
    
    return codelists


def _generate_bronze_ddl(als_data: Dict, form_classification: Dict) -> Dict[str, str]:
    """
    生成Bronze层DDL语句
    
    Returns:
        {form_oid: ddl_statement}
    """
    ddl_statements = {}
    
    # 构建fields索引
    fields_by_form = {}
    for field in als_data['fields']:
        form_oid = field['form_oid']
        if form_oid not in fields_by_form:
            fields_by_form[form_oid] = []
        fields_by_form[form_oid].append(field)
    
    # 为每个form生成DDL
    for form in als_data['forms']:
        form_oid = form['oid']
        table_name = form_oid.lower()
        
        if form_oid not in fields_by_form:
            continue
        
        # 构建列定义
        columns = [
            "    usubjid TEXT NOT NULL",  # 标准列
            "    folder_oid TEXT",
            "    folder_instance_id INTEGER",
            "    record_date DATE"
        ]
        
        # 添加字段列
        added_columns = set()  # 跟踪已添加的列名
        for field in fields_by_form[form_oid]:
            variable_oid = field.get('variable_oid')
            if not variable_oid or (isinstance(variable_oid, float) and pd.isna(variable_oid)):
                # 跳过没有variable_oid的field
                continue
            
            col_name = str(variable_oid).lower()
            
            # 跳过重复列名
            if col_name in added_columns:
                logger.warning(f"Duplicate column {col_name} in form {form_oid}, skipping")
                continue
            
            col_type = _map_data_format(field['data_format'])
            columns.append(f"    {col_name} {col_type}")
            added_columns.add(col_name)
        
        # 生成CREATE TABLE语句
        columns_str = ',\n'.join(columns)
        ddl = f"""
CREATE TABLE IF NOT EXISTS bronze.{table_name} (
{columns_str},
    PRIMARY KEY (usubjid, folder_oid, folder_instance_id, record_date)
);
"""
        ddl_statements[form_oid] = ddl
    
    return ddl_statements


def _map_data_format(data_format: str) -> str:
    """映射ALS数据类型到DuckDB类型"""
    data_format = str(data_format).upper()
    
    if 'TEXT' in data_format or 'CHAR' in data_format:
        return 'TEXT'
    elif 'DATE' in data_format:
        return 'DATE'
    elif 'TIME' in data_format:
        return 'TIMESTAMP'
    elif 'INTEGER' in data_format or 'INT' in data_format:
        return 'INTEGER'
    elif 'FLOAT' in data_format or 'DOUBLE' in data_format:
        return 'DOUBLE'
    else:
        return 'TEXT'  # 默认


def _populate_schema_docs(meta: MetadataManager, als_data: Dict, 
                          form_classification: Dict, study_code: str):
    """填充schema_docs metadata"""
    logger.info("Populating schema_docs...")
    
    # 为每个form的每个field添加文档
    fields_by_form = {}
    for field in als_data['fields']:
        form_oid = field['form_oid']
        if form_oid not in fields_by_form:
            fields_by_form[form_oid] = []
        fields_by_form[form_oid].append(field)
    
    for form in als_data['forms']:
        form_oid = form['oid']
        table_name = form_oid.lower()
        
        if form_oid not in fields_by_form:
            continue
        
        # 标准列文档
        meta.add_schema_doc(
            layer='bronze',
            table_name=table_name,
            column_name='usubjid',
            data_type='TEXT',
            description='Unique Subject Identifier',
            source='Standard EDC column'
        )
        
        # 添加字段文档
        added_columns = set()  # 跟踪已添加的列
        for field in fields_by_form[form_oid]:
            variable_oid = field.get('variable_oid')
            if not variable_oid or (isinstance(variable_oid, float) and pd.isna(variable_oid)):
                continue
            
            col_name = str(variable_oid).lower()
            
            # 跳过重复列
            if col_name in added_columns:
                continue
            
            data_type = _map_data_format(field['data_format'])
            
            # 生成example_values（如果有codelist）
            example_values = None
            if 'codelist' in field and field['codelist']:
                example_values = list(field['codelist'].keys())[:5]
            
            meta.add_schema_doc(
                layer='bronze',
                table_name=table_name,
                column_name=col_name,
                data_type=data_type,
                description=field['label'],
                source=f"{form_oid}.{field['field_oid']}",
                example_values=example_values
            )
            added_columns.add(col_name)
    
    logger.info(f"Schema docs populated for {len(fields_by_form)} Bronze tables")


def _populate_data_catalog(meta: MetadataManager, als_data: Dict,
                           form_classification: Dict, study_code: str):
    """填充data_catalog metadata"""
    logger.info("Populating data_catalog...")
    
    # 按schema分类变量
    added_vars = set()  # 跟踪已添加的变量
    for form in als_data['forms']:
        form_oid = form['oid']
        
        # 确定schema
        schema = None
        if form_oid in form_classification['baseline']:
            schema = 'baseline'
        elif form_oid in form_classification['longitudinal']:
            schema = 'longitudinal'
        elif form_oid in form_classification['occurrence']:
            schema = 'occurrence'
        else:
            continue  # 未分类的form
        
        # 添加该form的所有fields
        for field in als_data['fields']:
            if field['form_oid'] != form_oid:
                continue
            
            variable_oid = field.get('variable_oid')
            if not variable_oid or (isinstance(variable_oid, float) and pd.isna(variable_oid)):
                continue
            
            var_name = str(variable_oid).lower()
            
            # 跳过重复变量
            var_key = (var_name, schema, study_code)
            if var_key in added_vars:
                continue
            
            # 转换codelist
            codelist = None
            if 'codelist' in field and field['codelist']:
                codelist = field['codelist']
            
            meta.add_variable(
                var_name=var_name,
                schema=schema,
                layer='bronze',
                label=field['label'],
                data_type=_map_data_format(field['data_format']),
                source_form=form_oid,
                source_field=field['field_oid'],
                codelist=codelist,
                is_derived=False,
                study_code=study_code
            )
            added_vars.add(var_key)
    
    logger.info(f"Data catalog populated for {len(als_data['fields'])} fields")


# 兼容性：保留旧的parse_als函数
def parse_als(als_path: str) -> Dict[str, Any]:
    """
    (Legacy) 解析ALS文件，返回字典
    新代码请使用parse_als_to_db()
    """
    return _parse_als_file(Path(als_path))
