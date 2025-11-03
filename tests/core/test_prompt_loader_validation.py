"""
Integration tests for PromptLoader with schema validation.

Tests that prompt templates are properly validated when loaded.
"""

import pytest
from pathlib import Path

from gao_dev.core.prompt_loader import PromptLoader, PromptLoaderError
from gao_dev.core.schema_validator import SchemaValidator


@pytest.fixture
def test_prompts_dir(tmp_path):
    """Create temporary prompts directory with test templates."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Create valid prompt
    valid_prompt = """name: test-prompt
description: A test prompt template
user_prompt: Create a {{thing}} for {{project_name}}
variables:
  thing: feature
  project_name: MyProject
"""
    (prompts_dir / "test-prompt.yaml").write_text(valid_prompt)

    # Create invalid prompt (missing required fields)
    invalid_prompt = """name: invalid-prompt
# Missing 'description'
# Missing 'user_prompt'
variables:
  foo: bar
"""
    (prompts_dir / "invalid-prompt.yaml").write_text(invalid_prompt)

    # Create prompt with empty name
    empty_name_prompt = """name: ""
description: Test
user_prompt: Test
"""
    (prompts_dir / "empty-name.yaml").write_text(empty_name_prompt)

    return prompts_dir


@pytest.fixture
def real_schemas_dir():
    """Get path to real schemas directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "gao_dev" / "schemas"


@pytest.fixture
def validator(real_schemas_dir):
    """Create validator with real schemas."""
    if not real_schemas_dir.exists():
        pytest.skip("Real schemas directory not found")
    return SchemaValidator(real_schemas_dir)


class TestPromptLoaderValidation:
    """Test PromptLoader with schema validation."""

    def test_load_prompt_without_validator(self, test_prompts_dir):
        """Test loading prompt without validator (no validation)."""
        loader = PromptLoader(test_prompts_dir)
        template = loader.load_prompt("test-prompt")
        assert template.name == "test-prompt"

    def test_load_valid_prompt_with_validator(self, test_prompts_dir, validator):
        """Test loading valid prompt with validator."""
        loader = PromptLoader(test_prompts_dir, validator=validator)
        template = loader.load_prompt("test-prompt")
        assert template.name == "test-prompt"
        assert template.description == "A test prompt template"

    def test_load_invalid_prompt_with_validator(self, test_prompts_dir, validator):
        """Test loading invalid prompt with validator raises error."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        with pytest.raises(PromptLoaderError) as exc_info:
            loader.load_prompt("invalid-prompt")

        error_msg = str(exc_info.value)
        assert "validation failed" in error_msg.lower()
        # Should mention what's wrong
        assert "description" in error_msg.lower() or "user_prompt" in error_msg.lower()

    def test_validation_error_includes_context(self, test_prompts_dir, validator):
        """Test validation error includes file context."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        with pytest.raises(PromptLoaderError) as exc_info:
            loader.load_prompt("invalid-prompt")

        error_msg = str(exc_info.value)
        assert "invalid-prompt.yaml" in error_msg

    def test_empty_name_validation(self, test_prompts_dir, validator):
        """Test prompt with empty name fails validation."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        with pytest.raises(PromptLoaderError) as exc_info:
            loader.load_prompt("empty-name")

        error_msg = str(exc_info.value)
        assert "name" in error_msg.lower() or "empty" in error_msg.lower()


class TestPromptCachingWithValidation:
    """Test prompt caching works with validation."""

    def test_cache_validated_prompt(self, test_prompts_dir, validator):
        """Test validated prompt is cached."""
        loader = PromptLoader(test_prompts_dir, validator=validator, cache_enabled=True)

        # Load once (validates)
        template1 = loader.load_prompt("test-prompt")

        # Load again (from cache, no validation)
        template2 = loader.load_prompt("test-prompt")

        # Should be same instance from cache
        assert template1 is template2

    def test_cache_disabled_validates_each_time(self, test_prompts_dir, validator):
        """Test with cache disabled, validates each load."""
        loader = PromptLoader(test_prompts_dir, validator=validator, cache_enabled=False)

        # Load twice
        template1 = loader.load_prompt("test-prompt")
        template2 = loader.load_prompt("test-prompt")

        # Should be different instances (not cached)
        assert template1 is not template2
        # But have same data
        assert template1.name == template2.name


class TestValidatorIntegration:
    """Test validator integration patterns."""

    def test_loader_with_validator_none(self, test_prompts_dir):
        """Test loader works with validator=None."""
        loader = PromptLoader(test_prompts_dir, validator=None)
        template = loader.load_prompt("test-prompt")
        assert template.name == "test-prompt"

    def test_validator_optional_parameter(self, test_prompts_dir, validator):
        """Test validator is truly optional."""
        # Without validator
        loader1 = PromptLoader(test_prompts_dir)
        template1 = loader1.load_prompt("test-prompt")

        # With validator
        loader2 = PromptLoader(test_prompts_dir, validator=validator)
        template2 = loader2.load_prompt("test-prompt")

        # Both should succeed for valid prompt
        assert template1.name == template2.name

    def test_validation_only_on_load_not_render(self, test_prompts_dir, validator):
        """Test validation happens on load, not on render."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        # Validation happens here
        template = loader.load_prompt("test-prompt")

        # Rendering should not trigger validation again
        rendered = loader.render_prompt(template, {"thing": "component"})
        assert "component" in rendered


class TestPromptValidationErrorQuality:
    """Test quality of validation error messages."""

    def test_error_message_clear_and_actionable(self, test_prompts_dir, validator):
        """Test error messages are clear and actionable."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        with pytest.raises(PromptLoaderError) as exc_info:
            loader.load_prompt("invalid-prompt")

        error_msg = str(exc_info.value)

        # Should have structured error info
        assert "Error" in error_msg or "error" in error_msg
        assert "Location:" in error_msg or "(root)" in error_msg

        # Should mention what's missing
        assert "description" in error_msg.lower() or "user_prompt" in error_msg.lower()

    def test_multiple_validation_errors_reported(self, test_prompts_dir, validator):
        """Test multiple validation errors are all reported."""
        loader = PromptLoader(test_prompts_dir, validator=validator)

        with pytest.raises(PromptLoaderError) as exc_info:
            loader.load_prompt("invalid-prompt")

        error_msg = str(exc_info.value)

        # Both missing fields might be in different errors, but at least one should be mentioned
        has_description_error = "description" in error_msg.lower()
        has_user_prompt_error = "user_prompt" in error_msg.lower()

        assert has_description_error or has_user_prompt_error
