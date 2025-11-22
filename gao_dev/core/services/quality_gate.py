"""
QualityGateManager Service - Validates workflow artifact outputs.

Extracted from GAODevOrchestrator (Epic 6, Story 6.4) to achieve SOLID principles.

Responsibilities:
- Validate workflow artifacts (files, directories, content)
- Check artifact existence and structure
- Publish quality gate validation events
- Support configurable quality gates

NOT responsible for:
- Workflow execution (WorkflowCoordinator)
- Story lifecycle (StoryLifecycleManager)
- Subprocess execution (ProcessExecutor)
- High-level orchestration (stays in orchestrator)
"""

import structlog
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..interfaces.event_bus import IEventBus
from ..events.event_bus import Event

logger = structlog.get_logger()


class QualityGateStatus(str, Enum):
    """Status of quality gate validation."""
    PASSED = "passed"
    FAILED = "failed"
    ADAPTED = "adapted"


@dataclass
class QualityGateResult:
    """Result of quality gate validation."""
    workflow_name: str
    status: QualityGateStatus
    success: bool
    missing_artifacts: List[str]
    action: str  # "continue", "retry", "adapt"
    adaptation_note: str = ""
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()


class QualityGateManager:
    """
    Validates workflow artifacts meet quality standards.

    Single Responsibility: Validate that workflows produced expected artifacts
    (files, directories, content) and report validation results.

    This service was extracted from GAODevOrchestrator (Epic 6, Story 6.4) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Validate workflow artifacts (existence, structure, content)
    - Configure quality gates per workflow
    - Publish validation events
    - Support alternative artifacts with adaptation logic

    NOT responsible for:
    - Workflow execution (WorkflowCoordinator)
    - Story lifecycle (StoryLifecycleManager)
    - File operations (Repository layer)
    - Subprocess execution (ProcessExecutor)

    Example:
        ```python
        quality_gate = QualityGateManager(
            project_root=Path("/project"),
            event_bus=bus
        )

        result = await quality_gate.validate_artifacts(
            workflow_name="prd",
            expected_artifacts=["docs/PRD.md"]
        )

        if result.status == QualityGateStatus.PASSED:
            print("Quality gate passed")
        ```
    """

    # Quality gate configurations per workflow
    DEFAULT_GATES: Dict[str, List[str]] = {
        "prd": ["docs/PRD.md"],
        "create-story": ["docs/stories"],
        "dev-story": [],  # dev-story artifacts vary
        "architecture": ["docs/ARCHITECTURE.md"],
    }

    def __init__(
        self,
        project_root: Path,
        event_bus: IEventBus,
        gates_config: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize quality gate manager with injected dependencies.

        Args:
            project_root: Root directory of the project
            event_bus: Event bus for publishing validation events
            gates_config: Optional custom quality gates configuration
        """
        self.project_root = project_root
        self.event_bus = event_bus
        self.gates = gates_config or self.DEFAULT_GATES

        logger.info(
            "quality_gate_manager_initialized",
            project_root=str(project_root),
            configured_gates=len(self.gates)
        )

    def validate_artifacts(
        self,
        workflow_name: str,
        expected_artifacts: Optional[List[str]] = None
    ) -> QualityGateResult:
        """
        Validate workflow produced expected artifacts.

        Checks if expected files/directories exist and applies logic to decide
        whether to continue, retry, or adapt.

        Args:
            workflow_name: Name of the workflow that executed
            expected_artifacts: Optional override of expected artifacts (uses config if not provided)

        Returns:
            QualityGateResult with validation status and details
        """
        logger.info(
            "validating_artifacts",
            workflow_name=workflow_name,
            has_overrides=expected_artifacts is not None
        )

        # Use provided artifacts or lookup from config
        artifacts = expected_artifacts or self.gates.get(workflow_name, [])

        if not artifacts:
            # No specific expectations for this workflow
            result = QualityGateResult(
                workflow_name=workflow_name,
                status=QualityGateStatus.PASSED,
                success=True,
                missing_artifacts=[],
                action="continue"
            )

            self.event_bus.publish(Event(
                type="QualityGateStarted",
                data={
                    "workflow_name": workflow_name,
                    "status": "no_gates_configured"
                }
            ))

            logger.info(
                "no_quality_gates_configured",
                workflow_name=workflow_name
            )

            return result

        # Check artifact existence
        missing = self._check_artifacts(artifacts)

        # For create-story workflow, we need to check directory content even if exists
        if workflow_name == "create-story" and not missing:
            # Directory exists, but we need to check if it has story files
            stories_dir = self.project_root / "docs" / "stories"
            if stories_dir.exists():
                story_files = list(stories_dir.glob("epic-*/story-*.md"))
                if not story_files:
                    # Directory exists but is empty - treat as missing
                    missing = ["docs/stories (empty)"]

        if not missing:
            # All artifacts exist - validation passed
            result = QualityGateResult(
                workflow_name=workflow_name,
                status=QualityGateStatus.PASSED,
                success=True,
                missing_artifacts=[],
                action="continue"
            )

            self.event_bus.publish(Event(
                type="QualityGatePassed",
                data={
                    "workflow_name": workflow_name,
                    "artifacts_found": len(artifacts)
                }
            ))

            logger.info(
                "quality_gate_passed",
                workflow_name=workflow_name,
                artifacts_found=len(artifacts)
            )

            return result

        # Some artifacts missing - apply workflow-specific logic
        result = self._apply_gate_logic(workflow_name, missing)

        self.event_bus.publish(Event(
            type="QualityGateFailed",
            data={
                "workflow_name": workflow_name,
                "missing_artifacts": missing,
                "action": result.action,
                "status": result.status.value
            }
        ))

        logger.warning(
            "quality_gate_failed",
            workflow_name=workflow_name,
            missing_count=len(missing),
            action=result.action
        )

        return result

    def _check_artifacts(self, artifacts: List[str]) -> List[str]:
        """
        Check which artifacts are missing.

        Args:
            artifacts: List of artifact paths (relative to project root)

        Returns:
            List of missing artifact paths
        """
        missing = []

        for artifact_path in artifacts:
            full_path = self.project_root / artifact_path
            if not full_path.exists():
                missing.append(artifact_path)

        return missing

    def _apply_gate_logic(
        self,
        workflow_name: str,
        missing_artifacts: List[str]
    ) -> QualityGateResult:
        """
        Apply workflow-specific logic for handling missing artifacts.

        Some artifacts can have alternatives or be optional.

        Args:
            workflow_name: Name of the workflow
            missing_artifacts: List of missing artifact paths

        Returns:
            QualityGateResult with decision logic applied
        """
        # PRD workflow: Check for epics.md alternative
        if workflow_name == "prd":
            epics_file = self.project_root / "docs" / "epics.md"
            if epics_file.exists():
                logger.info(
                    "found_alternative_artifact",
                    workflow=workflow_name,
                    expected="docs/PRD.md",
                    found="docs/epics.md"
                )
                return QualityGateResult(
                    workflow_name=workflow_name,
                    status=QualityGateStatus.ADAPTED,
                    success=False,
                    missing_artifacts=missing_artifacts,
                    action="adapt",
                    adaptation_note="epics.md found instead of PRD.md, proceeding with epics"
                )
            else:
                # No PRD and no epics - need retry
                return QualityGateResult(
                    workflow_name=workflow_name,
                    status=QualityGateStatus.FAILED,
                    success=False,
                    missing_artifacts=missing_artifacts,
                    action="retry",
                    adaptation_note="PRD and epics.md both missing"
                )

        # create-story workflow: Check for story files
        if workflow_name == "create-story":
            stories_dir = self.project_root / "docs" / "stories"
            if stories_dir.exists():
                # Directory exists, check if it has any story files
                story_files = list(stories_dir.glob("epic-*/story-*.md"))
                if story_files:
                    logger.info(
                        "story_directory_has_content",
                        workflow=workflow_name,
                        story_count=len(story_files)
                    )
                    return QualityGateResult(
                        workflow_name=workflow_name,
                        status=QualityGateStatus.PASSED,
                        success=True,
                        missing_artifacts=[],
                        action="continue"
                    )

            # Directory missing or empty - need retry
            return QualityGateResult(
                workflow_name=workflow_name,
                status=QualityGateStatus.FAILED,
                success=False,
                missing_artifacts=missing_artifacts,
                action="retry",
                adaptation_note="stories directory is empty or missing"
            )

        # Default: adapt (continue with what we have)
        return QualityGateResult(
            workflow_name=workflow_name,
            status=QualityGateStatus.ADAPTED,
            success=False,
            missing_artifacts=missing_artifacts,
            action="adapt",
            adaptation_note=f"Some artifacts missing for {workflow_name}, continuing anyway"
        )

    def add_workflow_gates(
        self,
        workflow_name: str,
        artifacts: List[str]
    ) -> None:
        """
        Add or update quality gates for a workflow.

        Allows runtime configuration of quality gates.

        Args:
            workflow_name: Name of the workflow
            artifacts: List of expected artifact paths
        """
        self.gates[workflow_name] = artifacts

        logger.info(
            "workflow_gates_configured",
            workflow_name=workflow_name,
            artifact_count=len(artifacts)
        )

    def get_workflow_gates(self, workflow_name: str) -> List[str]:
        """
        Get quality gates for a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of expected artifact paths
        """
        return self.gates.get(workflow_name, [])

    def disable_workflow_gates(self, workflow_name: str) -> None:
        """
        Disable quality gates for a workflow.

        Args:
            workflow_name: Name of the workflow
        """
        if workflow_name in self.gates:
            self.gates[workflow_name] = []

        logger.info(
            "workflow_gates_disabled",
            workflow_name=workflow_name
        )
