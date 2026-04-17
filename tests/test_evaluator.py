"""Tests for the Evaluator — core test runner that connects providers to criteria."""

from promptqa.config import Criterion, TestCase
from promptqa.evaluator import CriterionResult, Evaluator
from promptqa.providers.mock import MockProvider


def _make_provider(responses: dict[str, str]) -> MockProvider:
    return MockProvider(responses=responses)


def _make_test_case(
    prompt: str,
    criteria: list[Criterion],
    name: str = "test",
    system: str = "",
) -> TestCase:
    return TestCase(name=name, prompt=prompt, criteria=criteria, system=system)


class TestCriteriaCheckers:
    """Verify individual criterion evaluation logic."""

    def test_contains_pass(self) -> None:
        provider = _make_provider({"q": "The capital is Copenhagen"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="contains", value="Copenhagen")])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_contains_fail(self) -> None:
        provider = _make_provider({"q": "The capital is Oslo"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="contains", value="Copenhagen")])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_not_contains_pass(self) -> None:
        provider = _make_provider({"q": "Dear Mr. Hansen"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="not_contains", value="Hey")])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_not_contains_fail(self) -> None:
        provider = _make_provider({"q": "Hey there!"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="not_contains", value="Hey")])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_contains_any_pass(self) -> None:
        provider = _make_provider({"q": "I cannot help with that"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q", [Criterion(type="contains_any", value=["cannot", "sorry"])]
        )

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_contains_any_fail(self) -> None:
        provider = _make_provider({"q": "Sure, here's how"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q", [Criterion(type="contains_any", value=["cannot", "sorry"])]
        )

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_max_length_pass(self) -> None:
        provider = _make_provider({"q": "Short answer."})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="max_length", value=100)])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_max_length_fail(self) -> None:
        provider = _make_provider({"q": "A" * 101})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="max_length", value=100)])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_unknown_criterion_type_fails(self) -> None:
        provider = _make_provider({"q": "answer"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="nonexistent", value="x")])

        results = evaluator.run([tc])

        assert results[0].passed is False
        assert "Unknown criterion type" in results[0].criterion_results[0].detail

    def test_min_length_pass(self) -> None:
        provider = _make_provider({"q": "A long enough response here"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="min_length", value=10)])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_min_length_fail(self) -> None:
        provider = _make_provider({"q": "Short"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="min_length", value=100)])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_equals_pass(self) -> None:
        provider = _make_provider({"q": "  Copenhagen  "})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="equals", value="Copenhagen")])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_equals_fail(self) -> None:
        provider = _make_provider({"q": "Copenhagen is great"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="equals", value="Copenhagen")])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_regex_pass(self) -> None:
        provider = _make_provider({"q": "The answer is 42."})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="regex", value=r"\d+")])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_regex_fail(self) -> None:
        provider = _make_provider({"q": "No numbers here"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="regex", value=r"\d+")])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_regex_invalid_pattern(self) -> None:
        provider = _make_provider({"q": "anything"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="regex", value="[invalid")])

        results = evaluator.run([tc])

        assert results[0].passed is False
        assert "Invalid regex" in results[0].criterion_results[0].detail

    def test_json_valid_pass(self) -> None:
        provider = _make_provider({"q": '{"key": "value", "num": 42}'})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="json_valid", value=True)])

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_json_valid_fail(self) -> None:
        provider = _make_provider({"q": "not json at all"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [Criterion(type="json_valid", value=True)])

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_contains_case_insensitive(self) -> None:
        provider = _make_provider({"q": "COPENHAGEN is the capital"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q",
            [Criterion(type="contains", value="copenhagen", case_insensitive=True)],
        )

        results = evaluator.run([tc])

        assert results[0].passed is True

    def test_equals_case_insensitive(self) -> None:
        provider = _make_provider({"q": "  HELLO WORLD  "})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q",
            [Criterion(type="equals", value="hello world", case_insensitive=True)],
        )

        results = evaluator.run([tc])

        assert results[0].passed is True


class TestEvaluatorResults:
    """Verify result structure and multi-criteria evaluation."""

    def test_result_contains_test_name(self) -> None:
        provider = _make_provider({"q": "answer"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [], name="My Test")

        results = evaluator.run([tc])

        assert results[0].test_name == "My Test"

    def test_result_contains_response_text(self) -> None:
        provider = _make_provider({"q": "the answer"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [])

        results = evaluator.run([tc])

        assert results[0].response_text == "the answer"

    def test_multiple_criteria_all_must_pass(self) -> None:
        provider = _make_provider({"q": "Copenhagen is the capital"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q",
            [
                Criterion(type="contains", value="Copenhagen"),
                Criterion(type="max_length", value=50),
            ],
        )

        results = evaluator.run([tc])

        assert results[0].passed is True
        assert len(results[0].criterion_results) == 2

    def test_one_failing_criterion_fails_test(self) -> None:
        provider = _make_provider({"q": "Copenhagen is the capital"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q",
            [
                Criterion(type="contains", value="Copenhagen"),
                Criterion(type="max_length", value=5),
            ],
        )

        results = evaluator.run([tc])

        assert results[0].passed is False

    def test_criterion_results_detail(self) -> None:
        provider = _make_provider({"q": "hello world"})
        evaluator = Evaluator(provider)
        tc = _make_test_case(
            "q",
            [Criterion(type="contains", value="hello", description="Must greet")],
        )

        results = evaluator.run([tc])
        cr = results[0].criterion_results[0]

        assert isinstance(cr, CriterionResult)
        assert cr.passed is True
        assert cr.criterion_type == "contains"
        assert cr.description == "Must greet"

    def test_multiple_test_cases(self) -> None:
        provider = _make_provider({"a": "alpha", "b": "beta"})
        evaluator = Evaluator(provider)
        tests = [
            _make_test_case("a", [Criterion(type="contains", value="alpha")]),
            _make_test_case("b", [Criterion(type="contains", value="gamma")]),
        ]

        results = evaluator.run(tests)

        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False

    def test_result_has_duration(self) -> None:
        provider = _make_provider({"q": "fast"})
        evaluator = Evaluator(provider)
        tc = _make_test_case("q", [])

        results = evaluator.run([tc])

        assert results[0].duration_ms >= 0.0
