"""Tests for Brian's prompt loading and rendering.

Tests Story 10.2: Prompt Extraction - Brian's Complexity Analysis
"""

import pytest
from pathlib import Path

from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.config_loader import ConfigLoader


class TestBrianPromptLoading:
    """Test Brian prompt template loading."""

    @pytest.fixture
    def project_root(self):
        """Get project root."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def prompt_loader(self, project_root):
        """Create PromptLoader for testing."""
        prompts_dir = project_root / "gao_dev" / "prompts"
        config_loader = ConfigLoader(project_root)
        return PromptLoader(prompts_dir=prompts_dir, config_loader=config_loader)

    def test_brian_prompt_exists(self, project_root):
        """Test that Brian prompt template file exists."""
        prompt_file = project_root / "gao_dev" / "prompts" / "agents" / "brian_analysis.yaml"
        assert prompt_file.exists(), f"Brian prompt template not found at {prompt_file}"

    def test_scale_levels_config_exists(self, project_root):
        """Test that scale levels config file exists."""
        config_file = project_root / "gao_dev" / "config" / "scale_levels.yaml"
        assert config_file.exists(), f"Scale levels config not found at {config_file}"

    def test_analysis_schema_exists(self, project_root):
        """Test that analysis response schema exists."""
        schema_file = project_root / "gao_dev" / "schemas" / "analysis_response.json"
        assert schema_file.exists(), f"Analysis response schema not found at {schema_file}"

    def test_brian_prompt_loads(self, prompt_loader):
        """Test Brian prompt loads from YAML."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        assert template.name == "brian_complexity_analysis"
        assert template.description == "Analyze project complexity and recommend scale level"
        assert "{{user_request}}" in template.user_prompt
        assert "{{scale_level_definitions}}" in template.user_prompt
        assert "{{json_schema}}" in template.user_prompt
        assert template.max_tokens == 2048
        assert template.temperature == 0.7

    def test_brian_prompt_has_variables(self, prompt_loader):
        """Test Brian prompt has required variables."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        # Check all required variables are defined
        assert "user_request" in template.variables
        assert "brian_persona" in template.variables
        assert "scale_level_definitions" in template.variables
        assert "json_schema" in template.variables

    def test_brian_prompt_renders_basic(self, prompt_loader):
        """Test prompt renders with basic variables."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        # Render user prompt
        rendered = prompt_loader.render_prompt(
            template,
            variables={
                "user_request": "Build a todo app",
                "brian_persona": "You are Brian Thompson...",
            }
        )

        # Check that variables were substituted in user_prompt
        assert "Build a todo app" in rendered

        # Check that template variables are not present
        assert "{{user_request}}" not in rendered
        assert "{{brian_persona}}" not in rendered

        # Render system prompt to check persona
        system_rendered = prompt_loader.render_system_prompt(
            template,
            variables={
                "brian_persona": "You are Brian Thompson...",
            }
        )

        # Check that persona is in system prompt
        assert "You are Brian Thompson..." in system_rendered

    def test_brian_prompt_renders_with_references(self, prompt_loader):
        """Test prompt renders with @file: references."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        # This should load scale_levels.yaml and analysis_response.json
        rendered = prompt_loader.render_prompt(
            template,
            variables={
                "user_request": "Build a todo app",
                "brian_persona": "",
            }
        )

        # Check that file references were resolved
        assert "Level 0" in rendered or "level 0" in rendered.lower()
        assert "Level 4" in rendered or "level 4" in rendered.lower()

        # Check that JSON schema is included
        assert "scale_level" in rendered
        assert "project_type" in rendered
        assert "estimated_stories" in rendered

        # Ensure no unresolved references
        assert "{{" not in rendered
        assert "@file:" not in rendered
        assert "@config:" not in rendered

    def test_brian_prompt_system_prompt(self, prompt_loader):
        """Test system prompt renders correctly."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        system_prompt = prompt_loader.render_system_prompt(
            template,
            variables={
                "brian_persona": "Senior Engineering Manager with expertise...",
            }
        )

        assert system_prompt is not None
        assert "Brian Thompson" in system_prompt
        assert "Senior Engineering Manager with expertise..." in system_prompt

    def test_brian_prompt_empty_persona(self, prompt_loader):
        """Test prompt works with empty persona."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        rendered = prompt_loader.render_prompt(
            template,
            variables={
                "user_request": "Fix a bug",
                "brian_persona": "",
            }
        )

        assert "Fix a bug" in rendered
        assert "{{" not in rendered

    def test_brian_prompt_metadata(self, prompt_loader):
        """Test prompt has correct metadata."""
        template = prompt_loader.load_prompt("agents/brian_analysis")

        assert template.metadata.get("category") == "analysis"
        assert template.metadata.get("agent") == "brian"
        assert template.metadata.get("phase") == 0

    def test_scale_levels_content(self, project_root):
        """Test scale levels file has expected content."""
        config_file = project_root / "gao_dev" / "config" / "scale_levels.yaml"
        content = config_file.read_text(encoding="utf-8")

        # Check all levels are present
        assert "Level 0" in content
        assert "Level 1" in content
        assert "Level 2" in content
        assert "Level 3" in content
        assert "Level 4" in content

    def test_analysis_schema_valid_json(self, project_root):
        """Test analysis response schema is valid JSON."""
        import json

        schema_file = project_root / "gao_dev" / "schemas" / "analysis_response.json"
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Check required fields
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Check all required fields are present
        required_fields = [
            "scale_level",
            "project_type",
            "is_greenfield",
            "is_brownfield",
            "is_game_project",
            "estimated_stories",
            "estimated_epics",
            "technical_complexity",
            "domain_complexity",
            "confidence",
            "reasoning",
            "needs_clarification",
            "clarifying_questions"
        ]

        for field in required_fields:
            assert field in schema["properties"], f"Missing field: {field}"
            assert field in schema["required"], f"Field not marked as required: {field}"


class TestBrianPromptCaching:
    """Test prompt caching behavior."""

    @pytest.fixture
    def project_root(self):
        """Get project root."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def prompt_loader(self, project_root):
        """Create PromptLoader with caching enabled."""
        prompts_dir = project_root / "gao_dev" / "prompts"
        config_loader = ConfigLoader(project_root)
        return PromptLoader(
            prompts_dir=prompts_dir,
            config_loader=config_loader,
            cache_enabled=True
        )

    def test_prompt_caching(self, prompt_loader):
        """Test that prompts are cached."""
        # Load prompt twice
        template1 = prompt_loader.load_prompt("agents/brian_analysis")
        template2 = prompt_loader.load_prompt("agents/brian_analysis")

        # Should be same instance (cached)
        assert template1 is template2

    def test_cache_clear(self, prompt_loader):
        """Test cache clearing."""
        # Load prompt
        template1 = prompt_loader.load_prompt("agents/brian_analysis")

        # Clear cache
        prompt_loader.clear_cache()

        # Load again
        template2 = prompt_loader.load_prompt("agents/brian_analysis")

        # Should be different instances
        assert template1 is not template2
        # But should have same content
        assert template1.name == template2.name

    def test_no_cache_option(self, prompt_loader):
        """Test loading without cache."""
        # Load with cache disabled
        template1 = prompt_loader.load_prompt("agents/brian_analysis", use_cache=False)
        template2 = prompt_loader.load_prompt("agents/brian_analysis", use_cache=False)

        # Should be different instances
        assert template1 is not template2
        # But should have same content
        assert template1.name == template2.name
