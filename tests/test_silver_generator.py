"""
Test Silver Generator

Test the Silver SQL generation functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prismdb import Database, init_database, MetadataManager, SilverGenerator


def setup_test_data(db: Database):
    """Setup test derivations and variables."""
    meta = MetadataManager(db)

    # Set study info
    meta.set_study_info(study_code="TEST001")

    # Add variables
    meta.add_variable(
        var_id="trtsdt",
        var_name="trtsdt",
        schema="baseline",
        var_label="First Treatment Date",
        data_type="date",
    )
    meta.add_variable(
        var_id="agegrp",
        var_name="agegroup",
        schema="baseline",
        var_label="Age Group",
        data_type="character",
    )
    meta.add_variable(
        var_id="teaefl",
        var_name="teaefl",
        schema="occurrence",
        var_label="Treatment-Emergent AE Flag",
        data_type="flag",
    )
    meta.add_variable(
        var_id="phga_chg",
        var_name="chg",
        schema="longitudinal",
        var_label="Change from Baseline",
        data_type="numeric",
        param_ref="PHGA",
    )

    # Add derivations
    meta.add_derivation(
        deriv_id="deriv_trtsdt",
        target_var="trtsdt",
        transformation="MIN(EXSTDT) where EXDOSE > 0",
        source_vars=["exstdt"],
        source_tables=["bronze.ex"],
        complexity="simple",
    )
    meta.add_derivation(
        deriv_id="deriv_agegrp",
        target_var="agegrp",
        transformation="age group categorization: <18, 18-64, >=65",
        source_vars=["age"],
        complexity="simple",
    )
    meta.add_derivation(
        deriv_id="deriv_teaefl",
        target_var="teaefl",
        transformation="CASE WHEN AE start date >= first treatment date THEN Y ELSE N",
        source_vars=["aestdtc", "trtsdt"],
        source_tables=["bronze.ae"],
        complexity="medium",
    )
    meta.add_derivation(
        deriv_id="deriv_phga_chg",
        target_var="phga_chg",
        transformation="AVAL - BASE where ABLFL = Y for baseline",
        source_vars=["aval", "base"],
        source_tables=["bronze.efficacy"],
        complexity="medium",
    )

    # Create sample Bronze tables
    db.create_schema("bronze")
    db.execute("""
        CREATE TABLE IF NOT EXISTS bronze.ex (
            usubjid TEXT,
            exstdt DATE,
            exdose DOUBLE
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS bronze.ae (
            usubjid TEXT,
            aestdtc DATE,
            aeterm TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS bronze.efficacy (
            usubjid TEXT,
            paramcd TEXT,
            visitnum INTEGER,
            aval DOUBLE
        )
    """)

    print("Test data setup complete.")


def test_silver_generator():
    """Test SilverGenerator."""
    print("=" * 60)
    print("Testing Silver Generator")
    print("=" * 60)

    # Initialize database
    db_path = "test_silver_gen.duckdb"
    sql_script = str(Path(__file__).parent.parent / "sql" / "init_meta.sql")

    db = init_database(db_path, sql_script)

    # Setup test data
    print("\n1. Setting up test data...")
    setup_test_data(db)

    # Create generator (without LLM for now)
    print("\n2. Creating SilverGenerator...")
    gen = SilverGenerator(db, api_key=None)  # No API key = template only

    # Generate SQL
    print("\n3. Generating SQL files...")
    output_dir = str(Path(__file__).parent.parent / "generated")
    log = gen.generate_all(output_dir=output_dir)

    # Print stats
    print("\n4. Generation Stats:")
    print(f"   Total: {log['stats']['total']}")
    print(f"   Template: {log['stats']['template']}")
    print(f"   LLM: {log['stats']['llm']}")
    print(f"   Skipped: {log['stats']['skipped']}")

    # Print derivation details
    print("\n5. Derivation Details:")
    for deriv in log["derivations"]:
        status = "✓" if deriv["status"] == "success" else "⚠"
        review = " (needs review)" if deriv["needs_review"] else ""
        print(
            f"   {status} {deriv['target_var']} [{deriv['schema']}] - {deriv['method']}{review}"
        )

    # Show generated files
    print("\n6. Generated Files:")
    for schema in ["baseline", "occurrence", "longitudinal"]:
        filepath = Path(output_dir) / f"derive_{schema}.sql"
        if filepath.exists():
            print(f"\n   --- {filepath.name} ---")
            content = filepath.read_text()
            print(content[:500] + "..." if len(content) > 500 else content)

    # Cleanup
    db.close()

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"\nTest database: {db_path}")
    print(f"Generated files: {output_dir}/")


if __name__ == "__main__":
    test_silver_generator()
