"""
ALS (EDC Schema) Parser
解析Medidata Rave ALS文件，提取Forms/Fields/Matrices信息
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import json


def parse_als(als_path: str) -> Dict[str, Any]:
    """
    解析ALS文件，返回结构化数据
    
    Returns:
        {
            "forms": [...],
            "fields": [...],
            "matrices": [...],
            "matrix_details": {...},
            "codelists": {...}
        }
    """
    als_path = Path(als_path)
    
    # 读取各sheet
    forms_df = pd.read_excel(als_path, sheet_name='Forms')
    fields_df = pd.read_excel(als_path, sheet_name='Fields')
    matrices_df = pd.read_excel(als_path, sheet_name='Matrices')
    
    # 读取codelist
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


def get_form_visits(form_oid: str, matrix_details: Dict) -> List[str]:
    """获取某个form出现在哪些visit"""
    visits = []
    for sheet_name, df in matrix_details.items():
        first_col = df.columns[0]  # FormOID列
        if form_oid in df[first_col].values:
            row = df[df[first_col] == form_oid].iloc[0]
            for col in df.columns[1:]:  # 跳过FormOID列
                if pd.notna(row[col]):
                    visits.append(col)
    return list(set(visits))


def is_form_addable(form_oid: str, matrices: List[Dict], matrix_details: Dict) -> bool:
    """检查form是否在Addable=True的matrix中"""
    addable_matrices = {m['oid'] for m in matrices if m['addable']}
    
    for sheet_name, df in matrix_details.items():
        # 从sheet名提取matrix OID (e.g., "Matrix1#AE" -> "AE")
        matrix_oid = sheet_name.split('#')[1] if '#' in sheet_name else ''
        if matrix_oid in addable_matrices:
            first_col = df.columns[0]
            if form_oid in df[first_col].values:
                row = df[df[first_col] == form_oid].iloc[0]
                # 检查是否有任何非空的visit标记
                for col in df.columns[1:]:
                    if pd.notna(row[col]):
                        return True
    return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        result = parse_als(sys.argv[1])
        print(f"Forms: {len(result['forms'])}")
        print(f"Fields: {len(result['fields'])}")
        print(f"Matrices: {len(result['matrices'])}")
        print(f"Codelists: {len(result['codelists'])}")
