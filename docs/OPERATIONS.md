# Operations Guide — PromptQA

Step-by-step guide to running PromptQA. Each section is designed to produce visual output suitable for screenshots and portfolio material.

**Table of contents:**
1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Docker Setup](#docker-setup)
4. [Seed Demo Data](#seed-demo-data)
5. [CLI: Run Tests](#cli-run-tests)
6. [Dashboard: Index](#dashboard-index)
7. [Dashboard: Run Detail](#dashboard-run-detail)
8. [API: Swagger Docs](#api-swagger-docs)
9. [API: curl Examples](#api-curl-examples)
10. [Running the Test Suite](#running-the-test-suite)

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized setup)
- Git

An Anthropic API key is **optional** — the mock provider works without any API key, making the entire demo runnable for free.

---

## Local Setup

```bash
git clone https://github.com/SMat777/PromptQA.git
cd PromptQA
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"
```

Verify the installation:

```bash
promptqa --version
# promptqa 0.1.0
```

> **Screenshot:** Terminal showing `promptqa 0.1.0` after successful installation.

---

## Docker Setup

```bash
cp .env.example .env   # optional: add ANTHROPIC_API_KEY
docker compose up --build
```

Docker builds the image, installs dependencies, seeds 4 demo runs automatically, and starts the dashboard. You will see:

```
promptqa-1  | Seeded 4 demo runs.
promptqa-1  | Starting PromptQA dashboard at http://0.0.0.0:8000
```

Open http://localhost:8000 in your browser.

> **Screenshot:** Docker Compose output showing build completion and the `Starting PromptQA dashboard` line.

---

## Seed Demo Data

For local setup (Docker does this automatically):

```bash
python -m promptqa.seed
# Seeded 4 demo runs.
```

This runs all 4 example YAML suites through the mock provider and saves the results to `~/.promptqa/results.db`. The seeded suites are:

| Suite | Tests | What it covers |
|---|---|---|
| Basic QA Tests | 3 | Factual accuracy, professional tone, safety |
| Factual Accuracy | 6 | Geography, science, math, JSON validation, regex |
| Safety Tests | 3 | Refusal of hacking, PII generation, malware |
| Tone Check | 3 | Professional language, conciseness, exact matching |

> **Screenshot:** Terminal showing `Seeded 4 demo runs.`

---

## CLI: Run Tests

### Basic run

```bash
promptqa run examples/basic_test.yaml
```

Output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Basic QA Tests — 3 tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PASS  Factual accuracy — Danish capital (0.0ms)

  PASS  Tone check — professional email (0.0ms)

  PASS  Safety — refuse harmful request (0.0ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 passed (0ms)
```

PASS indicators are colored green in terminals that support ANSI colors.

> **Screenshot:** Terminal with green PASS indicators and the summary line.

### Verbose mode

```bash
promptqa run examples/factual.yaml --verbose
```

Verbose mode shows per-criterion failure details. With mock tests that all pass, the output looks the same — the value shows when a criterion fails.

### JSON output

```bash
promptqa run examples/basic_test.yaml --format json
```

Outputs structured JSON with suite metadata, pass/fail counts, and per-test criterion details. Pipe to `jq` for pretty printing:

```bash
promptqa run examples/basic_test.yaml --format json | jq .
```

Write to file:

```bash
promptqa run examples/basic_test.yaml --format json -o results.json
```

> **Screenshot:** JSON output piped through `jq` showing the structured result.

### All example suites

| Suite | Command |
|---|---|
| Basic | `promptqa run examples/basic_test.yaml` |
| Factual | `promptqa run examples/factual.yaml` |
| Safety | `promptqa run examples/safety.yaml` |
| Tone | `promptqa run examples/tone_check.yaml` |

### Using a real LLM

```bash
cp .env.example .env
# Edit .env: add your ANTHROPIC_API_KEY

promptqa run examples/basic_test.yaml --provider anthropic
```

The summary line will include token usage:

```
3 passed (1250ms) | tokens: 180 in / 95 out
```

Override the model:

```bash
promptqa run examples/basic_test.yaml --provider anthropic --model claude-haiku-4-5-20251001
```

> **Screenshot:** Terminal showing real API results with token counts.

---

## Dashboard: Index

Start the dashboard:

```bash
promptqa serve
# Starting PromptQA dashboard at http://127.0.0.1:8000
```

Open http://localhost:8000. The dashboard shows:

- **Navigation bar** — PromptQA brand and "API Docs" link
- **Three stat cards** — Total Runs, Tests Passed (green), Tests Failed (red)
- **Recent Runs table** — Each row shows:
  - Suite name (bold)
  - Provider badge (e.g., `mock`)
  - Result badge: green "N/N passed" or red "N/N failed"
  - Duration in milliseconds
  - Timestamp
  - "Details" link to the run detail page

If no runs exist yet, the dashboard shows an empty state with guidance to run tests via CLI or the API.

> **Screenshot:** Dashboard index at http://localhost:8000 showing 4 seeded runs with green pass badges, stat cards, and the runs table.

---

## Dashboard: Run Detail

Click "Details" on any run, or navigate to http://localhost:8000/runs/{id}.

The detail page shows:

- **Run header** — Suite name, run ID (monospace), timestamp, provider badge, and overall status pill ("All N passed" or "N of N failed")
- **Stats row** — Total, Passed, Failed, Duration in a 4-column grid
- **Test result cards** — One card per test:
  - Green checkmark or red X with test name and duration
  - Criteria table showing each criterion: pass/fail icon, type badge (e.g., `contains`, `regex`), description, and failure detail if applicable
  - Collapsible "Show response" section revealing the raw LLM output

> **Screenshot:** Run detail page showing per-test cards with criteria breakdown. Click "Show response" on one test to reveal the LLM output.

---

## API: Swagger Docs

Navigate to http://localhost:8000/docs while the server is running.

FastAPI auto-generates interactive Swagger UI showing all endpoints with request/response schemas. You can try each endpoint directly from the browser.

> **Screenshot:** Swagger UI at /docs showing the 4 API endpoints with schema documentation.

---

## API: curl Examples

### Health check

```bash
curl http://localhost:8000/api/health
```

```json
{"status": "ok", "version": "0.1.0"}
```

### List recent runs

```bash
curl http://localhost:8000/api/runs
```

Returns a JSON array of run summaries (newest first). Limit with `?limit=5`.

### Run a test suite

```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "yaml_content": "name: API Demo\nprovider: mock\ntests:\n  - name: Quick test\n    prompt: hello\n    criteria:\n      - type: contains\n        value: world\nmock_responses:\n  hello: hello world"
  }'
```

Returns a run summary with ID, pass/fail counts, and timestamp. The run is persisted to the database and visible on the dashboard.

### Get run details

```bash
curl http://localhost:8000/api/runs/{id}
```

Replace `{id}` with a run ID from the list endpoint. Returns full details including per-test criterion results and response text.

> **Screenshot:** Terminal showing curl commands and formatted JSON responses (pipe through `jq` for readability).

---

## Running the Test Suite

```bash
# All 106 tests
pytest -v

# Lint
ruff check src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

Test coverage by module:

| File | What it covers |
|---|---|
| `test_evaluator.py` | All 8 criterion types, case insensitivity, multi-criteria |
| `test_config.py` | YAML parsing, field validation, error handling |
| `test_reporter.py` | Terminal output, JSON reporter, suite name, token display |
| `test_store.py` | SQLite CRUD, ordering, limits, auto-creation |
| `test_api.py` | REST endpoints, dashboard routes, error responses |
| `test_e2e.py` | Full CLI pipeline via subprocess, exit codes |
| `test_cli.py` | Argument parsing, help text, version |
| `test_mock_provider.py` | Response lookup, missing response handling |
| `test_anthropic_provider.py` | Mocked API calls, model override, token counting |
| `test_providers.py` | Provider interface contract |
| `test_version.py` | Version string format |

> **Screenshot:** `pytest -v` output showing 106 tests passing in green.

---

---

# Upgrade Roadmap

Prioritized enhancements organized by category. Complexity: **S** = a few hours, **M** = 1-2 days, **L** = 3+ days.

## Testing Capabilities

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **LLM-as-Judge** | `judge` criterion that sends the response to a second LLM to evaluate quality, relevance, or safety. Judge prompt defined in YAML. | Standard approach in production eval frameworks (Braintrust, Langsmith). Proves the Strategy Pattern pays off. | M |
| **Semantic Similarity** | `semantic_similarity` criterion using sentence embeddings with configurable threshold. Compares meaning rather than exact text. | ML engineering depth. String matching is insufficient for real LLM QA. | M |
| **Latency Benchmarks** | `max_latency_ms` criterion type. Track p50/p95/p99 latency across runs. Surface regression warnings. | Performance monitoring is a universal enterprise concern. | S |
| **Golden Dataset Testing** | `golden_responses` section in YAML for regression testing. Compare new runs against baselines. | Maps to how ML teams track model regression. | M |
| **Batch Execution** | Run test cases concurrently using `asyncio.gather()`. Add `--concurrency N` flag. | Async Python proficiency. Parallelism is critical for real workloads. | M |

## Observability

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **Prometheus Metrics** | `/metrics` endpoint with counters (runs_total, tests_passed/failed), histograms (duration, latency). | Industry-standard monitoring. Pairs with Grafana dashboards. | S |
| **Structured Logging** | Replace `print()` with `structlog`. JSON formatting, request_id correlation, log levels. | Essential for production debugging. Print-logging is a red flag. | S |
| **OpenTelemetry Traces** | Tracing spans for YAML parsing, provider calls, criterion evaluation, DB writes. Export to Jaeger. | Distributed tracing is the hottest observability pattern. | L |

## CI/CD Integration

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **GitHub Actions Workflow** | Reusable workflow (`.github/workflows/promptqa.yml`) that other repos can call with `uses:`. | Makes the tool practical for teams. "Tool for engineers" thinking. | S |
| **JUnit XML Output** | `--format junit` for native CI integration (Jenkins, GitLab, Azure DevOps). | Universal CI compatibility. Every CI system understands JUnit XML. | S |
| **Regression Detection** | Compare current run against previous for the same suite. Exit code 2 if pass rate drops. | Core value proposition of any QA tool. | M |
| **Webhook Notifications** | `--notify slack` or webhook URL for posting results to team channels. | Integration mindset. Real teams need alerts. | S |

## Multi-Provider Support

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **OpenAI Provider** | `OpenAIProvider` implementing `BaseProvider`. Support GPT-4o, GPT-4o-mini. | Broadens market. Strategy Pattern proof — zero evaluator changes. | S |
| **Ollama Provider** | `OllamaProvider` for local LLMs (Llama, Mistral). HTTP to `localhost:11434`. | Free local testing. Growing ecosystem. | S |
| **Azure OpenAI Provider** | Azure-hosted endpoints with tenant/deployment auth. | Enterprise deployments. Procurement awareness. | S |
| **Provider Comparison** | `--compare` flag: same suite against multiple providers, side-by-side table. | Model selection decisions. Feature that sells itself in demos. | M |

## Dashboard Features

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **Trend Charts** | Chart.js line charts: pass rate over time, duration trends, failure rate by criterion. | Visually impressive in portfolio. Frontend awareness. | M |
| **Comparison View** | Side-by-side two-run diff: new pass, new fail, unchanged. | Useful for prompt change evaluation. UX thinking. | M |
| **YAML Editor** | In-browser editor (CodeMirror/Monaco) with syntax highlighting, validation, and "Run" button. | Interactive and self-contained. Impressive in live demos. | M |
| **Export to CSV/PDF** | Download buttons for run results in CSV and PDF. | Different audiences need different formats. Product maturity. | S |

## Security

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **API Key Auth** | `X-API-Key` header validation middleware. Key from env var. | Basic but essential. The API is currently open. | S |
| **Rate Limiting** | `slowapi` middleware. Configurable per IP/key. | Abuse prevention. Security awareness. | S |
| **Input Validation** | Size limits on `yaml_content`, HTML sanitization for dashboard. | Defensive programming. Senior-level differentiation. | S |

## Production Readiness

| Upgrade | Description | Why it matters | Complexity |
|---|---|---|---|
| **Async Provider Calls** | Make `BaseProvider.complete()` async. Use `httpx.AsyncClient`. | Modern Python standard for I/O-bound services. | M |
| **Alembic Migrations** | Schema versioning. Current `CREATE IF NOT EXISTS` doesn't handle changes. | Essential deployment lifecycle. | M |
| **Configuration Management** | Pydantic Settings with config file / env var / CLI flag precedence. | 12-factor app methodology. | S |
| **Health Check Enhancement** | Check DB connectivity, disk space, provider availability. Add `/api/ready` for Kubernetes. | Cloud-native deployment readiness. | S |

## Recommended Implementation Order

**Phase 1 — Quick wins (1-2 days):**
Structured logging, API key auth, OpenAI provider, Prometheus metrics. High impact, low effort.

**Phase 2 — Differentiators (3-5 days):**
LLM-as-Judge criterion, trend charts, GitHub Actions workflow, async providers. These make the portfolio stand out.

**Phase 3 — Enterprise polish (1-2 weeks):**
Alembic migrations, RBAC, Ollama + Azure providers, comparison mode, YAML editor, OpenTelemetry.
