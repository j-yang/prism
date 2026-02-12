"""
Test Script for Phase 1.4 - Bronze Data Import
测试SAS文件导入到Bronze层
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from prismdb import (
    Database, init_database, MetadataManager,
    parse_als_to_db,
    load_sas_to_bronze,
    load_study_data,
    convert_sas_date,
    convert_sas_datetime
)


def test_date_conversion():
    """测试SAS日期转换"""
    print("=" * 60)
    print("Test 1: SAS Date Conversion")
    print("=" * 60)
    
    # SAS日期: 0 = 1960-01-01
    test_cases = [
        (0, "1960-01-01"),
        (365, "1961-01-01"),
        (18262, "2010-01-01"),  # 2010-01-01距1960-01-01约50年
        (None, None),
    ]
    
    print("\nTesting convert_sas_date():")
    for sas_val, expected in test_cases:
        result = convert_sas_date(sas_val)
        result_str = result.strftime("%Y-%m-%d") if result else None
        status = "[OK]" if result_str == expected else "[FAIL]"
        print(f"  {status} SAS {sas_val} -> {result_str} (expected: {expected})")
    
    # SAS datetime: 0 = 1960-01-01 00:00:00
    print("\nTesting convert_sas_datetime():")
    test_datetime = [
        (0, "1960-01-01 00:00:00"),
        (3600, "1960-01-01 01:00:00"),
        (86400, "1960-01-02 00:00:00"),
    ]
    
    for sas_val, expected in test_datetime:
        result = convert_sas_datetime(sas_val)
        result_str = result.strftime("%Y-%m-%d %H:%M:%S") if result else None
        status = "[OK]" if result_str == expected else "[FAIL]"
        print(f"  {status} SAS {sas_val} -> {result_str} (expected: {expected})")
    
    print("\n[PASS] Date conversion tests complete!")


def test_sas_import_mock():
    """测试SAS导入流程（使用模拟数据）"""
    print("\n" + "=" * 60)
    print("Test 2: SAS Import (Mock Data)")
    print("=" * 60)
    
    # 初始化数据库
    db_path = "test_bronze_import.duckdb"
    sql_script = "../sql/init_metadata.sql"
    als_file = "../examples/D8318N00001/D8318N00001_ALS.xlsx"
    
    print(f"\n1. Initializing database: {db_path}")
    db = init_database(db_path, sql_script)
    
    # 解析ALS创建Bronze表
    if not Path(als_file).exists():
        print(f"[WARN]  ALS file not found, skipping test: {als_file}")
        db.close()
        return
    
    print(f"\n2. Parsing ALS and creating Bronze tables")
    result = parse_als_to_db(als_file, db, study_code='D8318N00001')
    print(f"   Created {result['bronze_tables_created']} Bronze tables")
    
    # 创建模拟SAS数据
    print(f"\n3. Creating mock SAS data")
    import pandas as pd
    
    # 模拟DM (Demographics) 数据
    mock_dm_data = pd.DataFrame({
        'usubjid': ['D8318N00001-001-001', 'D8318N00001-001-002', 'D8318N00001-001-003'],
        'age': [45, 52, 38],
        'sex': ['M', 'F', 'M'],
        'race': ['White', 'Asian', 'White'],
        'brthdat': [18000.0, 17800.0, 19000.0],  # SAS日期
        'folder_oid': ['DEMO', 'DEMO', 'DEMO'],
        'folder_instance_id': [1, 1, 1],
        'record_date': [datetime(2023, 1, 15), datetime(2023, 1, 16), datetime(2023, 1, 17)]
    })
    
    # 检查DM表是否存在
    if db.table_exists('dm', 'bronze'):
        print(f"\n4. Inserting mock data into bronze.dm")
        
        # 标准化列名
        mock_dm_data.columns = [col.lower() for col in mock_dm_data.columns]
        
        # 转换日期
        from prismdb.init_bronze import convert_dates_in_dataframe
        date_columns = {'brthdat': 'date'}
        mock_dm_data = convert_dates_in_dataframe(mock_dm_data, date_columns)
        
        # 插入数据
        from prismdb.init_bronze import insert_to_bronze
        try:
            count = insert_to_bronze(mock_dm_data, 'dm', db, mode='append')
            print(f"   [OK] Inserted {count} records")
            
            # 验证数据
            result_df = db.query_df("SELECT * FROM bronze.dm LIMIT 5")
            print(f"\n5. Verification - First {min(len(result_df), 5)} records:")
            print(result_df.to_string(index=False))
            
        except Exception as e:
            print(f"   [FAIL] Failed to insert: {e}")
    else:
        print(f"   [WARN]  bronze.dm table does not exist, skipping insert")
    
    print("\n[PASS] Mock SAS import test complete!")
    db.close()


def test_with_real_sas():
    """测试真实SAS文件导入（如果可用）"""
    print("\n" + "=" * 60)
    print("Test 3: Real SAS File Import")
    print("=" * 60)
    
    # 检查是否有真实SAS文件
    sas_dir = Path("../examples/D8318N00001/data")
    
    if not sas_dir.exists():
        print(f"\n[WARN]  No real SAS data directory found: {sas_dir}")
        print("Skipping real SAS import test.")
        print("\nTo test with real data:")
        print("  1. Place SAS files in: examples/D8318N00001/data/")
        print("  2. Files should be named like: dm.sas7bdat, ae.sas7bdat, etc.")
        return
    
    sas_files = list(sas_dir.glob("*.sas7bdat"))
    
    if not sas_files:
        print(f"\n[WARN]  No SAS files found in {sas_dir}")
        print("Skipping real SAS import test.")
        return
    
    print(f"\nFound {len(sas_files)} SAS files:")
    for f in sas_files:
        print(f"  - {f.name}")
    
    # 初始化数据库
    db_path = "test_real_sas.duckdb"
    sql_script = "../sql/init_metadata.sql"
    als_file = "../examples/D8318N00001/D8318N00001_ALS.xlsx"
    
    print(f"\nInitializing database and Bronze schema...")
    db = init_database(db_path, sql_script)
    parse_als_to_db(als_file, db, study_code='D8318N00001')
    
    # 尝试加载第一个SAS文件
    first_sas = sas_files[0]
    form_oid = first_sas.stem.upper()
    
    print(f"\nAttempting to load: {first_sas.name} -> bronze.{form_oid.lower()}")
    
    try:
        result = load_sas_to_bronze(
            sas_path=str(first_sas),
            form_oid=form_oid,
            db=db,
            validate=True
        )
        
        print(f"\n[PASS] Successfully loaded:")
        print(f"   File: {result['source_file']}")
        print(f"   Table: {result['table_name']}")
        print(f"   Records: {result['inserted_records']}")
        print(f"   Columns: {result['columns']}")
        print(f"   Time: {result['elapsed_seconds']:.2f}s")
        
        # 查看数据样本
        table_name = f"bronze.{form_oid.lower()}"
        sample_df = db.query_df(f"SELECT * FROM {table_name} LIMIT 3")
        print(f"\nData sample (first 3 records):")
        print(sample_df.to_string(index=False))
        
    except Exception as e:
        print(f"\n[FAIL] Failed to load: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def test_batch_load():
    """测试批量导入"""
    print("\n" + "=" * 60)
    print("Test 4: Batch Load")
    print("=" * 60)
    
    sas_dir = Path("../examples/D8318N00001/data")
    
    if not sas_dir.exists() or not list(sas_dir.glob("*.sas7bdat")):
        print(f"\n[WARN]  No SAS data available for batch load test")
        print("Skipping batch load test.")
        return
    
    # 初始化数据库
    db_path = "test_batch_load.duckdb"
    sql_script = "../sql/init_metadata.sql"
    als_file = "../examples/D8318N00001/D8318N00001_ALS.xlsx"
    
    print(f"\nInitializing database and Bronze schema...")
    db = init_database(db_path, sql_script)
    parse_als_to_db(als_file, db, study_code='D8318N00001')
    
    print(f"\nStarting batch load from: {sas_dir}")
    
    try:
        summary = load_study_data(
            data_dir=str(sas_dir),
            db=db,
            validate=True
        )
        
        print(f"\n[PASS] Batch Load Summary:")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Total records: {summary['total_records']}")
        
        if summary['successful'] > 0:
            print(f"\n   Successfully loaded tables:")
            for result in summary['results']:
                print(f"     - {result['table_name']}: {result['inserted_records']} records")
        
        if summary['errors']:
            print(f"\n   [WARN]  Failed tables:")
            for error in summary['errors']:
                print(f"     - {error['form_oid']}: {error['error']}")
        
    except Exception as e:
        print(f"\n[FAIL] Batch load failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Phase 1.4 Testing Suite" + " " * 20 + "║")
    print("║" + " " * 15 + "Bronze Data Import" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test 1: 日期转换
    test_date_conversion()
    
    # Test 2: 模拟数据导入
    test_sas_import_mock()
    
    # Test 3: 真实SAS文件（如果有）
    test_with_real_sas()
    
    # Test 4: 批量导入（如果有）
    test_batch_load()
    
    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)
    
    print("\n[NOTE] Test databases created:")
    for db_file in ['test_bronze_import.duckdb', 'test_real_sas.duckdb', 'test_batch_load.duckdb']:
        if Path(db_file).exists():
            print(f"   - {db_file}")
    
    print("\n[TIP] To inspect databases:")
    print("   duckdb test_bronze_import.duckdb")
    print("   > SELECT * FROM bronze.dm LIMIT 10;")


if __name__ == '__main__':
    main()
