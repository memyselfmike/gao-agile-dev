"""
Tests for QualityGateManager service.

Tests artifact validation, quality gate logic, and event publishing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
import tempfile
import shutil

from gao_dev.core.services.quality_gate import (
    QualityGateManager,
    QualityGateResult,
    QualityGateStatus
)
from gao_dev.core.interfaces.event_bus import IEventBus


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    bus = MagicMock(spec=IEventBus)
    bus.publish = MagicMock()
    return bus


@pytest.fixture
def quality_gate_manager(temp_project_dir, mock_event_bus):
    """Create QualityGateManager with mocked dependencies."""
    return QualityGateManager(
        project_root=temp_project_dir,
        event_bus=mock_event_bus
    )


class TestQualityGateInitialization:
    """Test QualityGateManager initialization."""

    def test_initialization_with_default_config(self, temp_project_dir, mock_event_bus):
        """Test initializing manager with default configuration."""
        # Act
        manager = QualityGateManager(
            project_root=temp_project_dir,
            event_bus=mock_event_bus
        )

        # Assert
        assert manager.project_root == temp_project_dir
        assert manager.event_bus == mock_event_bus
        assert "prd" in manager.gates
        assert "create-story" in manager.gates
        assert "architecture" in manager.gates

    def test_initialization_with_custom_config(self, temp_project_dir, mock_event_bus):
        """Test initializing manager with custom gate configuration."""
        # Arrange
        custom_gates = {
            "prd": ["docs/PRD.md", "docs/requirements.md"],
            "build": ["dist/app.jar"]
        }

        # Act
        manager = QualityGateManager(
            project_root=temp_project_dir,
            event_bus=mock_event_bus,
            gates_config=custom_gates
        )

        # Assert
        assert manager.gates == custom_gates
        assert len(manager.gates) == 2


class TestArtifactValidation:
    """Test artifact validation logic."""

    def test_validate_artifacts_all_present(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test validation when all artifacts are present."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "PRD.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.success is True
        assert result.action == "continue"
        assert len(result.missing_artifacts) == 0

        # Verify event published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "QualityGatePassed"

    def test_validate_artifacts_missing(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test validation when artifacts are missing."""
        # Arrange - don't create any files

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        assert result.status == QualityGateStatus.FAILED
        assert result.success is False
        assert result.action == "retry"
        assert "docs/PRD.md" in result.missing_artifacts

        # Verify event published
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "QualityGateFailed"

    def test_validate_artifacts_no_gates_configured(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test validation when workflow has no configured gates."""
        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="unknown-workflow"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.success is True
        assert result.action == "continue"

        # Verify event published
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "QualityGateStarted"

    def test_validate_artifacts_with_custom_list(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test validation with custom artifact list."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "custom.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd",
            expected_artifacts=["docs/custom.md"]
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.success is True
        assert len(result.missing_artifacts) == 0


class TestPRDWorkflowGates:
    """Test PRD workflow-specific quality gate logic."""

    def test_prd_with_alternative_artifact(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test PRD workflow adapts when epics.md exists instead."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "epics.md").touch()
        # Don't create PRD.md

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        assert result.status == QualityGateStatus.ADAPTED
        assert result.action == "adapt"
        assert "epics.md" in result.adaptation_note
        assert "docs/PRD.md" in result.missing_artifacts

    def test_prd_no_artifacts_at_all(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test PRD workflow retries when neither PRD nor epics exist."""
        # Arrange - no files created

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        assert result.status == QualityGateStatus.FAILED
        assert result.action == "retry"



class TestCreateStoryWorkflowGates:
    """Test create-story workflow-specific quality gate logic."""

    def test_create_story_with_stories_present(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test create-story when story files exist."""
        # Arrange
        (temp_project_dir / "docs" / "stories" / "epic-1").mkdir(parents=True)
        (temp_project_dir / "docs" / "stories" / "epic-1" / "story-1.1.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="create-story"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.action == "continue"
        assert len(result.missing_artifacts) == 0

    def test_create_story_no_stories_directory(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test create-story when stories directory missing."""
        # Arrange - no stories directory

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="create-story"
        )

        # Assert
        assert result.status == QualityGateStatus.FAILED
        assert result.action == "retry"
        assert "docs/stories" in result.missing_artifacts

    def test_create_story_empty_directory(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test create-story when stories directory is empty."""
        # Arrange
        (temp_project_dir / "docs" / "stories").mkdir(parents=True)
        # Don't create any story files

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="create-story"
        )

        # Assert
        assert result.status == QualityGateStatus.FAILED
        assert result.action == "retry"



class TestArchitectureWorkflowGates:
    """Test architecture workflow quality gates."""

    def test_architecture_with_file_present(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test architecture workflow when file exists."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "ARCHITECTURE.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="architecture"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.action == "continue"

    def test_architecture_with_file_missing(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test architecture workflow when file missing."""
        # Arrange - no ARCHITECTURE.md

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="architecture"
        )

        # Assert
        assert result.status == QualityGateStatus.ADAPTED
        assert result.action == "adapt"



class TestEventPublishing:
    """Test quality gate event publishing."""

    def test_publishes_passed_event(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test that QualityGatePassed event is published on success."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "PRD.md").touch()

        # Act
        quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "QualityGatePassed"
        assert event.data["workflow_name"] == "prd"

    def test_publishes_failed_event(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test that QualityGateFailed event is published on failure."""
        # Arrange - no artifacts

        # Act
        quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        event = mock_event_bus.publish.call_args[0][0]
        assert event.type == "QualityGateFailed"
        assert "missing_artifacts" in event.data

    def test_event_includes_metadata(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test that events include proper metadata."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "PRD.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        event = mock_event_bus.publish.call_args[0][0]
        assert "timestamp" in event.data or result.timestamp is not None
        assert event.data["workflow_name"] == "prd"


class TestQualityGateConfiguration:
    """Test runtime quality gate configuration."""

    def test_add_workflow_gates(self, quality_gate_manager):
        """Test adding gates for a new workflow."""
        # Arrange
        new_gates = ["dist/app.jar", "dist/app.map"]

        # Act
        quality_gate_manager.add_workflow_gates(
            workflow_name="build",
            artifacts=new_gates
        )

        # Assert
        assert quality_gate_manager.gates["build"] == new_gates

    def test_get_workflow_gates(self, quality_gate_manager):
        """Test getting gates for a workflow."""
        # Act
        gates = quality_gate_manager.get_workflow_gates("prd")

        # Assert
        assert "docs/PRD.md" in gates

    def test_get_nonexistent_workflow_gates(self, quality_gate_manager):
        """Test getting gates for nonexistent workflow returns empty list."""
        # Act
        gates = quality_gate_manager.get_workflow_gates("nonexistent")

        # Assert
        assert gates == []

    def test_disable_workflow_gates(self, quality_gate_manager):
        """Test disabling gates for a workflow."""
        # Act
        quality_gate_manager.disable_workflow_gates("prd")

        # Assert
        assert quality_gate_manager.gates["prd"] == []

    def test_disabled_workflow_passes_validation(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test that disabled workflow gates always pass validation."""
        # Arrange
        quality_gate_manager.disable_workflow_gates("prd")

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="prd"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.action == "continue"


class TestQualityGateResult:
    """Test QualityGateResult dataclass."""

    def test_result_creation(self):
        """Test creating a QualityGateResult."""
        # Act
        result = QualityGateResult(
            workflow_name="prd",
            status=QualityGateStatus.PASSED,
            success=True,
            missing_artifacts=[],
            action="continue"
        )

        # Assert
        assert result.workflow_name == "prd"
        assert result.status == QualityGateStatus.PASSED
        assert result.timestamp is not None

    def test_result_with_missing_artifacts(self):
        """Test result with missing artifacts."""
        # Act
        result = QualityGateResult(
            workflow_name="prd",
            status=QualityGateStatus.FAILED,
            success=False,
            missing_artifacts=["docs/PRD.md", "docs/requirements.md"],
            action="retry"
        )

        # Assert
        assert len(result.missing_artifacts) == 2
        assert "docs/PRD.md" in result.missing_artifacts

    def test_result_with_adaptation_note(self):
        """Test result with adaptation note."""
        # Act
        result = QualityGateResult(
            workflow_name="prd",
            status=QualityGateStatus.ADAPTED,
            success=False,
            missing_artifacts=["docs/PRD.md"],
            action="adapt",
            adaptation_note="Using alternative artifact"
        )

        # Assert
        assert result.adaptation_note == "Using alternative artifact"


class TestMultipleArtifacts:
    """Test validation with multiple artifacts."""

    def test_multiple_artifacts_all_present(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test validation when multiple artifacts are present."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "file1.md").touch()
        (temp_project_dir / "docs" / "file2.md").touch()

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="custom",
            expected_artifacts=["docs/file1.md", "docs/file2.md"]
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert len(result.missing_artifacts) == 0

    def test_multiple_artifacts_some_missing(
        self,
        quality_gate_manager,
        temp_project_dir,
        mock_event_bus
    ):
        """Test validation when some artifacts are missing."""
        # Arrange
        (temp_project_dir / "docs").mkdir()
        (temp_project_dir / "docs" / "file1.md").touch()
        # file2.md not created

        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="custom",
            expected_artifacts=["docs/file1.md", "docs/file2.md"]
        )

        # Assert
        assert result.status == QualityGateStatus.ADAPTED
        assert "docs/file2.md" in result.missing_artifacts
        assert "docs/file1.md" not in result.missing_artifacts


class TestDevStoryWorkflow:
    """Test dev-story workflow which has no specific artifacts."""

    def test_dev_story_no_gates_configured(
        self,
        quality_gate_manager,
        mock_event_bus
    ):
        """Test dev-story workflow which has no gates."""
        # Act
        result = quality_gate_manager.validate_artifacts(
            workflow_name="dev-story"
        )

        # Assert
        assert result.status == QualityGateStatus.PASSED
        assert result.action == "continue"
        assert len(result.missing_artifacts) == 0
