# PromptQA

**Systematic LLM output testing and quality assurance.**

Define test cases in YAML. Run them against any LLM. Get structured pass/fail results.
Built to bring QA methodology into the world of AI — because LLM outputs deserve the same rigor as any other software.

---

## What This Project Demonstrates

| Concept | Where in the code | Why it matters |
|---|---|---|
| **Strategy Pattern** | `src/promptqa/providers/base.py` | Swap LLM backends without changing evaluation logic |
| **Test-Driven Development** | `tests/` | Every feature starts with a failing test |
| **YAML-driven configuration** | `examples/basic_test.yaml` | Declarative test definitions, no code changes needed |
| **Structured result objects** | `src/promptqa/providers/base.py` | Dataclasses over dicts — typed, documented, IDE-friendly |
| **CI/CD pipeline** | `.github/workflows/ci.yml` | Automated quality gates: pytest, ruff, mypy |

---

## Architecture

```
                         promptqa run tests.yaml --provider anthropic
                                        |
                                        v
                    +-------------------------------------------+
                    |               CLI (cli.py)                |
                    |   Parses args, selects provider, starts   |
                    +-------------------+-----------------------+
                                        |
                                        v
                    +-------------------------------------------+
                    |          Config Loader (config.py)         |
                    |   Reads YAML, validates test definitions   |
                    +-------------------+-----------------------+
                                        |
                                        v
                    +-------------------------------------------+
                    |          Evaluator (evaluator.py)          |
                    |   Runs each test case:                     |
                    |   1. Send prompt to provider               |
                    |   2. Check response against criteria       |
                    |   3. Collect results                       |
                    +-------------------+-----------------------+
                                        |
                      provider.complete(prompt, system)
                                        |
              +-------------------------+-------------------------+
              |                         |                         |
              v                         v                         v
    +------------------+   +---------------------+   +-------------------+
    |   MockProvider   |   | AnthropicProvider    |   |  (OllamaProvider) |
    |                  |   |                      |   |                   |
    |  Returns pre-    |   |  Calls Claude API    |   |  Runs local LLM   |
    |  defined YAML    |   |  with your API key   |   |  via Ollama       |
    |  responses       |   |                      |   |  (coming soon)    |
    +------------------+   +---------------------+   +-------------------+
         (free)              (requires API key)          (free, local)
              |                         |                         |
              +-------------------------+-------------------------+
                                        |
                                        v
                    +-------------------------------------------+
                    |          Reporter (reporter.py)            |
                    |   Formats results: pass/fail, summary,    |
                    |   token usage, timing                     |
                    +-------------------------------------------+
```

> **Strategy Pattern:** The evaluator doesn't know which provider is active.
> It calls `provider.complete()` — the concrete provider handles the rest.
> Adding a new provider means implementing one class. Zero changes to evaluation logic.
> See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a deeper explanation.

---

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) [Ollama](https://ollama.com/) for free local LLM testing — no API key needed

### Installation

```bash
# Clone the repo
git clone https://github.com/SMat777/PromptQA.git
cd PromptQA

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy the environment template
cp .env.example .env

# Add your Anthropic API key (only needed for --provider anthropic)
# Get one at: https://console.anthropic.com/
```

### Usage

```bash
# Run tests with mock provider (free, no API key)
promptqa run examples/basic_test.yaml

# Run with Claude API
promptqa run examples/basic_test.yaml --provider anthropic

# Verbose output
promptqa run examples/basic_test.yaml --verbose

# Check version
promptqa --version
```

### Running without an API key

PromptQA ships with a **mock provider** that uses pre-defined responses from your YAML file.
This is how the test suite runs — deterministic, free, no external dependencies.

For free LLM testing with real model responses, consider [Ollama](https://ollama.com/):
```bash
brew install ollama          # macOS
ollama pull llama3.2         # Download a model
ollama serve                 # Start local server
```
The architecture (Strategy Pattern) makes adding an Ollama provider straightforward —
see [issue #12](../../issues) for status.

---

## Project Structure

```
PromptQA/
├── src/promptqa/
│   ├── __init__.py          # Package version
│   ├── __main__.py          # python -m promptqa entry point
│   ├── cli.py               # Argument parsing and command routing
│   ├── config.py            # YAML test case loader (issue #3)
│   ├── providers/
│   │   ├── base.py          # BaseProvider ABC — the Strategy interface
│   │   ├── mock.py          # MockProvider — YAML responses (issue #2)
│   │   └── anthropic.py     # AnthropicProvider — Claude API (issue #7)
│   ├── evaluator.py         # Core test runner (issue #4)
│   └── reporter.py          # Terminal output formatting (issue #6)
├── tests/                   # pytest test suite
├── examples/                # YAML test configurations
├── docs/
│   ├── ARCHITECTURE.md      # Strategy Pattern deep-dive
│   └── LEARNING.md          # Development journal
└── .github/
    ├── workflows/ci.yml     # Automated testing pipeline
    └── ISSUE_TEMPLATE/      # Structured issue creation
```

---

## Development Workflow

This project follows a structured agile workflow:

1. **Issues** define scope — each feature is one issue with acceptance criteria
2. **Feature branches** isolate work — `feature/provider-interface`, `feature/yaml-loader`
3. **TDD** drives implementation — red, green, refactor
4. **PRs** document decisions — each PR includes a learning reflection
5. **CI** validates quality — every push runs tests, linting, and type checking

### Running Tests

```bash
pytest                  # Run all tests
pytest -v               # Verbose output
ruff check src/ tests/  # Lint check
mypy src/               # Type check
```

---

## Development Phases

| Phase | Focus | Status |
|---|---|---|
| **0** | Project setup, structure, CI | `in progress` |
| **1** | Core architecture: providers, config, evaluator | `planned` |
| **2** | CLI interface and terminal reporter | `planned` |
| **3** | Anthropic API integration | `planned` |
| **4** | Documentation, examples, polish | `planned` |

See [Issues](../../issues) for the full breakdown.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **Python 3.11+** | Core language |
| **Anthropic SDK** | Claude API integration |
| **PyYAML** | Test case configuration |
| **pytest** | Test framework |
| **ruff** | Fast linting |
| **mypy** | Static type checking |
| **GitHub Actions** | CI/CD pipeline |

---

## Background

This project grows out of 8 years of systematic software testing at Brunata A/S
combined with daily use of Claude Code and MCP server architecture for AI workflows.
The core idea: LLM outputs should be tested with the same rigor as any other software —
defined criteria, reproducible results, clear pass/fail.

---

## License

[MIT](LICENSE)
