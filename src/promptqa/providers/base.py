"""Base provider interface — the Strategy in Strategy Pattern.

Why Strategy Pattern?
    PromptQA needs to send prompts to different LLM backends (mock, Anthropic,
    Ollama) without the evaluator knowing which one is active. The Strategy
    Pattern lets us swap providers at runtime via the --provider flag while
    keeping the evaluation logic identical.

    See docs/ARCHITECTURE.md for diagrams and detailed explanation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    """Structured response from any LLM provider.

    Attributes:
        text: The generated text from the LLM.
        model: Which model produced the response.
        input_tokens: Tokens used in the prompt (0 for mock).
        output_tokens: Tokens in the response (0 for mock).
    """

    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseProvider(ABC):
    """Abstract base class that all LLM providers must implement.

    This is the 'Strategy' interface. Each concrete provider (MockProvider,
    AnthropicProvider) implements `complete()` with its own logic, but the
    evaluator only sees this interface.
    """

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> ProviderResponse:
        """Send a prompt to the LLM and return a structured response.

        Args:
            prompt: The user prompt to send.
            system: Optional system prompt for context/instructions.

        Returns:
            ProviderResponse with the LLM's output and metadata.
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """Return the provider name (e.g., 'mock', 'anthropic')."""
        ...
