"""
Test Gold Engine

Test the Gold analysis script generation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prismdb import Database, init_database, MetadataManager, GoldEngine


def setup_test_data(db: Database):
    """Setup test outputs and silver data."""
    meta = MetadataManager(db)

    # Set study info
    meta.set_study_info(study_code="TEST001")

    # Add output definitions
    meta.add_output(
        output_id="T1_demog",
        output_type="table",
        schema="baseline",
        title="Demographics and Baseline Characteristics",
        population="SAFFL",
        section="demographics",
    )
    meta.add_output(
        output_id="T4_teae",
        output_type="table",
        schema="occurrence",
        title="Treatment-Emergent Adverse Events Summary",
        population="SAFFL",
        section="safety",
    )

    # Add variables
    meta.add_variable(
        var_id="age",
        var_name="age",
        schema="baseline",
        var_label="Age",
        data_type="numeric",
    )
    meta.add_variable(
        var_id="sex",
        var_name="sex",
        schema="baseline",
        var_label="Sex",
        data_type="character",
    )
    meta.add_variable(
        var_id="trta",
        var_name="trta",
        schema="baseline",
        var_label="Actual Treatment",
        data_type="character",
    )
    meta.add_variable(
        var_id="saffl",
        var_name="saffl",
        schema="baseline",
        var_label="Safety Flag",
        data_type="flag",
    )

    # Link outputs to variables
    meta.add_output_variable(output_id="T1_demog", var_id="age", role="measure")
    meta.add_output_variable(output_id="T1_demog", var_id="sex", role="measure")
    meta.add_output_variable(output_id="T1_demog", var_id="trta", role="group")

    # Create Silver tables with mock data
    db.create_schema("silver")

    # Silver baseline
    db.execute("""
        CREATE TABLE IF NOT EXISTS silver.baseline (
            usubjid TEXT PRIMARY KEY,
            trta TEXT,
            saffl TEXT,
            age DOUBLE,
            sex TEXT,
            race TEXT
        )
    """)

    import pandas as pd

    mock_data = pd.DataFrame(
        [
            {
                "usubjid": "001",
                "trta": "Drug A",
                "saffl": "Y",
                "age": 45,
                "sex": "M",
                "race": "White",
            },
            {
                "usubjid": "002",
                "trta": "Drug A",
                "saffl": "Y",
                "age": 52,
                "sex": "F",
                "race": "Asian",
            },
            {
                "usubjid": "003",
                "trta": "Drug A",
                "saffl": "Y",
                "age": 38,
                "sex": "M",
                "race": "White",
            },
            {
                "usubjid": "004",
                "trta": "Placebo",
                "saffl": "Y",
                "age": 55,
                "sex": "F",
                "race": "White",
            },
            {
                "usubjid": "005",
                "trta": "Placebo",
                "saffl": "Y",
                "age": 42,
                "sex": "M",
                "race": "Black",
            },
            {
                "usubjid": "006",
                "trta": "Placebo",
                "saffl": "N",
                "age": 60,
                "sex": "M",
                "race": "White",
            },
        ]
    )

    for _, row in mock_data.iterrows():
        db.execute(
            """
            INSERT INTO silver.baseline (usubjid, trta, saffl, age, sex, race)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                row["usubjid"],
                row["trta"],
                row["saffl"],
                row["age"],
                row["sex"],
                row["race"],
            ),
        )

    # Silver occurrence (AE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS silver.occurrence (
            usubjid TEXT,
            trta TEXT,
            teaefl TEXT,
            aesoc TEXT,
            aedecod TEXT
        )
    """)

    ae_data = pd.DataFrame(
        [
            {
                "usubjid": "001",
                "trta": "Drug A",
                "teaefl": "Y",
                "aesoc": "Infections",
                "aedecod": "URI",
            },
            {
                "usubjid": "001",
                "trta": "Drug A",
                "teaefl": "Y",
                "aesoc": "GI",
                "aedecod": "Nausea",
            },
            {
                "usubjid": "002",
                "trta": "Drug A",
                "teaefl": "Y",
                "aesoc": "Infections",
                "aedecod": "URI",
            },
            {
                "usubjid": "004",
                "trta": "Placebo",
                "teaefl": "Y",
                "aesoc": "CNS",
                "aedecod": "Headache",
            },
        ]
    )

    for _, row in ae_data.iterrows():
        db.execute(
            """
            INSERT INTO silver.occurrence (usubjid, trta, teaefl, aesoc, aedecod)
            VALUES (?, ?, ?, ?, ?)
        """,
            (row["usubjid"], row["trta"], row["teaefl"], row["aesoc"], row["aedecod"]),
        )

    print("Test data setup complete.")


def test_gold_engine():
    """Test GoldEngine."""
    print("=" * 60)
    print("Testing Gold Engine")
    print("=" * 60)

    # Initialize database
    db_path = "test_gold.duckdb"
    sql_script = str(Path(__file__).parent.parent / "sql" / "init_meta.sql")
    gold_script = str(Path(__file__).parent.parent / "sql" / "init_gold.sql")

    db = init_database(db_path, sql_script)

    # Initialize Gold schema
    with open(gold_script, "r") as f:
        gold_sql = f.read()
    db.execute_script(gold_sql)

    # Setup test data
    print("\n1. Setting up test data...")
    setup_test_data(db)

    # Create engine
    print("\n2. Creating GoldEngine...")
    gen = GoldEngine(db, api_key=None)  # No API key = template only

    # Generate scripts
    print("\n3. Generating analysis scripts...")
    output_dir = str(Path(__file__).parent.parent / "generated" / "analysis")
    log = gen.generate_all(output_dir=output_dir)

    # Print stats
    print("\n4. Generation Stats:")
    print(f"   Total: {log['stats']['total']}")
    print(f"   Template: {log['stats']['template']}")
    print(f"   LLM: {log['stats']['llm']}")
    print(f"   Skipped: {log['stats']['skipped']}")

    # Print output details
    print("\n5. Output Details:")
    for output in log["outputs"]:
        status = "✓" if output["status"] == "success" else "⚠"
        print(
            f"   {status} {output['output_id']} [{output['schema']}] - {output['method']}"
        )

    # Show generated files
    print("\n6. Generated Files:")
    analysis_dir = Path(output_dir)
    for f in sorted(analysis_dir.glob("*.py")):
        print(f"\n   --- {f.name} ---")
        content = f.read_text()
        print(content[:800] + "..." if len(content) > 800 else content)

    # Cleanup
    db.close()

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"\nTest database: {db_path}")
    print(f"Generated scripts: {output_dir}/")


if __name__ == "__main__":
    test_gold_engine()
