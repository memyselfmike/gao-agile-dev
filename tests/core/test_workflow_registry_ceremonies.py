"""
Unit tests for WorkflowRegistry ceremony workflow loading and validation.

Story 28.1: Ceremony Workflow Types
Tests ceremony workflow definitions, loading, and metadata validation.
"""

import pytest
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.config_loader import ConfigLoader


@pytest.fixture
def config_loader(tmp_path):
    """Create a config loader for tests."""
    return ConfigLoader(project_root=tmp_path)


@pytest.fixture
def workflow_registry(config_loader):
    """Create a workflow registry for tests."""
    registry = WorkflowRegistry(config_loader)
    registry.index_workflows()
    return registry


class TestCeremonyWorkflowLoading:
    """Test ceremony workflows load successfully."""

    def test_planning_ceremony_loads(self, workflow_registry):
        """Test planning ceremony workflow loads successfully."""
        workflow = workflow_registry.get_workflow("planning-ceremony")
        assert workflow is not None
        assert workflow.name == "planning-ceremony"
        assert workflow.description is not None
        assert workflow.category == "ceremonies"
        assert workflow.phase == 5

    def test_standup_ceremony_loads(self, workflow_registry):
        """Test standup ceremony workflow loads successfully."""
        workflow = workflow_registry.get_workflow("standup-ceremony")
        assert workflow is not None
        assert workflow.name == "standup-ceremony"
        assert workflow.description is not None
        assert workflow.category == "ceremonies"
        assert workflow.phase == 5

    def test_retrospective_ceremony_loads(self, workflow_registry):
        """Test retrospective ceremony workflow loads successfully."""
        workflow = workflow_registry.get_workflow("retrospective-ceremony")
        assert workflow is not None
        assert workflow.name == "retrospective-ceremony"
        assert workflow.description is not None
        assert workflow.category == "ceremonies"
        assert workflow.phase == 5

    def test_all_three_ceremonies_present(self, workflow_registry):
        """Test all three ceremony workflows are present."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")
        ceremony_names = [w.name for w in ceremonies]

        assert "planning-ceremony" in ceremony_names
        assert "standup-ceremony" in ceremony_names
        assert "retrospective-ceremony" in ceremony_names
        assert len(ceremony_names) >= 3


class TestCeremonyMetadataValidation:
    """Test ceremony-specific metadata validation."""

    def test_planning_ceremony_metadata(self, workflow_registry):
        """Test planning ceremony has valid metadata."""
        workflow = workflow_registry.get_workflow("planning-ceremony")
        assert workflow is not None

        # Check metadata exists
        assert workflow.metadata is not None
        assert isinstance(workflow.metadata, dict)

        # Check required fields
        assert "ceremony_type" in workflow.metadata
        assert "participants" in workflow.metadata
        assert "trigger" in workflow.metadata

        # Check values
        assert workflow.metadata["ceremony_type"] == "planning"
        assert isinstance(workflow.metadata["participants"], list)
        assert len(workflow.metadata["participants"]) > 0
        assert "John" in workflow.metadata["participants"]
        assert "Winston" in workflow.metadata["participants"]
        assert "Bob" in workflow.metadata["participants"]
        assert workflow.metadata["trigger"] == "epic_start"

    def test_standup_ceremony_metadata(self, workflow_registry):
        """Test standup ceremony has valid metadata."""
        workflow = workflow_registry.get_workflow("standup-ceremony")
        assert workflow is not None

        # Check metadata exists
        assert workflow.metadata is not None

        # Check required fields
        assert "ceremony_type" in workflow.metadata
        assert "participants" in workflow.metadata
        assert "trigger" in workflow.metadata

        # Check values
        assert workflow.metadata["ceremony_type"] == "standup"
        assert isinstance(workflow.metadata["participants"], list)
        assert len(workflow.metadata["participants"]) > 0
        assert "Bob" in workflow.metadata["participants"]
        assert "Amelia" in workflow.metadata["participants"]
        assert "Murat" in workflow.metadata["participants"]
        assert workflow.metadata["trigger"] == "story_interval"

    def test_retrospective_ceremony_metadata(self, workflow_registry):
        """Test retrospective ceremony has valid metadata."""
        workflow = workflow_registry.get_workflow("retrospective-ceremony")
        assert workflow is not None

        # Check metadata exists
        assert workflow.metadata is not None

        # Check required fields
        assert "ceremony_type" in workflow.metadata
        assert "participants" in workflow.metadata
        assert "trigger" in workflow.metadata

        # Check values
        assert workflow.metadata["ceremony_type"] == "retrospective"
        assert isinstance(workflow.metadata["participants"], list)
        assert len(workflow.metadata["participants"]) > 0
        # Retrospective includes all team members
        assert len(workflow.metadata["participants"]) >= 6
        assert workflow.metadata["trigger"] == "epic_completion"

    def test_all_ceremonies_have_duration_estimate(self, workflow_registry):
        """Test all ceremonies have duration estimate in metadata."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert "duration_estimate" in ceremony.metadata
            assert ceremony.metadata["duration_estimate"] is not None

    def test_all_ceremonies_have_success_criteria(self, workflow_registry):
        """Test all ceremonies have success criteria in metadata."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert "success_criteria" in ceremony.metadata
            assert isinstance(ceremony.metadata["success_criteria"], list)
            assert len(ceremony.metadata["success_criteria"]) > 0


class TestCategoryRecognition:
    """Test category 'ceremonies' is recognized."""

    def test_ceremonies_category_filtering(self, workflow_registry):
        """Test ceremonies can be filtered by category."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")
        assert len(ceremonies) >= 3

        # All should be category="ceremonies"
        for workflow in ceremonies:
            assert workflow.category == "ceremonies"

    def test_ceremonies_phase_filtering(self, workflow_registry):
        """Test ceremonies can be filtered by phase 5."""
        phase_5_workflows = workflow_registry.list_workflows(phase=5)
        assert len(phase_5_workflows) >= 3

        # All should be phase 5
        for workflow in phase_5_workflows:
            assert workflow.phase == 5

    def test_combined_filtering(self, workflow_registry):
        """Test combined phase and category filtering."""
        ceremonies = workflow_registry.list_workflows(phase=5, category="ceremonies")
        assert len(ceremonies) >= 3

        # All should match both filters
        for workflow in ceremonies:
            assert workflow.phase == 5
            assert workflow.category == "ceremonies"


class TestWorkflowInstructions:
    """Test workflow instructions are valid."""

    def test_planning_ceremony_instructions(self, workflow_registry):
        """Test planning ceremony has valid instructions."""
        workflow = workflow_registry.get_workflow("planning-ceremony")
        assert workflow is not None

        # Check templates exist
        assert workflow.templates is not None
        assert "main" in workflow.templates
        assert workflow.templates["main"] is not None
        assert len(workflow.templates["main"]) > 0

        # Check instructions mention key concepts
        instructions = workflow.templates["main"]
        assert "planning" in instructions.lower()
        assert "ceremony" in instructions.lower()
        assert "epic" in instructions.lower()

    def test_standup_ceremony_instructions(self, workflow_registry):
        """Test standup ceremony has valid instructions."""
        workflow = workflow_registry.get_workflow("standup-ceremony")
        assert workflow is not None

        assert workflow.templates is not None
        assert "main" in workflow.templates

        instructions = workflow.templates["main"]
        assert "standup" in instructions.lower()
        assert "blocker" in instructions.lower() or "blockers" in instructions.lower()

    def test_retrospective_ceremony_instructions(self, workflow_registry):
        """Test retrospective ceremony has valid instructions."""
        workflow = workflow_registry.get_workflow("retrospective-ceremony")
        assert workflow is not None

        assert workflow.templates is not None
        assert "main" in workflow.templates

        instructions = workflow.templates["main"]
        assert "retrospective" in instructions.lower()
        assert "learning" in instructions.lower() or "learnings" in instructions.lower()


class TestVariablePlaceholders:
    """Test variable placeholders are present."""

    def test_planning_ceremony_variables(self, workflow_registry):
        """Test planning ceremony has required variables."""
        workflow = workflow_registry.get_workflow("planning-ceremony")
        assert workflow is not None

        # Check variables exist
        assert workflow.variables is not None
        assert "epic_num" in workflow.variables
        assert "feature_name" in workflow.variables

        # Check variable definitions
        assert workflow.variables["epic_num"]["required"] is True
        assert workflow.variables["feature_name"]["required"] is True

    def test_standup_ceremony_variables(self, workflow_registry):
        """Test standup ceremony has required variables."""
        workflow = workflow_registry.get_workflow("standup-ceremony")
        assert workflow is not None

        # Check variables exist
        assert workflow.variables is not None
        assert "epic_num" in workflow.variables
        assert "feature_name" in workflow.variables
        assert "date" in workflow.variables

    def test_retrospective_ceremony_variables(self, workflow_registry):
        """Test retrospective ceremony has required variables."""
        workflow = workflow_registry.get_workflow("retrospective-ceremony")
        assert workflow is not None

        # Check variables exist
        assert workflow.variables is not None
        assert "epic_num" in workflow.variables
        assert "feature_name" in workflow.variables
        assert "stories_completed" in workflow.variables
        assert "total_stories" in workflow.variables

    def test_variable_placeholders_in_instructions(self, workflow_registry):
        """Test variable placeholders present in instructions."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            instructions = ceremony.templates.get("main", "")
            # Should have at least one variable placeholder
            assert "{{" in instructions
            assert "}}" in instructions


class TestOutputFiles:
    """Test output file paths are defined."""

    def test_planning_ceremony_output(self, workflow_registry):
        """Test planning ceremony has output file defined."""
        workflow = workflow_registry.get_workflow("planning-ceremony")
        assert workflow is not None
        assert workflow.output_file is not None
        assert "planning" in workflow.output_file
        assert "{{epic_num}}" in workflow.output_file

    def test_standup_ceremony_output(self, workflow_registry):
        """Test standup ceremony has output file defined."""
        workflow = workflow_registry.get_workflow("standup-ceremony")
        assert workflow is not None
        assert workflow.output_file is not None
        assert "standup" in workflow.output_file
        assert "{{date}}" in workflow.output_file

    def test_retrospective_ceremony_output(self, workflow_registry):
        """Test retrospective ceremony has output file defined."""
        workflow = workflow_registry.get_workflow("retrospective-ceremony")
        assert workflow is not None
        assert workflow.output_file is not None
        assert "retro" in workflow.output_file or "retrospective" in workflow.output_file


class TestRequiredTools:
    """Test required tools are specified."""

    def test_all_ceremonies_require_ceremony_orchestrator(self, workflow_registry):
        """Test all ceremonies require ceremony_orchestrator tool."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.required_tools is not None
            assert "ceremony_orchestrator" in ceremony.required_tools

    def test_all_ceremonies_require_file_operations(self, workflow_registry):
        """Test all ceremonies require file read/write tools."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.required_tools is not None
            # Should have at least read_file and write_file
            assert "read_file" in ceremony.required_tools or "write_file" in ceremony.required_tools


class TestAgentAssignment:
    """Test agent assignment for ceremonies."""

    def test_all_ceremonies_have_agent(self, workflow_registry):
        """Test all ceremonies have an agent assigned."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.author is not None
            # Bob is the facilitator for all ceremonies
            assert ceremony.author == "Bob"

    def test_agent_in_participants(self, workflow_registry):
        """Test ceremony facilitator (agent) is in participants list."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.author in ceremony.metadata["participants"]


class TestWorkflowFlags:
    """Test workflow flags are set correctly."""

    def test_ceremonies_are_autonomous(self, workflow_registry):
        """Test ceremonies are marked as autonomous."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.autonomous is True

    def test_ceremonies_are_not_iterative(self, workflow_registry):
        """Test ceremonies are not marked as iterative."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.iterative is False

    def test_ceremonies_are_not_web_bundle(self, workflow_registry):
        """Test ceremonies are not marked as web_bundle."""
        ceremonies = workflow_registry.list_workflows(category="ceremonies")

        for ceremony in ceremonies:
            assert ceremony.web_bundle is False


class TestCeremonyMetadataValidationLogic:
    """Test the validation logic for ceremony metadata."""

    def test_validate_ceremony_metadata_with_valid_data(self, workflow_registry):
        """Test validation passes with valid ceremony metadata."""
        valid_metadata = {
            "ceremony_type": "planning",
            "participants": ["John", "Winston", "Bob"],
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(valid_metadata, "test-ceremony")
        assert result is True

    def test_validate_ceremony_metadata_missing_ceremony_type(self, workflow_registry):
        """Test validation fails when ceremony_type is missing."""
        invalid_metadata = {
            "participants": ["John", "Winston", "Bob"],
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_missing_participants(self, workflow_registry):
        """Test validation fails when participants is missing."""
        invalid_metadata = {
            "ceremony_type": "planning",
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_missing_trigger(self, workflow_registry):
        """Test validation fails when trigger is missing."""
        invalid_metadata = {
            "ceremony_type": "planning",
            "participants": ["John", "Winston", "Bob"]
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_invalid_ceremony_type(self, workflow_registry):
        """Test validation fails with invalid ceremony_type."""
        invalid_metadata = {
            "ceremony_type": "invalid_type",
            "participants": ["John", "Winston", "Bob"],
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_empty_participants(self, workflow_registry):
        """Test validation fails with empty participants list."""
        invalid_metadata = {
            "ceremony_type": "planning",
            "participants": [],
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_invalid_trigger(self, workflow_registry):
        """Test validation fails with invalid trigger."""
        invalid_metadata = {
            "ceremony_type": "planning",
            "participants": ["John", "Winston", "Bob"],
            "trigger": "invalid_trigger"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False

    def test_validate_ceremony_metadata_participants_not_list(self, workflow_registry):
        """Test validation fails when participants is not a list."""
        invalid_metadata = {
            "ceremony_type": "planning",
            "participants": "John, Winston, Bob",  # String instead of list
            "trigger": "epic_start"
        }

        result = workflow_registry._validate_ceremony_metadata(invalid_metadata, "test-ceremony")
        assert result is False
