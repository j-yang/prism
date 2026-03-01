"""CLI for PRISM Meta Generator.

Generate clinical trial metadata from mock shells using LLM.
"""

import argparse
import json
from pathlib import Path

from prism.core.database import Database
from prism.meta.excel_writer import write_meta_excel
from prism.meta.extractor import extract_mock_shell
from prism.meta.generator import MetaGenerator
from prism.meta.loader import load_specs_to_meta


def cmd_generate(args):
    """Generate metadata from mock shell."""
    print(f"Extracting mock shell: {args.mock}")

    context = extract_mock_shell(args.mock)
    print(f"Found {len(context.deliverables)} deliverables")

    if args.list_only:
        for d in context.deliverables:
            print(f"  {d.deliverable_id}: {d.title}")
        return

    print(f"Loading ALS: {args.als}")

    provider_name = args.provider or "deepseek"

    generator = MetaGenerator(
        provider=provider_name,
        als_path=args.als,
    )

    if args.debug:
        print(f"Debugging deliverable: {args.debug}")
        specs = [generator.debug_deliverable(context, args.debug, verbose=args.verbose)]
    else:
        print("Generating metadata...")
        deliverable_ids = None
        if args.deliverables:
            deliverable_ids = [d.strip() for d in args.deliverables.split(",")]
        specs = generator.generate_for_context(context, deliverable_ids)

    print(f"Generated {len(specs)} specs")

    study_info = {
        "protocol_no": context.protocol_no,
        "study_title": context.study_title,
    }

    if args.format == "excel":
        output_path = args.output or "meta_generated.xlsx"
        saved_path = write_meta_excel(specs, output_path, study_info)
        print(f"Excel saved to: {saved_path}")
    else:
        output_path = args.output or "meta_generated.json"
        output_data = {
            "study_title": context.study_title,
            "protocol_no": context.protocol_no,
            "specs": [
                {
                    "silver_variables": [vars(v) for v in s.silver_variables],
                    "params": [vars(p) for p in s.params],
                    "confidence_notes": s.confidence_notes,
                }
                for s in specs
            ],
        }
        Path(output_path).write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"JSON saved to: {output_path}")

    review_count = sum(len(s.confidence_notes) for s in specs)
    if review_count > 0:
        print(f"\n{review_count} items need review (see review_needed sheet in Excel)")


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

        from prism.core.models import GeneratedSpec, ParamSpec, SilverVariableSpec

        silver_vars = []
        for _, row in silver_df.iterrows():
            var_name = clean_value(row.get("var_name"))
            if var_name:
                silver_vars.append(
                    SilverVariableSpec(
                        var_name=var_name,
                        var_label=clean_value(row.get("var_label"))
                        or clean_value(row.get("label"))
                        or "",
                        schema=clean_value(row.get("schema")) or "baseline",
                        data_type=clean_value(row.get("data_type")),
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
                params.append(
                    ParamSpec(
                        paramcd=paramcd,
                        parameter=clean_value(row.get("parameter")) or "",
                        category=clean_value(row.get("category")),
                        unit=clean_value(row.get("unit")),
                    )
                )

        spec = GeneratedSpec(silver_variables=silver_vars, params=params)
        specs = [spec]
    else:
        data = json.loads(meta_path.read_text())
        from prism.core.models import GeneratedSpec

        specs = [GeneratedSpec(**s) for s in data.get("specs", [])]

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
        description="PRISM Meta Generator - Generate clinical trial metadata from mock shells"
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "zhipu"],
        default="deepseek",
        help="LLM provider to use",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate", help="Generate metadata from mock shell"
    )
    gen_parser.add_argument(
        "--mock", required=True, help="Path to mock shell (docx/xlsx)"
    )
    gen_parser.add_argument("--als", required=True, help="Path to ALS Excel file")
    gen_parser.add_argument("--output", "-o", help="Output file path")
    gen_parser.add_argument(
        "--format", choices=["excel", "json"], default="excel", help="Output format"
    )
    gen_parser.add_argument(
        "--deliverables", "-d", help="Comma-separated deliverable IDs to process"
    )
    gen_parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list deliverables, do not generate",
    )
    gen_parser.add_argument(
        "--debug",
        metavar="ID",
        help="Debug a single deliverable (e.g., --debug 14.3.1)",
    )
    gen_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed reasoning",
    )

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

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "load":
        cmd_load(args)
    elif args.command == "extract":
        cmd_extract(args)


if __name__ == "__main__":
    main()
