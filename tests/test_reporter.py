"""Tests for the Reporter — structured terminal output formatting."""

import json
import os

from promptqa.evaluator import CriterionResult, TestResult
from promptqa.reporter import JsonReporter, Reporter


def _passing_result(name: str = "Test A") -> TestResult:
    return TestResult(
        test_name=name,
        passed=True,
        response_text="good response",
        criterion_results=[
            CriterionResult(passed=True, criterion_type="contains", description="check")
        ],
        duration_ms=12.5,
    )


def _failing_result(name: str = "Test B") -> TestResult:
    return TestResult(
        test_name=name,
        passed=False,
        response_text="bad response",
        criterion_results=[
            CriterionResult(
                passed=False,
                criterion_type="contains",
                description="Must have X",
                detail="Expected 'X' in response",
            )
        ],
        duration_ms=8.3,
    )


class TestReporterOutput:
    """Verify report content and structure."""

    def test_passing_test_shows_pass_indicator(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()])

        assert "PASS" in output
        assert "Test A" in output

    def test_failing_test_shows_fail_indicator(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_failing_result()])

        assert "FAIL" in output
        assert "Test B" in output

    def test_summary_shows_counts(self) -> None:
        reporter = Reporter(use_color=False)
        results = [_passing_result(), _failing_result()]
        output = reporter.format(results)

        assert "1 passed" in output
        assert "1 failed" in output

    def test_summary_shows_total(self) -> None:
        reporter = Reporter(use_color=False)
        results = [_passing_result(), _passing_result("Test C")]
        output = reporter.format(results)

        assert "2 passed" in output

    def test_verbose_shows_criterion_detail(self) -> None:
        reporter = Reporter(use_color=False, verbose=True)
        output = reporter.format([_failing_result()])

        assert "Expected 'X' in response" in output

    def test_non_verbose_hides_criterion_detail(self) -> None:
        reporter = Reporter(use_color=False, verbose=False)
        output = reporter.format([_failing_result()])

        assert "Expected 'X' in response" not in output

    def test_duration_shown(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()])

        assert "12.5" in output or "12.5ms" in output

    def test_all_passing_shows_success_message(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()])

        assert "passed" in output.lower()

    def test_suite_name_in_header(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()], suite_name="My Suite")

        assert "My Suite" in output

    def test_token_usage_shown_when_present(self) -> None:
        result = TestResult(
            test_name="API test",
            passed=True,
            response_text="ok",
            input_tokens=50,
            output_tokens=30,
        )
        reporter = Reporter(use_color=False)
        output = reporter.format([result])

        assert "tokens: 50 in / 30 out" in output

    def test_token_usage_hidden_when_zero(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()])

        assert "tokens" not in output


class TestReporterColor:
    """Verify color behavior and NO_COLOR support."""

    def test_no_color_env_disables_color(self, monkeypatch: object) -> None:
        os.environ["NO_COLOR"] = "1"
        try:
            reporter = Reporter()
            assert reporter.use_color is False
        finally:
            del os.environ["NO_COLOR"]

    def test_explicit_color_false(self) -> None:
        reporter = Reporter(use_color=False)
        output = reporter.format([_passing_result()])

        assert "\033[" not in output


class TestJsonReporter:
    """Verify JSON output format."""

    def test_valid_json_output(self) -> None:
        reporter = JsonReporter()
        output = reporter.format([_passing_result()], suite_name="Suite", provider="mock")

        data = json.loads(output)
        assert data["suite"] == "Suite"
        assert data["provider"] == "mock"

    def test_counts(self) -> None:
        reporter = JsonReporter()
        results = [_passing_result(), _failing_result()]
        data = json.loads(reporter.format(results))

        assert data["total"] == 2
        assert data["passed"] == 1
        assert data["failed"] == 1

    def test_result_structure(self) -> None:
        reporter = JsonReporter()
        data = json.loads(reporter.format([_passing_result()]))

        result = data["results"][0]
        assert result["name"] == "Test A"
        assert result["passed"] is True
        assert "criteria" in result
        assert result["criteria"][0]["type"] == "contains"

    def test_failed_criteria_detail(self) -> None:
        reporter = JsonReporter()
        data = json.loads(reporter.format([_failing_result()]))

        criterion = data["results"][0]["criteria"][0]
        assert criterion["passed"] is False
        assert "Expected" in criterion["detail"]

    def test_duration_included(self) -> None:
        reporter = JsonReporter()
        data = json.loads(reporter.format([_passing_result()]))

        assert data["duration_ms"] >= 0
        assert data["results"][0]["duration_ms"] >= 0
