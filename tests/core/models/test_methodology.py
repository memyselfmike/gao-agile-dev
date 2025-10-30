"""Tests for methodology models.

Story 5.1: Test ComplexityAssessment, WorkflowSequence, and supporting models.
"""

import pytest
from datetime import timedelta

from gao_dev.core.models.methodology import (
    ComplexityLevel,
    ProjectType,
    ComplexityAssessment,
    WorkflowStep,
    WorkflowSequence,
    ValidationResult,
)


class TestComplexityLevel:
    """Test ComplexityLevel enum."""

    def test_all_levels_exist(self):
        """Test all complexity levels are defined."""
        assert ComplexityLevel.TRIVIAL
        assert ComplexityLevel.SMALL
        assert ComplexityLevel.MEDIUM
        assert ComplexityLevel.LARGE
        assert ComplexityLevel.XLARGE

    def test_level_values(self):
        """Test complexity level values."""
        assert ComplexityLevel.TRIVIAL.value == "trivial"
        assert ComplexityLevel.SMALL.value == "small"
        assert ComplexityLevel.MEDIUM.value == "medium"
        assert ComplexityLevel.LARGE.value == "large"
        assert ComplexityLevel.XLARGE.value == "xlarge"


class TestProjectType:
    """Test ProjectType enum."""

    def test_all_types_exist(self):
        """Test all project types are defined."""
        assert ProjectType.WEB_APP
        assert ProjectType.API
        assert ProjectType.CLI
        assert ProjectType.LIBRARY
        assert ProjectType.MOBILE_APP
        assert ProjectType.DESKTOP_APP
        assert ProjectType.DATA_PIPELINE
        assert ProjectType.ML_MODEL
        assert ProjectType.UNKNOWN

    def test_type_values(self):
        """Test project type values."""
        assert ProjectType.WEB_APP.value == "web_app"
        assert ProjectType.API.value == "api"
        assert ProjectType.CLI.value == "cli"


class TestComplexityAssessment:
    """Test ComplexityAssessment dataclass."""

    def test_minimal_assessment(self):
        """Test creating assessment with minimal required fields."""
        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM
        )

        assert assessment.complexity_level == ComplexityLevel.MEDIUM
        assert assessment.project_type is None
        assert assessment.estimated_stories is None
        assert assessment.estimated_epics is None
        assert assessment.confidence == 0.5  # Default
        assert assessment.reasoning == ""  # Default
        assert assessment.metadata == {}  # Default

    def test_full_assessment(self):
        """Test creating assessment with all fields."""
        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.LARGE,
            project_type=ProjectType.WEB_APP,
            estimated_stories=20,
            estimated_epics=3,
            confidence=0.85,
            reasoning="Detected complex web application",
            metadata={"scale_level": 3, "methodology": "bmad"}
        )

        assert assessment.complexity_level == ComplexityLevel.LARGE
        assert assessment.project_type == ProjectType.WEB_APP
        assert assessment.estimated_stories == 20
        assert assessment.estimated_epics == 3
        assert assessment.confidence == 0.85
        assert assessment.reasoning == "Detected complex web application"
        assert assessment.metadata["scale_level"] == 3

    def test_confidence_validation_too_low(self):
        """Test confidence must be >= 0.0."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            ComplexityAssessment(
                complexity_level=ComplexityLevel.MEDIUM,
                confidence=-0.1
            )

    def test_confidence_validation_too_high(self):
        """Test confidence must be <= 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            ComplexityAssessment(
                complexity_level=ComplexityLevel.MEDIUM,
                confidence=1.1
            )

    def test_confidence_validation_edge_cases(self):
        """Test confidence edge cases (0.0 and 1.0 are valid)."""
        # 0.0 should be valid
        assessment1 = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            confidence=0.0
        )
        assert assessment1.confidence == 0.0

        # 1.0 should be valid
        assessment2 = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            confidence=1.0
        )
        assert assessment2.confidence == 1.0

    def test_estimated_stories_validation(self):
        """Test estimated_stories must be >= 0."""
        with pytest.raises(ValueError, match="Estimated stories must be >= 0"):
            ComplexityAssessment(
                complexity_level=ComplexityLevel.MEDIUM,
                estimated_stories=-1
            )

    def test_estimated_epics_validation(self):
        """Test estimated_epics must be >= 0."""
        with pytest.raises(ValueError, match="Estimated epics must be >= 0"):
            ComplexityAssessment(
                complexity_level=ComplexityLevel.MEDIUM,
                estimated_epics=-1
            )


class TestWorkflowStep:
    """Test WorkflowStep dataclass."""

    def test_minimal_workflow_step(self):
        """Test creating workflow step with minimal fields."""
        step = WorkflowStep(
            workflow_name="create-prd",
            phase="planning"
        )

        assert step.workflow_name == "create-prd"
        assert step.phase == "planning"
        assert step.required is True  # Default
        assert step.depends_on == []  # Default
        assert step.parallel_group is None  # Default

    def test_full_workflow_step(self):
        """Test creating workflow step with all fields."""
        step = WorkflowStep(
            workflow_name="implement-feature",
            phase="implementation",
            required=True,
            depends_on=["create-prd", "create-stories"],
            parallel_group=2
        )

        assert step.workflow_name == "implement-feature"
        assert step.phase == "implementation"
        assert step.required is True
        assert step.depends_on == ["create-prd", "create-stories"]
        assert step.parallel_group == 2

    def test_optional_workflow_step(self):
        """Test creating optional workflow step."""
        step = WorkflowStep(
            workflow_name="create-tech-spec",
            phase="solutioning",
            required=False
        )

        assert step.required is False


class TestWorkflowSequence:
    """Test WorkflowSequence dataclass."""

    def test_empty_workflow_sequence(self):
        """Test creating empty workflow sequence."""
        sequence = WorkflowSequence()

        assert sequence.workflows == []
        assert sequence.total_phases == 0
        assert sequence.estimated_duration is None
        assert sequence.can_parallelize is False
        assert sequence.metadata == {}

    def test_workflow_sequence_with_steps(self):
        """Test creating workflow sequence with steps."""
        steps = [
            WorkflowStep("create-prd", "planning"),
            WorkflowStep("create-stories", "planning"),
            WorkflowStep("implement", "implementation")
        ]

        sequence = WorkflowSequence(
            workflows=steps,
            total_phases=2,
            can_parallelize=False,
            metadata={"methodology": "bmad"}
        )

        assert len(sequence.workflows) == 3
        assert sequence.total_phases == 2
        assert sequence.can_parallelize is False
        assert sequence.metadata["methodology"] == "bmad"

    def test_workflow_sequence_with_duration(self):
        """Test workflow sequence with estimated duration."""
        sequence = WorkflowSequence(
            workflows=[WorkflowStep("implement", "implementation")],
            estimated_duration=timedelta(days=5)
        )

        assert sequence.estimated_duration == timedelta(days=5)

    def test_workflow_sequence_parallelizable(self):
        """Test workflow sequence that can parallelize."""
        steps = [
            WorkflowStep("task1", "phase1", parallel_group=1),
            WorkflowStep("task2", "phase1", parallel_group=1),
        ]

        sequence = WorkflowSequence(
            workflows=steps,
            can_parallelize=True
        )

        assert sequence.can_parallelize is True


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating valid validation result."""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_invalid_result_with_errors(self):
        """Test creating invalid validation result with errors."""
        result = ValidationResult(
            valid=False,
            errors=["Invalid scale_level: 5"],
            warnings=["Unknown project_type"]
        )

        assert result.valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert "Invalid scale_level" in result.errors[0]

    def test_valid_with_warnings(self):
        """Test valid result can have warnings."""
        result = ValidationResult(
            valid=True,
            warnings=["Deprecated config option used"]
        )

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
