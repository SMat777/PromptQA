"""Test the CLI interface — argument parsing and command routing."""

import subprocess
import sys


class TestCLIVersion:
    """Verify that --version outputs the correct version string."""

    def test_version_flag(self) -> None:
        """Running `python -m promptqa --version` should print the version."""
        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "promptqa" in result.stdout
        assert "0.1.0" in result.stdout

    def test_help_flag(self) -> None:
        """Running `promptqa --help` should show usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "run" in result.stdout


class TestCLIRunCommand:
    """Verify the 'run' subcommand argument parsing."""

    def test_run_help(self) -> None:
        """Running `promptqa run --help` should show run-specific options."""
        result = subprocess.run(
            [sys.executable, "-m", "promptqa", "run", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--provider" in result.stdout
        assert "mock" in result.stdout
        assert "anthropic" in result.stdout

    def test_no_command_shows_help(self) -> None:
        """Running `promptqa` without a command should show help, not error."""
        result = subprocess.run(
            [sys.executable, "-m", "promptqa"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
