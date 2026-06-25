import argparse
import importlib
import sys
import os

PARSERS = {
    "bns": {
        "module": "ingestion.parse_bns",
        "description": "Parse Bharatiya Nyaya Sanhita, 2023"
    },
    "bnss": {
        "module": "ingestion.parse_bnss",
        "description": "Parse Bharatiya Nagarik Suraksha Sanhita, 2023"
    },
    "bsa": {
        "module": "ingestion.parse_bsa",
        "description": "Parse Bharatiya Sakshya Adhiniyam, 2023"
    }
}


def list_parsers() -> None:
    print("Available statute parsers:")
    for name, info in PARSERS.items():
        print(f"  {name}: {info['description']}")


def run_parser(parser_name: str) -> bool:
    info = PARSERS.get(parser_name)
    if info is None:
        print(f"Unknown parser: {parser_name}")
        return False

    # Ensure project root is on sys.path so we can import ingestion modules
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    module = importlib.import_module(info["module"])
    if not hasattr(module, "main"):
        print(f"Parser module {info['module']} does not expose a main() function.")
        return False

    print(f"Running parser: {parser_name} ({info['description']})")
    module.main()
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run statute parsers for the legal AI ingestion pipeline."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--parser",
        choices=sorted(PARSERS.keys()),
        help="Run only one parser by name."
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all configured statute parsers in sequence."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available statute parsers."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list:
        list_parsers()
        return 0

    if args.parser:
        success = run_parser(args.parser)
        return 0 if success else 1

    if args.all:
        failed = []
        for parser_name in sorted(PARSERS.keys()):
            success = run_parser(parser_name)
            if not success:
                failed.append(parser_name)

        if failed:
            print("\nFailed parsers:", ", ".join(failed))
            return 1
        return 0

    print("No parser specified. Use --parser <name> or --all. Use --list to see available parsers.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
