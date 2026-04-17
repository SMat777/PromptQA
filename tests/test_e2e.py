"""End-to-end tests — verify the full pipeline via CLI subprocess."""

import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestEndToEnd:
    """Run the actual CLI and verify output and exit codes."""

    def test_basic_example_passes(self) -> None:
        """All tests in basic_test.yaml should pass with mock provider."""
        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "run", str(EXAMPLES_DIR / "basic_test.yaml")],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "PASS" in result.stdout
        assert "3 passed" in result.stdout

    def test_verbose_flag_shows_detail(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "promptqa", "run",
                str(EXAMPLES_DIR / "basic_test.yaml"), "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_no_color_flag(self) -> None:
        result = subprocess.run(
            [
                sys.executable, "-m", "promptqa", "run",
                str(EXAMPLES_DIR / "basic_test.yaml"), "--no-color",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "\033[" not in result.stdout

    def test_missing_config_exits_with_error(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "run", "nonexistent.yaml"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_exit_code_1_on_failure(self, tmp_path: Path) -> None:
        """A test designed to fail should produce exit code 1."""
        config = tmp_path / "failing.yaml"
        config.write_text("""
name: "Failing Suite"
provider: mock
tests:
  - name: "Will fail"
    prompt: "hello"
    criteria:
      - type: contains
        value: "IMPOSSIBLE_STRING"
mock_responses:
  "hello": "world"
""")

        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "run", str(config)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "FAIL" in result.stdout
        assert "1 failed" in result.stdout
