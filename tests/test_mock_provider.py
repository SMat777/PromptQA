"""Tests for MockProvider — the first concrete Strategy Pattern implementation."""

import pytest

from promptqa.providers.base import BaseProvider, ProviderResponse
from promptqa.providers.mock import MockProvider


class TestMockProviderContract:
    """Verify MockProvider fulfills the BaseProvider interface."""

    def test_is_base_provider(self) -> None:
        provider = MockProvider(responses={})
        assert isinstance(provider, BaseProvider)

    def test_name_returns_mock(self) -> None:
        provider = MockProvider(responses={})
        assert provider.name() == "mock"


class TestMockProviderResponses:
    """Verify response lookup and error handling."""

    def test_returns_matching_response(self) -> None:
        responses = {"What is Python?": "A programming language."}
        provider = MockProvider(responses=responses)

        result = provider.complete("What is Python?")

        assert isinstance(result, ProviderResponse)
        assert result.text == "A programming language."
        assert result.model == "mock"

    def test_token_counts_are_zero(self) -> None:
        provider = MockProvider(responses={"hi": "hello"})
        result = provider.complete("hi")

        assert result.input_tokens == 0
        assert result.output_tokens == 0

    def test_system_prompt_is_accepted(self) -> None:
        """System prompt is accepted but ignored by mock — matches the interface."""
        provider = MockProvider(responses={"hi": "hello"})
        result = provider.complete("hi", system="Be friendly")

        assert result.text == "hello"

    def test_missing_prompt_raises_key_error(self) -> None:
        provider = MockProvider(responses={"hi": "hello"})

        with pytest.raises(KeyError, match="No mock response defined for prompt"):
            provider.complete("unknown prompt")

    def test_empty_responses_raises_on_any_prompt(self) -> None:
        provider = MockProvider(responses={})

        with pytest.raises(KeyError):
            provider.complete("anything")

    def test_multiple_responses(self) -> None:
        responses = {
            "What is 2+2?": "4",
            "What is the capital of Denmark?": "Copenhagen",
        }
        provider = MockProvider(responses=responses)

        assert provider.complete("What is 2+2?").text == "4"
        assert provider.complete("What is the capital of Denmark?").text == "Copenhagen"
