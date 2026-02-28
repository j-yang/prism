"""
Test Script for Phase 1.3 - ALS Parser v3.1
测试ALS解析、Bronze DDL生成和metadata填充
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prism import Database, init_database, MetadataManager, parse_als_to_db


def test_phase_1_3():
    """测试Phase 1.3 - ALS解析器"""

    print("=" * 60)
    print("Phase 1.3 Testing - ALS Parser v3.1")
    print("=" * 60)

    als_file = str(
        Path(__file__).parent.parent
        / "examples"
        / "D8318N00001"
        / "D8318N00001_ALS.xlsx"
    )
    db_path = "test_als_v31.duckdb"
    sql_script = str(Path(__file__).parent.parent / "sql" / "init_meta.sql")
    study_code = "D8318N00001"

    if not Path(als_file).exists():
        print(f"\nALS file not found: {als_file}")
        print("Skipping test...")
        return

    print(f"\n1. Initializing database: {db_path}")
    print("-" * 60)

    db = init_database(db_path, sql_script)

    print(f"\n2. Parsing ALS file: {als_file}")
    print("-" * 60)

    result = parse_als_to_db(als_file, db, study_code)

    print(f"\nALS Parsing Results:")
    print(f"  - Study: {result['study_code']}")
    print(f"  - Total forms: {result['forms_total']}")
    print(f"  - Forms by type:")
    print(f"    * Baseline: {result['forms_by_type']['baseline']}")
    print(f"    * Longitudinal: {result['forms_by_type']['longitudinal']}")
    print(f"    * Occurrence: {result['forms_by_type']['occurrence']}")
    print(f"  - Total fields: {result['fields_total']}")
    print(f"  - Total codelists: {result['codelists_total']}")
    print(f"  - Bronze tables created: {result['bronze_tables_created']}")

    print("\n" + "=" * 60)
    print("3. Verifying Bronze Schema")
    print("=" * 60)

    bronze_tables = db.list_tables("bronze")
    print(f"\nBronze tables ({len(bronze_tables)}):")
    for i, table in enumerate(bronze_tables[:10], 1):
        print(f"  {i}. bronze.{table}")
    if len(bronze_tables) > 10:
        print(f"  ... and {len(bronze_tables) - 10} more tables")

    if bronze_tables:
        sample_table = bronze_tables[0]
        print(f"\nSample table structure: bronze.{sample_table}")
        cols = db.query_df(f"DESCRIBE bronze.{sample_table}")
        for _, row in cols.iterrows():
            print(f"  - {row['column_name']}: {row['column_type']}")

    print("\n" + "=" * 60)
    print("4. Verifying Metadata")
    print("=" * 60)

    meta = MetadataManager(db)

    baseline_vars = meta.get_variables(schema="baseline")
    longitudinal_vars = meta.get_variables(schema="longitudinal")
    occurrence_vars = meta.get_variables(schema="occurrence")

    print(f"\nVariables:")
    print(f"  - Baseline: {len(baseline_vars)}")
    print(f"  - Longitudinal: {len(longitudinal_vars)}")
    print(f"  - Occurrence: {len(occurrence_vars)}")

    if baseline_vars:
        print(f"\n  Sample baseline variables:")
        for var in baseline_vars[:5]:
            print(f"    * {var['var_id']}: {var['var_label']} ({var['data_type']})")

    if longitudinal_vars:
        print(f"\n  Sample longitudinal variables:")
        for var in longitudinal_vars[:5]:
            print(f"    * {var['var_id']}: {var['var_label']} ({var['data_type']})")

    if occurrence_vars:
        print(f"\n  Sample occurrence variables:")
        for var in occurrence_vars[:5]:
            print(f"    * {var['var_id']}: {var['var_label']} ({var['data_type']})")

    print("\n" + "=" * 60)
    print("5. Form Classification Details")
    print("=" * 60)

    classification = result["classification"]

    print(f"\nBaseline forms ({len(classification['baseline'])}):")
    for form_oid in list(classification["baseline"])[:5]:
        print(f"  - {form_oid}")
    if len(classification["baseline"]) > 5:
        print(f"  ... and {len(classification['baseline']) - 5} more")

    print(f"\nLongitudinal forms ({len(classification['longitudinal'])}):")
    for form_oid in list(classification["longitudinal"])[:5]:
        print(f"  - {form_oid}")
    if len(classification["longitudinal"]) > 5:
        print(f"  ... and {len(classification['longitudinal']) - 5} more")

    print(f"\nOccurrence forms ({len(classification['occurrence'])}):")
    for form_oid in list(classification["occurrence"])[:5]:
        print(f"  - {form_oid}")
    if len(classification["occurrence"]) > 5:
        print(f"  ... and {len(classification['occurrence']) - 5} more")

    print("\n" + "=" * 60)
    print("Phase 1.3 Tests Complete!")
    print("=" * 60)

    db.close()

    print(f"\nTest database created: {db_path}")
    print("You can inspect it with: duckdb test_als_v31.duckdb")


if __name__ == "__main__":
    test_phase_1_3()
