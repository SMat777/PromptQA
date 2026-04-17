"""MockProvider — returns pre-defined responses from a dictionary.

Used for deterministic testing without API calls or costs.
Responses are typically loaded from the `mock_responses` section
of a YAML test configuration file.
"""

from promptqa.providers.base import BaseProvider, ProviderResponse


class MockProvider(BaseProvider):
    """Concrete Strategy that returns pre-defined responses.

    Args:
        responses: Mapping of prompt strings to response strings.
    """

    def __init__(self, responses: dict[str, str]) -> None:
        self._responses = responses

    def complete(self, prompt: str, system: str = "") -> ProviderResponse:
        """Look up the prompt in the response dictionary.

        Raises:
            KeyError: If no mock response is defined for the given prompt.
        """
        if prompt not in self._responses:
            raise KeyError(f"No mock response defined for prompt: '{prompt}'")

        return ProviderResponse(
            text=self._responses[prompt],
            model="mock",
        )

    def name(self) -> str:
        return "mock"
