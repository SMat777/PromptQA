"""Test provider base class contract."""

import pytest

from promptqa.providers.base import BaseProvider, ProviderResponse


class TestProviderResponse:
    """Verify the structured response dataclass."""

    def test_minimal_response(self) -> None:
        """ProviderResponse should work with just text and model."""
        response = ProviderResponse(text="Hello", model="mock")
        assert response.text == "Hello"
        assert response.model == "mock"
        assert response.input_tokens == 0
        assert response.output_tokens == 0

    def test_full_response(self) -> None:
        """ProviderResponse should store token counts when provided."""
        response = ProviderResponse(
            text="Answer",
            model="claude-sonnet-4-20250514",
            input_tokens=10,
            output_tokens=5,
        )
        assert response.input_tokens == 10
        assert response.output_tokens == 5


class TestBaseProviderContract:
    """Verify that BaseProvider cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self) -> None:
        """BaseProvider is abstract — instantiating it should raise TypeError.

        Why: The Strategy Pattern requires concrete implementations.
        BaseProvider defines the interface, not the behavior.
        """
        with pytest.raises(TypeError):
            BaseProvider()  # type: ignore[abstract]
