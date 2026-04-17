"""Command-line interface for PromptQA."""

import argparse
import sys

from promptqa import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all CLI options."""
    parser = argparse.ArgumentParser(
        prog="promptqa",
        description="Systematic LLM output testing and quality assurance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  promptqa run tests.yaml                   Run tests with mock provider
  promptqa run tests.yaml --provider anthropic  Run with Claude API
  promptqa run tests.yaml --verbose         Show detailed output
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run test cases against an LLM provider")
    run_parser.add_argument("config", help="Path to YAML test configuration file")
    run_parser.add_argument(
        "--provider",
        choices=["mock", "anthropic"],
        default="mock",
        help="LLM provider to use (default: mock)",
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed test output",
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Command routing will be added in later issues
    if args.command == "run":
        print(f"Running tests from: {args.config}")
        print(f"Provider: {args.provider}")
        print("(Not yet implemented — see issue #4)")
