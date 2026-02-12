"""
Form Classifier v2
根据ALS信息将forms分类为 baseline / longitudinal / occurrence
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def classify_forms(forms: List[Dict], fields: List[Dict], matrices: List[Dict], 
                  matrix_details: Dict) -> Dict[str, List[str]]:
    """
    分类所有forms
    
    分类规则:
    1. 在Addable=True的matrix中有标记 → occurrence
    2. 出现在多个visit → longitudinal  
    3. 只在一个或零个visit → baseline
    
    Args:
        forms: Forms列表
        fields: Fields列表  
        matrices: Matrices列表
        matrix_details: Matrix details字典
    
    Returns:
        {
            "baseline": [form_oid, ...],
            "longitudinal": [form_oid, ...],
            "occurrence": [form_oid, ...]
        }
    """
    result = {
        'baseline': [],
        'longitudinal': [],
        'occurrence': []
    }
    
    # 构建addable matrices集合
    addable_matrices = {m['oid'] for m in matrices if m.get('addable', False)}
    
    for form in forms:
        form_oid = form['oid']
        
        # 检查是否在addable matrix中
        if _is_form_addable(form_oid, addable_matrices, matrix_details):
            result['occurrence'].append(form_oid)
            logger.debug(f"{form_oid} -> occurrence (in addable matrix)")
            continue
        
        # 检查出现在多少个visit
        visits = _get_form_visits(form_oid, matrix_details)
        
        if len(visits) > 1:
            result['longitudinal'].append(form_oid)
            logger.debug(f"{form_oid} -> longitudinal ({len(visits)} visits)")
        else:
            result['baseline'].append(form_oid)
            logger.debug(f"{form_oid} -> baseline ({len(visits)} visit)")
    
    logger.info(f"Form classification: baseline={len(result['baseline'])}, "
                f"longitudinal={len(result['longitudinal'])}, "
                f"occurrence={len(result['occurrence'])}")
    
    return result


def _get_form_visits(form_oid: str, matrix_details: Dict) -> List[str]:
    """获取某个form出现在哪些visit"""
    visits = set()
    
    for sheet_name, df in matrix_details.items():
        if df.empty:
            continue
        
        first_col = df.columns[0]  # FormOID列
        
        # 检查form是否在此matrix中
        if form_oid in df[first_col].values:
            row = df[df[first_col] == form_oid].iloc[0]
            
            # 检查所有visit列
            for col in df.columns[1:]:
                cell_value = row[col]
                # 非空值表示在该visit出现
                if _is_visit_marked(cell_value):
                    visits.add(col)
    
    return list(visits)


def _is_form_addable(form_oid: str, addable_matrices: set, matrix_details: Dict) -> bool:
    """检查form是否在Addable=True的matrix中"""
    for sheet_name, df in matrix_details.items():
        if df.empty:
            continue
        
        # 从sheet名提取matrix OID (e.g., "Matrix1#AE" -> "AE")
        matrix_oid = sheet_name.split('#')[1] if '#' in sheet_name else ''
        
        if matrix_oid in addable_matrices:
            first_col = df.columns[0]
            
            if form_oid in df[first_col].values:
                row = df[df[first_col] == form_oid].iloc[0]
                
                # 检查是否有任何visit标记
                for col in df.columns[1:]:
                    if _is_visit_marked(row[col]):
                        return True
    
    return False


def _is_visit_marked(cell_value) -> bool:
    """判断cell是否表示在该visit出现"""
    import pandas as pd
    
    if pd.isna(cell_value):
        return False
    
    # 常见的标记: 'X', '1', '*', 等
    str_value = str(cell_value).strip().upper()
    return str_value in ['X', '1', '*', 'Y', 'YES', 'TRUE']


# 兼容旧代码
def generate_data_catalog(parsed_als: Dict[str, Any]) -> List[Dict]:
    """
    (Legacy) 生成数据字典
    新代码请使用parse_als_v2.py中的函数
    """
    result = []
    for field in parsed_als['fields']:
        result.append({
            'form': field['form_oid'],
            'field': field['field_oid'],
            'variable': field['variable_oid'],
            'label': field['label'],
            'type': field['data_format']
        })
    return result
