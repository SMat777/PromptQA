"""Command-line interface for PromptQA."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from promptqa import __version__
from promptqa.config import load_config
from promptqa.evaluator import Evaluator
from promptqa.providers.base import BaseProvider
from promptqa.providers.mock import MockProvider
from promptqa.reporter import Reporter


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all CLI options."""
    parser = argparse.ArgumentParser(
        prog="promptqa",
        description="Systematic LLM output testing and quality assurance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  promptqa run tests.yaml                       Run tests with mock provider
  promptqa run tests.yaml --provider anthropic   Run with Claude API
  promptqa run tests.yaml --verbose              Show detailed output
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run test cases against an LLM provider")
    run_parser.add_argument("config", help="Path to YAML test configuration file")
    run_parser.add_argument(
        "--provider",
        choices=["mock", "anthropic"],
        default=None,
        help="LLM provider to use (default: from config file)",
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed test output",
    )
    run_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    return parser


def _create_provider(provider_name: str, mock_responses: dict[str, str]) -> BaseProvider:
    """Factory: map provider name string to concrete BaseProvider instance."""
    if provider_name == "mock":
        return MockProvider(responses=mock_responses)

    if provider_name == "anthropic":
        try:
            from promptqa.providers.anthropic import AnthropicProvider
        except ImportError:
            print(
                "Error: Anthropic SDK not installed. "
                "Install it with: pip install promptqa[anthropic]",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            return AnthropicProvider()
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Error: Unknown provider '{provider_name}'", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    load_dotenv()

    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        _run(args)


def _run(args: argparse.Namespace) -> None:
    """Execute the 'run' command: load config, run tests, report results."""
    config_path = Path(args.config)

    try:
        suite = load_config(config_path)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid config: {e}", file=sys.stderr)
        sys.exit(1)

    provider_name = args.provider or suite.provider
    provider = _create_provider(provider_name, suite.mock_responses)

    evaluator = Evaluator(provider)
    results = evaluator.run(suite.tests)

    use_color = not args.no_color
    reporter = Reporter(use_color=use_color, verbose=args.verbose)
    print(reporter.format(results))

    if any(not r.passed for r in results):
        sys.exit(1)
