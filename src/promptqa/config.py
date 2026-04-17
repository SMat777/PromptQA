"""YAML config loader — parses test definitions into typed dataclasses.

Validates required fields at load time so errors surface immediately,
not halfway through a test run.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Criterion:
    """A single evaluation criterion for an LLM response.

    Attributes:
        type: The check type (contains, not_contains, contains_any, max_length).
        value: The expected value — string, list, or int depending on type.
        description: Human-readable explanation of what this criterion checks.
    """

    type: str
    value: Any
    description: str = ""


@dataclass
class TestCase:
    """A single test case: prompt in, criteria to check against.

    Attributes:
        name: Descriptive name shown in test output.
        prompt: The prompt sent to the LLM provider.
        criteria: List of criteria the response must satisfy.
        system: Optional system prompt for provider context.
    """

    name: str
    prompt: str
    criteria: list[Criterion]
    system: str = ""


@dataclass
class TestSuite:
    """A collection of test cases loaded from a YAML file.

    Attributes:
        name: Suite name shown in report header.
        description: What this suite tests.
        provider: Default provider (mock, anthropic).
        tests: The test cases to run.
        mock_responses: Prompt-to-response mapping for MockProvider.
    """

    name: str
    description: str
    provider: str
    tests: list[TestCase]
    mock_responses: dict[str, str] = field(default_factory=dict)


def load_config(path: Path) -> TestSuite:
    """Load and validate a YAML test configuration file.

    Args:
        path: Path to the YAML file.

    Returns:
        A validated TestSuite ready for the evaluator.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If required fields are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    _validate_required(raw, "name")
    _validate_required(raw, "tests")

    tests = [_parse_test_case(t) for t in raw["tests"]]

    return TestSuite(
        name=raw["name"],
        description=raw.get("description", ""),
        provider=raw.get("provider", "mock"),
        tests=tests,
        mock_responses=raw.get("mock_responses", {}),
    )


def _parse_test_case(raw: dict[str, Any]) -> TestCase:
    """Parse a single test case from raw YAML data."""
    criteria = [
        Criterion(
            type=c["type"],
            value=c["value"],
            description=c.get("description", ""),
        )
        for c in raw.get("criteria", [])
    ]

    return TestCase(
        name=raw["name"],
        prompt=raw["prompt"],
        criteria=criteria,
        system=raw.get("system", ""),
    )


def _validate_required(raw: dict[str, Any], field_name: str) -> None:
    """Raise ValueError if a required field is missing."""
    if field_name not in raw:
        raise ValueError(f"Missing required field: '{field_name}'")
