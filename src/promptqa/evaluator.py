"""Evaluator — runs test cases against an LLM provider and checks criteria.

The evaluator only depends on the BaseProvider interface (Strategy Pattern),
so it works identically with MockProvider, AnthropicProvider, or any future
provider without code changes.
"""

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

from promptqa.config import Criterion, TestCase
from promptqa.providers.base import BaseProvider

CheckerFn: TypeAlias = Callable[[str, Criterion], "CriterionResult"]


@dataclass
class CriterionResult:
    """Result of evaluating a single criterion against an LLM response.

    Attributes:
        passed: Whether the criterion was satisfied.
        criterion_type: The type of check (contains, max_length, etc.).
        description: Human-readable description of the criterion.
        detail: Explanation of why it passed or failed.
    """

    passed: bool
    criterion_type: str
    description: str
    detail: str = ""


@dataclass
class TestResult:
    """Result of running a single test case.

    Attributes:
        test_name: Name of the test case.
        passed: True only if ALL criteria passed.
        response_text: The raw LLM response.
        criterion_results: Per-criterion pass/fail details.
        duration_ms: Time taken for the provider call in milliseconds.
    """

    test_name: str
    passed: bool
    response_text: str
    criterion_results: list[CriterionResult] = field(default_factory=list)
    duration_ms: float = 0.0


class Evaluator:
    """Runs test cases through a provider and evaluates responses against criteria.

    Args:
        provider: Any BaseProvider implementation (injected, not created here).
    """

    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def run(self, test_cases: list[TestCase]) -> list[TestResult]:
        """Execute all test cases and return results."""
        return [self._run_single(tc) for tc in test_cases]

    def _run_single(self, test_case: TestCase) -> TestResult:
        """Run one test case: call provider, check all criteria."""
        start = time.perf_counter()
        response = self._provider.complete(test_case.prompt, test_case.system)
        duration_ms = (time.perf_counter() - start) * 1000

        criterion_results = [
            _check_criterion(response.text, c) for c in test_case.criteria
        ]

        return TestResult(
            test_name=test_case.name,
            passed=all(cr.passed for cr in criterion_results),
            response_text=response.text,
            criterion_results=criterion_results,
            duration_ms=duration_ms,
        )


# --- Criterion checkers ---
# Each function takes the response text and a Criterion, returns CriterionResult.


def _check_criterion(text: str, criterion: Criterion) -> CriterionResult:
    """Route to the correct checker based on criterion type."""
    checkers: dict[str, CheckerFn] = {
        "contains": _check_contains,
        "not_contains": _check_not_contains,
        "contains_any": _check_contains_any,
        "max_length": _check_max_length,
        "min_length": _check_min_length,
        "equals": _check_equals,
        "regex": _check_regex,
        "json_valid": _check_json_valid,
    }

    checker = checkers.get(criterion.type)
    if checker is None:
        return CriterionResult(
            passed=False,
            criterion_type=criterion.type,
            description=criterion.description,
            detail=f"Unknown criterion type: '{criterion.type}'",
        )

    return checker(text, criterion)


def _ci(text: str, c: Criterion) -> str:
    """Apply case-insensitive lowering if the criterion requests it."""
    return text.lower() if c.case_insensitive else text


def _check_contains(text: str, c: Criterion) -> CriterionResult:
    passed = str(c.value).lower() in text.lower() if c.case_insensitive else str(c.value) in text
    return CriterionResult(
        passed=passed,
        criterion_type="contains",
        description=c.description,
        detail=f"Expected '{c.value}' in response" if not passed else "",
    )


def _check_not_contains(text: str, c: Criterion) -> CriterionResult:
    t, v = (_ci(text, c), str(c.value).lower()) if c.case_insensitive else (text, str(c.value))
    passed = v not in t
    return CriterionResult(
        passed=passed,
        criterion_type="not_contains",
        description=c.description,
        detail=f"Found unwanted '{c.value}' in response" if not passed else "",
    )


def _check_contains_any(text: str, c: Criterion) -> CriterionResult:
    values = c.value if isinstance(c.value, list) else [c.value]
    t = text.lower() if c.case_insensitive else text
    found = [v for v in values if (v.lower() if c.case_insensitive else v) in t]
    passed = len(found) > 0
    return CriterionResult(
        passed=passed,
        criterion_type="contains_any",
        description=c.description,
        detail="" if passed else f"None of {values} found in response",
    )


def _check_max_length(text: str, c: Criterion) -> CriterionResult:
    max_len = int(c.value)
    passed = len(text) <= max_len
    return CriterionResult(
        passed=passed,
        criterion_type="max_length",
        description=c.description,
        detail="" if passed else f"Response length {len(text)} exceeds max {max_len}",
    )


def _check_min_length(text: str, c: Criterion) -> CriterionResult:
    min_len = int(c.value)
    passed = len(text) >= min_len
    return CriterionResult(
        passed=passed,
        criterion_type="min_length",
        description=c.description,
        detail="" if passed else f"Response length {len(text)} below min {min_len}",
    )


def _check_equals(text: str, c: Criterion) -> CriterionResult:
    expected = str(c.value)
    actual = text.strip()
    if c.case_insensitive:
        passed = actual.lower() == expected.lower()
    else:
        passed = actual == expected
    return CriterionResult(
        passed=passed,
        criterion_type="equals",
        description=c.description,
        detail="" if passed else f"Expected exact match '{expected}', got '{actual}'",
    )


def _check_regex(text: str, c: Criterion) -> CriterionResult:
    pattern = str(c.value)
    flags = re.IGNORECASE if c.case_insensitive else 0
    try:
        passed = re.search(pattern, text, flags) is not None
    except re.error as e:
        return CriterionResult(
            passed=False,
            criterion_type="regex",
            description=c.description,
            detail=f"Invalid regex pattern: {e}",
        )
    return CriterionResult(
        passed=passed,
        criterion_type="regex",
        description=c.description,
        detail="" if passed else f"Pattern '{pattern}' not found in response",
    )


def _check_json_valid(text: str, c: Criterion) -> CriterionResult:
    try:
        json.loads(text)
        passed = True
        detail = ""
    except json.JSONDecodeError as e:
        passed = False
        detail = f"Invalid JSON: {e}"
    return CriterionResult(
        passed=passed,
        criterion_type="json_valid",
        description=c.description,
        detail=detail,
    )
