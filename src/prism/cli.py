"""PRISM CLI Entry Point."""

import sys


def main():
    if len(sys.argv) < 2:
        print("PRISM - Clinical Trial Data Pipeline")
        print("\nUsage: prism <command> [options]")
        print("\nCommands:")
        print("  meta      Generate and manage clinical trial metadata")
        print("  silver    Generate Silver layer transformations")
        print("  gold      Generate Gold layer transformations")
        print("  platinum  Generate PowerPoint slide decks")
        print("\nOptions:")
        print("  --provider {deepseek,zhipu}  LLM provider (default: deepseek)")
        print("\nRun 'prism <command> --help' for more information.")
        sys.exit(1)

    provider = "deepseek"
    args = sys.argv[1:]

    if args and args[0].startswith("--provider"):
        if args[0] == "--provider" and len(args) > 1:
            provider = args[1]
            args = args[2:]
        elif "=" in args[0]:
            provider = args[0].split("=")[1]
            args = args[1:]

    if not args:
        print("Error: No command specified")
        sys.exit(1)

    command = args[0]

    if command == "meta":
        from prism.meta.cli import main as meta_main

        meta_args = ["prism", "--provider", provider] + args[1:]
        sys.argv = meta_args
        meta_main()
    elif command == "silver":
        from prism.silver.cli import main as silver_main

        silver_args = ["prism", "--provider", provider] + args[1:]
        sys.argv = silver_args
        sys.exit(silver_main())
    elif command == "gold":
        from prism.gold.cli import main as gold_main

        gold_args = ["prism", "--provider", provider] + args[1:]
        sys.argv = gold_args
        sys.exit(gold_main())
    elif command == "platinum":
        from prism.platinum.cli import main as platinum_main

        platinum_args = ["prism", "--provider", provider] + args[1:]
        sys.argv = platinum_args
        sys.exit(platinum_main())
    elif command == "spec":
        print("Command 'spec' is deprecated. Use 'meta' instead.")
        sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: meta, silver, gold, platinum")
        sys.exit(1)


if __name__ == "__main__":
    main()
