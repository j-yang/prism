"""CLI for PRISM Silver Generator.

Generate Python Polars transformations for Silver layer.
"""

import argparse
from pathlib import Path


def cmd_generate(args):
    """Generate Silver transformations for a schema."""
    from prism.silver.agent import SilverAgent

    db_path = args.db
    als_path = args.als

    if not db_path:
        print("Error: --db is required")
        return 1

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    schema = args.schema
    output_dir = args.output or "generated/silver"

    print(f"Generating Silver transformations for {schema} schema...")
    print(f"Database: {db_path}")

    if als_path:
        print(f"ALS: {als_path}")

    agent = SilverAgent(
        provider=args.provider,
        db_path=db_path,
        als_path=als_path,
    )

    transforms = agent.generate_schema_transforms(schema)

    if not transforms.transforms:
        print(f"No transforms generated for {schema} schema")
        return 0

    output_path = agent.save_python_file(transforms, output_dir)

    high_conf = sum(1 for t in transforms.transforms if t.confidence == "high")
    med_conf = sum(1 for t in transforms.transforms if t.confidence == "medium")
    low_conf = sum(1 for t in transforms.transforms if t.confidence == "low")

    print("\nConfidence breakdown:")
    print(f"  High:   {high_conf}")
    print(f"  Medium: {med_conf}")
    print(f"  Low:    {low_conf} (needs review)")

    if low_conf > 0:
        print(f"\n⚠️  {low_conf} transforms need review (marked with WARNING)")

    print(f"\n✅ Saved to: {output_path}")
    print("\nNext steps:")
    print(f"  1. Review the generated code in {output_path}")
    print(f"  2. Run: uv run python {output_path} to test")

    return 0


def cmd_list(args):
    """List registered Silver transforms."""
    from prism.transforms import list_transforms

    transforms = list_transforms()

    if not transforms:
        print("No transforms registered")
        return 0

    print(f"Registered transforms ({len(transforms)}):")
    for name in sorted(transforms):
        print(f"  - {name}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PRISM Silver Generator - Generate Polars transformations"
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "zhipu"],
        default="deepseek",
        help="LLM provider to use",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate", help="Generate Silver transformations"
    )
    gen_parser.add_argument(
        "--schema",
        required=True,
        choices=["baseline", "longitudinal", "occurrence"],
        help="Schema to generate transforms for",
    )
    gen_parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB database with meta tables",
    )
    gen_parser.add_argument(
        "--als",
        help="Path to ALS Excel file (optional, for context)",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        default="generated/silver",
        help="Output directory (default: generated/silver)",
    )

    _list_parser = subparsers.add_parser("list", help="List registered transforms")

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "list":
        return cmd_list(args)

    return 0


if __name__ == "__main__":
    exit(main())
