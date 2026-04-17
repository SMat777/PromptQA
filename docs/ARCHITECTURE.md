# Architecture — PromptQA

## Overview

PromptQA is built around one central design decision: **the evaluation logic should never know which LLM it's talking to.** This is achieved through the Strategy Pattern — one of the Gang of Four design patterns — applied to the provider layer.

---

## Strategy Pattern — Why and How

### The Problem

PromptQA needs to send prompts to different LLM backends:
- **Mock** — pre-defined responses for testing (free, deterministic)
- **Anthropic** — Claude API for real evaluation (paid, non-deterministic)
- **Ollama** — local LLMs for development (free, non-deterministic)

Without a pattern, this leads to scattered `if/else` blocks:

```python
# Without Strategy Pattern — hard to extend, easy to break
def evaluate(prompt, provider_name):
    if provider_name == "mock":
        response = read_yaml_response(prompt)
    elif provider_name == "anthropic":
        response = call_claude_api(prompt)
    elif provider_name == "ollama":
        response = call_ollama(prompt)
    # Every new provider = another elif + risk of breaking existing ones
```

### The Solution

The Strategy Pattern defines a common interface (`BaseProvider`) that all providers implement. The evaluator only sees the interface — it calls `provider.complete()` without knowing or caring which concrete class is behind it.

```
┌────────────────────────────────────────────────────────────┐
│                    BaseProvider (ABC)                       │
│                                                            │
│   + complete(prompt, system) -> ProviderResponse           │
│   + name() -> str                                          │
└────────────────────────┬───────────────────────────────────┘
                         │ implements
          ┌──────────────┼──────────────┐
          │              │              │
          v              v              v
   ┌──────────┐  ┌──────────────┐  ┌─────────────┐
   │   Mock   │  │  Anthropic   │  │  (Ollama)   │
   │ Provider │  │  Provider    │  │  Provider   │
   │          │  │              │  │             │
   │ Reads    │  │ Calls Claude │  │ Calls local │
   │ YAML     │  │ API          │  │ Ollama API  │
   └──────────┘  └──────────────┘  └─────────────┘
```

### In Code

```python
# src/promptqa/providers/base.py

class BaseProvider(ABC):
    """The Strategy interface — defines what every provider must do."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> ProviderResponse:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
```

```python
# The evaluator only depends on the interface, not the implementation
class Evaluator:
    def __init__(self, provider: BaseProvider):
        self.provider = provider  # Could be any concrete provider

    def run(self, test_case: TestCase) -> TestResult:
        response = self.provider.complete(test_case.prompt, test_case.system)
        # Evaluate response against criteria — same logic for ALL providers
```

### Why This Matters

1. **Open/Closed Principle** — adding a new provider means creating one new class. Zero changes to existing code.
2. **Testability** — MockProvider makes tests deterministic. No API keys needed in CI.
3. **Single Responsibility** — each provider handles only its own API communication.
4. **Runtime flexibility** — the `--provider` CLI flag selects the strategy at runtime.

---

## Data Flow

```
User runs: promptqa run tests.yaml --provider anthropic

    1. CLI parses arguments
       └─> provider = "anthropic", config = "tests.yaml"

    2. Config loader reads YAML
       └─> List[TestCase] with prompts, system prompts, criteria

    3. Provider factory creates AnthropicProvider
       └─> Reads ANTHROPIC_API_KEY from environment

    4. Evaluator iterates test cases
       └─> For each test:
           a. provider.complete(prompt, system) → ProviderResponse
           b. Check response.text against each criterion
           c. Collect TestResult (pass/fail + details)

    5. Reporter formats results
       └─> Terminal output with colors, summary, token usage
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| ABC over Protocol | Explicit is better than implicit — ABC forces implementation of all methods at class definition time, not at runtime |
| Dataclasses for responses | Structured, typed, IDE-friendly — no guessing what keys exist in a dict |
| YAML over JSON for config | More readable for humans, supports comments, natural for test definitions |
| Subprocess tests for CLI | Tests the actual user experience, not internal functions — catches argument parsing bugs |
| Mock as default provider | Safe default — no API key needed, no cost, deterministic results |
| Deferred provider import | `AnthropicProvider` imported inside function — mock users never load the Anthropic SDK |
| TextBlock type narrowing | Anthropic SDK returns union type — isinstance check satisfies mypy strict and handles edge cases |
| Dict dispatch for criteria | `{"contains": _check_contains}` is cleaner than if/elif and adding a new criterion is a one-line change |
| NO_COLOR env support | Respects the [no-color.org](https://no-color.org/) standard for accessibility and CI |
| Exit codes for CI | Exit 0 on all pass, 1 on any failure — integrates directly into CI pipelines |

---

## Criterion System

The evaluator checks each response against a list of criteria. Each criterion type is a pure function:

```python
def _check_contains(text: str, c: Criterion) -> CriterionResult:
    passed = str(c.value) in text
    return CriterionResult(
        passed=passed,
        criterion_type="contains",
        description=c.description,
        detail=f"Expected '{c.value}' in response" if not passed else "",
    )
```

Available types: `contains`, `not_contains`, `contains_any`, `max_length`.

Adding a new type requires two changes:
1. Write the checker function
2. Add it to the dispatch dict in `_check_criterion()`

---

## File Map

```
src/promptqa/
├── __init__.py          # Version string
├── __main__.py          # python -m promptqa entry point
├── cli.py               # Argument parsing, provider factory, command routing
├── config.py            # YAML → TestSuite with typed dataclasses
├── providers/
│   ├── base.py          # BaseProvider ABC + ProviderResponse dataclass
│   ├── mock.py          # MockProvider — dict-based response lookup
│   └── anthropic.py     # AnthropicProvider — Claude API with TextBlock handling
├── evaluator.py         # Core runner: provider.complete() → criteria checks → TestResult
└── reporter.py          # Terminal output with ANSI colors and NO_COLOR support
```

---

*Last updated: Phase 4. See [LEARNING.md](LEARNING.md) for the development journal.*
