# PromptQA

**Systematic testing and quality assurance for LLM outputs.**

Define test cases in YAML, run them against an LLM, and get structured pass/fail results.

---

## Overview

| Concept | Location | Purpose |
|---|---|---|
| **Strategy Pattern** | `providers/base.py` | Swap LLM backends without touching evaluation logic |
| **YAML configuration** | `examples/` | Declarative test definitions — no code changes needed |
| **Typed dataclasses** | `config.py`, `evaluator.py` | Structured result objects instead of loose dicts |
| **CI/CD** | `.github/workflows/ci.yml` | Automated quality control: pytest, ruff, mypy |

---

## How It Works

### 1. Define a test case in YAML

```yaml
name: "My tests"
provider: mock

tests:
  - name: "Check factual accuracy"
    prompt: "What is the capital of Denmark?"
    system: "Answer in one sentence."
    criteria:
      - type: contains
        value: "Copenhagen"
      - type: max_length
        value: 100

mock_responses:
  "What is the capital of Denmark?": "The capital of Denmark is Copenhagen."
```

### 2. Run the tests

```bash
# With mock provider (free, pre-defined responses from YAML)
promptqa run tests.yaml

# With Claude API (real LLM responses)
promptqa run tests.yaml --provider anthropic

# With detailed per-criterion output
promptqa run tests.yaml --verbose

# JSON output for CI/CD integration
promptqa run tests.yaml --format json -o results.json
```

### 3. Read the results

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
My tests — 1 test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  PASS  Check factual accuracy (0.1ms)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1 passed (0ms)
```

### Using a real LLM

```bash
cp .env.example .env       # Add your ANTHROPIC_API_KEY
promptqa run tests.yaml --provider anthropic --model claude-haiku-4-5-20251001
```

---

## Criterion Types

| Type | Value | Passes when |
|---|---|---|
| `contains` | string | Value found in response |
| `not_contains` | string | Value not found in response |
| `contains_any` | list | At least one value found |
| `max_length` | int | Response length <= value |
| `min_length` | int | Response length >= value |
| `equals` | string | Stripped response exactly matches value |
| `regex` | pattern | `re.search(pattern, text)` matches |
| `json_valid` | `true` | Response is valid JSON |

All text-based criteria support `case_insensitive: true`.

---

## Architecture

```
                   promptqa run tests.yaml --provider anthropic
                                        |
                                        v
                  +-------------------------------------------+
                  | CLI (cli.py)                              |
                  | Parses arguments, selects provider        |
                  +---------------------+---------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Config Loader (config.py)                 |
                  | Reads YAML, validates test definitions    |
                  +---------------------+---------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Evaluator (evaluator.py)                  |
                  | For each test case:                       |
                  | 1. Send prompt to provider                |
                  | 2. Check response against criteria        |
                  | 3. Collect results                        |
                  +---------------------+---------------------+
                                        |
                    provider.complete(prompt, system)
                                        |
                 +----------------------+--------------------------+
                 |                      |                          |
                 v                      v                          v
       +-------------------+  +-----------------------+  +-------------------+
       | MockProvider      |  | AnthropicProvider     |  | (OllamaProvider)  |
       |                   |  |                       |  |                   |
       | Returns pre-      |  | Calls Claude API     |  | Runs local LLM   |
       | defined responses |  | with your API key    |  | via Ollama        |
       | from YAML         |  |                       |  |                   |
       +-------------------+  +-----------------------+  +-------------------+
          (free)                (requires API key)         (free, local)
                 +----------------------+--------------------------+
                                        |
                                        v
                  +-------------------------------------------+
                  | Reporter (reporter.py)                    |
                  | Formats: pass/fail, summary,              |
                  | token usage, timing                       |
                  +-------------------------------------------+
```

**Strategy Pattern:** The evaluator doesn't know which provider is active — it calls `provider.complete()` and the concrete provider handles the rest. Adding a new provider requires one new class and zero changes to evaluation logic. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## Tech Stack

| Tool | Role |
|---|---|
| Python 3.11+ | Language |
| Anthropic SDK | Claude API integration (optional) |
| PyYAML | Test case configuration |
| pytest | Test framework |
| ruff | Linting |
| mypy (strict) | Static type checking |
| GitHub Actions | CI/CD pipeline |

---

## Getting Started

```bash
git clone https://github.com/SMat777/PromptQA.git
cd PromptQA
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"

# Run with mock provider (free)
promptqa run examples/basic_test.yaml
```

---

## Examples

| Suite | File | What it tests |
|---|---|---|
| **Basic** | `examples/basic_test.yaml` | Facts, tone, and safety — 3 tests |
| **Tone** | `examples/tone_check.yaml` | Professional vs. casual communication |
| **Safety** | `examples/safety.yaml` | Refusal of harmful requests |
| **Factual** | `examples/factual.yaml` | Correct answers, JSON validation, regex matching |

---

## Project Structure

```
src/promptqa/
├── __init__.py              # Package version
├── __main__.py              # Entry point for python -m promptqa
├── cli.py                   # Argument parsing and command routing
├── config.py                # YAML -> typed TestSuite/TestCase/Criterion dataclasses
├── providers/
│   ├── base.py              # BaseProvider ABC — Strategy interface
│   ├── mock.py              # MockProvider — dict-based responses from YAML
│   └── anthropic.py         # AnthropicProvider — Claude API
├── evaluator.py             # Runs test cases: provider -> criteria checks -> TestResult
└── reporter.py              # Terminal and JSON output formatting

tests/                       # 89 tests — pytest
examples/                    # 4 YAML suites with mock responses
docs/
└── ARCHITECTURE.md          # Strategy Pattern documentation
```

New provider? Implement `BaseProvider` in `providers/`, add to factory in `cli.py`.
New criterion? Write the checker function, add to dispatch dict in `evaluator.py`.
