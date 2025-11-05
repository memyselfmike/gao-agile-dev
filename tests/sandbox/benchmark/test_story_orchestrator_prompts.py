"""Tests for story orchestrator prompt templates (Story 10.3)."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from gao_dev.sandbox.benchmark.story_orchestrator import (
    StoryOrchestrator,
    StoryResult,
    StoryStatus,
)
from gao_dev.sandbox.benchmark.config import StoryConfig
from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.config_loader import ConfigLoader


class TestStoryPromptTemplates:
    """Tests for story phase prompt templates."""

    @pytest.fixture
    def prompts_dir(self):
        """Get prompts directory."""
        return Path(__file__).parent.parent.parent.parent / "gao_dev" / "prompts"

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temporary project path."""
        project_path = tmp_path / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    @pytest.fixture
    def prompt_loader(self, prompts_dir, temp_project_path):
        """Create PromptLoader instance."""
        config_loader = ConfigLoader(temp_project_path)
        return PromptLoader(prompts_dir, config_loader)

    @pytest.fixture
    def orchestrator(self, temp_project_path, prompt_loader):
        """Create StoryOrchestrator with PromptLoader."""
        return StoryOrchestrator(
            project_path=temp_project_path,
            prompt_loader=prompt_loader,
        )

    @pytest.fixture
    def sample_story(self):
        """Create sample story config."""
        return StoryConfig(
            name="Test Story",
            agent="Amelia",
            description="Test story description",
            acceptance_criteria=[
                "Criteria 1: Feature works",
                "Criteria 2: Tests pass",
                "Criteria 3: Documentation updated",
            ],
            story_points=3,
        )

    def test_story_creation_prompt_loads(self, prompt_loader):
        """Test story_creation prompt template loads."""
        template = prompt_loader.load_prompt("story_phases/story_creation")

        assert template is not None
        assert template.name == "story_creation"
        assert template.description == "Bob creates story specification"
        assert "agent_name" in template.variables
        assert template.variables["agent_name"] == "Bob"

    def test_story_implementation_prompt_loads(self, prompt_loader):
        """Test story_implementation prompt template loads."""
        template = prompt_loader.load_prompt("story_phases/story_implementation")

        assert template is not None
        assert template.name == "story_implementation"
        assert template.description == "Amelia implements story"
        assert "agent_name" in template.variables
        assert template.variables["agent_name"] == "Amelia"

    def test_story_validation_prompt_loads(self, prompt_loader):
        """Test story_validation prompt template loads."""
        template = prompt_loader.load_prompt("story_phases/story_validation")

        assert template is not None
        assert template.name == "story_validation"
        assert template.description == "Murat validates story"
        assert "agent_name" in template.variables
        assert template.variables["agent_name"] == "Murat"

    def test_all_story_prompts_have_correct_metadata(self, prompt_loader):
        """Test all story prompts have correct metadata."""
        creation = prompt_loader.load_prompt("story_phases/story_creation")
        implementation = prompt_loader.load_prompt("story_phases/story_implementation")
        validation = prompt_loader.load_prompt("story_phases/story_validation")

        # Check metadata
        assert creation.metadata["category"] == "story_workflow"
        assert creation.metadata["phase"] == "creation"
        assert creation.metadata["agent"] == "Bob"

        assert implementation.metadata["category"] == "story_workflow"
        assert implementation.metadata["phase"] == "implementation"
        assert implementation.metadata["agent"] == "Amelia"

        assert validation.metadata["category"] == "story_workflow"
        assert validation.metadata["phase"] == "validation"
        assert validation.metadata["agent"] == "Murat"

    def test_reusable_fragments_exist(self, prompts_dir):
        """Test that all reusable fragments were created."""
        common_dir = prompts_dir / "common"

        # Check responsibility fragments
        responsibilities_dir = common_dir / "responsibilities"
        assert (responsibilities_dir / "scrum_master_story_creation.md").exists()
        assert (responsibilities_dir / "developer_implementation.md").exists()
        assert (responsibilities_dir / "test_architect_validation.md").exists()

        # Check output format fragments
        outputs_dir = common_dir / "outputs"
        assert (outputs_dir / "story_specification_format.md").exists()
        assert (outputs_dir / "test_report_format.md").exists()

    def test_reusable_fragments_have_content(self, prompts_dir):
        """Test that reusable fragments have meaningful content."""
        common_dir = prompts_dir / "common"

        # Check scrum master responsibilities
        scrum_master = common_dir / "responsibilities" / "scrum_master_story_creation.md"
        content = scrum_master.read_text()
        assert "Review the Story" in content
        assert "Enhance Acceptance Criteria" in content
        assert "ONE story at a time" in content

        # Check developer responsibilities
        developer = common_dir / "responsibilities" / "developer_implementation.md"
        content = developer.read_text()
        assert "Implement THIS Story" in content
        assert "Write Tests" in content
        assert "80%+ test coverage" in content

        # Check test architect responsibilities
        test_architect = common_dir / "responsibilities" / "test_architect_validation.md"
        content = test_architect.read_text()
        assert "Run Tests" in content
        assert "Verify Acceptance Criteria" in content
        assert "Validation Checklist" in content

    def test_story_creation_prompt_renders(self, orchestrator, sample_story):
        """Test story creation prompt renders correctly."""
        result = StoryResult(
            story_name="Test Story",
            epic_name="Test Epic",
            agent="Amelia",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )

        prompt = orchestrator._create_story_creation_prompt(sample_story, result)

        # Check prompt contains expected content (user_prompt only, system_prompt separate)
        # The method returns only user_prompt, system_prompt "You are Bob..." is separate
        assert "Test Epic" in prompt
        assert "Test Story" in prompt
        assert "Criteria 1: Feature works" in prompt
        assert "Criteria 2: Tests pass" in prompt
        assert "ONE story at a time" in prompt
        assert "Scrum Master Responsibilities" in prompt  # From fragment file

    def test_story_implementation_prompt_renders(self, orchestrator, sample_story):
        """Test story implementation prompt renders correctly."""
        result = StoryResult(
            story_name="Test Story",
            epic_name="Test Epic",
            agent="Amelia",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )
        result.metadata["creation_output"] = "Bob's notes here"

        prompt = orchestrator._create_story_implementation_prompt(sample_story, result)

        # Check prompt contains expected content (user_prompt only)
        # System prompt "You are Amelia..." is rendered separately
        assert "Test Epic" in prompt
        assert "Test Story" in prompt
        assert "Criteria 1: Feature works" in prompt
        assert "Bob's notes here" in prompt
        assert "Implement THIS Story" in prompt or "Developer Responsibilities" in prompt

    def test_story_validation_prompt_renders(self, orchestrator, sample_story):
        """Test story validation prompt renders correctly."""
        result = StoryResult(
            story_name="Test Story",
            epic_name="Test Epic",
            agent="Murat",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )
        result.metadata["implementation_output"] = "Amelia's implementation notes"

        prompt = orchestrator._create_story_validation_prompt(sample_story, result)

        # Check prompt contains expected content (user_prompt only)
        # System prompt "You are Murat..." is rendered separately
        assert "Test Epic" in prompt
        assert "Test Story" in prompt
        assert "Criteria 1: Feature works" in prompt
        assert "Amelia's implementation notes" in prompt
        assert "Run Tests" in prompt or "Test Architect Responsibilities" in prompt

    def test_prompts_use_file_references(self, prompt_loader):
        """Test that prompts use @file: references for fragments."""
        creation = prompt_loader.load_prompt("story_phases/story_creation")
        implementation = prompt_loader.load_prompt("story_phases/story_implementation")
        validation = prompt_loader.load_prompt("story_phases/story_validation")

        # Check that variables reference files
        assert creation.variables["responsibilities"].startswith("@file:")
        assert creation.variables["output_format"].startswith("@file:")

        assert implementation.variables["responsibilities"].startswith("@file:")

        assert validation.variables["responsibilities"].startswith("@file:")
        assert validation.variables["output_format"].startswith("@file:")

    def test_file_references_resolve(self, prompt_loader):
        """Test that @file: references resolve correctly."""
        creation = prompt_loader.load_prompt("story_phases/story_creation")

        # Render with minimal variables
        rendered = prompt_loader.render_prompt(
            creation,
            variables={
                "story_overview": "Test overview",
                "acceptance_criteria": "Test criteria",
                "project_path": "/test/path",
            },
        )

        # Should contain content from referenced files
        assert "Review the Story" in rendered  # From scrum_master_story_creation.md
        assert "Story Specification Output Format" in rendered  # From story_specification_format.md

    def test_prompts_contain_important_directives(self, orchestrator, sample_story):
        """Test that all prompts contain important directives about ONE story."""
        result = StoryResult(
            story_name="Test",
            epic_name="Epic",
            agent="Amelia",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )

        creation_prompt = orchestrator._create_story_creation_prompt(sample_story, result)
        implementation_prompt = orchestrator._create_story_implementation_prompt(
            sample_story, result
        )
        validation_prompt = orchestrator._create_story_validation_prompt(
            sample_story, result
        )

        # All prompts should emphasize ONE story
        assert "ONE story" in creation_prompt or "this ONE story" in creation_prompt.lower()
        assert "ONE story" in implementation_prompt or "this ONE story" in implementation_prompt.lower()
        assert "ONE story" in validation_prompt or "this ONE story" in validation_prompt.lower()

    def test_prompts_include_acceptance_criteria(self, orchestrator, sample_story):
        """Test that all prompts include acceptance criteria."""
        result = StoryResult(
            story_name="Test",
            epic_name="Epic",
            agent="Amelia",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )

        creation_prompt = orchestrator._create_story_creation_prompt(sample_story, result)
        implementation_prompt = orchestrator._create_story_implementation_prompt(
            sample_story, result
        )
        validation_prompt = orchestrator._create_story_validation_prompt(
            sample_story, result
        )

        # All should contain acceptance criteria
        for criterion in sample_story.acceptance_criteria:
            assert criterion in creation_prompt
            assert criterion in implementation_prompt
            assert criterion in validation_prompt

    def test_prompts_include_project_path(self, orchestrator, sample_story, temp_project_path):
        """Test that prompts include project path."""
        result = StoryResult(
            story_name="Test",
            epic_name="Epic",
            agent="Amelia",
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )

        creation_prompt = orchestrator._create_story_creation_prompt(sample_story, result)
        implementation_prompt = orchestrator._create_story_implementation_prompt(
            sample_story, result
        )
        validation_prompt = orchestrator._create_story_validation_prompt(
            sample_story, result
        )

        project_path_str = str(temp_project_path)
        assert project_path_str in creation_prompt
        assert project_path_str in implementation_prompt
        assert project_path_str in validation_prompt


class TestPromptLoaderIntegration:
    """Integration tests for PromptLoader with StoryOrchestrator."""

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temp project path."""
        return tmp_path / "integration_test"

    def test_orchestrator_creates_default_prompt_loader(self, temp_project_path):
        """Test that orchestrator creates default PromptLoader if not provided."""
        temp_project_path.mkdir(parents=True, exist_ok=True)
        orchestrator = StoryOrchestrator(project_path=temp_project_path)

        assert orchestrator.prompt_loader is not None
        assert isinstance(orchestrator.prompt_loader, PromptLoader)

    def test_orchestrator_uses_provided_prompt_loader(self, temp_project_path):
        """Test that orchestrator uses provided PromptLoader."""
        temp_project_path.mkdir(parents=True, exist_ok=True)
        prompts_dir = Path(__file__).parent.parent.parent.parent / "gao_dev" / "prompts"
        config_loader = ConfigLoader(temp_project_path)
        custom_loader = PromptLoader(prompts_dir, config_loader)

        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            prompt_loader=custom_loader,
        )

        assert orchestrator.prompt_loader is custom_loader

    def test_end_to_end_prompt_generation(self, temp_project_path):
        """Test end-to-end prompt generation with real templates."""
        temp_project_path.mkdir(parents=True, exist_ok=True)
        orchestrator = StoryOrchestrator(project_path=temp_project_path)

        story = StoryConfig(
            name="User Authentication",
            agent="Amelia",
            description="Implement user login and registration",
            acceptance_criteria=[
                "Users can register with email",
                "Users can login",
                "Sessions are secure",
            ],
            story_points=5,
        )

        result = StoryResult(
            story_name=story.name,
            epic_name="Auth System",
            agent=story.agent,
            status=StoryStatus.IN_PROGRESS,
            start_time=Mock(),
        )

        # Generate all three prompts
        creation_prompt = orchestrator._create_story_creation_prompt(story, result)
        implementation_prompt = orchestrator._create_story_implementation_prompt(story, result)
        validation_prompt = orchestrator._create_story_validation_prompt(story, result)

        # Verify all prompts are generated and contain expected content
        assert len(creation_prompt) > 100
        assert len(implementation_prompt) > 100
        assert len(validation_prompt) > 100

        # Check key elements (user_prompt content)
        # System prompts with agent names are rendered separately
        assert "Scrum Master" in creation_prompt  # Role mentioned in content
        assert "Developer" in implementation_prompt  # Role mentioned in content
        assert "Test Architect" in validation_prompt  # Role mentioned in content

        assert "User Authentication" in creation_prompt
        assert "User Authentication" in implementation_prompt
        assert "User Authentication" in validation_prompt

        assert all(c in creation_prompt for c in story.acceptance_criteria)
        assert all(c in implementation_prompt for c in story.acceptance_criteria)
        assert all(c in validation_prompt for c in story.acceptance_criteria)


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with existing code."""

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temp project path."""
        return tmp_path / "compat_test"

    def test_orchestrator_works_without_prompt_loader_parameter(self, temp_project_path):
        """Test that existing code without prompt_loader parameter still works."""
        temp_project_path.mkdir(parents=True, exist_ok=True)

        # Old-style initialization (no prompt_loader parameter)
        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            api_key=None,
            git_manager=None,
            metrics_aggregator=None,
        )

        assert orchestrator.prompt_loader is not None
        assert isinstance(orchestrator.prompt_loader, PromptLoader)

    def test_story_execution_still_works(self, temp_project_path):
        """Test that story execution still works with new prompt system."""
        temp_project_path.mkdir(parents=True, exist_ok=True)
        orchestrator = StoryOrchestrator(project_path=temp_project_path)

        story = StoryConfig(
            name="Test Story",
            agent="Amelia",
            description="Test",
            acceptance_criteria=["Works"],
            story_points=1,
        )

        # Should execute without errors
        result = orchestrator.execute_story(story, "Test Epic")

        assert result.status == StoryStatus.COMPLETED
        assert len(result.acceptance_criteria_met) > 0
