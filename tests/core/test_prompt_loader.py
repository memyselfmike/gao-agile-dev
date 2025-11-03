"""Tests for PromptLoader."""

import pytest
from pathlib import Path

from gao_dev.core.prompt_loader import (
    PromptLoader,
    PromptNotFoundError,
    ReferenceResolutionError
)
from gao_dev.core.models.prompt_template import PromptTemplate
from gao_dev.core.config_loader import ConfigLoader


@pytest.fixture
def prompts_dir(tmp_path):
    """Create temporary prompts directory with test prompts."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    # Create a simple prompt
    simple = prompts / "simple.yaml"
    simple.write_text("""
name: simple
description: Simple prompt
user_prompt: Hello {{name}}
variables:
  name: World
""", encoding="utf-8")

    # Create a prompt in subdirectory
    subdir = prompts / "nested"
    subdir.mkdir()
    nested = subdir / "prompt.yaml"
    nested.write_text("""
name: nested
description: Nested prompt
user_prompt: Nested {{value}}
variables:
  value: test
""", encoding="utf-8")

    # Create test file for @file: references
    test_file = prompts / "context.txt"
    test_file.write_text("This is test context", encoding="utf-8")

    return prompts


@pytest.fixture
def config_loader(tmp_path):
    """Create config loader for testing."""
    config_file = tmp_path / "gao-dev.yaml"
    config_file.write_text("""
test_key: test_value
claude_model: claude-3
""", encoding="utf-8")
    return ConfigLoader(tmp_path)


def test_prompt_loader_creation(prompts_dir):
    """Test basic prompt loader creation."""
    loader = PromptLoader(prompts_dir)

    assert loader.prompts_dir == prompts_dir
    assert loader.cache_enabled is True


def test_load_simple_prompt(prompts_dir):
    """Test loading a simple prompt."""
    loader = PromptLoader(prompts_dir)

    template = loader.load_prompt("simple")

    assert template.name == "simple"
    assert template.description == "Simple prompt"
    assert template.user_prompt == "Hello {{name}}"


def test_load_nested_prompt(prompts_dir):
    """Test loading prompt from subdirectory."""
    loader = PromptLoader(prompts_dir)

    template = loader.load_prompt("nested")

    assert template.name == "nested"
    assert template.description == "Nested prompt"


def test_load_nonexistent_prompt(prompts_dir):
    """Test loading non-existent prompt."""
    loader = PromptLoader(prompts_dir)

    with pytest.raises(PromptNotFoundError, match="not found"):
        loader.load_prompt("nonexistent")


def test_prompt_caching(prompts_dir):
    """Test that prompts are cached."""
    loader = PromptLoader(prompts_dir, cache_enabled=True)

    # Load twice
    template1 = loader.load_prompt("simple")
    template2 = loader.load_prompt("simple")

    # Should be same object (cached)
    assert template1 is template2


def test_cache_disabled(prompts_dir):
    """Test loading with cache disabled."""
    loader = PromptLoader(prompts_dir, cache_enabled=False)

    # Load twice
    template1 = loader.load_prompt("simple")
    template2 = loader.load_prompt("simple")

    # Should be different objects (not cached)
    assert template1 is not template2


def test_cache_bypass(prompts_dir):
    """Test bypassing cache with use_cache=False."""
    loader = PromptLoader(prompts_dir, cache_enabled=True)

    # Load with caching
    template1 = loader.load_prompt("simple")

    # Load bypassing cache
    template2 = loader.load_prompt("simple", use_cache=False)

    # First is cached, second is fresh load
    assert template1 is not template2


def test_clear_cache(prompts_dir):
    """Test clearing the cache."""
    loader = PromptLoader(prompts_dir)

    # Load and cache
    template1 = loader.load_prompt("simple")

    # Clear cache
    loader.clear_cache()

    # Load again
    template2 = loader.load_prompt("simple")

    # Should be different objects
    assert template1 is not template2


def test_render_prompt_basic(prompts_dir):
    """Test basic prompt rendering."""
    loader = PromptLoader(prompts_dir)
    template = loader.load_prompt("simple")

    rendered = loader.render_prompt(template, {"name": "Alice"})

    assert rendered == "Hello Alice"


def test_render_with_template_defaults(prompts_dir):
    """Test rendering with template default values."""
    loader = PromptLoader(prompts_dir)
    template = loader.load_prompt("simple")

    # Don't provide name, should use default
    rendered = loader.render_prompt(template, {})

    assert rendered == "Hello World"


def test_file_reference_resolution(prompts_dir):
    """Test @file: reference resolution."""
    loader = PromptLoader(prompts_dir)

    # Create template with file reference
    template = PromptTemplate(
        name="with_file",
        description="Prompt with file ref",
        system_prompt=None,
        user_prompt="Context: {{context}}",
        variables={"context": "@file:context.txt"}
    )

    rendered = loader.render_prompt(template, {})

    assert rendered == "Context: This is test context"


def test_file_reference_absolute_path(prompts_dir, tmp_path):
    """Test @file: with absolute path."""
    loader = PromptLoader(prompts_dir)

    # Create file outside prompts dir
    external_file = tmp_path / "external.txt"
    external_file.write_text("External content", encoding="utf-8")

    template = PromptTemplate(
        name="with_abs_file",
        description="Prompt with absolute file ref",
        system_prompt=None,
        user_prompt="Content: {{content}}",
        variables={"content": f"@file:{external_file}"}
    )

    rendered = loader.render_prompt(template, {})

    assert rendered == "Content: External content"


def test_file_reference_not_found(prompts_dir):
    """Test @file: reference to non-existent file."""
    loader = PromptLoader(prompts_dir)

    template = PromptTemplate(
        name="bad_file",
        description="Prompt with bad file ref",
        system_prompt=None,
        user_prompt="Content: {{content}}",
        variables={"content": "@file:nonexistent.txt"}
    )

    with pytest.raises(ReferenceResolutionError, match="File not found"):
        loader.render_prompt(template, {})


def test_config_reference_resolution(prompts_dir, config_loader):
    """Test @config: reference resolution."""
    loader = PromptLoader(prompts_dir, config_loader=config_loader)

    template = PromptTemplate(
        name="with_config",
        description="Prompt with config ref",
        system_prompt=None,
        user_prompt="Model: {{model}}",
        variables={"model": "@config:claude_model"}
    )

    rendered = loader.render_prompt(template, {})

    assert rendered == "Model: claude-3"


def test_config_reference_no_loader(prompts_dir):
    """Test @config: reference without config loader."""
    loader = PromptLoader(prompts_dir, config_loader=None)

    template = PromptTemplate(
        name="with_config",
        description="Prompt with config ref",
        system_prompt=None,
        user_prompt="Model: {{model}}",
        variables={"model": "@config:claude_model"}
    )

    with pytest.raises(ReferenceResolutionError, match="no config loader"):
        loader.render_prompt(template, {})


def test_config_reference_key_not_found(prompts_dir, config_loader):
    """Test @config: reference to non-existent key."""
    loader = PromptLoader(prompts_dir, config_loader=config_loader)

    template = PromptTemplate(
        name="bad_config",
        description="Prompt with bad config ref",
        system_prompt=None,
        user_prompt="Value: {{value}}",
        variables={"value": "@config:nonexistent_key"}
    )

    with pytest.raises(ReferenceResolutionError, match="Config key not found"):
        loader.render_prompt(template, {})


def test_mixed_references(prompts_dir, config_loader):
    """Test mixing @file: and @config: references."""
    loader = PromptLoader(prompts_dir, config_loader=config_loader)

    template = PromptTemplate(
        name="mixed",
        description="Prompt with mixed refs",
        system_prompt=None,
        user_prompt="Context: {{context}}, Model: {{model}}",
        variables={
            "context": "@file:context.txt",
            "model": "@config:claude_model"
        }
    )

    rendered = loader.render_prompt(template, {})

    assert rendered == "Context: This is test context, Model: claude-3"


def test_user_vars_override_references(prompts_dir):
    """Test that user variables override file references."""
    loader = PromptLoader(prompts_dir)

    template = PromptTemplate(
        name="override",
        description="Test override",
        system_prompt=None,
        user_prompt="Content: {{content}}",
        variables={"content": "@file:context.txt"}
    )

    # Provide explicit value (should override file reference)
    rendered = loader.render_prompt(template, {"content": "User value"})

    assert rendered == "Content: User value"


def test_render_system_prompt(prompts_dir):
    """Test rendering system prompt."""
    loader = PromptLoader(prompts_dir)

    template = PromptTemplate(
        name="with_system",
        description="Prompt with system",
        system_prompt="You are {{role}}",
        user_prompt="Do {{task}}",
        variables={"role": "assistant", "task": "something"}
    )

    system = loader.render_system_prompt(template, {"role": "developer"})
    assert system == "You are developer"


def test_render_system_prompt_none(prompts_dir):
    """Test rendering when system prompt is None."""
    loader = PromptLoader(prompts_dir)

    template = PromptTemplate(
        name="no_system",
        description="Prompt without system",
        system_prompt=None,
        user_prompt="Hello",
        variables={}
    )

    system = loader.render_system_prompt(template, {})
    assert system is None


def test_file_reference_relative_to_project(prompts_dir, tmp_path):
    """Test @file: relative to project root."""
    # Create config loader with project root
    config_file = tmp_path / "gao-dev.yaml"
    config_file.write_text("test: value", encoding="utf-8")
    config_loader = ConfigLoader(tmp_path)

    # Create file in project root
    project_file = tmp_path / "project_file.txt"
    project_file.write_text("Project content", encoding="utf-8")

    loader = PromptLoader(prompts_dir, config_loader=config_loader)

    template = PromptTemplate(
        name="project_file",
        description="File from project",
        system_prompt=None,
        user_prompt="Content: {{content}}",
        variables={"content": "@file:project_file.txt"}
    )

    rendered = loader.render_prompt(template, {})
    assert rendered == "Content: Project content"


def test_find_prompt_variations(prompts_dir):
    """Test finding prompts with different naming conventions."""
    loader = PromptLoader(prompts_dir)

    # Direct file: simple.yaml
    assert loader._find_prompt_file("simple") == prompts_dir / "simple.yaml"

    # Subdirectory with prompt.yaml
    assert loader._find_prompt_file("nested") == prompts_dir / "nested" / "prompt.yaml"

    # Alternative: template.yaml
    alt_dir = prompts_dir / "alternative"
    alt_dir.mkdir()
    alt_template = alt_dir / "template.yaml"
    alt_template.write_text("""
name: alternative
description: Alternative
user_prompt: Test
""", encoding="utf-8")

    assert loader._find_prompt_file("alternative") == alt_template


def test_reference_resolution_preserves_non_references(prompts_dir):
    """Test that non-reference strings are preserved."""
    loader = PromptLoader(prompts_dir)

    template = PromptTemplate(
        name="normal",
        description="Normal strings",
        system_prompt=None,
        user_prompt="Email: {{email}}, File: {{filename}}",
        variables={
            "email": "user@example.com",  # Contains @ but not @file:
            "filename": "config.yaml"  # Not a reference
        }
    )

    rendered = loader.render_prompt(template, {})
    assert rendered == "Email: user@example.com, File: config.yaml"


def test_complex_rendering_scenario(prompts_dir, config_loader):
    """Test complex rendering with multiple features."""
    # Create additional test file
    details_file = prompts_dir / "details.txt"
    details_file.write_text("Detailed information", encoding="utf-8")

    loader = PromptLoader(prompts_dir, config_loader=config_loader)

    template = PromptTemplate(
        name="complex",
        description="Complex prompt",
        system_prompt="You are {{role}} using {{model}}",
        user_prompt="Project: {{project}}\nContext: {{context}}\nDetails: {{details}}",
        variables={
            "role": "developer",
            "model": "@config:claude_model",
            "project": "MyApp",
            "context": "@file:context.txt",
            "details": "@file:details.txt"
        }
    )

    system = loader.render_system_prompt(template, {"role": "architect"})
    user = loader.render_prompt(template, {"project": "CustomApp"})

    assert system == "You are architect using claude-3"
    assert "CustomApp" in user
    assert "This is test context" in user
    assert "Detailed information" in user
