"""
Meta-prompt engine that extends PromptLoader with reference resolution.

This module orchestrates all resolvers, handles automatic context injection,
supports nested references, and detects cycles.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog
import yaml
from jinja2 import Template

from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.models.prompt_template import PromptTemplate
from .resolver_registry import ReferenceResolverRegistry
from .exceptions import (
    CircularReferenceError,
    MaxDepthExceededError,
)

logger = structlog.get_logger(__name__)


class MetaPromptEngine:
    """
    Meta-prompt engine that extends PromptLoader with reference resolution.

    Composition over inheritance - wraps PromptLoader rather than extending it.
    Provides:
    - All reference types: @doc:, @checklist:, @query:, @context:, @config:, @file:
    - Automatic context injection per workflow
    - Nested reference resolution with cycle detection
    - Caching and performance optimization
    - Backward compatibility with Epic 10's PromptLoader

    Example:
        ```python
        engine = MetaPromptEngine(
            prompt_loader=PromptLoader(prompts_dir=Path("gao_dev/config/prompts")),
            resolver_registry=resolver_registry,
            auto_injection_config=Path("gao_dev/config/auto_injection.yaml")
        )

        # Load and render prompt with meta-prompts
        template = engine.load_prompt("tasks/implement_story")
        rendered = engine.render_prompt(
            template,
            variables={"epic": 3, "story": 1},
            workflow_name="implement_story"
        )
        ```
    """

    def __init__(
        self,
        prompt_loader: PromptLoader,
        resolver_registry: ReferenceResolverRegistry,
        auto_injection_config: Optional[Path] = None,
        max_depth: int = 3,
        enable_meta_prompts: bool = True,
    ):
        """
        Initialize meta-prompt engine.

        Args:
            prompt_loader: PromptLoader instance for template loading
            resolver_registry: Registry of all reference resolvers
            auto_injection_config: Path to auto-injection YAML config
            max_depth: Maximum nesting depth for references
            enable_meta_prompts: Feature flag for meta-prompt rendering
        """
        self.prompt_loader = prompt_loader
        self.resolver_registry = resolver_registry
        self.max_depth = max_depth
        self.enable_meta_prompts = enable_meta_prompts
        self.auto_injection = self._load_auto_injection_config(auto_injection_config)

        logger.info(
            "meta_prompt_engine_initialized",
            max_depth=max_depth,
            enable_meta_prompts=enable_meta_prompts,
            auto_injection_workflows=len(self.auto_injection),
        )

    def load_prompt(self, prompt_name: str, use_cache: bool = True) -> PromptTemplate:
        """
        Load prompt template (delegates to PromptLoader).

        Args:
            prompt_name: Name of the prompt (without .yaml extension)
            use_cache: Whether to use cached version if available

        Returns:
            PromptTemplate instance
        """
        return self.prompt_loader.load_prompt(prompt_name, use_cache)

    def render_prompt(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        workflow_name: Optional[str] = None,
    ) -> str:
        """
        Render prompt with meta-prompt support.

        Process:
        1. Add automatic context for workflow
        2. Render template with variables (Epic 10 logic)
        3. Resolve all meta-prompt references
        4. Return final rendered prompt

        Args:
            template: PromptTemplate to render
            variables: Dictionary of variable values
            workflow_name: Optional workflow name for auto-injection

        Returns:
            Rendered prompt string

        Raises:
            CircularReferenceError: If circular reference detected
            MaxDepthExceededError: If max nesting depth exceeded
        """
        try:
            # Step 1: Add automatic context injection
            if workflow_name and workflow_name in self.auto_injection:
                logger.debug(
                    "applying_auto_injection",
                    workflow=workflow_name,
                    injection_keys=list(self.auto_injection[workflow_name].keys()),
                )
                auto_vars = self._get_auto_injection_variables(workflow_name, variables)
                variables = {**variables, **auto_vars}

            # Step 2: Standard template rendering (Epic 10)
            rendered = self.prompt_loader.render_prompt(template, variables)

            # Step 3: Resolve meta-prompt references (if enabled)
            if self.enable_meta_prompts:
                final = self._resolve_references(rendered, variables, depth=0)
            else:
                final = rendered

            logger.info(
                "prompt_rendered",
                template=template.name,
                workflow=workflow_name,
                content_length=len(final),
            )
            return final

        except (CircularReferenceError, MaxDepthExceededError):
            # Re-raise these critical errors
            raise
        except Exception as e:
            # Fallback to standard rendering on error
            logger.error(
                "meta_prompt_rendering_failed",
                template=template.name,
                workflow=workflow_name,
                error=str(e),
            )
            # Fallback to Epic 10 rendering
            return self.prompt_loader.render_prompt(template, variables)

    def render_system_prompt(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        workflow_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        Render system prompt with meta-prompt support.

        Args:
            template: PromptTemplate to render
            variables: Dictionary of variable values
            workflow_name: Optional workflow name for auto-injection

        Returns:
            Rendered system prompt or None if not defined
        """
        if not template.system_prompt:
            return None

        try:
            # Step 1: Add automatic context injection
            if workflow_name and workflow_name in self.auto_injection:
                auto_vars = self._get_auto_injection_variables(workflow_name, variables)
                variables = {**variables, **auto_vars}

            # Step 2: Standard template rendering (Epic 10)
            rendered = self.prompt_loader.render_system_prompt(template, variables)

            if rendered is None:
                return None

            # Step 3: Resolve meta-prompt references (if enabled)
            if self.enable_meta_prompts:
                final = self._resolve_references(rendered, variables, depth=0)
            else:
                final = rendered

            return final

        except Exception as e:
            # Fallback to standard rendering on error
            logger.error(
                "system_prompt_rendering_failed",
                template=template.name,
                error=str(e),
            )
            return self.prompt_loader.render_system_prompt(template, variables)

    def _resolve_references(
        self, content: str, context: Dict[str, Any], depth: int = 0
    ) -> str:
        """
        Resolve all references in content.

        Supports nested references up to max_depth.

        Args:
            content: Content to resolve references in
            context: Context dict with variables for resolution
            depth: Current recursion depth

        Returns:
            Content with all references resolved

        Raises:
            MaxDepthExceededError: If max nesting depth exceeded
            CircularReferenceError: If circular reference detected
        """
        if depth > self.max_depth:
            raise MaxDepthExceededError(
                f"Maximum nesting depth ({self.max_depth}) exceeded. "
                "Possible circular reference."
            )

        # Find all references in content
        references = self._find_references(content)

        if not references:
            return content  # Base case: no references

        logger.debug(
            "resolving_references",
            count=len(references),
            depth=depth,
            references=references[:5],  # Log first 5
        )

        # Resolve each reference
        for ref_str in references:
            try:
                # Use registry to resolve (handles caching and nested resolution)
                resolved = self.resolver_registry.resolve(ref_str, context)

                # Replace reference with resolved content
                content = content.replace(ref_str, resolved)

                logger.debug(
                    "reference_resolved",
                    reference=ref_str,
                    resolved_length=len(resolved),
                    depth=depth,
                )

            except (CircularReferenceError, MaxDepthExceededError):
                # Re-raise these critical errors
                raise
            except Exception as e:
                # Log warning and replace with empty string
                logger.warning(
                    "reference_resolution_failed",
                    reference=ref_str,
                    error=str(e),
                    depth=depth,
                )
                # Replace with empty string and continue
                content = content.replace(ref_str, "")

        # Note: Nested resolution is handled by ReferenceResolverRegistry
        # We don't need to recursively call _resolve_references here

        return content

    def _find_references(self, content: str) -> list[str]:
        """
        Find all @{type}:{value} references in content.

        Returns list of reference strings (e.g., ["@doc:path/file.md", "@context:epic"])

        Args:
            content: Content to search for references

        Returns:
            List of reference strings found
        """
        import re

        # Match @type:value pattern
        # Type must start with letter or underscore, followed by alphanumerics/underscores
        # Value is everything until whitespace or newline
        pattern = r"@([a-zA-Z_][a-zA-Z0-9_]*):([^\s]+)"
        matches = re.findall(pattern, content)
        references = [f"@{ref_type}:{ref_value}" for ref_type, ref_value in matches]
        return references

    def _has_references(self, content: str) -> bool:
        """
        Check if content contains any references.

        Args:
            content: Content to check

        Returns:
            True if content contains references
        """
        return "@" in content and ":" in content

    def _get_auto_injection_variables(
        self, workflow_name: str, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get automatic injection variables for workflow.

        Example:
            workflow_name = "implement_story"
            -> Returns variables with auto-injected context

        Args:
            workflow_name: Name of the workflow
            variables: Current variables for context

        Returns:
            Dict of auto-injected variables
        """
        auto_vars = {}
        config = self.auto_injection[workflow_name]

        for key, reference in config.items():
            try:
                # Render reference with current variables (for {{epic}}, {{story}}, etc.)
                rendered_ref = self._render_template_string(reference, variables)

                # Resolve the reference
                resolved = self.resolver_registry.resolve(rendered_ref, variables)
                auto_vars[key] = resolved

                logger.debug(
                    "auto_injection_variable_resolved",
                    workflow=workflow_name,
                    key=key,
                    reference=rendered_ref,
                    resolved_length=len(resolved),
                )

            except Exception as e:
                # Log warning but don't fail entire render
                logger.warning(
                    "auto_injection_failed",
                    workflow=workflow_name,
                    key=key,
                    reference=reference,
                    error=str(e),
                )
                # Don't add this variable
                continue

        return auto_vars

    def _render_template_string(self, template_str: str, variables: Dict[str, Any]) -> str:
        """
        Render a template string with variables.

        Args:
            template_str: Template string with {{variable}} placeholders
            variables: Variables to substitute

        Returns:
            Rendered string
        """
        try:
            template = Template(template_str)
            return template.render(**variables)
        except Exception as e:
            logger.warning(
                "template_string_rendering_failed", template=template_str, error=str(e)
            )
            return template_str

    def _load_auto_injection_config(self, config_path: Optional[Path]) -> Dict[str, Dict[str, str]]:
        """
        Load automatic context injection configuration.

        Format (YAML):
            implement_story:
              story_context: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
              epic_context: "@context:epic_definition"
              architecture: "@context:architecture"
              testing_checklist: "@checklist:testing/unit-test-standards"

            create_story:
              epic_context: "@context:epic_definition"
              prd: "@context:prd"

        Args:
            config_path: Path to auto-injection YAML config

        Returns:
            Dict mapping workflow names to injection configs
        """
        if not config_path or not config_path.exists():
            logger.info("auto_injection_config_not_found", path=str(config_path))
            return {}

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            logger.info(
                "auto_injection_config_loaded",
                path=str(config_path),
                workflows=list(config.keys()),
            )
            return config

        except Exception as e:
            logger.error(
                "auto_injection_config_load_failed", path=str(config_path), error=str(e)
            )
            return {}

    def clear_cache(self) -> None:
        """Clear the prompt cache and resolver cache."""
        self.prompt_loader.clear_cache()
        self.resolver_registry.invalidate_cache()
        logger.debug("caches_cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        return {
            "resolver_cache": self.resolver_registry.get_cache_stats(),
            "prompt_loader_cache_size": len(self.prompt_loader._cache),
        }
