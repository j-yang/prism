"""CLI for Spec Agent."""

import argparse
import json
import sys
from pathlib import Path

from prism.spec.extractor import extract_mock_shell
from prism.spec.generator import SpecGenerator, generate_spec
from prism.spec.excel_writer import write_spec_excel
from prism.spec.learner import DiffLearner
from prism.spec.memory import get_memory_store


def cmd_generate(args):
    """Generate spec from mock shell."""
    print(f"Extracting mock shell: {args.mock}")

    context = extract_mock_shell(args.mock)
    print(f"Found {len(context.deliverables)} deliverables")

    if args.list_only:
        for d in context.deliverables:
            print(f"  {d.deliverable_id}: {d.title}")
        return

    print(f"Loading ALS: {args.als}")

    deliverable_ids = args.deliverables.split(",") if args.deliverables else None

    print("Generating specifications...")

    generator = SpecGenerator(args.als, args.memory_db)
    specs = generator.generate_for_context(context, deliverable_ids)

    print(f"Generated {len(specs)} specs")

    study_info = {
        "protocol_no": context.protocol_no,
        "study_title": context.study_title,
    }

    if args.format == "excel":
        output_path = args.output or "spec_generated.xlsx"
        saved_path = write_spec_excel(specs, output_path, study_info)
        print(f"Excel saved to: {saved_path}")
    else:
        output_path = args.output or "spec_generated.json"
        output_data = {
            "study_title": context.study_title,
            "protocol_no": context.protocol_no,
            "specs": [vars(s) for s in specs],
        }
        Path(output_path).write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"JSON saved to: {output_path}")

    for spec in specs:
        if spec.confidence_notes:
            print(f"\n{spec.deliverable_id} needs review:")
            for note in spec.confidence_notes:
                print(f"  - {note}")


def cmd_learn(args):
    """Learn from corrected spec."""
    print(f"Learning from corrections...")
    print(f"  Original: {args.original}")
    print(f"  Corrected: {args.corrected}")

    learner = DiffLearner(args.memory_db)

    original = json.loads(Path(args.original).read_text())
    corrected = json.loads(Path(args.corrected).read_text())

    patterns = learner.learn_from_diff(original, corrected, args.study, use_llm=True)

    print(f"Learned {len(patterns)} patterns:")
    for p in patterns:
        print(f"  [{p.pattern_type}] {p.input_pattern}")
        print(f"    Rule: {p.rule}")


def cmd_patterns(args):
    """Manage learned patterns."""
    memory = get_memory_store(args.memory_db)

    if args.action == "list":
        patterns = memory.get_patterns(args.type)
        print(f"Total patterns: {len(patterns)}")
        for p in patterns:
            print(f"\n[{p['pattern_id']}] {p['pattern_type']}")
            print(f"  Input: {p['input_pattern']}")
            print(f"  Rule: {p['rule']}")
            print(f"  Source: {p['source_study']}")

    elif args.action == "show":
        patterns = memory.get_patterns()
        for p in patterns:
            if p["pattern_id"].startswith(args.id):
                print(json.dumps(p, indent=2, default=str))
                return
        print(f"Pattern not found: {args.id}")

    elif args.action == "stats":
        stats = memory.get_stats()
        print("Memory Store Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.action == "clear":
        if args.force:
            memory.clear_all()
            print("All patterns cleared.")
        else:
            print("Use --force to confirm clearing all patterns.")


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
        description="PRISM Spec Agent - Generate clinical trial specs from mock shells"
    )
    parser.add_argument("--memory-db", help="Path to memory database")

    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Generate spec from mock shell")
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

    learn_parser = subparsers.add_parser("learn", help="Learn from corrected spec")
    learn_parser.add_argument(
        "--original", required=True, help="Original generated spec JSON"
    )
    learn_parser.add_argument("--corrected", required=True, help="Corrected spec JSON")
    learn_parser.add_argument("--study", required=True, help="Study ID")

    patterns_parser = subparsers.add_parser("patterns", help="Manage learned patterns")
    patterns_parser.add_argument("action", choices=["list", "show", "stats", "clear"])
    patterns_parser.add_argument("--type", help="Filter by pattern type")
    patterns_parser.add_argument("--id", help="Pattern ID to show")
    patterns_parser.add_argument(
        "--force", action="store_true", help="Confirm destructive action"
    )

    extract_parser = subparsers.add_parser("extract", help="Extract mock shell to JSON")
    extract_parser.add_argument("--mock", required=True, help="Path to mock shell")
    extract_parser.add_argument("--output", "-o", help="Output JSON path")

    args = parser.parse_args()

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "patterns":
        cmd_patterns(args)
    elif args.command == "extract":
        cmd_extract(args)


if __name__ == "__main__":
    main()
