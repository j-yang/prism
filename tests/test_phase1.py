"""
Test Script for Phase 1.1 & 1.2
测试DuckDB连接和Metadata表功能
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from prismdb import Database, init_database, MetadataManager

def test_phase_1():
    """测试Phase 1.1 和 1.2"""
    
    print("=" * 60)
    print("Phase 1.1 & 1.2 Testing")
    print("=" * 60)
    
    # 测试数据库路径
    db_path = "test_prism.duckdb"
    sql_script = "../sql/init_metadata.sql"
    
    print(f"\n1. Initializing database: {db_path}")
    print("-" * 60)
    
    # 初始化数据库
    db = init_database(db_path, sql_script)
    
    # 列出schemas
    print("\nSchemas created:")
    schemas = db.list_schemas()
    for schema in schemas:
        print(f"  - {schema}")
    
    # 列出meta表
    print("\nMeta tables created:")
    meta_tables = db.list_tables('meta')
    for table in meta_tables:
        print(f"  - meta.{table}")
    
    print("\n" + "=" * 60)
    print("2. Testing Metadata Manager")
    print("=" * 60)
    
    # 创建元数据管理器
    meta = MetadataManager(db)
    
    # 测试添加schema docs
    print("\nAdding schema documentation...")
    meta.add_schema_doc(
        layer='bronze',
        table_name='demog',
        column_name='usubjid',
        data_type='TEXT',
        description='Unique Subject Identifier',
        source='USUBJID field',
        example_values=['001-001', '001-002']
    )
    meta.add_schema_doc(
        layer='bronze',
        table_name='demog',
        column_name='age',
        data_type='INTEGER',
        description='Age at screening',
        source='AGE field'
    )
    
    # 查询schema docs
    docs = meta.get_schema_docs(layer='bronze', table_name='demog')
    print(f"Schema docs added: {len(docs)} records")
    for doc in docs:
        print(f"  - {doc['column_name']}: {doc['data_type']} - {doc['description']}")
    
    # 测试添加变量
    print("\nAdding variables to data catalog...")
    meta.add_variable(
        var_name='usubjid',
        schema='baseline',
        layer='bronze',
        label='Subject ID',
        data_type='TEXT',
        source_form='Demog',
        source_field='USUBJID',
        is_derived=False
    )
    meta.add_variable(
        var_name='age',
        schema='baseline',
        layer='bronze',
        label='Age',
        data_type='INTEGER',
        source_form='Demog',
        source_field='AGE',
        is_derived=False
    )
    meta.add_variable(
        var_name='trtsdt',
        schema='baseline',
        layer='silver',
        label='First Treatment Date',
        data_type='DATE',
        is_derived=True,
        derivation_id='deriv_trtsdt'
    )
    
    # 查询变量
    vars_bronze = meta.get_variables(layer='bronze')
    vars_silver = meta.get_variables(layer='silver', is_derived=True)
    print(f"Variables (bronze): {len(vars_bronze)} records")
    print(f"Variables (silver derived): {len(vars_silver)} records")
    
    # 测试添加衍生规则
    print("\nAdding derivations...")
    meta.add_derivation(
        derivation_id='deriv_trtsdt',
        target_var='trtsdt',
        target_schema='baseline',
        transformation_sql="SELECT usubjid, MIN(trtsdt) as trtsdt FROM bronze.ex GROUP BY usubjid",
        depends_on=['trtsdt'],
        complexity='simple',
        description='First treatment start date from EX domain',
        execution_order=1
    )
    
    derivations = meta.get_derivations()
    print(f"Derivations added: {len(derivations)} records")
    for deriv in derivations:
        print(f"  - {deriv['derivation_id']}: {deriv['target_var']} ({deriv['complexity']})")
    
    # 测试添加output spec
    print("\nAdding output specifications...")
    meta.add_output_spec(
        output_id='T1_demog',
        output_type='table',
        schema='baseline',
        source_table='silver.baseline',
        required_vars=['usubjid', 'age', 'sex', 'race', 'trta'],
        filter_condition="saffl = 'Y'",
        group_by={'group1': 'TRTA'},
        stats_required=['n', 'mean', 'sd', 'median'],
        analysis_method='descriptive',
        title_template='Demographics and Baseline Characteristics',
        block='demographics',
        sort_order=1
    )
    
    outputs = meta.get_output_specs()
    print(f"Output specs added: {len(outputs)} records")
    for out in outputs:
        print(f"  - {out['output_id']}: {out['output_type']} ({out['schema']})")
    
    # 测试添加output assembly
    print("\nAdding output assembly rules...")
    meta.add_output_assembly(
        output_id='T1_demog',
        component_type='row',
        component_order=1,
        select_condition="variable IN ('AGE', 'SEX', 'RACE')",
        layout_template='by_variable'
    )
    
    assembly = meta.get_output_assembly('T1_demog')
    print(f"Assembly rules added: {len(assembly)} records")
    
    # 测试查询功能
    print("\n" + "=" * 60)
    print("3. Testing Query Functions")
    print("=" * 60)
    
    # 查询所有bronze变量
    print("\nBronze variables:")
    bronze_vars = meta.get_variables(layer='bronze', schema='baseline')
    for var in bronze_vars:
        print(f"  - {var['var_name']}: {var['data_type']} ({var['source_form']}.{var['source_field']})")
    
    # 查询所有衍生变量
    print("\nDerived variables:")
    derived_vars = meta.get_variables(is_derived=True)
    for var in derived_vars:
        print(f"  - {var['var_name']} (from {var['derivation_id']})")
    
    # 查询baseline schema的outputs
    print("\nBaseline outputs:")
    baseline_outputs = meta.get_output_specs(schema='baseline')
    for out in baseline_outputs:
        print(f"  - {out['output_id']}: {out['title_template']}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 1.1 & 1.2 Tests Complete!")
    print("=" * 60)
    
    # 关闭数据库
    db.close()
    
    print(f"\nTest database created: {db_path}")
    print("You can inspect it with: duckdb test_prism.duckdb")


if __name__ == '__main__':
    test_phase_1()
