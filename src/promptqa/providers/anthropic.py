"""AnthropicProvider — sends prompts to Claude via the Anthropic SDK.

Reads configuration from environment variables:
    ANTHROPIC_API_KEY  — required, your API key from console.anthropic.com
    ANTHROPIC_MODEL    — optional, defaults to claude-sonnet-4-20250514
"""

import os

import anthropic
from anthropic.types import TextBlock

from promptqa.providers.base import BaseProvider, ProviderResponse

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024


class AnthropicProvider(BaseProvider):
    """Concrete Strategy that calls the Claude API.

    Args:
        api_key: Override for ANTHROPIC_API_KEY env var (primarily for testing).
    """

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Export it or add it to your .env file. "
                "Get a key at: https://console.anthropic.com/"
            )

        self._client = anthropic.Anthropic(api_key=key)
        self._model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    def complete(self, prompt: str, system: str = "") -> ProviderResponse:
        """Send prompt to Claude and return structured response."""
        message = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        first_block = message.content[0]
        if not isinstance(first_block, TextBlock):
            raise TypeError(f"Expected TextBlock, got {type(first_block).__name__}")

        return ProviderResponse(
            text=first_block.text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    def name(self) -> str:
        return "anthropic"
