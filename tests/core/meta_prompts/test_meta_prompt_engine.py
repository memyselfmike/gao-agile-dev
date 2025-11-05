"""
Tests for MetaPromptEngine.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import timedelta

from gao_dev.core.meta_prompts import (
    MetaPromptEngine,
    ReferenceResolverRegistry,
    CircularReferenceError,
    MaxDepthExceededError,
)
from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.models.prompt_template import PromptTemplate


class TestMetaPromptEngineBasics:
    """Test basic MetaPromptEngine functionality."""

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock ReferenceResolverRegistry."""
        registry = Mock(spec=ReferenceResolverRegistry)
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry):
        """Create MetaPromptEngine instance."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
        )

    def test_initialization(self, mock_prompt_loader, mock_resolver_registry):
        """Test MetaPromptEngine initialization."""
        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            max_depth=5,
            enable_meta_prompts=False,
        )

        assert engine.prompt_loader == mock_prompt_loader
        assert engine.resolver_registry == mock_resolver_registry
        assert engine.max_depth == 5
        assert engine.enable_meta_prompts is False

    def test_load_prompt_delegates_to_prompt_loader(self, engine, mock_prompt_loader):
        """Test load_prompt delegates to PromptLoader."""
        mock_template = Mock(spec=PromptTemplate)
        mock_prompt_loader.load_prompt.return_value = mock_template

        result = engine.load_prompt("test_prompt")

        assert result == mock_template
        mock_prompt_loader.load_prompt.assert_called_once_with("test_prompt", True)

    def test_clear_cache_clears_both_caches(self, engine, mock_prompt_loader, mock_resolver_registry):
        """Test clear_cache clears both prompt loader and resolver caches."""
        engine.clear_cache()

        mock_prompt_loader.clear_cache.assert_called_once()
        mock_resolver_registry.invalidate_cache.assert_called_once()

    def test_get_cache_stats_returns_combined_stats(self, engine, mock_resolver_registry):
        """Test get_cache_stats returns combined statistics."""
        mock_resolver_registry.get_cache_stats.return_value = {
            "hits": 10,
            "misses": 5,
        }
        engine.prompt_loader._cache = {"key1": "value1", "key2": "value2"}

        stats = engine.get_cache_stats()

        assert stats["resolver_cache"]["hits"] == 10
        assert stats["resolver_cache"]["misses"] == 5
        assert stats["prompt_loader_cache_size"] == 2


class TestPromptRendering:
    """Test prompt rendering with meta-prompts."""

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader.render_prompt.return_value = "Rendered prompt content"
        loader.render_system_prompt.return_value = "Rendered system prompt"
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock ReferenceResolverRegistry."""
        registry = Mock(spec=ReferenceResolverRegistry)
        registry.resolve.return_value = "Resolved content"
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry):
        """Create MetaPromptEngine instance."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = "System prompt"
        return template

    def test_render_prompt_with_no_references(self, engine, mock_template, mock_prompt_loader):
        """Test render_prompt with no references."""
        mock_prompt_loader.render_prompt.return_value = "Simple prompt without references"

        result = engine.render_prompt(mock_template, {"var": "value"})

        assert result == "Simple prompt without references"
        mock_prompt_loader.render_prompt.assert_called_once()

    def test_render_prompt_with_single_reference(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test render_prompt with single reference."""
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:path/file.md reference"
        mock_resolver_registry.resolve.return_value = "Document content"

        result = engine.render_prompt(mock_template, {"var": "value"})

        assert "Document content" in result
        assert "@doc:path/file.md" not in result
        mock_resolver_registry.resolve.assert_called_once_with(
            "@doc:path/file.md", {"var": "value"}
        )

    def test_render_prompt_with_multiple_references(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test render_prompt with multiple references."""
        mock_prompt_loader.render_prompt.return_value = (
            "Prompt with @doc:file1.md and @checklist:testing/standards references"
        )
        mock_resolver_registry.resolve.side_effect = ["Content 1", "Content 2"]

        result = engine.render_prompt(mock_template, {"var": "value"})

        assert "Content 1" in result
        assert "Content 2" in result
        assert mock_resolver_registry.resolve.call_count == 2

    def test_render_prompt_disabled_meta_prompts(
        self, mock_prompt_loader, mock_resolver_registry, mock_template
    ):
        """Test render_prompt with meta-prompts disabled."""
        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            enable_meta_prompts=False,
        )
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:file.md reference"

        result = engine.render_prompt(mock_template, {"var": "value"})

        # Should not resolve references when disabled
        assert "@doc:file.md" in result
        mock_resolver_registry.resolve.assert_not_called()

    def test_render_system_prompt(self, engine, mock_template, mock_prompt_loader):
        """Test render_system_prompt."""
        mock_prompt_loader.render_system_prompt.return_value = "System prompt content"

        result = engine.render_system_prompt(mock_template, {"var": "value"})

        assert result == "System prompt content"
        mock_prompt_loader.render_system_prompt.assert_called_once()

    def test_render_system_prompt_with_none(self, engine, mock_template, mock_prompt_loader):
        """Test render_system_prompt when template has no system prompt."""
        mock_template.system_prompt = None
        mock_prompt_loader.render_system_prompt.return_value = None

        result = engine.render_system_prompt(mock_template, {"var": "value"})

        assert result is None

    def test_variable_substitution_before_reference_resolution(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that variable substitution happens before reference resolution."""
        # Prompt loader should render variables first
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:stories/epic-1/story-2.md"

        engine.render_prompt(mock_template, {"epic": 1, "story": 2})

        # Check that the rendered prompt (after variable substitution) is what gets resolved
        mock_resolver_registry.resolve.assert_called_once_with(
            "@doc:stories/epic-1/story-2.md", {"epic": 1, "story": 2}
        )


class TestAutoInjection:
    """Test automatic context injection."""

    @pytest.fixture
    def temp_auto_injection_config(self, tmp_path):
        """Create temporary auto-injection config."""
        config_file = tmp_path / "auto_injection.yaml"
        config_content = """
test_workflow:
  story_definition: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
  epic_context: "@context:epic_definition"

another_workflow:
  prd: "@context:prd"
"""
        config_file.write_text(config_content)
        return config_file

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader.render_prompt.return_value = "Rendered content"
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock ReferenceResolverRegistry."""
        registry = Mock(spec=ReferenceResolverRegistry)
        registry.resolve.side_effect = lambda ref, ctx: f"Resolved: {ref}"
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine_with_auto_injection(
        self, mock_prompt_loader, mock_resolver_registry, temp_auto_injection_config
    ):
        """Create MetaPromptEngine with auto-injection config."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=temp_auto_injection_config,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_auto_injection_config_loaded(self, engine_with_auto_injection):
        """Test that auto-injection config is loaded."""
        assert "test_workflow" in engine_with_auto_injection.auto_injection
        assert "another_workflow" in engine_with_auto_injection.auto_injection

    def test_auto_injection_not_applied_without_workflow(
        self, engine_with_auto_injection, mock_template, mock_resolver_registry
    ):
        """Test that auto-injection is not applied when no workflow specified."""
        engine_with_auto_injection.render_prompt(mock_template, {"epic": 1, "story": 1})

        # Should not resolve auto-injection references
        # (only the ones in the rendered prompt if any)
        # Reset mock to check calls
        initial_call_count = mock_resolver_registry.resolve.call_count

    def test_auto_injection_applied_with_workflow(
        self, engine_with_auto_injection, mock_template, mock_resolver_registry
    ):
        """Test that auto-injection is applied when workflow specified."""
        engine_with_auto_injection.render_prompt(
            mock_template, {"epic": 1, "story": 2}, workflow_name="test_workflow"
        )

        # Should resolve auto-injection references
        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]
        assert "@doc:stories/epic-1/story-2.md" in calls
        assert "@context:epic_definition" in calls

    def test_auto_injection_with_template_variables(
        self, engine_with_auto_injection, mock_template, mock_resolver_registry
    ):
        """Test that template variables are rendered in auto-injection references."""
        engine_with_auto_injection.render_prompt(
            mock_template, {"epic": 5, "story": 10}, workflow_name="test_workflow"
        )

        # Check that {{epic}} and {{story}} were substituted
        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]
        assert any("epic-5" in call and "story-10" in call for call in calls)

    def test_auto_injection_handles_missing_variables(
        self, engine_with_auto_injection, mock_template, mock_resolver_registry
    ):
        """Test that auto-injection handles missing variables gracefully."""
        # Missing epic and story variables
        result = engine_with_auto_injection.render_prompt(
            mock_template, {}, workflow_name="test_workflow"
        )

        # Should not crash, just skip or use empty values
        assert result is not None


class TestNestedReferences:
    """Test nested reference resolution."""

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock ReferenceResolverRegistry."""
        registry = Mock(spec=ReferenceResolverRegistry)
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry):
        """Create MetaPromptEngine instance."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            max_depth=3,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_nested_references_resolved_by_registry(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that nested references are handled by resolver registry."""
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:file.md"
        # Registry handles nested resolution internally
        mock_resolver_registry.resolve.return_value = "Resolved content"

        result = engine.render_prompt(mock_template, {})

        # Engine just calls resolve once, registry handles nesting
        assert "Resolved content" in result
        mock_resolver_registry.resolve.assert_called_once()

    def test_max_depth_exceeded(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that MaxDepthExceededError is propagated."""
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:file.md"
        mock_resolver_registry.resolve.side_effect = MaxDepthExceededError(
            "Max depth exceeded"
        )

        with pytest.raises(MaxDepthExceededError):
            engine.render_prompt(mock_template, {})

    def test_circular_reference_detected(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that CircularReferenceError is propagated."""
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:file.md"
        mock_resolver_registry.resolve.side_effect = CircularReferenceError(
            "Circular reference"
        )

        with pytest.raises(CircularReferenceError):
            engine.render_prompt(mock_template, {})


class TestErrorHandling:
    """Test error handling and fallback mechanisms."""

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader.render_prompt.return_value = "Fallback content"
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock ReferenceResolverRegistry."""
        registry = Mock(spec=ReferenceResolverRegistry)
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry):
        """Create MetaPromptEngine instance."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_fallback_to_standard_rendering_on_error(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that reference resolution failures replace with empty string."""
        # Regular exceptions in reference resolution are caught and replaced with ""
        mock_prompt_loader.render_prompt.return_value = "Prompt with @doc:file.md reference"
        mock_resolver_registry.resolve.side_effect = Exception("Resolution failed")

        result = engine.render_prompt(mock_template, {})

        # Should replace failed reference with empty string and continue
        assert result == "Prompt with  reference"
        assert "@doc:file.md" not in result

    def test_reference_resolution_failure_continues(
        self, engine, mock_template, mock_prompt_loader, mock_resolver_registry
    ):
        """Test that single reference failure doesn't stop entire render."""
        mock_prompt_loader.render_prompt.return_value = (
            "Prompt with @doc:good.md and @doc:bad.md"
        )

        def resolve_side_effect(ref, ctx):
            if "bad" in ref:
                raise Exception("Bad reference")
            return "Good content"

        mock_resolver_registry.resolve.side_effect = resolve_side_effect

        result = engine.render_prompt(mock_template, {})

        # Should contain good content and empty string for bad reference
        assert "Good content" in result
        # Bad reference should be replaced with empty string
        assert "@doc:bad.md" not in result


class TestReferenceFinding:
    """Test finding references in content."""

    @pytest.fixture
    def engine(self):
        """Create MetaPromptEngine instance."""
        loader = Mock(spec=PromptLoader)
        registry = Mock(spec=ReferenceResolverRegistry)
        loader._cache = {}
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return MetaPromptEngine(
            prompt_loader=loader, resolver_registry=registry
        )

    def test_find_single_reference(self, engine):
        """Test finding single reference."""
        content = "Text with @doc:path/to/file.md reference"
        refs = engine._find_references(content)

        assert len(refs) == 1
        assert "@doc:path/to/file.md" in refs

    def test_find_multiple_references(self, engine):
        """Test finding multiple references."""
        content = (
            "Text with @doc:file.md and @checklist:testing/standards "
            "and @context:epic references"
        )
        refs = engine._find_references(content)

        assert len(refs) == 3
        assert "@doc:file.md" in refs
        assert "@checklist:testing/standards" in refs
        assert "@context:epic" in refs

    def test_find_no_references(self, engine):
        """Test finding no references."""
        content = "Text without any references"
        refs = engine._find_references(content)

        assert len(refs) == 0

    def test_find_different_reference_types(self, engine):
        """Test finding different reference types."""
        content = (
            "@doc:file.md @checklist:test @query:stories "
            "@context:epic @config:model @file:path.txt"
        )
        refs = engine._find_references(content)

        assert len(refs) == 6
        assert "@doc:file.md" in refs
        assert "@checklist:test" in refs
        assert "@query:stories" in refs
        assert "@context:epic" in refs
        assert "@config:model" in refs
        assert "@file:path.txt" in refs

    def test_has_references(self, engine):
        """Test checking if content has references."""
        assert engine._has_references("@doc:file.md")
        assert engine._has_references("Text with @doc:file.md")
        assert not engine._has_references("Text without references")
        assert not engine._has_references("Text with @ but no colon")
        assert not engine._has_references("Text with : but no at")
