"""CLI for PRISM Platinum Generator.

Generate PowerPoint slide decks from clinical trial deliverables.
"""

import argparse
import json
from pathlib import Path


def cmd_generate(args):
    """Generate PPTX slide deck from deliverables."""
    from prism.platinum.agent import PlatinumAgent
    from prism.platinum.renderer import PPTXRenderer

    db_path = args.db
    output_path = args.output or "generated/platinum/report.pptx"

    if not db_path:
        print("Error: --db is required")
        return 1

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    print(f"Generating slide deck from: {db_path}")

    import duckdb

    con = duckdb.connect(db_path, read_only=True)

    try:
        study_info_rows = con.execute("SELECT * FROM meta.study_info").fetchall()

        study_info = {}
        if study_info_rows:
            cols = [
                desc[0]
                for desc in con.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'meta' AND table_name = 'study_info'"
                ).fetchall()
            ]
            row = study_info_rows[0]
            study_info = dict(zip(cols, row))

        study_info.setdefault("study_title", "Clinical Study Report")
        study_info.setdefault("protocol_no", "")

        deliverables_query = "SELECT * FROM meta.platinum_dictionary"
        params = []

        if args.deliverables:
            deliv_ids = [d.strip() for d in args.deliverables.split(",")]
            placeholders = ",".join("?" * len(deliv_ids))
            deliverables_query += f" WHERE deliverable_id IN ({placeholders})"
            params = deliv_ids

        if args.type:
            if "WHERE" in deliverables_query:
                deliverables_query += " AND deliverable_type = ?"
            else:
                deliverables_query += " WHERE deliverable_type = ?"
            params.append(args.type)

        deliverables_rows = con.execute(deliverables_query, params).fetchall()

        if not deliverables_rows:
            print("No deliverables found in meta.platinum_dictionary")
            return 1

        cols = [
            desc[0]
            for desc in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'meta' AND table_name = 'platinum_dictionary'"
            ).fetchall()
        ]

        deliverables = [dict(zip(cols, row)) for row in deliverables_rows]

        print(f"Found {len(deliverables)} deliverables")

    finally:
        con.close()

    agent = PlatinumAgent(provider=args.provider, db_path=db_path)

    print("\nGenerating slide content...")
    slide_deck = agent.generate_slide_deck(study_info, deliverables)

    print(f"\nRendering {len(slide_deck.slides)} slides to PPTX...")
    renderer = PPTXRenderer()
    renderer.render_slide_deck(slide_deck)
    saved_path = renderer.save(output_path)

    print(f"\n✅ Slide deck saved to: {saved_path}")

    return 0


def cmd_preview(args):
    """Preview slide content as JSON."""
    from prism.platinum.agent import PlatinumAgent

    db_path = args.db
    deliverable_id = args.deliverable_id

    if not db_path:
        print("Error: --db is required")
        return 1

    if not deliverable_id:
        print("Error: --deliverable-id is required")
        return 1

    import duckdb

    con = duckdb.connect(db_path, read_only=True)

    try:
        deliverables_rows = con.execute(
            "SELECT * FROM meta.platinum_dictionary WHERE deliverable_id = ?",
            [deliverable_id],
        ).fetchall()

        if not deliverables_rows:
            print(f"Deliverable not found: {deliverable_id}")
            return 1

        cols = [
            desc[0]
            for desc in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'meta' AND table_name = 'platinum_dictionary'"
            ).fetchall()
        ]

        deliverable = dict(zip(cols, deliverables_rows[0]))

    finally:
        con.close()

    agent = PlatinumAgent(provider=args.provider, db_path=db_path)

    print(f"Previewing deliverable: {deliverable_id}")
    print("-" * 60)

    result = agent.generate_deliverable_slides(deliverable)

    print(json.dumps(result.model_dump(), indent=2, default=str))

    return 0


def cmd_list(args):
    """List deliverables in database."""
    db_path = args.db

    if not db_path:
        print("Error: --db is required")
        return 1

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    import duckdb

    con = duckdb.connect(db_path, read_only=True)

    try:
        rows = con.execute(
            "SELECT deliverable_id, deliverable_type, title, population "
            "FROM meta.platinum_dictionary "
            "ORDER BY deliverable_id"
        ).fetchall()

        if not rows:
            print("No deliverables found in meta.platinum_dictionary")
            return 0

        print(f"Deliverables ({len(rows)}):")
        print("-" * 80)
        for row in rows:
            deliv_id, deliv_type, title, population = row
            print(f"{deliv_id:<12} [{deliv_type:<8}] {title[:50]}")
            if population:
                print(f"             Population: {population}")

    finally:
        con.close()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PRISM Platinum Generator - Generate PowerPoint slide decks"
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "zhipu"],
        default="deepseek",
        help="LLM provider to use",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate PPTX slide deck")
    gen_parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB database with meta tables",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        default="generated/platinum/report.pptx",
        help="Output file path (default: generated/platinum/report.pptx)",
    )
    gen_parser.add_argument(
        "--deliverables",
        "-d",
        help="Comma-separated deliverable IDs to include",
    )
    gen_parser.add_argument(
        "--type",
        choices=["table", "listing", "figure"],
        help="Filter by deliverable type",
    )

    preview_parser = subparsers.add_parser(
        "preview", help="Preview slide content as JSON"
    )
    preview_parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB database",
    )
    preview_parser.add_argument(
        "--deliverable-id",
        required=True,
        help="Deliverable ID to preview",
    )

    list_parser = subparsers.add_parser("list", help="List deliverables in database")
    list_parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB database",
    )

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "preview":
        return cmd_preview(args)
    elif args.command == "list":
        return cmd_list(args)

    return 0


if __name__ == "__main__":
    exit(main())
