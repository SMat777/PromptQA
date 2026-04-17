"""Tests for the SQLite result store."""

from pathlib import Path

from promptqa.evaluator import CriterionResult, TestResult
from promptqa.store import Store


def _make_results() -> list[TestResult]:
    return [
        TestResult(
            test_name="Test A",
            passed=True,
            response_text="good response",
            criterion_results=[
                CriterionResult(passed=True, criterion_type="contains", description="check")
            ],
            duration_ms=10.5,
            input_tokens=50,
            output_tokens=30,
        ),
        TestResult(
            test_name="Test B",
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
            duration_ms=8.2,
        ),
    ]


class TestStore:
    """Verify SQLite persistence operations."""

    def test_save_and_list_runs(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        run_id = store.save_run(_make_results(), "Suite A", "mock")

        runs = store.get_runs()

        assert len(runs) == 1
        assert runs[0].id == run_id
        assert runs[0].suite_name == "Suite A"
        assert runs[0].provider == "mock"
        assert runs[0].total == 2
        assert runs[0].passed == 1
        assert runs[0].failed == 1
        store.close()

    def test_get_run_detail(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        run_id = store.save_run(_make_results(), "Suite A", "mock")

        detail = store.get_run(run_id)

        assert detail is not None
        assert detail.id == run_id
        assert len(detail.results) == 2
        assert detail.results[0]["test_name"] == "Test A"
        assert detail.results[0]["passed"] is True
        assert detail.results[0]["input_tokens"] == 50
        assert len(detail.results[0]["criteria"]) == 1  # type: ignore[arg-type]
        store.close()

    def test_get_run_not_found(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")

        assert store.get_run("nonexistent") is None
        store.close()

    def test_multiple_runs_ordered_by_newest(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        id1 = store.save_run(_make_results(), "First", "mock")
        id2 = store.save_run(_make_results(), "Second", "mock")

        runs = store.get_runs()

        assert len(runs) == 2
        assert runs[0].id == id2
        assert runs[1].id == id1
        store.close()

    def test_limit_parameter(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        for i in range(5):
            store.save_run(_make_results(), f"Suite {i}", "mock")

        runs = store.get_runs(limit=3)

        assert len(runs) == 3
        store.close()

    def test_duration_stored_correctly(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        store.save_run(_make_results(), "Suite", "mock")

        runs = store.get_runs()

        assert runs[0].duration_ms == 18.7  # 10.5 + 8.2
        store.close()

    def test_criteria_preserved_in_detail(self, tmp_path: Path) -> None:
        store = Store(db_path=tmp_path / "test.db")
        run_id = store.save_run(_make_results(), "Suite", "mock")

        detail = store.get_run(run_id)
        assert detail is not None
        criterion = detail.results[1]["criteria"][0]  # type: ignore[index]
        assert criterion["type"] == "contains"  # type: ignore[index]
        assert criterion["detail"] == "Expected 'X' in response"  # type: ignore[index]
        store.close()

    def test_auto_creates_parent_dirs(self, tmp_path: Path) -> None:
        deep_path = tmp_path / "a" / "b" / "c" / "test.db"
        store = Store(db_path=deep_path)

        store.save_run(_make_results(), "Suite", "mock")
        assert len(store.get_runs()) == 1
        store.close()
