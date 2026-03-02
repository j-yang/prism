"""CLI for PRISM Meta Tools.

Utilities for loading metadata to database and extracting mock shells.
"""

import argparse
import json
from pathlib import Path

from prism.core.database import Database
from prism.meta.excel_writer import write_meta_excel
from prism.meta.extractor import extract_mock_shell
from prism.meta.loader import load_specs_to_meta


def cmd_load(args):
    """Load generated metadata to meta tables."""
    meta_path = Path(args.meta)

    if meta_path.suffix == ".xlsx":
        import pandas as pd

        def clean_value(val):
            """Convert nan to None."""
            if pd.isna(val):
                return None
            return val

        silver_df = pd.read_excel(meta_path, sheet_name="silver_variables")
        params_df = pd.read_excel(meta_path, sheet_name="params")

        from prism.meta.definitions.models import (
            MetaDefinitions,
            ParamDefinition,
            SilverVariableDefinition,
        )

        silver_vars = []
        for _, row in silver_df.iterrows():
            var_name = clean_value(row.get("var_name"))
            if var_name:
                used_in = clean_value(row.get("used_in"))
                if used_in and isinstance(used_in, str):
                    used_in = [x.strip() for x in used_in.split(",")]
                else:
                    used_in = []

                silver_vars.append(
                    SilverVariableDefinition(
                        var_name=var_name,
                        var_label=clean_value(row.get("var_label"))
                        or clean_value(row.get("label"))
                        or "",
                        schema=clean_value(row.get("schema")) or "baseline",
                        data_type=clean_value(row.get("data_type")),
                        description=clean_value(row.get("description")) or "",
                        used_in=used_in,
                        confidence=clean_value(row.get("confidence")) or "medium",
                        source_vars=clean_value(row.get("source_vars")),
                        transformation=clean_value(row.get("transformation"))
                        or clean_value(row.get("derivation")),
                        transformation_type=clean_value(row.get("transformation_type"))
                        or "direct",
                    )
                )

        params = []
        for _, row in params_df.iterrows():
            paramcd = clean_value(row.get("paramcd"))
            if paramcd:
                used_in = clean_value(row.get("used_in"))
                if used_in and isinstance(used_in, str):
                    used_in = [x.strip() for x in used_in.split(",")]
                else:
                    used_in = []

                params.append(
                    ParamDefinition(
                        paramcd=paramcd,
                        parameter=clean_value(row.get("parameter")) or "",
                        category=clean_value(row.get("category")),
                        unit=clean_value(row.get("unit")),
                        used_in=used_in,
                    )
                )

        definitions = MetaDefinitions(silver_variables=silver_vars, params=params)
        specs = [definitions]
    else:
        data = json.loads(meta_path.read_text())
        from prism.meta.definitions.models import MetaDefinitions

        specs = [MetaDefinitions(**data)]

    db_path = args.db or args.meta.replace(".xlsx", ".duckdb").replace(
        ".json", ".duckdb"
    )

    with Database(db_path) as db:
        from prism.meta.schema import generate_meta_ddl

        ddl = generate_meta_ddl()
        db.execute_script(ddl)

        summary = load_specs_to_meta(db, specs)

        print("Loaded to meta tables:")
        print(f"  Silver variables: {summary['silver_variables']}")
        print(f"  Params: {summary['params']}")
        print(f"  Gold statistics: {summary['gold_statistics']}")
        print(f"  Platinum: {summary['platinum']}")

        if summary["errors"]:
            print(f"\nErrors: {len(summary['errors'])}")
            for err in summary["errors"][:5]:
                print(f"  {err}")


def cmd_extract(args):
    """Extract mock shell to JSON for inspection."""
    print(f"Extracting: {args.mock}")

    context = extract_mock_shell(args.mock, args.output)

    print(f"Study: {context.study_title}")
    print(f"Protocol: {context.protocol_no}")
    print(f"Deliverables: {len(context.deliverables)}")

    for d in context.deliverables:
        print(f"  {d.deliverable_id} ({d.deliverable_type}): {d.title[:50]}...")


def main():
    parser = argparse.ArgumentParser(
        description="PRISM Meta Tools - Utilities for metadata management"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load", help="Load generated metadata to meta tables"
    )
    load_parser.add_argument(
        "--meta", required=True, help="Path to generated metadata file (xlsx/json)"
    )
    load_parser.add_argument(
        "--db", help="Path to DuckDB database (default: same name as meta file)"
    )

    extract_parser = subparsers.add_parser("extract", help="Extract mock shell to JSON")
    extract_parser.add_argument("--mock", required=True, help="Path to mock shell")
    extract_parser.add_argument("--output", "-o", help="Output JSON path")

    args = parser.parse_args()

    if args.command == "load":
        cmd_load(args)
    elif args.command == "extract":
        cmd_extract(args)


if __name__ == "__main__":
    main()
