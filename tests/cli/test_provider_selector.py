"""Tests for ProviderSelector.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""


def test_provider_selector_imports():
    """Test that ProviderSelector can be imported."""
    from gao_dev.cli.provider_selector import ProviderSelector

    assert ProviderSelector is not None
