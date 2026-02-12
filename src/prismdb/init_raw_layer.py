"""
Initialize Raw Layer
整合 parse_als + classify_forms + generate_schema
从ALS文件创建Raw Layer数据库
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional

from .parse_als import parse_als
from .classify_forms import classify_forms, generate_data_catalog
from .generate_schema import generate_raw_layer_ddl


def init_raw_layer(
    als_path: str,
    db_path: str,
    study_code: str,
    study_name: Optional[str] = None,
    indication: Optional[str] = None
) -> dict:
    """
    从ALS初始化Raw Layer
    
    Steps:
    1. 解析ALS
    2. 分类forms
    3. 生成data_catalog
    4. 生成DDL
    5. 创建数据库
    
    Returns:
        {
            'classification': {...},
            'catalog_count': int,
            'ddl_path': str,
            'db_path': str
        }
    """
    als_path = Path(als_path)
    db_path = Path(db_path)
    
    print(f"[1/5] Parsing ALS: {als_path.name}")
    parsed = parse_als(str(als_path))
    print(f"      Found {len(parsed['forms'])} forms, {len(parsed['fields'])} fields")
    
    print(f"[2/5] Classifying forms...")
    classification = classify_forms(parsed)
    print(f"      Static: {len(classification['static'])}")
    print(f"      Longitudinal: {len(classification['longitudinal'])}")
    print(f"      Occurrence: {len(classification['occurrence'])}")
    
    print(f"[3/5] Generating data catalog...")
    catalog = generate_data_catalog(parsed, classification, study_code)
    print(f"      Generated {len(catalog)} catalog entries")
    
    print(f"[4/5] Generating DDL...")
    ddl = generate_raw_layer_ddl(catalog)
    
    # 保存DDL到文件
    ddl_path = db_path.parent / 'create_raw_layer.sql'
    ddl_path.write_text(ddl, encoding='utf-8')
    print(f"      Saved DDL to {ddl_path}")
    
    print(f"[5/5] Creating database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 执行DDL
    cursor.executescript(ddl)
    
    # 插入study记录
    cursor.execute('''
        INSERT OR REPLACE INTO studies (study_code, study_name, indication, edc_schema_file)
        VALUES (?, ?, ?, ?)
    ''', (study_code, study_name or study_code, indication, str(als_path)))
    
    # 插入data_catalog
    for entry in catalog:
        cursor.execute('''
            INSERT OR REPLACE INTO data_catalog 
            (study_code, var_name, structure, label, data_type, source_form, source_field, codelist)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry['study_code'],
            entry['var_name'],
            entry['structure'],
            entry['label'],
            entry['data_type'],
            entry['source_form'],
            entry['source_field'],
            json.dumps(entry.get('codelist')) if entry.get('codelist') else None
        ))
    
    conn.commit()
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM data_catalog")
    catalog_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Database: {db_path}")
    print(f"Tables: {', '.join(tables)}")
    print(f"Catalog entries: {catalog_count}")
    
    # 保存分类报告
    report_path = db_path.parent / 'classification_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(classification, f, indent=2, ensure_ascii=False)
    print(f"Classification report: {report_path}")
    
    return {
        'classification': classification,
        'catalog_count': catalog_count,
        'ddl_path': str(ddl_path),
        'db_path': str(db_path),
        'tables': tables
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python init_raw_layer.py <als_path> <db_path> <study_code> [study_name] [indication]")
        sys.exit(1)
    
    als_path = sys.argv[1]
    db_path = sys.argv[2]
    study_code = sys.argv[3]
    study_name = sys.argv[4] if len(sys.argv) > 4 else None
    indication = sys.argv[5] if len(sys.argv) > 5 else None
    
    result = init_raw_layer(als_path, db_path, study_code, study_name, indication)
    print(f"\nDone! Database created at: {result['db_path']}")
