"""Tests for ProviderValidator.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""


def test_provider_validator_imports():
    """Test that ProviderValidator can be imported."""
    from gao_dev.cli.provider_validator import ProviderValidator

    assert ProviderValidator is not None


def test_exceptions_defined():
    """Test that all custom exceptions are defined."""
    from gao_dev.cli.exceptions import (
        ProviderSelectionError,
        ProviderSelectionCancelled,
        ProviderValidationFailed,
        PreferenceSaveError,
        PreferenceLoadError,
    )

    assert issubclass(ProviderSelectionCancelled, ProviderSelectionError)
    assert issubclass(ProviderValidationFailed, ProviderSelectionError)
    assert issubclass(PreferenceSaveError, ProviderSelectionError)
    assert issubclass(PreferenceLoadError, ProviderSelectionError)


def test_data_models_defined():
    """Test that all data models are defined."""
    from gao_dev.cli.models import ProviderConfig, ProviderPreferences, ValidationResult

    assert ProviderConfig is not None
    assert ProviderPreferences is not None
    assert ValidationResult is not None
