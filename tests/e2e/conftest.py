"""Pytest configuration and fixtures for E2E tests.

Epic 36: Test Infrastructure
Story 36.1: Cost-Free Test Execution
Story 36.3: ChatHarness Implementation

This module provides provider configuration for E2E tests with a three-tier
precedence system that defaults to cost-free local models.

Additionally provides pytest fixtures for ChatHarness with automatic cleanup.
"""

import os
import subprocess
from typing import Any, Dict, Tuple
import pytest
import structlog

logger = structlog.get_logger()


def get_e2e_test_provider() -> Tuple[str, Dict[str, Any]]:
    """
    Get provider configuration for E2E tests with precedence resolution.

    Three-tier precedence (highest to lowest):
    1. E2E_TEST_PROVIDER environment variable (test-specific override)
    2. AGENT_PROVIDER environment variable (global preference from Epic 35)
    3. Default: opencode/ollama/deepseek-r1 (cost-free)

    Returns:
        Tuple of (provider_name, provider_config)

    Examples:
        >>> # Default (no env vars)
        >>> provider, config = get_e2e_test_provider()
        >>> assert provider == "opencode"
        >>> assert config["ai_provider"] == "ollama"
        >>> assert config["model"] == "deepseek-r1"

        >>> # With E2E_TEST_PROVIDER override
        >>> os.environ["E2E_TEST_PROVIDER"] = "claude-code"
        >>> provider, config = get_e2e_test_provider()
        >>> assert provider == "claude-code"

        >>> # With AGENT_PROVIDER (still cost-free)
        >>> os.environ["AGENT_PROVIDER"] = "claude-code"
        >>> provider, config = get_e2e_test_provider()
        >>> assert provider == "opencode"  # Overridden to cost-free
    """
    # Tier 1: E2E_TEST_PROVIDER (highest precedence)
    e2e_provider = os.getenv("E2E_TEST_PROVIDER")
    if e2e_provider:
        logger.info(
            "e2e_provider_selected",
            tier=1,
            source="E2E_TEST_PROVIDER",
            provider=e2e_provider,
        )
        if e2e_provider == "claude-code":
            return ("claude-code", {})
        elif e2e_provider == "opencode":
            return (
                "opencode",
                {
                    "ai_provider": os.getenv("E2E_AI_PROVIDER", "ollama"),
                    "use_local": True,
                    "model": os.getenv("E2E_MODEL", "deepseek-r1"),
                },
            )

    # Tier 2: AGENT_PROVIDER (global preference from Epic 35)
    # Override to cost-free even if AGENT_PROVIDER is set to Claude
    agent_provider = os.getenv("AGENT_PROVIDER")
    if agent_provider:
        logger.info(
            "e2e_provider_selected",
            tier=2,
            source="AGENT_PROVIDER",
            provider=agent_provider,
            override="cost-free",
        )
        # Force cost-free for E2E tests regardless of AGENT_PROVIDER
        if agent_provider == "claude-code":
            # Override to cost-free
            return (
                "opencode",
                {
                    "ai_provider": "ollama",
                    "use_local": True,
                    "model": "deepseek-r1",
                },
            )
        elif agent_provider == "opencode":
            return (
                "opencode",
                {
                    "ai_provider": os.getenv("AI_PROVIDER", "ollama"),
                    "use_local": True,
                    "model": os.getenv("MODEL", "deepseek-r1"),
                },
            )

    # Tier 3: Default (cost-free)
    logger.info("e2e_provider_selected", tier=3, source="default", provider="opencode")
    return (
        "opencode",
        {
            "ai_provider": "ollama",
            "use_local": True,
            "model": "deepseek-r1",
        },
    )


def validate_ollama_available(model: str = "deepseek-r1") -> bool:
    """
    Check if ollama is running and the specified model is available.

    Args:
        model: Model name to check for (default: deepseek-r1)

    Returns:
        True if ollama is running and model is available, False otherwise

    Error Messages:
        - FileNotFoundError: ollama not installed
        - TimeoutExpired: ollama command timed out
        - returncode != 0: ollama not running
        - Model not in output: model not installed

    Examples:
        >>> if not validate_ollama_available():
        ...     pytest.skip("Ollama not available")
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            print("\n" + "=" * 70)
            print("ERROR: ollama is not running")
            print("=" * 70)
            print("\nOllama must be installed and running to execute E2E tests.")
            print("\nSetup Instructions:")
            print("  1. Install ollama: https://ollama.ai/")
            print("  2. Start ollama service")
            print(f"  3. Pull {model} model: ollama pull {model}")
            print("\nAlternative: Override provider with environment variable:")
            print("  export E2E_TEST_PROVIDER=claude-code")
            print("\nNote: Using Claude API will incur costs:")
            print("  - Input: $0.003/1K tokens")
            print("  - Output: $0.015/1K tokens")
            print("=" * 70 + "\n")
            logger.error("ollama_not_running", returncode=result.returncode)
            return False

        if model not in result.stdout:
            print("\n" + "=" * 70)
            print(f"ERROR: {model} model not installed")
            print("=" * 70)
            print(f"\nThe {model} model is not available in ollama.")
            print("\nSetup Instructions:")
            print(f"  Run: ollama pull {model}")
            print("\nAvailable models:")
            print(result.stdout)
            print("\nAlternative models:")
            print("  - llama2: ollama pull llama2")
            print("  - codellama: ollama pull codellama")
            print("\nTo use a different model:")
            print(f"  export E2E_MODEL=llama2")
            print("=" * 70 + "\n")
            logger.error("model_not_available", model=model, available=result.stdout)
            return False

        logger.info("ollama_validated", model=model, status="available")
        return True

    except FileNotFoundError:
        print("\n" + "=" * 70)
        print("ERROR: ollama not installed")
        print("=" * 70)
        print("\nOllama is not installed on this system.")
        print("\nSetup Instructions:")
        print("  Install from: https://ollama.ai/")
        print("\nAlternative: Override provider with environment variable:")
        print("  export E2E_TEST_PROVIDER=claude-code")
        print("\nNote: Using Claude API will incur costs:")
        print("  - Input: $0.003/1K tokens")
        print("  - Output: $0.015/1K tokens")
        print("=" * 70 + "\n")
        logger.error("ollama_not_installed")
        return False

    except subprocess.TimeoutExpired:
        print("\n" + "=" * 70)
        print("ERROR: ollama command timed out")
        print("=" * 70)
        print("\nThe ollama command did not respond within 5 seconds.")
        print("\nTroubleshooting:")
        print("  1. Check if ollama service is running")
        print("  2. Restart ollama service")
        print("  3. Check system resources")
        print("\nAlternative: Override provider with environment variable:")
        print("  export E2E_TEST_PROVIDER=claude-code")
        print("=" * 70 + "\n")
        logger.error("ollama_timeout")
        return False


# Story 36.3: ChatHarness pytest fixture with automatic cleanup
@pytest.fixture
def chat_harness():
    """
    Provide ChatHarness with automatic cleanup.

    Spawns gao-dev start subprocess in capture mode and ensures
    clean shutdown even if test fails.

    Usage:
        def test_something(chat_harness):
            chat_harness.send("help")
            output = chat_harness.expect(["commands"])

    Yields:
        ChatHarness: Started ChatHarness instance

    Note:
        - Automatically starts subprocess before test
        - Automatically closes subprocess after test
        - Uses capture_mode=True by default
        - 30-second default timeout
    """
    from tests.e2e.harness.chat_harness import ChatHarness

    harness = ChatHarness(capture_mode=True, timeout=30)
    harness.start()

    try:
        yield harness
    finally:
        harness.close()
        logger.info("chat_harness_fixture_cleaned_up")
