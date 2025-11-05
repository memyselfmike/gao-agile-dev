"""
Prompt loader with reference resolution and caching.

This module provides infrastructure for loading prompt templates from YAML files,
resolving file and config references, and caching for performance.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog

from .models.prompt_template import PromptTemplate
from .config_loader import ConfigLoader
from .schema_validator import SchemaValidator, SchemaValidationError


logger = structlog.get_logger()


class PromptLoaderError(Exception):
    """Base exception for prompt loader errors."""

    pass


class PromptNotFoundError(PromptLoaderError):
    """Raised when a prompt template cannot be found."""

    pass


class ReferenceResolutionError(PromptLoaderError):
    """Raised when a reference (@file: or @config:) cannot be resolved."""

    pass


class PromptLoader:
    """
    Load and render prompt templates with reference resolution.

    Features:
    - Load YAML prompt templates
    - Render templates with {{variable}} substitution
    - Resolve @file:path references
    - Resolve @config:key references
    - Cache loaded prompts for performance

    Example:
        ```python
        loader = PromptLoader(
            prompts_dir=Path("gao_dev/prompts"),
            config_loader=config_loader
        )

        # Load template
        template = loader.load_prompt("prd")

        # Render with variables
        rendered = loader.render_prompt(template, {
            "project_name": "MyApp",
            "context": "@file:docs/context.md"
        })
        ```
    """

    def __init__(
        self,
        prompts_dir: Path,
        config_loader: Optional[ConfigLoader] = None,
        cache_enabled: bool = True,
        validator: Optional[SchemaValidator] = None,
    ):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt YAML files
            config_loader: Optional config loader for @config: references
            cache_enabled: Whether to cache loaded prompts
            validator: Optional SchemaValidator for prompt validation
        """
        self.prompts_dir = prompts_dir
        self.config_loader = config_loader
        self.cache_enabled = cache_enabled
        self.validator = validator
        self._cache: Dict[str, PromptTemplate] = {}

    def load_prompt(self, prompt_name: str, use_cache: bool = True) -> PromptTemplate:
        """
        Load prompt template by name.

        Args:
            prompt_name: Name of the prompt (without .yaml extension)
            use_cache: Whether to use cached version if available

        Returns:
            PromptTemplate instance

        Raises:
            PromptNotFoundError: If prompt file not found
            ValueError: If prompt YAML is invalid
        """
        # Check cache first
        if use_cache and self.cache_enabled and prompt_name in self._cache:
            logger.debug("prompt_cache_hit", prompt_name=prompt_name)
            return self._cache[prompt_name]

        # Find prompt file
        prompt_file = self._find_prompt_file(prompt_name)
        if not prompt_file:
            raise PromptNotFoundError(f"Prompt '{prompt_name}' not found in {self.prompts_dir}")

        # Load template
        logger.debug("loading_prompt", prompt_name=prompt_name, path=str(prompt_file))
        try:
            # Load YAML first for validation
            import yaml

            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_data = yaml.safe_load(f)

            # Validate against schema if validator provided
            if self.validator and prompt_data:
                try:
                    self.validator.validate_or_raise(
                        prompt_data, "prompt", context=str(prompt_file.name)
                    )
                except SchemaValidationError as e:
                    logger.error(
                        "prompt_schema_validation_failed",
                        prompt_name=prompt_name,
                        path=str(prompt_file),
                        errors=e.result.errors,
                    )
                    raise PromptLoaderError(
                        f"Prompt validation failed for '{prompt_name}':\n{e}"
                    ) from e

            # Create template from validated data
            template = PromptTemplate.from_yaml(prompt_file)
        except PromptLoaderError:
            raise
        except Exception as e:
            logger.error("prompt_load_failed", prompt_name=prompt_name, error=str(e))
            raise

        # Cache if enabled
        if self.cache_enabled:
            self._cache[prompt_name] = template

        return template

    def render_prompt(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        """
        Render prompt template with variable substitution and reference resolution.

        Resolves references in this order:
        1. Merge template defaults with user variables
        2. Resolve @file:path references
        3. Resolve @config:key references
        4. Perform {{mustache}} substitution

        Args:
            template: PromptTemplate to render
            variables: Dictionary of variable values

        Returns:
            Rendered prompt string

        Raises:
            ReferenceResolutionError: If a reference cannot be resolved
        """
        # Resolve references first
        resolved = self._resolve_references(template.variables, variables)

        # Render with resolved variables
        return template.render(resolved)

    def render_system_prompt(
        self, template: PromptTemplate, variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Render system prompt with variable substitution and reference resolution.

        Args:
            template: PromptTemplate to render
            variables: Dictionary of variable values

        Returns:
            Rendered system prompt or None if not defined
        """
        if not template.system_prompt:
            return None

        # Resolve references first
        resolved = self._resolve_references(template.variables, variables)

        # Render with resolved variables
        return template.render_system_prompt(resolved)

    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()
        logger.debug("prompt_cache_cleared")

    def _find_prompt_file(self, prompt_name: str) -> Optional[Path]:
        """
        Find prompt YAML file by name.

        Searches for:
        1. {prompt_name}.yaml
        2. {prompt_name}/prompt.yaml
        3. {prompt_name}/template.yaml

        Args:
            prompt_name: Name of the prompt

        Returns:
            Path to prompt file or None if not found
        """
        # Try direct file
        direct_file = self.prompts_dir / f"{prompt_name}.yaml"
        if direct_file.exists():
            return direct_file

        # Try subdirectory with prompt.yaml
        subdir_prompt = self.prompts_dir / prompt_name / "prompt.yaml"
        if subdir_prompt.exists():
            return subdir_prompt

        # Try subdirectory with template.yaml
        subdir_template = self.prompts_dir / prompt_name / "template.yaml"
        if subdir_template.exists():
            return subdir_template

        return None

    def _resolve_references(
        self, template_vars: Dict[str, Any], user_vars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve @file: and @config: references.

        Args:
            template_vars: Variables from template defaults
            user_vars: Variables from user

        Returns:
            Dictionary with resolved references

        Raises:
            ReferenceResolutionError: If a reference cannot be resolved
        """
        # Merge variables (user overrides template)
        resolved = {**template_vars, **user_vars}

        # Resolve all references
        for key, value in list(resolved.items()):
            if isinstance(value, str):
                if value.startswith("@file:"):
                    # File reference
                    file_path = value[6:]  # Remove @file: prefix
                    resolved[key] = self._load_file(file_path)
                elif value.startswith("@config:"):
                    # Config reference
                    config_key = value[8:]  # Remove @config: prefix
                    resolved[key] = self._load_config(config_key)

        return resolved

    def _load_file(self, file_path: str) -> str:
        """
        Load file contents from @file: reference.

        Supports:
        - Absolute paths
        - Relative paths (relative to prompts_dir or project root)

        Args:
            file_path: Path to file

        Returns:
            File contents as string

        Raises:
            ReferenceResolutionError: If file cannot be loaded
        """
        path = Path(file_path)

        # Try as absolute path
        if path.is_absolute() and path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception as e:
                raise ReferenceResolutionError(f"Failed to read file {path}: {e}")

        # Try relative to prompts directory
        prompts_relative = self.prompts_dir / path
        if prompts_relative.exists():
            try:
                return prompts_relative.read_text(encoding="utf-8")
            except Exception as e:
                raise ReferenceResolutionError(f"Failed to read file {prompts_relative}: {e}")

        # Try relative to config loader's project root
        if self.config_loader:
            project_relative = self.config_loader.project_root / path
            if project_relative.exists():
                try:
                    return project_relative.read_text(encoding="utf-8")
                except Exception as e:
                    raise ReferenceResolutionError(f"Failed to read file {project_relative}: {e}")

        raise ReferenceResolutionError(
            f"File not found: {file_path} "
            f"(searched in: absolute, {self.prompts_dir}, "
            f"{self.config_loader.project_root if self.config_loader else 'N/A'})"
        )

    def _load_config(self, config_key: str) -> Any:
        """
        Load value from @config: reference.

        Args:
            config_key: Configuration key (e.g., "claude_model")

        Returns:
            Configuration value

        Raises:
            ReferenceResolutionError: If config loader not available or key not found
        """
        if not self.config_loader:
            raise ReferenceResolutionError(
                f"Cannot resolve @config:{config_key} - no config loader provided"
            )

        value = self.config_loader.get(config_key)
        if value is None:
            raise ReferenceResolutionError(f"Config key not found: {config_key}")

        return value
