"""Provider selector service.

Main service for selecting providers based on configured strategy.
"""

from typing import Optional, List, Dict, Any
import structlog

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.selection import (
    IProviderSelectionStrategy,
    AutoDetectStrategy,
    ProviderSelectionError,
)

logger = structlog.get_logger(__name__)


class ProviderSelector:
    """
    Service for selecting the best provider.

    Uses a configurable selection strategy to choose from available providers.
    """

    def __init__(
        self,
        factory: ProviderFactory,
        strategy: Optional[IProviderSelectionStrategy] = None,
    ):
        """
        Initialize provider selector.

        Args:
            factory: Provider factory for creating providers
            strategy: Selection strategy (defaults to AutoDetect)
        """
        self.factory = factory
        self.strategy = strategy or AutoDetectStrategy()

    def select_provider(
        self,
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IAgentProvider:
        """
        Select the best provider for the given model.

        Args:
            model: Canonical model name
            context: Additional context for selection

        Returns:
            Selected provider instance

        Raises:
            ProviderSelectionError: If no suitable provider found
        """
        logger.info(
            "provider_selector_starting",
            model=model,
            strategy=self.strategy.__class__.__name__,
        )

        # Get all available providers
        available_providers = self._get_available_providers()

        if not available_providers:
            raise ProviderSelectionError(
                "No providers available. Install Claude Code, OpenCode, "
                "or set API keys for direct API access."
            )

        # Use strategy to select
        selected = self.strategy.select_provider(
            available_providers, model, context
        )

        if not selected:
            raise ProviderSelectionError(
                f"Strategy {self.strategy.__class__.__name__} "
                f"could not select a provider for model '{model}'"
            )

        logger.info(
            "provider_selector_selected",
            provider=selected.name,
            model=model,
            strategy=self.strategy.__class__.__name__,
        )

        return selected

    def _get_available_providers(self) -> List[IAgentProvider]:
        """
        Get list of available providers.

        Returns:
            List of available provider instances
        """
        available = []
        provider_names = self.factory.list_providers()

        for name in provider_names:
            try:
                # Try to create provider
                provider = self.factory.create_provider(name)

                # TODO: Could add validation here
                available.append(provider)

            except Exception as e:
                logger.debug(
                    "provider_not_available",
                    provider=name,
                    error=str(e),
                )

        return available
