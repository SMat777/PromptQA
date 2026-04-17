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
