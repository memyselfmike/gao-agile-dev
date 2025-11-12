"""Tests for InteractivePrompter.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""


def test_interactive_prompter_imports():
    """Test that InteractivePrompter can be imported."""
    from gao_dev.cli.interactive_prompter import InteractivePrompter

    assert InteractivePrompter is not None
