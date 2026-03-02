"""
End-to-End MVP Test: Bronze → Silver → Gold → Platinum

This script demonstrates the complete PRISM-DB pipeline:
1. Initialize database (meta + gold + traceability)
2. Create test data (Silver layer)
3. Run Gold analysis (with traceability)
4. Generate Platinum portal
5. Start local server for review

Run: python scripts/run_mvp_pipeline.py
"""

import sys
import os
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from olympusdb import (
    Database,
    init_database,
    MetadataManager,
    GoldEngine,
    PlatinumGenerator,
)


def init_db(db_path: str) -> Database:
    """Initialize database with all schemas."""
    print("\n" + "=" * 60)
    print("Step 1: Initialize Database")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent

    # Meta schema
    print("  - Creating meta schema (11 tables)...")
    db = init_database(db_path, str(base_dir / "sql" / "init_meta.sql"))

    # Gold schema
    print("  - Creating gold schema (3 tables)...")
    with open(base_dir / "sql" / "init_gold.sql", "r") as f:
        db.execute_script(f.read())

    # Traceability schema
    print("  - Creating traceability schema (2 tables)...")
    with open(base_dir / "sql" / "init_traceability.sql", "r") as f:
        db.execute_script(f.read())

    print(f"  ✓ Database initialized: {db_path}")
    return db


def create_test_data(db: Database):
    """Create test data for MVP demo."""
    print("\n" + "=" * 60)
    print("Step 2: Create Test Data")
    print("=" * 60)

    meta = MetadataManager(db)

    # Study info
    print("  - Setting study info...")
    meta.set_study_info(study_code="MVP001", indication="IIM")

    # Create Silver schema and table
    print("  - Creating silver.baseline table...")
    db.create_schema("silver")
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

    # Insert test data
    print("  - Inserting test subjects...")
    test_data = [
        ("001", "Drug A", "Y", 45, "M", "White"),
        ("002", "Drug A", "Y", 52, "F", "Asian"),
        ("003", "Drug A", "Y", 38, "M", "White"),
        ("004", "Drug A", "Y", 61, "F", "White"),
        ("005", "Drug A", "Y", 29, "M", "Black"),
        ("006", "Placebo", "Y", 55, "F", "White"),
        ("007", "Placebo", "Y", 42, "M", "Asian"),
        ("008", "Placebo", "Y", 48, "F", "White"),
        ("009", "Placebo", "Y", 35, "M", "White"),
        ("010", "Placebo", "N", 60, "M", "White"),  # Excluded from SAFFL
    ]

    for row in test_data:
        db.execute(
            "INSERT OR REPLACE INTO silver.baseline VALUES (?, ?, ?, ?, ?, ?)", row
        )

    # Create output definitions
    print("  - Creating output definitions...")
    meta.add_output(
        output_id="T1_demog",
        output_type="table",
        schema="baseline",
        title="Demographics and Baseline Characteristics",
        population="SAFFL",
        section="Tables",
    )

    # Link variables
    for var in ["age", "sex", "race", "trta", "saffl"]:
        meta.add_variable(
            var_id=var,
            var_name=var,
            schema="baseline",
            var_label=var.upper(),
            data_type="character"
            if var in ["sex", "race", "trta", "saffl"]
            else "numeric",
        )
        meta.add_output_variable(output_id="T1_demog", var_id=var)

    print(f"  ✓ Test data created: {len(test_data)} subjects")


def run_gold_analysis(db: Database):
    """Run Gold analysis and write traceability."""
    print("\n" + "=" * 60)
    print("Step 3: Run Gold Analysis")
    print("=" * 60)

    # Compute statistics directly
    print("  - Computing demographics statistics...")

    # Clear existing Gold data
    db.execute("DELETE FROM gold.baseline WHERE output_id = 'T1_demog'")
    db.execute("DELETE FROM meta.data_lineage WHERE target_output_id = 'T1_demog'")

    # Get data
    df = db.query_df("SELECT * FROM silver.baseline WHERE saffl = 'Y'")

    results = []
    lineage_records = []

    for trta in df["trta"].unique():
        subset = df[df["trta"] == trta]
        subjects = subset["usubjid"].tolist()

        # AGE statistics
        ages = subset["age"].dropna().tolist()
        import numpy as np

        stats = {
            "n": len(ages),
            "mean": round(np.mean(ages), 1),
            "sd": round(np.std(ages, ddof=1), 1),
            "median": round(np.median(ages), 1),
            "min": int(np.min(ages)),
            "max": int(np.max(ages)),
        }

        for stat_name, stat_value in stats.items():
            results.append(
                {
                    "output_id": "T1_demog",
                    "group1_name": "TRTA",
                    "group1_value": trta,
                    "variable": "AGE",
                    "stat_name": stat_name,
                    "stat_value": stat_value,
                    "stat_display": str(stat_value),
                }
            )

        # Record lineage for 'n'
        lineage_records.append(
            {
                "lineage_id": f"T1_demog_{trta}_AGE_n",
                "target_output_id": "T1_demog",
                "target_group_name": "TRTA",
                "target_group_value": trta,
                "target_variable": "AGE",
                "target_stat_name": "n",
                "target_stat_value": stats["n"],
                "source_table": "silver.baseline",
                "source_subjects": json.dumps(subjects),
                "source_record_count": len(subjects),
                "source_query": f"SELECT usubjid, age FROM silver.baseline WHERE saffl = 'Y' AND trta = '{trta}'",
            }
        )

        # SEX statistics
        for sex in subset["sex"].unique():
            n = len(subset[subset["sex"] == sex])
            pct = round(100 * n / len(subset), 0)

            results.append(
                {
                    "output_id": "T1_demog",
                    "group1_name": "TRTA",
                    "group1_value": trta,
                    "variable": "SEX",
                    "category": sex,
                    "stat_name": "n",
                    "stat_value": n,
                    "stat_display": str(n),
                }
            )

            results.append(
                {
                    "output_id": "T1_demog",
                    "group1_name": "TRTA",
                    "group1_value": trta,
                    "variable": "SEX",
                    "category": sex,
                    "stat_name": "pct",
                    "stat_value": pct,
                    "stat_display": f"{pct:.0f}%",
                }
            )

    # Insert results
    print(f"  - Inserting {len(results)} Gold records...")
    for r in results:
        db.execute(
            """
            INSERT INTO gold.baseline 
            (output_id, group1_name, group1_value, variable, category, stat_name, stat_value, stat_display)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                r["output_id"],
                r["group1_name"],
                r["group1_value"],
                r["variable"],
                r.get("category"),
                r["stat_name"],
                r["stat_value"],
                r["stat_display"],
            ),
        )

    # Insert lineage
    print(f"  - Inserting {len(lineage_records)} lineage records...")
    for lin in lineage_records:
        db.execute(
            """
            INSERT INTO meta.data_lineage
            (lineage_id, target_output_id, target_group_name, target_group_value,
             target_variable, target_stat_name, target_stat_value,
             source_table, source_subjects, source_record_count, source_query)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                lin["lineage_id"],
                lin["target_output_id"],
                lin["target_group_name"],
                lin["target_group_value"],
                lin["target_variable"],
                lin["target_stat_name"],
                lin["target_stat_value"],
                lin["source_table"],
                lin["source_subjects"],
                lin["source_record_count"],
                lin["source_query"],
            ),
        )

    print(
        f"  ✓ Gold analysis complete: {len(results)} statistics, {len(lineage_records)} lineage records"
    )


def generate_platinum(db: Database, db_path: str):
    """Generate Platinum portal."""
    print("\n" + "=" * 60)
    print("Step 4: Generate Platinum Portal")
    print("=" * 60)

    gen = PlatinumGenerator(db)
    result = gen.generate(output_dir="generated/platinum", db_path=db_path)

    print(f"  ✓ Portal generated at: {result['output_dir']}")
    print(f"    Files: {', '.join(result['files'])}")
    return result["output_dir"]


def start_server(output_dir: str):
    """Start local HTTP server."""
    print("\n" + "=" * 60)
    print("Step 5: Start Local Server")
    print("=" * 60)

    print(f"\n  Starting server at: http://localhost:8000")
    print(f"  Serving files from: {output_dir}")
    print("\n  Press Ctrl+C to stop the server")
    print("\n" + "=" * 60)

    os.chdir(output_dir)
    subprocess.run([sys.executable, "-m", "http.server", "8000"])


def main():
    """Run the complete MVP pipeline."""
    print("\n" + "=" * 60)
    print("PRISM-DB MVP Pipeline")
    print("Bronze → Silver → Gold → Platinum")
    print("=" * 60)

    db_path = "study.duckdb"

    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        # Step 1: Initialize database
        db = init_db(db_path)

        # Step 2: Create test data
        create_test_data(db)

        # Step 3: Run Gold analysis
        run_gold_analysis(db)

        # Step 4: Generate Platinum
        output_dir = generate_platinum(db, db_path)

        # Close database
        db.close()

        # Step 5: Start server
        start_server(output_dir)

    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
