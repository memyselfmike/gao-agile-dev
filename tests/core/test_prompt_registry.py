"""Tests for PromptRegistry."""

import pytest
from pathlib import Path

from gao_dev.core.prompt_registry import (
    PromptRegistry,
    PromptAlreadyRegisteredError
)
from gao_dev.core.models.prompt_template import PromptTemplate
from gao_dev.core.config_loader import ConfigLoader


@pytest.fixture
def prompts_dir(tmp_path):
    """Create temporary prompts directory with test prompts."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    # Create prompts in different categories
    planning = prompts / "planning"
    planning.mkdir()

    prd = planning / "prd.yaml"
    prd.write_text("""
name: prd
description: Create PRD
user_prompt: Create PRD for {{project}}
variables:
  project: MyProject
metadata:
  category: planning
  phase: 2
""", encoding="utf-8")

    # Create analysis prompt
    analysis = prompts / "analysis"
    analysis.mkdir()

    research = analysis / "research.yaml"
    research.write_text("""
name: research
description: Research prompt
user_prompt: Research {{topic}}
variables:
  topic: technology
metadata:
  category: analysis
  phase: 1
""", encoding="utf-8")

    # Create implementation prompt
    impl = prompts / "implementation"
    impl.mkdir()

    story = impl / "story.yaml"
    story.write_text("""
name: create-story
description: Create user story
user_prompt: Create story for {{feature}}
variables:
  feature: feature
metadata:
  category: implementation
  phase: 4
""", encoding="utf-8")

    # Create prompt without metadata
    simple = prompts / "simple.yaml"
    simple.write_text("""
name: simple
description: Simple prompt
user_prompt: Hello {{name}}
variables:
  name: World
""", encoding="utf-8")

    return prompts


@pytest.fixture
def config_loader(tmp_path):
    """Create config loader for testing."""
    return ConfigLoader(tmp_path)


def test_registry_creation(prompts_dir):
    """Test basic registry creation."""
    registry = PromptRegistry(prompts_dir)

    assert registry.prompts_dir == prompts_dir
    assert registry.cache_enabled is True


def test_index_prompts(prompts_dir):
    """Test indexing prompts from directory."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Should find all 4 prompts
    prompts = registry.get_all_prompts()
    assert len(prompts) >= 4

    # Check specific prompts exist
    assert "prd" in prompts
    assert "research" in prompts
    assert "create-story" in prompts
    assert "simple" in prompts


def test_index_prompts_only_once(prompts_dir):
    """Test that prompts are only indexed once."""
    registry = PromptRegistry(prompts_dir)

    # Index twice
    registry.index_prompts()
    count1 = len(registry.get_all_prompts())

    registry.index_prompts()
    count2 = len(registry.get_all_prompts())

    # Should be same count (not doubled)
    assert count1 == count2


def test_index_prompts_rescan(prompts_dir):
    """Test rescanning prompts."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Add new prompt
    new_prompt = prompts_dir / "new.yaml"
    new_prompt.write_text("""
name: new
description: New prompt
user_prompt: New {{var}}
variables:
  var: value
""", encoding="utf-8")

    # Rescan
    registry.index_prompts(rescan=True)

    # Should find new prompt
    assert registry.prompt_exists("new")


def test_get_prompt(prompts_dir):
    """Test getting prompt by name."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    template = registry.get_prompt("prd")

    assert template is not None
    assert template.name == "prd"
    assert template.description == "Create PRD"


def test_get_nonexistent_prompt(prompts_dir):
    """Test getting non-existent prompt."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    template = registry.get_prompt("nonexistent")

    assert template is None


def test_prompt_exists(prompts_dir):
    """Test checking if prompt exists."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    assert registry.prompt_exists("prd") is True
    assert registry.prompt_exists("nonexistent") is False


def test_list_all_prompts(prompts_dir):
    """Test listing all prompts."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    prompts = registry.list_prompts()

    assert len(prompts) >= 4
    # Should be sorted by name
    names = [p.name for p in prompts]
    assert names == sorted(names)


def test_list_prompts_by_category(prompts_dir):
    """Test listing prompts by category."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Filter by planning
    planning_prompts = registry.list_prompts(category="planning")
    assert len(planning_prompts) == 1
    assert planning_prompts[0].name == "prd"

    # Filter by analysis
    analysis_prompts = registry.list_prompts(category="analysis")
    assert len(analysis_prompts) == 1
    assert analysis_prompts[0].name == "research"

    # Filter by implementation
    impl_prompts = registry.list_prompts(category="implementation")
    assert len(impl_prompts) == 1
    assert impl_prompts[0].name == "create-story"


def test_list_prompts_by_phase(prompts_dir):
    """Test listing prompts by phase."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Phase 1 (analysis)
    phase1 = registry.list_prompts(phase=1)
    assert len(phase1) == 1
    assert phase1[0].name == "research"

    # Phase 2 (planning)
    phase2 = registry.list_prompts(phase=2)
    assert len(phase2) == 1
    assert phase2[0].name == "prd"

    # Phase 4 (implementation)
    phase4 = registry.list_prompts(phase=4)
    assert len(phase4) == 1
    assert phase4[0].name == "create-story"


def test_register_prompt(prompts_dir):
    """Test registering prompt programmatically."""
    registry = PromptRegistry(prompts_dir)

    new_template = PromptTemplate(
        name="custom",
        description="Custom prompt",
        system_prompt=None,
        user_prompt="Custom {{var}}",
        variables={"var": "value"}
    )

    registry.register_prompt(new_template)

    # Should be available
    assert registry.prompt_exists("custom")
    retrieved = registry.get_prompt("custom")
    assert retrieved.name == "custom"


def test_register_duplicate_prompt_error(prompts_dir):
    """Test that registering duplicate raises error."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Try to register existing prompt
    duplicate = PromptTemplate(
        name="prd",  # Already exists
        description="Duplicate",
        system_prompt=None,
        user_prompt="Duplicate",
        variables={}
    )

    with pytest.raises(PromptAlreadyRegisteredError):
        registry.register_prompt(duplicate, allow_override=False)


def test_register_prompt_with_override(prompts_dir):
    """Test registering prompt with override."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # Get original
    original = registry.get_prompt("prd")
    assert original.description == "Create PRD"

    # Override
    override = PromptTemplate(
        name="prd",
        description="Overridden PRD",
        system_prompt=None,
        user_prompt="Overridden",
        variables={}
    )

    registry.register_prompt(override, allow_override=True)

    # Should be replaced
    updated = registry.get_prompt("prd")
    assert updated.description == "Overridden PRD"


def test_override_prompt(prompts_dir):
    """Test override_prompt convenience method."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    override = PromptTemplate(
        name="prd",
        description="Override via method",
        system_prompt=None,
        user_prompt="Override",
        variables={}
    )

    registry.override_prompt(override)

    updated = registry.get_prompt("prd")
    assert updated.description == "Override via method"


def test_unregister_prompt(prompts_dir):
    """Test unregistering a prompt."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    assert registry.prompt_exists("prd")

    # Unregister
    result = registry.unregister_prompt("prd")
    assert result is True

    # Should no longer exist
    assert registry.prompt_exists("prd") is False


def test_unregister_nonexistent_prompt(prompts_dir):
    """Test unregistering non-existent prompt."""
    registry = PromptRegistry(prompts_dir)

    result = registry.unregister_prompt("nonexistent")
    assert result is False


def test_get_categories(prompts_dir):
    """Test getting list of categories."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    categories = registry.get_categories()

    assert "planning" in categories
    assert "analysis" in categories
    assert "implementation" in categories
    # Should be sorted
    assert categories == sorted(categories)


def test_get_phases(prompts_dir):
    """Test getting list of phases."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    phases = registry.get_phases()

    assert 1 in phases
    assert 2 in phases
    assert 4 in phases
    # Should be sorted
    assert phases == sorted(phases)


def test_clear_registry(prompts_dir):
    """Test clearing the registry."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    assert len(registry.get_all_prompts()) > 0

    registry.clear()

    # After clear, internal state should be empty
    assert len(registry._prompts) == 0
    assert registry._indexed is False

    # Note: get_all_prompts() will auto-index again, so it won't be empty
    # This is intentional - clear() resets state but doesn't prevent re-indexing


def test_index_prompts_nonexistent_directory(tmp_path):
    """Test indexing when directory doesn't exist."""
    nonexistent = tmp_path / "nonexistent"
    registry = PromptRegistry(nonexistent)

    # Should not raise error, just log warning
    registry.index_prompts()

    assert len(registry.get_all_prompts()) == 0


def test_skip_workflow_yaml_files(prompts_dir):
    """Test that workflow.yaml files are skipped."""
    # Create workflow.yaml (should be ignored)
    workflow = prompts_dir / "workflow.yaml"
    workflow.write_text("""
name: workflow
description: Should be ignored
""", encoding="utf-8")

    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # workflow should not be indexed
    assert not registry.prompt_exists("workflow")


def test_skip_config_files(prompts_dir):
    """Test that config files are skipped."""
    # Create config.yaml (should be ignored)
    config = prompts_dir / "config.yaml"
    config.write_text("""
name: config
description: Should be ignored
""", encoding="utf-8")

    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # config should not be indexed
    assert not registry.prompt_exists("config")


def test_invalid_prompt_file_skipped(prompts_dir):
    """Test that invalid prompts are skipped."""
    # Create invalid prompt
    invalid = prompts_dir / "invalid.yaml"
    invalid.write_text("invalid: yaml: content:", encoding="utf-8")

    registry = PromptRegistry(prompts_dir)

    # Should not raise error, just skip invalid file
    registry.index_prompts()


def test_auto_index_on_get(prompts_dir):
    """Test that prompts are auto-indexed on first get."""
    registry = PromptRegistry(prompts_dir)

    # Don't call index_prompts() explicitly
    template = registry.get_prompt("prd")

    # Should still work (auto-indexed)
    assert template is not None
    assert template.name == "prd"


def test_auto_index_on_exists(prompts_dir):
    """Test that prompts are auto-indexed on first exists check."""
    registry = PromptRegistry(prompts_dir)

    # Don't call index_prompts() explicitly
    exists = registry.prompt_exists("prd")

    # Should still work (auto-indexed)
    assert exists is True


def test_auto_index_on_list(prompts_dir):
    """Test that prompts are auto-indexed on first list."""
    registry = PromptRegistry(prompts_dir)

    # Don't call index_prompts() explicitly
    prompts = registry.list_prompts()

    # Should still work (auto-indexed)
    assert len(prompts) >= 4


def test_get_all_prompts_returns_copy(prompts_dir):
    """Test that get_all_prompts returns a copy."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    prompts1 = registry.get_all_prompts()
    prompts2 = registry.get_all_prompts()

    # Should be different dict objects
    assert prompts1 is not prompts2

    # But contain same data
    assert prompts1.keys() == prompts2.keys()


def test_registry_with_config_loader(prompts_dir, config_loader):
    """Test registry with config loader."""
    registry = PromptRegistry(prompts_dir, config_loader=config_loader)

    assert registry.config_loader is config_loader
    assert registry.loader.config_loader is config_loader


def test_cache_disabled(prompts_dir):
    """Test registry with caching disabled."""
    registry = PromptRegistry(prompts_dir, cache_enabled=False)

    assert registry.cache_enabled is False
    assert registry.loader.cache_enabled is False


def test_nested_directory_structure(tmp_path):
    """Test indexing prompts in nested directories."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    # Create deeply nested structure
    deep = prompts / "level1" / "level2" / "level3"
    deep.mkdir(parents=True)

    deep_prompt = deep / "deep.yaml"
    deep_prompt.write_text("""
name: deep
description: Deeply nested
user_prompt: Deep {{var}}
variables:
  var: value
""", encoding="utf-8")

    registry = PromptRegistry(prompts)
    registry.index_prompts()

    # Should find deeply nested prompt
    assert registry.prompt_exists("deep")


def test_list_prompts_combined_filters(prompts_dir):
    """Test listing prompts with both category and phase filters."""
    registry = PromptRegistry(prompts_dir)
    registry.index_prompts()

    # This should work but return empty if no prompts match both
    prompts = registry.list_prompts(category="planning", phase=1)

    # planning is phase 2, so this should be empty
    assert len(prompts) == 0

    # But this should work
    prompts = registry.list_prompts(category="planning", phase=2)
    assert len(prompts) == 1
    assert prompts[0].name == "prd"
