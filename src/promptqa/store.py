"""SQLite result store — persists test run history for the API and dashboard."""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from promptqa.evaluator import TestResult

DEFAULT_DB_PATH = Path.home() / ".promptqa" / "results.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          TEXT PRIMARY KEY,
    suite_name  TEXT NOT NULL,
    provider    TEXT NOT NULL,
    total       INTEGER NOT NULL,
    passed      INTEGER NOT NULL,
    failed      INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES runs(id),
    test_name     TEXT NOT NULL,
    passed        INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    duration_ms   REAL NOT NULL,
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    criteria_json TEXT NOT NULL DEFAULT '[]'
);
"""


@dataclass
class RunSummary:
    """Lightweight run record for list views."""

    id: str
    suite_name: str
    provider: str
    total: int
    passed: int
    failed: int
    duration_ms: float
    created_at: str


@dataclass
class RunDetail(RunSummary):
    """Full run record including per-test results."""

    results: list[dict[str, object]]


class Store:
    """SQLite-backed persistence for test runs.

    Args:
        db_path: Path to the SQLite database file. Parent directories
                 are created automatically.
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def save_run(
        self,
        test_results: list[TestResult],
        suite_name: str,
        provider: str,
    ) -> str:
        """Persist a completed test run. Returns the run ID."""
        run_id = uuid.uuid4().hex[:12]
        passed = sum(1 for r in test_results if r.passed)
        total_ms = sum(r.duration_ms for r in test_results)

        self._conn.execute(
            "INSERT INTO runs (id, suite_name, provider, total, passed, failed, duration_ms) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, suite_name, provider, len(test_results), passed,
             len(test_results) - passed, round(total_ms, 2)),
        )

        for r in test_results:
            criteria = [
                {
                    "type": cr.criterion_type,
                    "passed": cr.passed,
                    "description": cr.description,
                    "detail": cr.detail,
                }
                for cr in r.criterion_results
            ]
            self._conn.execute(
                "INSERT INTO results "
                "(run_id, test_name, passed, response_text, duration_ms, "
                "input_tokens, output_tokens, criteria_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, r.test_name, int(r.passed), r.response_text,
                 round(r.duration_ms, 2), r.input_tokens, r.output_tokens,
                 json.dumps(criteria)),
            )

        self._conn.commit()
        return run_id

    def get_runs(self, limit: int = 50) -> list[RunSummary]:
        """List recent runs, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)
        ).fetchall()
        return [RunSummary(**dict(r)) for r in rows]

    def get_run(self, run_id: str) -> RunDetail | None:
        """Get a single run with all per-test results."""
        row = self._conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if row is None:
            return None

        result_rows = self._conn.execute(
            "SELECT * FROM results WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()

        results = []
        for r in result_rows:
            d = dict(r)
            d["criteria"] = json.loads(d.pop("criteria_json"))
            d["passed"] = bool(d["passed"])
            results.append(d)

        run_dict = dict(row)
        return RunDetail(**run_dict, results=results)

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
