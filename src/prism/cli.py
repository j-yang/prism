"""PRISM CLI Entry Point."""

import sys


def main():
    if len(sys.argv) < 2:
        print("PRISM - Clinical Trial Data Pipeline")
        print("\nUsage: prism <command> [options]")
        print("\nCommands:")
        print("  spec     Generate and manage clinical trial specifications")
        print("\nRun 'prism spec --help' for more information.")
        sys.exit(1)

    command = sys.argv[1]

    if command == "spec":
        from prism.spec.cli import main as spec_main

        sys.argv = [sys.argv[0]] + sys.argv[2:]
        spec_main()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: spec")
        sys.exit(1)


if __name__ == "__main__":
    main()
