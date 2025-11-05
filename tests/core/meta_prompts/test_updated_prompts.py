"""
Tests for updated prompts with meta-prompt references (Story 13.6).

This test suite verifies that all 10 core prompts updated in Story 13.6
work correctly with the MetaPromptEngine and maintain backward compatibility.
"""

import pytest
from pathlib import Path
import yaml

from gao_dev.core.prompt_loader import PromptLoader


class TestUpdatedPrompts:
    """Test all updated prompts."""

    @pytest.fixture
    def prompts_dir(self):
        """Get prompts directory."""
        prompts_dir = Path("gao_dev/prompts")
        if not prompts_dir.exists():
            pytest.skip(f"Prompts directory not found: {prompts_dir}")
        return prompts_dir

    @pytest.fixture
    def prompt_loader(self, prompts_dir):
        """Create PromptLoader."""
        return PromptLoader(prompts_dir=prompts_dir, cache_enabled=True)

    def _load_yaml(self, prompt_path):
        """Load YAML file directly."""
        with open(prompt_path) as f:
            return yaml.safe_load(f)

    def test_all_prompts_load_successfully(self, prompt_loader):
        """Test that all 10 updated prompts load without errors."""
        updated_prompts = [
            "tasks/create_prd",
            "tasks/create_architecture",
            "tasks/create_story",
            "tasks/implement_story",
            "tasks/validate_story",
            "agents/brian_analysis",
            "story_phases/story_creation",
            "story_phases/story_implementation",
            "story_phases/story_validation",
        ]

        for prompt_name in updated_prompts:
            template = prompt_loader.load_prompt(prompt_name)
            assert template is not None, f"Failed to load {prompt_name}"
            assert template.name, f"{prompt_name} has no name"
            assert template.user_prompt, f"{prompt_name} has no user_prompt"

    def test_all_prompts_version_2(self, prompts_dir):
        """Test that all updated prompts are version 2.0.0."""
        updated_prompts = [
            "tasks/create_prd.yaml",
            "tasks/create_architecture.yaml",
            "tasks/create_story.yaml",
            "tasks/implement_story.yaml",
            "tasks/validate_story.yaml",
            "agents/brian_analysis.yaml",
            "story_phases/story_creation.yaml",
            "story_phases/story_implementation.yaml",
            "story_phases/story_validation.yaml",
        ]

        for prompt_file in updated_prompts:
            prompt_path = prompts_dir / prompt_file
            data = self._load_yaml(prompt_path)
            assert data.get("version") == "2.0.0", (
                f"{prompt_file} should be version 2.0.0, got {data.get('version')}"
            )

    def test_all_prompts_have_meta_prompts_enabled(self, prompts_dir):
        """Test that all updated prompts have meta_prompts.enabled = true."""
        updated_prompts = [
            "tasks/create_prd.yaml",
            "tasks/create_architecture.yaml",
            "tasks/create_story.yaml",
            "tasks/implement_story.yaml",
            "tasks/validate_story.yaml",
            "agents/brian_analysis.yaml",
            "story_phases/story_creation.yaml",
            "story_phases/story_implementation.yaml",
            "story_phases/story_validation.yaml",
        ]

        for prompt_file in updated_prompts:
            prompt_path = prompts_dir / prompt_file
            data = self._load_yaml(prompt_path)
            assert "meta_prompts" in data, f"{prompt_file} missing meta_prompts"
            assert data["meta_prompts"]["enabled"] is True, (
                f"{prompt_file} should have meta_prompts.enabled = true"
            )

    def test_prompts_contain_meta_prompt_references(self, prompts_dir):
        """Test that updated prompts contain meta-prompt references."""
        # These prompts should have meta-prompt references
        prompts_with_references = {
            "tasks/create_prd.yaml": ["@context:", "@doc:"],
            "tasks/create_architecture.yaml": ["@context:", "@doc:"],
            "tasks/create_story.yaml": ["@context:", "@doc:", "@query:"],
            "tasks/implement_story.yaml": ["@doc:", "@context:", "@checklist:"],
            "tasks/validate_story.yaml": ["@doc:", "@checklist:"],
            "agents/brian_analysis.yaml": ["@config:"],
            "story_phases/story_creation.yaml": ["@context:", "@doc:"],
            "story_phases/story_implementation.yaml": ["@context:", "@checklist:", "@doc:"],
            "story_phases/story_validation.yaml": ["@checklist:", "@doc:"],
        }

        for prompt_file, expected_refs in prompts_with_references.items():
            prompt_path = prompts_dir / prompt_file
            data = self._load_yaml(prompt_path)
            user_prompt = data.get("user_prompt", "")

            for ref_type in expected_refs:
                assert ref_type in user_prompt, (
                    f"{prompt_file} should contain {ref_type} reference"
                )

    def test_prompts_have_feature_variable(self, prompts_dir):
        """Test that prompts have 'feature' variable for context resolution."""
        # All prompts using @context: should have feature variable
        prompts_needing_feature = [
            "tasks/create_prd.yaml",
            "tasks/create_architecture.yaml",
            "tasks/create_story.yaml",
            "tasks/implement_story.yaml",
            "tasks/validate_story.yaml",
            "story_phases/story_creation.yaml",
            "story_phases/story_implementation.yaml",
            "story_phases/story_validation.yaml",
        ]

        for prompt_file in prompts_needing_feature:
            prompt_path = prompts_dir / prompt_file
            data = self._load_yaml(prompt_path)
            variables = data.get("variables", {})
            assert "feature" in variables, (
                f"{prompt_file} should have 'feature' variable"
            )

    def test_backward_compatibility(self, prompt_loader):
        """Test that prompts work with Epic 10 PromptLoader."""
        # Load and render a prompt without MetaPromptEngine
        template = prompt_loader.load_prompt("tasks/create_prd")

        # Should be able to render with basic variables
        rendered = prompt_loader.render_prompt(
            template,
            variables={"project_name": "Test Project", "agent": "John", "feature": "test"}
        )

        # Should contain variables
        assert "Test Project" in rendered

        # References won't be resolved (this is expected)
        # But prompt should still render without errors

    def test_implement_story_has_comprehensive_references(self, prompts_dir):
        """Test that implement_story has all necessary references."""
        prompt_path = prompts_dir / "tasks/implement_story.yaml"
        data = self._load_yaml(prompt_path)
        user_prompt = data.get("user_prompt", "")

        # Should have all key reference types
        assert "@doc:stories" in user_prompt, "Should reference story document"
        assert "@context:epic_definition" in user_prompt, "Should reference epic context"
        assert "@context:architecture" in user_prompt, "Should reference architecture"
        assert "@context:coding_standards" in user_prompt, "Should reference coding standards"
        assert "@checklist:testing/unit-test-standards" in user_prompt, "Should reference test standards"
        assert "@checklist:code-quality/solid-principles" in user_prompt, "Should reference SOLID principles"

    def test_validate_story_has_quality_checklists(self, prompts_dir):
        """Test that validate_story has comprehensive quality checklists."""
        prompt_path = prompts_dir / "tasks/validate_story.yaml"
        data = self._load_yaml(prompt_path)
        user_prompt = data.get("user_prompt", "")

        # Should have quality checklists
        assert "@checklist:testing/qa-comprehensive" in user_prompt
        assert "@checklist:code-quality/code-review-checklist" in user_prompt
        assert "@checklist:testing/unit-test-standards" in user_prompt

    def test_create_story_has_query_reference(self, prompts_dir):
        """Test that create_story uses query to list existing stories."""
        prompt_path = prompts_dir / "tasks/create_story.yaml"
        data = self._load_yaml(prompt_path)
        user_prompt = data.get("user_prompt", "")

        # Should query for existing stories
        assert "@query:stories.where" in user_prompt

    def test_brian_analysis_uses_config_references(self, prompts_dir):
        """Test that brian_analysis uses config references."""
        prompt_path = prompts_dir / "agents/brian_analysis.yaml"
        data = self._load_yaml(prompt_path)
        user_prompt = data.get("user_prompt", "")

        # Should use config references for scale levels and schema
        assert "@config:" in user_prompt


class TestPromptSizeReduction:
    """Test that prompt complexity has been reduced."""

    @pytest.fixture
    def prompts_dir(self):
        """Get prompts directory."""
        prompts_dir = Path("gao_dev/prompts")
        if not prompts_dir.exists():
            pytest.skip(f"Prompts directory not found: {prompts_dir}")
        return prompts_dir

    def _load_yaml(self, prompt_path):
        """Load YAML file directly."""
        with open(prompt_path) as f:
            return yaml.safe_load(f)

    def test_implement_story_has_fewer_variables(self, prompts_dir):
        """Test that implement_story has reduced content variables."""
        prompt_path = prompts_dir / "tasks/implement_story.yaml"
        data = self._load_yaml(prompt_path)
        variables = data.get("variables", {})

        # Should have basic variables
        assert "epic" in variables
        assert "story" in variables
        assert "agent" in variables
        assert "feature" in variables

        # Should NOT have content variables (they're now meta-prompt references)
        assert "story_content" not in variables, "story_content should be @doc: reference"
        assert "acceptance_criteria" not in variables, "acceptance_criteria should be @doc: reference"
        assert "epic_definition" not in variables, "epic_definition should be @context: reference"
        assert "architecture" not in variables, "architecture should be @context: reference"
        assert "coding_standards" not in variables, "coding_standards should be @context: reference"
        assert "qa_checklist" not in variables, "qa_checklist should be @checklist: reference"

    def test_story_phases_have_reduced_complexity(self, prompts_dir):
        """Test that story phase prompts are simpler."""
        phase_prompts = [
            "story_phases/story_creation.yaml",
            "story_phases/story_implementation.yaml",
            "story_phases/story_validation.yaml",
        ]

        for prompt_file in phase_prompts:
            prompt_path = prompts_dir / prompt_file
            data = self._load_yaml(prompt_path)
            user_prompt = data.get("user_prompt", "")

            # Should use meta-prompt references instead of @file: for common content
            assert "@doc:" in user_prompt or "@context:" in user_prompt or "@checklist:" in user_prompt, (
                f"{prompt_file} should use meta-prompt references"
            )


class TestMigrationGuideAndExamples:
    """Test that documentation was created."""

    def test_migration_guide_exists(self):
        """Test that migration guide was created."""
        migration_guide = Path("docs/MIGRATION_GUIDE_EPIC_13.md")
        assert migration_guide.exists(), "Migration guide should exist"

        content = migration_guide.read_text()
        assert "Epic 13" in content
        assert "Meta-Prompt" in content
        assert "@doc:" in content
        assert "@context:" in content
        assert "@checklist:" in content
        assert "@query:" in content

    def test_examples_documentation_exists(self):
        """Test that examples documentation was created."""
        examples_doc = Path("docs/examples/meta-prompt-examples.md")
        assert examples_doc.exists(), "Examples documentation should exist"

        content = examples_doc.read_text()
        assert "Meta-Prompt Examples" in content
        assert "@doc:" in content
        assert "@context:" in content
        assert "@checklist:" in content
        assert "@query:" in content
        assert "Example" in content or "example" in content
