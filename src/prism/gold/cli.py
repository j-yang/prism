"""CLI for PRISM Gold Generator.

Generate Python Polars transformations for Gold layer.
"""

import argparse
from pathlib import Path


def cmd_generate(args):
    """Generate Gold transformations for a schema."""
    from prism.gold.agent import GoldAgent

    db_path = args.db

    if not db_path:
        print("Error: --db is required")
        return 1

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    schema = args.schema
    output_dir = args.output or "generated/gold"

    print(f"Generating Gold transformations for {schema} schema...")
    print(f"Database: {db_path}")

    agent = GoldAgent(
        provider=args.provider,
        db_path=db_path,
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
    """List registered Gold transforms."""
    from prism.transforms import list_transforms

    transforms = list_transforms()

    gold_transforms = [t for t in transforms if t.endswith("_gold")]

    if not gold_transforms:
        print("No Gold transforms registered")
        return 0

    print(f"Registered Gold transforms ({len(gold_transforms)}):")
    for name in sorted(gold_transforms):
        print(f"  - {name}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="PRISM Gold Generator - Generate statistical aggregations"
    )
    parser.add_argument(
        "--provider",
        choices=["deepseek", "zhipu"],
        default="deepseek",
        help="LLM provider to use",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate Gold transformations")
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
        "--output",
        "-o",
        default="generated/gold",
        help="Output directory (default: generated/gold)",
    )

    _list_parser = subparsers.add_parser("list", help="List registered Gold transforms")

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "list":
        return cmd_list(args)

    return 0


if __name__ == "__main__":
    exit(main())
