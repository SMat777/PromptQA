"""Seed demo data — populates the SQLite store with example test runs."""

from pathlib import Path

from promptqa.config import load_config
from promptqa.evaluator import Evaluator
from promptqa.providers.mock import MockProvider
from promptqa.store import Store

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def seed(store: Store | None = None) -> int:
    """Run all example suites and persist results. Returns number of runs created."""
    if store is None:
        store = Store()

    examples = sorted(EXAMPLES_DIR.glob("*.yaml"))
    count = 0

    for example in examples:
        suite = load_config(example)
        provider = MockProvider(responses=suite.mock_responses)
        evaluator = Evaluator(provider)
        results = evaluator.run(suite.tests)
        store.save_run(results, suite.name, "mock")
        count += 1

    return count


if __name__ == "__main__":
    n = seed()
    print(f"Seeded {n} demo runs.")
