"""Tests for AnthropicProvider — Claude API integration.

Uses unittest.mock to patch the Anthropic SDK client so tests
run without an API key or network access.
"""

from unittest.mock import MagicMock, patch

import pytest
from anthropic.types import TextBlock

from promptqa.providers.base import BaseProvider, ProviderResponse


class TestAnthropicProviderContract:
    """Verify AnthropicProvider fulfills the BaseProvider interface."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_is_base_provider(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        assert isinstance(provider, BaseProvider)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_name_returns_anthropic(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        assert provider.name() == "anthropic"


class TestAnthropicProviderAuth:
    """Verify API key handling."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_raises_error(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            AnthropicProvider()

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    def test_accepts_valid_key(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        assert provider is not None


class TestAnthropicProviderComplete:
    """Verify the complete() method with mocked API responses."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_complete_returns_provider_response(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(spec=TextBlock, text="The capital is Copenhagen.")]
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 8

        with patch.object(provider._client.messages, "create", return_value=mock_response):
            result = provider.complete("What is the capital of Denmark?")

        assert isinstance(result, ProviderResponse)
        assert result.text == "The capital is Copenhagen."
        assert result.model == "claude-sonnet-4-20250514"
        assert result.input_tokens == 15
        assert result.output_tokens == 8

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_complete_passes_system_prompt(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(spec=TextBlock, text="reply")]
        mock_response.model = "claude-sonnet-4-20250514"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            provider.complete("hello", system="Be concise")

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["system"] == "Be concise"

    @patch.dict(
        "os.environ",
        {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "claude-haiku-4-5-20251001"},
    )
    def test_custom_model_from_env(self) -> None:
        from promptqa.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()

        mock_response = MagicMock()
        mock_response.content = [MagicMock(spec=TextBlock, text="reply")]
        mock_response.model = "claude-haiku-4-5-20251001"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 3

        with patch.object(
            provider._client.messages, "create", return_value=mock_response
        ) as mock_create:
            provider.complete("test")

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
