"""Tests for provider selector service."""

import pytest
from unittest.mock import Mock, MagicMock

from gao_dev.core.providers.selector import ProviderSelector, ProviderSelectionError
from gao_dev.core.providers.selection import AutoDetectStrategy
from gao_dev.core.providers.factory import ProviderFactory


class TestProviderSelector:
    """Test provider selector service."""

    def test_initialization(self):
        """Test selector initializes correctly."""
        factory = Mock()

        selector = ProviderSelector(factory)

        assert selector.factory == factory
        assert isinstance(selector.strategy, AutoDetectStrategy)

    def test_custom_strategy(self):
        """Test selector accepts custom strategy."""
        factory = Mock()
        strategy = Mock()

        selector = ProviderSelector(factory, strategy=strategy)

        assert selector.strategy == strategy

    def test_selects_provider(self):
        """Test selector selects provider using strategy."""
        # Create mock factory
        factory = Mock()
        factory.list_providers.return_value = ["claude-code"]

        # Create mock provider
        mock_provider = Mock()
        mock_provider.name = "claude-code"
        factory.create_provider.return_value = mock_provider

        # Create selector
        selector = ProviderSelector(factory)

        # Select
        selected = selector.select_provider(model="sonnet-4.5")

        assert selected == mock_provider

    def test_raises_error_if_no_providers_available(self):
        """Test raises error if no providers available."""
        factory = Mock()
        factory.list_providers.return_value = []

        selector = ProviderSelector(factory)

        with pytest.raises(ProviderSelectionError, match="No providers available"):
            selector.select_provider(model="sonnet-4.5")

    def test_raises_error_if_strategy_returns_none(self):
        """Test raises error if strategy can't select provider."""
        factory = Mock()
        factory.list_providers.return_value = ["custom-provider"]

        mock_provider = Mock()
        mock_provider.name = "custom-provider"  # Won't match fallback chain
        factory.create_provider.return_value = mock_provider

        selector = ProviderSelector(factory)

        with pytest.raises(ProviderSelectionError, match="could not select"):
            selector.select_provider(model="sonnet-4.5")

    def test_handles_provider_creation_failure(self):
        """Test handles provider creation failures gracefully."""
        factory = Mock()
        factory.list_providers.return_value = ["claude-code", "opencode"]

        # First provider fails, second succeeds
        mock_provider = Mock()
        mock_provider.name = "opencode"

        def create_side_effect(name):
            if name == "claude-code":
                raise Exception("Provider not available")
            return mock_provider

        factory.create_provider.side_effect = create_side_effect

        selector = ProviderSelector(factory)

        # Should select opencode (claude-code failed)
        selected = selector.select_provider(model="sonnet-4.5")

        assert selected == mock_provider

    def test_passes_context_to_strategy(self):
        """Test passes context to selection strategy."""
        factory = Mock()
        factory.list_providers.return_value = ["claude-code"]

        mock_provider = Mock()
        mock_provider.name = "claude-code"
        factory.create_provider.return_value = mock_provider

        strategy = Mock()
        strategy.select_provider.return_value = mock_provider

        selector = ProviderSelector(factory, strategy=strategy)

        context = {"project": "test"}
        selector.select_provider(model="sonnet-4.5", context=context)

        # Verify strategy was called with context
        strategy.select_provider.assert_called_once()
        call_args = strategy.select_provider.call_args
        # Check positional args (available_providers, model, context)
        assert len(call_args.args) >= 2
        assert call_args.args[1] == "sonnet-4.5"
        assert call_args.args[2] == context
