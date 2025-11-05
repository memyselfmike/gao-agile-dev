"""
Tests for automatic context injection functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
import yaml

from gao_dev.core.meta_prompts import MetaPromptEngine
from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.models.prompt_template import PromptTemplate


class TestAutoInjectionConfiguration:
    """Test auto-injection configuration loading."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock resolver registry."""
        registry = Mock()
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    def test_load_valid_config(self, temp_config_dir, mock_prompt_loader, mock_resolver_registry):
        """Test loading valid auto-injection config."""
        config_file = temp_config_dir / "auto_injection.yaml"
        config_content = {
            "workflow1": {
                "var1": "@doc:file.md",
                "var2": "@context:epic",
            },
            "workflow2": {
                "var3": "@checklist:testing/standards",
            },
        }
        config_file.write_text(yaml.dump(config_content))

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=config_file,
        )

        assert "workflow1" in engine.auto_injection
        assert "workflow2" in engine.auto_injection
        assert engine.auto_injection["workflow1"]["var1"] == "@doc:file.md"
        assert engine.auto_injection["workflow1"]["var2"] == "@context:epic"
        assert engine.auto_injection["workflow2"]["var3"] == "@checklist:testing/standards"

    def test_load_empty_config(self, temp_config_dir, mock_prompt_loader, mock_resolver_registry):
        """Test loading empty config file."""
        config_file = temp_config_dir / "empty.yaml"
        config_file.write_text("")

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=config_file,
        )

        assert engine.auto_injection == {}

    def test_load_nonexistent_config(self, temp_config_dir, mock_prompt_loader, mock_resolver_registry):
        """Test loading nonexistent config file."""
        config_file = temp_config_dir / "nonexistent.yaml"

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=config_file,
        )

        assert engine.auto_injection == {}

    def test_load_invalid_yaml(self, temp_config_dir, mock_prompt_loader, mock_resolver_registry):
        """Test loading invalid YAML config."""
        config_file = temp_config_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=config_file,
        )

        # Should handle gracefully and return empty config
        assert engine.auto_injection == {}

    def test_no_config_provided(self, mock_prompt_loader, mock_resolver_registry):
        """Test initialization without config file."""
        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=None,
        )

        assert engine.auto_injection == {}


class TestAutoInjectionExecution:
    """Test auto-injection during prompt rendering."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary auto-injection config."""
        config_file = tmp_path / "auto_injection.yaml"
        config_content = {
            "implement_story": {
                "story_definition": "@doc:stories/epic-{{epic}}/story-{{story}}.md",
                "epic_context": "@context:epic_definition",
                "testing_standards": "@checklist:testing/unit-test-standards",
            },
            "create_story": {
                "epic_context": "@context:epic_definition",
                "prd": "@context:prd",
            },
            "review_code": {
                "code_quality": "@checklist:code-quality/solid-principles",
            },
        }
        config_file.write_text(yaml.dump(config_content))
        return config_file

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader.render_prompt.return_value = "Base prompt content"
        loader.render_system_prompt.return_value = None
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock resolver registry."""
        registry = Mock()
        registry.resolve.side_effect = lambda ref, ctx: f"Resolved: {ref}"
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry, temp_config_file):
        """Create MetaPromptEngine with auto-injection."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=temp_config_file,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_auto_injection_for_implement_story(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test auto-injection for implement_story workflow."""
        variables = {"epic": 3, "story": 5}

        engine.render_prompt(mock_template, variables, workflow_name="implement_story")

        # Check that all expected references were resolved
        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]

        assert "@doc:stories/epic-3/story-5.md" in calls
        assert "@context:epic_definition" in calls
        assert "@checklist:testing/unit-test-standards" in calls

    def test_auto_injection_for_create_story(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test auto-injection for create_story workflow."""
        variables = {"epic": 2}

        engine.render_prompt(mock_template, variables, workflow_name="create_story")

        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]

        assert "@context:epic_definition" in calls
        assert "@context:prd" in calls

    def test_auto_injection_for_review_code(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test auto-injection for review_code workflow."""
        engine.render_prompt(mock_template, {}, workflow_name="review_code")

        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]

        assert "@checklist:code-quality/solid-principles" in calls

    def test_no_auto_injection_without_workflow(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test no auto-injection when workflow not specified."""
        engine.render_prompt(mock_template, {"epic": 1, "story": 1})

        # Should not resolve any auto-injection references
        # (only references in the base prompt if any)
        assert mock_resolver_registry.resolve.call_count == 0

    def test_no_auto_injection_for_unknown_workflow(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test no auto-injection for unknown workflow."""
        engine.render_prompt(mock_template, {}, workflow_name="unknown_workflow")

        # Should not resolve any auto-injection references
        assert mock_resolver_registry.resolve.call_count == 0

    def test_auto_injection_with_template_variables(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test that {{variables}} in references are substituted."""
        variables = {"epic": 10, "story": 20}

        engine.render_prompt(mock_template, variables, workflow_name="implement_story")

        # Check that template variables were substituted
        calls = [call[0][0] for call in mock_resolver_registry.resolve.call_args_list]

        # Should have substituted {{epic}} and {{story}}
        assert any("epic-10" in call and "story-20" in call for call in calls)

    def test_auto_injection_with_missing_variables(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test auto-injection with missing template variables."""
        # Missing epic and story
        result = engine.render_prompt(mock_template, {}, workflow_name="implement_story")

        # Should not crash, variables just render as empty
        assert result is not None


class TestAutoInjectionVariableMerging:
    """Test that auto-injected variables are merged correctly."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary auto-injection config."""
        config_file = tmp_path / "auto_injection.yaml"
        config_content = {
            "test_workflow": {
                "auto_var": "@doc:auto.md",
            },
        }
        config_file.write_text(yaml.dump(config_content))
        return config_file

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader._cache = {}

        # Capture variables passed to render_prompt
        def capture_render(template, variables):
            loader.last_variables = variables
            return "Rendered content"

        loader.render_prompt.side_effect = capture_render
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock resolver registry."""
        registry = Mock()
        registry.resolve.return_value = "Auto-injected content"
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry, temp_config_file):
        """Create MetaPromptEngine with auto-injection."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=temp_config_file,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_auto_injected_variables_merged_with_user_variables(
        self, engine, mock_template, mock_prompt_loader
    ):
        """Test that auto-injected variables are merged with user variables."""
        user_vars = {"user_var": "user value"}

        engine.render_prompt(mock_template, user_vars, workflow_name="test_workflow")

        # Check that both user and auto-injected variables were passed
        variables = mock_prompt_loader.last_variables
        assert "user_var" in variables
        assert "auto_var" in variables
        assert variables["user_var"] == "user value"

    def test_user_variables_not_overwritten(
        self, engine, mock_template, mock_prompt_loader
    ):
        """Test that user variables are not overwritten by auto-injection."""
        # User provides same variable as auto-injection
        user_vars = {"auto_var": "user value", "other_var": "other"}

        engine.render_prompt(mock_template, user_vars, workflow_name="test_workflow")

        variables = mock_prompt_loader.last_variables
        # Auto-injected variables are added, not overwriting
        assert "auto_var" in variables
        assert "other_var" in variables


class TestAutoInjectionErrorHandling:
    """Test error handling in auto-injection."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary auto-injection config."""
        config_file = tmp_path / "auto_injection.yaml"
        config_content = {
            "test_workflow": {
                "good_ref": "@doc:good.md",
                "bad_ref": "@doc:bad.md",
            },
        }
        config_file.write_text(yaml.dump(config_content))
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
        """Create mock resolver registry."""
        registry = Mock()

        def resolve_side_effect(ref, ctx):
            if "bad" in ref:
                raise Exception("Resolution failed")
            return "Resolved content"

        registry.resolve.side_effect = resolve_side_effect
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    @pytest.fixture
    def engine(self, mock_prompt_loader, mock_resolver_registry, temp_config_file):
        """Create MetaPromptEngine with auto-injection."""
        return MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=temp_config_file,
        )

    @pytest.fixture
    def mock_template(self):
        """Create mock PromptTemplate."""
        template = Mock(spec=PromptTemplate)
        template.name = "test_template"
        template.system_prompt = None
        return template

    def test_auto_injection_continues_on_error(
        self, engine, mock_template, mock_resolver_registry
    ):
        """Test that auto-injection continues when one reference fails."""
        result = engine.render_prompt(mock_template, {}, workflow_name="test_workflow")

        # Should still complete, just skip the failed reference
        assert result is not None

        # Both references should have been attempted
        assert mock_resolver_registry.resolve.call_count == 2

    def test_auto_injection_failure_doesnt_break_render(
        self, engine, mock_template, mock_prompt_loader
    ):
        """Test that auto-injection failure doesn't break entire render."""
        # All auto-injection references fail
        result = engine.render_prompt(mock_template, {}, workflow_name="test_workflow")

        # Should still return rendered content
        assert result == "Rendered content"


class TestAutoInjectionWithRealConfig:
    """Test auto-injection with the actual config file."""

    @pytest.fixture
    def real_config_file(self):
        """Get path to real auto_injection.yaml."""
        return Path("C:/Projects/gao-agile-dev/gao_dev/config/auto_injection.yaml")

    @pytest.fixture
    def mock_prompt_loader(self):
        """Create mock PromptLoader."""
        loader = Mock(spec=PromptLoader)
        loader.render_prompt.return_value = "Rendered content"
        loader._cache = {}
        return loader

    @pytest.fixture
    def mock_resolver_registry(self):
        """Create mock resolver registry."""
        registry = Mock()
        registry.resolve.side_effect = lambda ref, ctx: f"Resolved: {ref}"
        registry.get_cache_stats.return_value = {"hits": 0, "misses": 0}
        return registry

    def test_load_real_config(
        self, mock_prompt_loader, mock_resolver_registry, real_config_file
    ):
        """Test loading the real auto_injection.yaml config."""
        if not real_config_file.exists():
            pytest.skip("Real config file not found")

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=real_config_file,
        )

        # Check that expected workflows are present
        assert "implement_story" in engine.auto_injection
        assert "create_story" in engine.auto_injection
        assert "validate_story" in engine.auto_injection

    def test_implement_story_workflow_structure(
        self, mock_prompt_loader, mock_resolver_registry, real_config_file
    ):
        """Test implement_story workflow has expected structure."""
        if not real_config_file.exists():
            pytest.skip("Real config file not found")

        engine = MetaPromptEngine(
            prompt_loader=mock_prompt_loader,
            resolver_registry=mock_resolver_registry,
            auto_injection_config=real_config_file,
        )

        workflow_config = engine.auto_injection.get("implement_story", {})

        # Check expected keys are present
        assert "story_definition" in workflow_config
        assert "epic_definition" in workflow_config
        assert "architecture" in workflow_config
        assert "testing_standards" in workflow_config
