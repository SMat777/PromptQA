"""Tests for the FastAPI REST API."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from promptqa.api.app import app
from promptqa.store import Store

BASIC_YAML = """
name: "API Test Suite"
provider: mock
tests:
  - name: "Simple test"
    prompt: "hello"
    criteria:
      - type: contains
        value: "world"
mock_responses:
  "hello": "hello world"
"""


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Create a test client with an isolated store."""
    store = Store(db_path=tmp_path / "test.db")
    with patch.object(
        __import__("promptqa.api.app", fromlist=["get_store"]),
        "get_store",
        return_value=store,
    ):
        # Reset the global store
        import promptqa.api.app as app_module
        original = app_module._store
        app_module._store = store
        yield TestClient(app)
        app_module._store = original
        store.close()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_includes_version(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert "version" in resp.json()


class TestRunsAPI:
    def test_create_run(self, client: TestClient) -> None:
        resp = client.post("/api/runs", json={"yaml_content": BASIC_YAML})
        assert resp.status_code == 200
        data = resp.json()
        assert data["suite_name"] == "API Test Suite"
        assert data["total"] == 1
        assert data["passed"] == 1

    def test_list_runs(self, client: TestClient) -> None:
        client.post("/api/runs", json={"yaml_content": BASIC_YAML})
        resp = client.get("/api/runs")
        assert resp.status_code == 200
        runs = resp.json()
        assert len(runs) == 1

    def test_get_run_detail(self, client: TestClient) -> None:
        create_resp = client.post("/api/runs", json={"yaml_content": BASIC_YAML})
        run_id = create_resp.json()["id"]

        resp = client.get(f"/api/runs/{run_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["test_name"] == "Simple test"

    def test_get_run_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/runs/nonexistent")
        assert resp.status_code == 404

    def test_invalid_yaml(self, client: TestClient) -> None:
        resp = client.post("/api/runs", json={"yaml_content": "{{invalid"})
        assert resp.status_code == 400


class TestDashboard:
    def test_dashboard_loads(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "PromptQA" in resp.text

    def test_run_detail_page(self, client: TestClient) -> None:
        create_resp = client.post("/api/runs", json={"yaml_content": BASIC_YAML})
        run_id = create_resp.json()["id"]

        resp = client.get(f"/runs/{run_id}")
        assert resp.status_code == 200
        assert "API Test Suite" in resp.text
