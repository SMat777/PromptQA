"""Reporter — formats test results as structured terminal output.

Supports colored output (ANSI escape codes) with graceful fallback
via the NO_COLOR environment variable (https://no-color.org/).
"""

import json
import os

from promptqa.evaluator import TestResult


class Reporter:
    """Formats a list of TestResult into readable terminal output.

    Args:
        use_color: Enable ANSI colors. Auto-detects NO_COLOR env var if not set.
        verbose: Show per-criterion details on failure.
    """

    def __init__(
        self,
        use_color: bool | None = None,
        verbose: bool = False,
    ) -> None:
        if use_color is None:
            self.use_color = "NO_COLOR" not in os.environ
        else:
            self.use_color = use_color
        self.verbose = verbose

    def format(self, results: list[TestResult], suite_name: str = "") -> str:
        """Format all results into a single output string."""
        lines: list[str] = []

        lines.append(self._header(len(results), suite_name))
        lines.append("")

        for result in results:
            lines.append(self._format_result(result))
            if self.verbose and not result.passed:
                for cr in result.criterion_results:
                    if not cr.passed:
                        lines.append(f"    {cr.detail}")
            lines.append("")

        lines.append(self._summary(results))

        return "\n".join(lines)

    def _header(self, count: int, suite_name: str = "") -> str:
        label = suite_name if suite_name else "PromptQA"
        title = f"{label} — {count} test{'s' if count != 1 else ''}"
        separator = "━" * 50
        return f"{separator}\n{title}\n{separator}"

    def _format_result(self, result: TestResult) -> str:
        if result.passed:
            indicator = self._green("PASS") if self.use_color else "PASS"
        else:
            indicator = self._red("FAIL") if self.use_color else "FAIL"

        duration = f"{result.duration_ms:.1f}ms"
        return f"  {indicator}  {result.test_name} ({duration})"

    def _summary(self, results: list[TestResult]) -> str:
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_ms = sum(r.duration_ms for r in results)
        total_in = sum(r.input_tokens for r in results)
        total_out = sum(r.output_tokens for r in results)

        parts: list[str] = []
        if passed > 0:
            count = f"{passed} passed"
            parts.append(self._green(count) if self.use_color else count)
        if failed > 0:
            count = f"{failed} failed"
            parts.append(self._red(count) if self.use_color else count)

        separator = "━" * 50
        summary = f"{', '.join(parts)} ({total_ms:.0f}ms)"
        if total_in > 0 or total_out > 0:
            summary += f" | tokens: {total_in} in / {total_out} out"
        return f"{separator}\n{summary}"

    @staticmethod
    def _green(text: str) -> str:
        return f"\033[32m{text}\033[0m"

    @staticmethod
    def _red(text: str) -> str:
        return f"\033[31m{text}\033[0m"


class JsonReporter:
    """Formats test results as JSON for CI/CD integration."""

    def format(
        self,
        results: list[TestResult],
        suite_name: str = "",
        provider: str = "",
    ) -> str:
        """Format results as a JSON string."""
        passed = sum(1 for r in results if r.passed)
        total_ms = sum(r.duration_ms for r in results)

        data = {
            "suite": suite_name,
            "provider": provider,
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "duration_ms": round(total_ms, 2),
            "results": [self._format_result(r) for r in results],
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def _format_result(result: TestResult) -> dict[str, object]:
        return {
            "name": result.test_name,
            "passed": result.passed,
            "duration_ms": round(result.duration_ms, 2),
            "response": result.response_text,
            "criteria": [
                {
                    "type": cr.criterion_type,
                    "passed": cr.passed,
                    "description": cr.description,
                    "detail": cr.detail,
                }
                for cr in result.criterion_results
            ],
        }
