"""
Form Classifier
根据ALS信息将forms分类为 static / longitudinal / occurrence
"""
from typing import Dict, List, Any
from parse_als import parse_als, get_form_visits, is_form_addable


def classify_forms(parsed_als: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    分类所有forms
    
    分类规则:
    1. 在Addable=True的matrix中有标记 → occurrence
    2. 出现在多个visit → longitudinal  
    3. 只在一个或零个visit → static
    
    Returns:
        {
            "static": [...],
            "longitudinal": [...],
            "occurrence": [...]
        }
    """
    forms = parsed_als['forms']
    matrices = parsed_als['matrices']
    matrix_details = parsed_als['matrix_details']
    
    result = {
        'static': [],
        'longitudinal': [],
        'occurrence': []
    }
    
    for form in forms:
        form_oid = form['oid']
        form_name = form['name']
        
        # 规则1: 检查是否addable
        if is_form_addable(form_oid, matrices, matrix_details):
            result['occurrence'].append({
                'form_oid': form_oid,
                'form_name': form_name,
                'reason': 'In addable matrix'
            })
            continue
        
        # 规则2&3: 检查visit数量
        visits = get_form_visits(form_oid, matrix_details)
        
        if len(visits) > 1:
            result['longitudinal'].append({
                'form_oid': form_oid,
                'form_name': form_name,
                'visits': visits,
                'reason': f'Appears in {len(visits)} visits'
            })
        else:
            result['static'].append({
                'form_oid': form_oid,
                'form_name': form_name,
                'visits': visits,
                'reason': 'Single visit or no visit matrix'
            })
    
    return result


def get_fields_by_form(parsed_als: Dict, form_oid: str) -> List[Dict]:
    """获取某个form的所有fields"""
    return [f for f in parsed_als['fields'] if f['form_oid'] == form_oid]


def generate_data_catalog(parsed_als: Dict, classification: Dict, study_code: str) -> List[Dict]:
    """
    生成data_catalog记录
    
    Returns:
        List of {study_code, var_name, structure, label, data_type, source_form, source_field, codelist}
    """
    catalog = []
    
    # Static fields
    for form_info in classification['static']:
        fields = get_fields_by_form(parsed_als, form_info['form_oid'])
        for field in fields:
            var_oid = field.get('variable_oid')
            if not var_oid or (isinstance(var_oid, float) and str(var_oid) == 'nan'):
                continue
            catalog.append({
                'study_code': study_code,
                'var_name': str(var_oid).lower(),
                'structure': 'static',
                'label': field.get('label', ''),
                'data_type': _map_data_type(field.get('data_format', '')),
                'source_form': form_info['form_oid'],
                'source_field': field['field_oid'],
                'codelist': field.get('codelist')
            })
    
    # Longitudinal fields
    for form_info in classification['longitudinal']:
        fields = get_fields_by_form(parsed_als, form_info['form_oid'])
        for field in fields:
            var_oid = field.get('variable_oid')
            if not var_oid or (isinstance(var_oid, float) and str(var_oid) == 'nan'):
                continue
            catalog.append({
                'study_code': study_code,
                'var_name': str(var_oid).lower(),
                'structure': 'longitudinal',
                'label': field.get('label', ''),
                'data_type': _map_data_type(field.get('data_format', '')),
                'source_form': form_info['form_oid'],
                'source_field': field['field_oid'],
                'codelist': field.get('codelist')
            })
    
    # Occurrence fields
    for form_info in classification['occurrence']:
        fields = get_fields_by_form(parsed_als, form_info['form_oid'])
        for field in fields:
            var_oid = field.get('variable_oid')
            if not var_oid or (isinstance(var_oid, float) and str(var_oid) == 'nan'):
                continue
            catalog.append({
                'study_code': study_code,
                'var_name': str(var_oid).lower(),
                'structure': 'occurrence',
                'label': field['label'],
                'data_type': _map_data_type(field['data_format']),
                'source_form': form_info['form_oid'],
                'source_field': field['field_oid'],
                'codelist': field.get('codelist')
            })
    
    return catalog


def _map_data_type(data_format: str) -> str:
    """将ALS DataFormat映射为SQLite数据类型"""
    if pd.isna(data_format):
        return 'TEXT'
    
    fmt = str(data_format).lower()
    
    if 'date' in fmt or fmt.startswith('yyyy'):
        return 'TEXT'  # 日期存为TEXT
    elif fmt.startswith('$'):
        return 'TEXT'
    elif '+' in fmt or fmt.isdigit():
        return 'REAL'
    else:
        return 'TEXT'


import pandas as pd

if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) > 1:
        als_path = sys.argv[1]
        study_code = sys.argv[2] if len(sys.argv) > 2 else 'STUDY'
        
        parsed = parse_als(als_path)
        classification = classify_forms(parsed)
        
        print(f"\n=== Classification Results ===")
        print(f"Static forms: {len(classification['static'])}")
        print(f"Longitudinal forms: {len(classification['longitudinal'])}")
        print(f"Occurrence forms: {len(classification['occurrence'])}")
        
        print(f"\n=== Static Forms ===")
        for f in classification['static'][:10]:
            print(f"  {f['form_oid']}: {f['form_name']}")
        
        print(f"\n=== Longitudinal Forms ===")
        for f in classification['longitudinal'][:10]:
            print(f"  {f['form_oid']}: {f['form_name']} ({len(f['visits'])} visits)")
        
        print(f"\n=== Occurrence Forms ===")
        for f in classification['occurrence'][:10]:
            print(f"  {f['form_oid']}: {f['form_name']}")
