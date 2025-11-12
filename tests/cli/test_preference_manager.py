"""Tests for PreferenceManager.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""


def test_preference_manager_imports():
    """Test that PreferenceManager can be imported."""
    from gao_dev.cli.preference_manager import PreferenceManager

    assert PreferenceManager is not None
