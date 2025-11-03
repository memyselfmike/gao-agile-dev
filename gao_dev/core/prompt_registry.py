"""
Prompt registry for discovery and management.

This module provides a registry for discovering prompts in directories,
registering prompts (for plugins), and managing prompt overrides.
"""

from pathlib import Path
from typing import Dict, List, Optional
import structlog

from .models.prompt_template import PromptTemplate
from .prompt_loader import PromptLoader
from .config_loader import ConfigLoader


logger = structlog.get_logger()


class PromptRegistryError(Exception):
    """Base exception for prompt registry errors."""
    pass


class PromptAlreadyRegisteredError(PromptRegistryError):
    """Raised when attempting to register a prompt that already exists."""
    pass


class PromptRegistry:
    """
    Discover and manage prompt templates.

    Features:
    - Discover prompts in directories (recursive)
    - Register prompts programmatically (for plugins)
    - Get prompt by name
    - List prompts by category
    - Override prompts (replace existing definitions)

    Example:
        ```python
        registry = PromptRegistry(
            prompts_dir=Path("gao_dev/prompts"),
            config_loader=config_loader
        )

        # Discover all prompts
        registry.index_prompts()

        # Get prompt
        template = registry.get_prompt("prd")

        # List by category
        planning_prompts = registry.list_prompts(category="planning")

        # Register custom prompt (from plugin)
        registry.register_prompt(custom_template, allow_override=True)
        ```
    """

    def __init__(
        self,
        prompts_dir: Path,
        config_loader: Optional[ConfigLoader] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize prompt registry.

        Args:
            prompts_dir: Directory containing prompt YAML files
            config_loader: Optional config loader for reference resolution
            cache_enabled: Whether to enable caching in loader
        """
        self.prompts_dir = prompts_dir
        self.config_loader = config_loader
        self.cache_enabled = cache_enabled

        # Create prompt loader
        self.loader = PromptLoader(
            prompts_dir=prompts_dir,
            config_loader=config_loader,
            cache_enabled=cache_enabled
        )

        # Registry of prompts
        self._prompts: Dict[str, PromptTemplate] = {}
        self._indexed = False

    def index_prompts(self, rescan: bool = False) -> None:
        """
        Scan and index all prompts from the prompts directory.

        Recursively discovers all .yaml files in the prompts directory
        and attempts to load them as prompt templates.

        Args:
            rescan: If True, clear existing index and rescan
        """
        if rescan:
            self._prompts.clear()
            self.loader.clear_cache()
            self._indexed = False

        if self._indexed and not rescan:
            logger.debug("prompts_already_indexed")
            return

        logger.info("indexing_prompts", directory=str(self.prompts_dir))

        if not self.prompts_dir.exists():
            logger.warning("prompts_directory_not_found", directory=str(self.prompts_dir))
            self._indexed = True
            return

        # Find all YAML files
        prompt_files = list(self.prompts_dir.rglob("*.yaml"))
        logger.debug("found_prompt_files", count=len(prompt_files))

        for prompt_file in prompt_files:
            # Skip certain files
            if prompt_file.name in ["config.yaml", "defaults.yaml", "workflow.yaml"]:
                continue

            try:
                template = PromptTemplate.from_yaml(prompt_file)
                self._prompts[template.name] = template
                logger.debug("prompt_indexed", name=template.name, path=str(prompt_file))
            except Exception as e:
                logger.warning(
                    "prompt_load_failed",
                    path=str(prompt_file),
                    error=str(e)
                )

        self._indexed = True
        logger.info("prompts_indexed", count=len(self._prompts))

    def register_prompt(
        self,
        template: PromptTemplate,
        allow_override: bool = False
    ) -> None:
        """
        Register a prompt template programmatically.

        Useful for plugins to add custom prompts at runtime.

        Args:
            template: PromptTemplate to register
            allow_override: If True, allow replacing existing prompts

        Raises:
            PromptAlreadyRegisteredError: If prompt exists and override not allowed
        """
        if template.name in self._prompts and not allow_override:
            raise PromptAlreadyRegisteredError(
                f"Prompt '{template.name}' already registered. "
                f"Use allow_override=True to replace it."
            )

        self._prompts[template.name] = template
        logger.info(
            "prompt_registered",
            name=template.name,
            override=template.name in self._prompts
        )

    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name.

        Args:
            name: Prompt name

        Returns:
            PromptTemplate if found, None otherwise
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        return self._prompts.get(name)

    def list_prompts(
        self,
        category: Optional[str] = None,
        phase: Optional[int] = None
    ) -> List[PromptTemplate]:
        """
        List prompts, optionally filtered by category or phase.

        Args:
            category: Filter by metadata.category
            phase: Filter by metadata.phase

        Returns:
            List of PromptTemplate objects
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        prompts = list(self._prompts.values())

        # Filter by category
        if category:
            prompts = [
                p for p in prompts
                if p.metadata.get("category") == category
            ]

        # Filter by phase
        if phase is not None:
            prompts = [
                p for p in prompts
                if p.metadata.get("phase") == phase
            ]

        # Sort by name
        prompts.sort(key=lambda p: p.name)
        return prompts

    def prompt_exists(self, name: str) -> bool:
        """
        Check if prompt exists in registry.

        Args:
            name: Prompt name

        Returns:
            True if prompt exists
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        return name in self._prompts

    def get_all_prompts(self) -> Dict[str, PromptTemplate]:
        """
        Get all prompts as dictionary.

        Returns:
            Dictionary mapping prompt name to PromptTemplate
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        return self._prompts.copy()

    def override_prompt(self, template: PromptTemplate) -> None:
        """
        Override an existing prompt template.

        Convenience method for register_prompt with allow_override=True.

        Args:
            template: PromptTemplate to register (replaces existing)
        """
        self.register_prompt(template, allow_override=True)

    def unregister_prompt(self, name: str) -> bool:
        """
        Unregister a prompt by name.

        Args:
            name: Prompt name to remove

        Returns:
            True if prompt was removed, False if not found
        """
        if name in self._prompts:
            del self._prompts[name]
            logger.info("prompt_unregistered", name=name)
            return True
        return False

    def get_categories(self) -> List[str]:
        """
        Get list of all prompt categories.

        Returns:
            Sorted list of unique categories
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        categories = set()
        for prompt in self._prompts.values():
            category = prompt.metadata.get("category")
            if category:
                categories.add(category)

        return sorted(categories)

    def get_phases(self) -> List[int]:
        """
        Get list of all prompt phases.

        Returns:
            Sorted list of unique phases
        """
        # Ensure prompts are indexed
        if not self._indexed:
            self.index_prompts()

        phases = set()
        for prompt in self._prompts.values():
            phase = prompt.metadata.get("phase")
            if phase is not None:
                phases.add(phase)

        return sorted(phases)

    def clear(self) -> None:
        """Clear all registered prompts and cache."""
        self._prompts.clear()
        self.loader.clear_cache()
        self._indexed = False
        logger.info("prompt_registry_cleared")
