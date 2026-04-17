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

---

## File Map

```
src/promptqa/
├── __init__.py          # Version string
├── __main__.py          # python -m promptqa entry point
├── cli.py               # Argument parsing, provider selection
├── config.py            # YAML → List[TestCase] (issue #3)
├── providers/
│   ├── base.py          # BaseProvider ABC + ProviderResponse
│   ├── mock.py          # MockProvider (issue #2)
│   └── anthropic.py     # AnthropicProvider (issue #7)
├── evaluator.py         # Core test runner (issue #4)
└── reporter.py          # Terminal output (issue #6)
```

---

*This document is updated as the architecture evolves. See [LEARNING.md](LEARNING.md) for the development journal.*
