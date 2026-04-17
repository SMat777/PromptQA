"""FastAPI application — REST API and dashboard for PromptQA."""

from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from promptqa import __version__
from promptqa.api.models import (
    HealthResponse,
    RunDetailResponse,
    RunRequest,
    RunSummaryResponse,
)
from promptqa.config import load_config
from promptqa.evaluator import Evaluator
from promptqa.providers.mock import MockProvider
from promptqa.store import Store

TEMPLATES_DIR = Path(__file__).parent.parent / "dashboard" / "templates"

app = FastAPI(
    title="PromptQA",
    description="Systematic LLM output testing and quality assurance",
    version=__version__,
)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_store: Store | None = None


def get_store() -> Store:
    """Get or create the global Store instance."""
    global _store  # noqa: PLW0603
    if _store is None:
        _store = Store()
    return _store


# --- API Endpoints ---


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version=__version__)


@app.post("/api/runs", response_model=RunSummaryResponse)
def create_run(req: RunRequest) -> RunSummaryResponse:
    """Execute a test suite from YAML content and persist results."""
    try:
        yaml.safe_load(req.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}") from e

    # Write to temp file for load_config (it validates structure)
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(req.yaml_content)
        tmp_path = Path(f.name)

    try:
        suite = load_config(tmp_path)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        tmp_path.unlink(missing_ok=True)

    provider_name = req.provider or suite.provider
    if provider_name == "mock":
        provider = MockProvider(responses=suite.mock_responses)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not supported via API. Use 'mock'.",
        )

    evaluator = Evaluator(provider)
    results = evaluator.run(suite.tests)

    store = get_store()
    run_id = store.save_run(results, suite.name, provider_name)
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve saved run")

    return RunSummaryResponse(
        id=run.id,
        suite_name=run.suite_name,
        provider=run.provider,
        total=run.total,
        passed=run.passed,
        failed=run.failed,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
    )


@app.get("/api/runs", response_model=list[RunSummaryResponse])
def list_runs(limit: int = 50) -> list[RunSummaryResponse]:
    """List recent test runs."""
    store = get_store()
    runs = store.get_runs(limit=limit)
    return [
        RunSummaryResponse(
            id=r.id, suite_name=r.suite_name, provider=r.provider,
            total=r.total, passed=r.passed, failed=r.failed,
            duration_ms=r.duration_ms, created_at=r.created_at,
        )
        for r in runs
    ]


@app.get("/api/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str) -> RunDetailResponse:
    """Get full details for a single run."""
    store = get_store()
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunDetailResponse(
        id=run.id, suite_name=run.suite_name, provider=run.provider,
        total=run.total, passed=run.passed, failed=run.failed,
        duration_ms=run.duration_ms, created_at=run.created_at,
        results=run.results,
    )


# --- Dashboard Routes ---


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    store = get_store()
    runs = store.get_runs(limit=20)
    total_runs = len(runs)
    total_passed = sum(r.passed for r in runs)
    total_failed = sum(r.failed for r in runs)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "runs": runs,
            "total_runs": total_runs,
            "total_passed": total_passed,
            "total_failed": total_failed,
        },
    )


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail_page(request: Request, run_id: str) -> HTMLResponse:
    store = get_store()
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return templates.TemplateResponse(
        request=request,
        name="run_detail.html",
        context={"run": run},
    )
