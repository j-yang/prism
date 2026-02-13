"""
Test Script for Phase 1 - Meta Schema v3.1
测试DuckDB连接和11张Meta表功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prismdb import Database, init_database, MetadataManager


def test_phase_1():
    """测试Phase 1 - 新11张Meta表"""

    print("=" * 60)
    print("Phase 1 Testing - Meta Schema v3.1")
    print("=" * 60)

    db_path = "test_prism_v31.duckdb"
    sql_script = str(Path(__file__).parent.parent / "sql" / "init_meta.sql")

    print(f"\n1. Initializing database: {db_path}")
    print("-" * 60)

    db = init_database(db_path, sql_script)

    print("\nSchemas created:")
    schemas = db.list_schemas()
    for schema in schemas:
        print(f"  - {schema}")

    print("\nMeta tables created:")
    meta_tables = db.list_tables("meta")
    for table in meta_tables:
        print(f"  - meta.{table}")

    print(f"\nTotal meta tables: {len(meta_tables)}")

    print("\n" + "=" * 60)
    print("2. Testing Metadata Manager")
    print("=" * 60)

    meta = MetadataManager(db)

    # 1. Study Info
    print("\n1) Setting study info...")
    meta.set_study_info(
        study_code="TEST001", indication="IIM", description="Test Study for Meta Schema"
    )
    study_info = meta.get_study_info()
    print(f"   Study: {study_info['study_code']} - {study_info['indication']}")

    # 2. Params
    print("\n2) Adding params...")
    meta.add_param(
        param_id="param_phga",
        paramcd="PHGA",
        param_label="Physician Global Assessment",
        category="efficacy",
        data_type="continuous",
        unit="points",
    )
    meta.add_param(
        param_id="param_alt",
        paramcd="ALT",
        param_label="Alanine Aminotransferase",
        category="safety",
        data_type="continuous",
        unit="U/L",
    )
    params = meta.get_params()
    print(f"   Params added: {len(params)} records")
    for p in params:
        print(f"     - {p['paramcd']}: {p['param_label']} ({p['category']})")

    # 3. Flags
    print("\n3) Adding flags...")
    meta.add_flag(
        flag_id="flag_teaefl",
        flag_name="TEAEFL",
        flag_label="Treatment-Emergent AE Flag",
        domain="AE",
        default_condition="ASTDT >= TRTSDT",
    )
    meta.add_flag(
        flag_id="flag_saefl",
        flag_name="SAEFL",
        flag_label="Serious AE Flag",
        domain="AE",
        default_condition="AESER = 'Y'",
    )
    flags = meta.get_flags()
    print(f"   Flags added: {len(flags)} records")
    for f in flags:
        print(f"     - {f['flag_name']}: {f['flag_label']} (domain: {f['domain']})")

    # 4. Visits
    print("\n4) Adding visits...")
    meta.add_visit(
        visit_id="visit_baseline",
        visit_name="BASELINE",
        visitnum=0,
        visit_label="Baseline",
        is_baseline=True,
        target_day=0,
    )
    meta.add_visit(
        visit_id="visit_week12",
        visit_name="WEEK12",
        visitnum=12,
        visit_label="Week 12",
        is_endpoint=True,
        target_day=84,
    )
    visits = meta.get_visits()
    print(f"   Visits added: {len(visits)} records")
    for v in visits:
        print(f"     - {v['visit_name']}: {v['visit_label']} (day {v['target_day']})")

    # 5. Variables
    print("\n5) Adding variables...")
    meta.add_variable(
        var_id="usubjid",
        var_name="usubjid",
        schema="baseline",
        var_label="Subject Identifier",
        data_type="character",
    )
    meta.add_variable(
        var_id="age",
        var_name="age",
        schema="baseline",
        var_label="Age at Screening",
        data_type="numeric",
    )
    meta.add_variable(
        var_id="phga",
        var_name="phga",
        schema="longitudinal",
        var_label="Physician Global Assessment",
        data_type="numeric",
        param_ref="PHGA",
    )
    meta.add_variable(
        var_id="teaefl",
        var_name="teaefl",
        schema="occurrence",
        var_label="Treatment-Emergent AE Flag",
        data_type="flag",
        flag_ref="TEAEFL",
    )
    variables = meta.get_variables()
    print(f"   Variables added: {len(variables)} records")
    for v in variables:
        print(f"     - {v['var_id']}: {v['var_label']} ({v['schema']})")

    # 6. Derivations
    print("\n6) Adding derivations...")
    meta.add_derivation(
        deriv_id="deriv_agegrp",
        target_var="agegrp",
        transformation="CASE WHEN age < 65 THEN '<65' ELSE '>=65' END",
        source_vars=["age"],
        transformation_type="sql",
        complexity="simple",
        description="Age group categorization",
    )
    derivations = meta.get_derivations()
    print(f"   Derivations added: {len(derivations)} records")
    for d in derivations:
        print(f"     - {d['deriv_id']}: {d['target_var']} ({d['complexity']})")

    # 7. Outputs
    print("\n7) Adding outputs...")
    meta.add_output(
        output_id="T1_demog",
        output_type="table",
        schema="baseline",
        title="Demographics and Baseline Characteristics",
        population="SAFFL",
        section="demographics",
    )
    meta.add_output(
        output_id="T2_teae",
        output_type="table",
        schema="occurrence",
        title="Treatment-Emergent Adverse Events",
        population="SAFFL",
        section="safety",
    )
    outputs = meta.get_outputs()
    print(f"   Outputs added: {len(outputs)} records")
    for o in outputs:
        print(f"     - {o['output_id']}: {o['title']} ({o['schema']})")

    # 8. Output Variables
    print("\n8) Adding output variables...")
    meta.add_output_variable(output_id="T1_demog", var_id="usubjid", role="group")
    meta.add_output_variable(output_id="T1_demog", var_id="age", role="measure")
    output_vars = meta.get_output_variables("T1_demog")
    print(f"   Output variables for T1_demog: {len(output_vars)} records")
    for ov in output_vars:
        print(f"     - {ov['var_name']}: {ov['role']}")

    # 9. Output Params
    print("\n9) Adding output params...")
    meta.add_output_param(output_id="T2_teae", paramcd="PHGA")
    output_params = meta.get_output_params("T2_teae")
    print(f"   Output params for T2_teae: {len(output_params)} records")

    # 10. Functions
    print("\n10) Adding functions...")
    meta.add_function(
        function_id="func_mean_sd",
        function_name="Calculate Mean and SD",
        impl_type="sql",
        description="Calculate mean, standard deviation for continuous variable",
    )
    functions = meta.get_functions()
    print(f"   Functions added: {len(functions)} records")
    for f in functions:
        print(f"     - {f['function_id']}: {f['function_name']} ({f['impl_type']})")

    # 11. Dependencies
    print("\n11) Adding dependencies...")
    meta.add_dependency("agegrp", "age")
    deps = meta.get_dependencies()
    print(f"   Dependencies added: {len(deps)} records")
    for d in deps:
        print(f"     - {d['from_var']} -> {d['to_var']}")

    print("\n" + "=" * 60)
    print("3. Testing Utility Methods")
    print("=" * 60)

    print("\nExecution order (topological sort):")
    exec_order = meta.get_execution_order()
    print(f"  {exec_order}")

    print("\nMissing derivations (variables without derivations):")
    missing = meta.get_missing_derivations()
    print(f"  {len(missing)} variables without derivations")

    print("\nOutput full spec for T1_demog:")
    full_spec = meta.get_output_full_spec("T1_demog")
    if full_spec:
        print(f"  Title: {full_spec['title']}")
        print(f"  Variables: {len(full_spec['variables'])}")
        print(f"  Params: {len(full_spec['params'])}")

    print("\n" + "=" * 60)
    print("✅ Phase 1 Tests Complete!")
    print("=" * 60)

    db.close()

    print(f"\nTest database created: {db_path}")
    print("You can inspect it with: duckdb test_prism_v31.duckdb")


if __name__ == "__main__":
    test_phase_1()
