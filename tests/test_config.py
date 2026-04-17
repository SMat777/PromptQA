"""Tests for YAML config loader — parsing test definitions into typed dataclasses."""

from pathlib import Path

import pytest

from promptqa.config import Criterion, TestCase, TestSuite, load_config

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestDataclasses:
    """Verify the config data structures."""

    def test_criterion_fields(self) -> None:
        c = Criterion(type="contains", value="hello", description="Must greet")
        assert c.type == "contains"
        assert c.value == "hello"
        assert c.description == "Must greet"

    def test_test_case_defaults(self) -> None:
        tc = TestCase(
            name="basic",
            prompt="Say hi",
            criteria=[],
        )
        assert tc.system == ""
        assert tc.criteria == []

    def test_test_suite_structure(self) -> None:
        suite = TestSuite(
            name="Demo",
            description="A demo suite",
            provider="mock",
            tests=[],
            mock_responses={},
        )
        assert suite.name == "Demo"
        assert suite.tests == []


class TestLoadConfig:
    """Verify YAML loading and validation."""

    def test_load_basic_example(self) -> None:
        suite = load_config(EXAMPLES_DIR / "basic_test.yaml")

        assert suite.name == "Basic QA Tests"
        assert suite.provider == "mock"
        assert len(suite.tests) == 3

    def test_first_test_case_structure(self) -> None:
        suite = load_config(EXAMPLES_DIR / "basic_test.yaml")
        tc = suite.tests[0]

        assert tc.name == "Factual accuracy — Danish capital"
        assert "capital of Denmark" in tc.prompt
        assert tc.system == "Answer in one sentence. Be factual and concise."
        assert len(tc.criteria) == 2

    def test_criteria_types_parsed(self) -> None:
        suite = load_config(EXAMPLES_DIR / "basic_test.yaml")
        criteria_types = [c.type for tc in suite.tests for c in tc.criteria]

        assert "contains" in criteria_types
        assert "not_contains" in criteria_types
        assert "max_length" in criteria_types
        assert "contains_any" in criteria_types

    def test_mock_responses_loaded(self) -> None:
        suite = load_config(EXAMPLES_DIR / "basic_test.yaml")

        assert len(suite.mock_responses) == 3
        assert "The capital of Denmark is Copenhagen." in suite.mock_responses.values()

    def test_contains_any_value_is_list(self) -> None:
        suite = load_config(EXAMPLES_DIR / "basic_test.yaml")
        safety_test = suite.tests[2]
        criterion = safety_test.criteria[0]

        assert criterion.type == "contains_any"
        assert isinstance(criterion.value, list)
        assert "cannot" in criterion.value

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/path.yaml"))

    def test_missing_name_raises_error(self, tmp_path: Path) -> None:
        config = tmp_path / "bad.yaml"
        config.write_text("tests: []")

        with pytest.raises(ValueError, match="name"):
            load_config(config)

    def test_missing_tests_raises_error(self, tmp_path: Path) -> None:
        config = tmp_path / "bad.yaml"
        config.write_text("name: Test\ndescription: x")

        with pytest.raises(ValueError, match="tests"):
            load_config(config)
