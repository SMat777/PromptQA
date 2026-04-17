"""Test that the package imports correctly and exposes a version."""


class TestPackageVersion:
    """Verify package identity — the most basic smoke test."""

    def test_version_is_string(self) -> None:
        """__version__ should be a non-empty string (semver format)."""
        from promptqa import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_is_semver(self) -> None:
        """Version should follow major.minor.patch format."""
        from promptqa import __version__

        parts = __version__.split(".")
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {__version__}"
        for part in parts:
            assert part.isdigit(), f"Non-numeric version part: {part}"
