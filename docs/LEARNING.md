# Development Journal — PromptQA

Each PR includes a learning reflection. This file collects the key takeaways.

---

## Phase 0 — Project Setup

**Date:** 2026-04-17
**PR:** #1 (feature/project-setup)

### What I built
- Repository structure with `pyproject.toml`, CI pipeline, issue/PR templates
- CLI skeleton with `argparse` subcommands
- `BaseProvider` ABC and `ProviderResponse` dataclass (Strategy Pattern foundation)
- 9 passing tests covering version, CLI and provider contract

### What I learned
- **`pyproject.toml`** is the modern replacement for `setup.py` — everything in one file: dependencies, tool configs (ruff, mypy, pytest), and package metadata
- **Strategy Pattern in Python** uses `ABC` (Abstract Base Class) from the `abc` module. Decorating a method with `@abstractmethod` means Python raises `TypeError` at instantiation time if any abstract method is missing — fail-fast instead of runtime surprises
- **Subprocess testing for CLI** (`subprocess.run`) tests the actual user experience rather than internal functions. This catches argument parsing bugs that unit tests on the parser object would miss
- **`ruff`** replaces both `flake8` and `isort` in a single, faster tool. The `select` config in `pyproject.toml` controls which rule sets are active

### What was challenging
- Getting the `pyproject.toml` build-backend right — `setuptools.build_meta` is the correct import path, not `setuptools.backends._legacy`
- Deciding between `ABC` and `Protocol` for the provider interface. Chose ABC because it's explicit: you know at class definition time if you forgot to implement a method, not when you first call it at runtime

### What I'd do differently
- Nothing yet — this is the foundation. The real test of the architecture comes when implementing the first concrete provider (MockProvider, issue #2)

---

## Phase 1 — Core Architecture

**Date:** 2026-04-17
**PRs:** #12 (MockProvider), #13 (Config Loader), #14 (Evaluator)

### What I built
- `MockProvider` — first concrete `BaseProvider` using dict-based response lookup
- YAML config loader with `Criterion`, `TestCase`, `TestSuite` dataclasses
- `Evaluator` with four criterion checkers: `contains`, `not_contains`, `contains_any`, `max_length`

### What I learned
- **Strategy Pattern in practice:** implementing `MockProvider` from `BaseProvider` ABC confirmed the architecture — the evaluator runs identically regardless of which provider is active, because it only calls `provider.complete()`
- **Dataclasses as domain model:** `TestCase` and `Criterion` replace raw dicts from PyYAML. This catches typos at attribute access time instead of getting `None` from a missing dict key
- **Criterion routing via dict dispatch:** `{"contains": _check_contains, ...}` is cleaner than `if/elif` chains and makes adding new criteria a one-line change
- **`Callable` type alias for mypy:** typing a dict of functions requires `Callable[[str, Criterion], CriterionResult]` — mypy strict mode enforces this

### What was challenging
- PyYAML's `safe_load` returns `Any`, which means every field access needs explicit typing. Dataclasses solve this by providing a typed layer on top of the raw YAML

---

## Phase 2 — CLI & Output

**Date:** 2026-04-17
**PR:** #15

### What I built
- `Reporter` with ANSI color output, verbose mode and `NO_COLOR` env support
- Full CLI wiring: `promptqa run tests.yaml` loads config → creates provider → runs evaluator → prints report
- Exit code 0/1 based on test results for CI integration
- End-to-end subprocess tests covering the full pipeline

### What I learned
- **ANSI escape codes** are simple (`\033[32m` for green, `\033[0m` for reset) but the `NO_COLOR` standard (no-color.org) is important for accessibility and CI environments
- **Exit codes as API:** returning 1 on failure means PromptQA integrates directly into CI pipelines — `promptqa run tests.yaml || exit 1`
- **Subprocess testing** for CLI catches bugs that unit tests on `argparse` miss — argument parsing, import errors, and output formatting all tested in one go

### What was challenging
- Balancing verbose and non-verbose output: too much detail makes failures hard to scan, too little makes debugging impossible. The solution: always show pass/fail per test, but criterion-level detail only in `--verbose`

---

## Phase 3 — Anthropic Integration

**Date:** 2026-04-17
**PR:** #16

### What I built
- `AnthropicProvider` — calls Claude API via the Anthropic SDK
- Environment-based config: `ANTHROPIC_API_KEY` (required) and `ANTHROPIC_MODEL` (optional)
- Type-safe `TextBlock` handling for the SDK's union response type

### What I learned
- **Mocking external APIs:** `unittest.mock.patch` with `MagicMock(spec=TextBlock)` ensures mocks match the real type signature. Without `spec`, mypy passes but the isinstance check in production code fails
- **Deferred imports:** importing `AnthropicProvider` inside the function (not at module level) means the anthropic SDK only loads when `--provider anthropic` is used — mock users never need it installed
- **Union type narrowing:** the Anthropic SDK returns `TextBlock | ThinkingBlock | ToolUseBlock | ...`. Using `isinstance(block, TextBlock)` satisfies mypy strict mode and handles edge cases

### What was challenging
- Getting mocks right for the Anthropic SDK: `message.content[0]` returns a union type, so `MagicMock()` alone doesn't satisfy `isinstance(block, TextBlock)`. The fix was `MagicMock(spec=TextBlock, text="...")` which creates a mock that passes isinstance checks
