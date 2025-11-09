"""Workflow selector for Adaptive Agile Methodology.

Selects appropriate workflows based on scale level.

Story 5.2: Extracted from brian_orchestrator.py
Story 28.2: Enhanced with ceremony injection
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
import structlog

from gao_dev.core.models.methodology import WorkflowStep
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.config_loader import ConfigLoader
from .scale_levels import ScaleLevel

logger = structlog.get_logger(__name__)


class WorkflowSelector:
    """Selects Adaptive Agile workflows based on scale level.

    Implements scale-adaptive workflow selection strategy where different
    scale levels get different workflow sequences.

    Story 28.2: Enhanced with ceremony injection capability.

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import (
            ScaleLevel,
            WorkflowSelector
        )

        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        # Returns: Planning + Implementation + Testing workflows + Ceremonies
        ```
    """

    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        workflow_registry: Optional[WorkflowRegistry] = None,
        config_dir: Optional[Path] = None
    ):
        """Initialize workflow selector with optional dependencies.

        Args:
            config_loader: Configuration loader instance
            workflow_registry: Workflow registry instance
            config_dir: Directory containing ceremony_triggers.yaml
        """
        self.config_loader = config_loader
        self.workflow_registry = workflow_registry
        self.ceremony_config = self._load_ceremony_config(config_dir)

    def _load_ceremony_config(self, config_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Load ceremony configuration from YAML.

        Args:
            config_dir: Directory containing ceremony_triggers.yaml

        Returns:
            Dictionary with ceremony configuration
        """
        if config_dir is None:
            # Default to project root config directory
            config_dir = Path(__file__).parent.parent.parent.parent / "config"

        config_file = config_dir / "ceremony_triggers.yaml"
        if not config_file.exists():
            logger.warning(
                "ceremony_config_not_found",
                path=str(config_file),
                message="Using default ceremony configuration"
            )
            return self._get_default_ceremony_config()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(
                "ceremony_config_load_error",
                path=str(config_file),
                error=str(e),
                message="Using default ceremony configuration"
            )
            return self._get_default_ceremony_config()

    def _get_default_ceremony_config(self) -> Dict[str, Any]:
        """Get default ceremony configuration.

        Returns:
            Default ceremony trigger configuration
        """
        return {
            "triggers": {
                "planning": {
                    "level_2": {"required": False, "trigger": "epic_start"},
                    "level_3": {"required": True, "trigger": "epic_start"},
                    "level_4": {"required": True, "trigger": "epic_start"}
                },
                "standup": {
                    "level_2": {"interval": 3, "threshold": 3},
                    "level_3": {"interval": 2, "quality_gate_trigger": True},
                    "level_4": {"interval": 1, "daily": True}
                },
                "retrospective": {
                    "level_1": {"trigger": "repeated_failure", "failure_threshold": 2},
                    "level_2": {"trigger": "epic_completion", "required": True},
                    "level_3": {"triggers": ["mid_epic_checkpoint", "epic_completion"]},
                    "level_4": {"triggers": ["phase_end", "epic_completion"]}
                }
            },
            "features": {
                "enable_ceremony_integration": True
            }
        }

    def select_workflows(
        self,
        scale_level: ScaleLevel,
        include_ceremonies: bool = True
    ) -> List[WorkflowStep]:
        """Select workflows for given scale level with optional ceremony injection.

        Args:
            scale_level: Adaptive Agile scale level (0-4)
            include_ceremonies: Whether to inject ceremonies (default: True)

        Returns:
            List of WorkflowSteps in execution order including ceremonies

        Raises:
            ValueError: If scale_level is invalid
        """
        # Check feature flag
        feature_enabled = self.ceremony_config.get("features", {}).get(
            "enable_ceremony_integration", True
        )
        if include_ceremonies and not feature_enabled:
            logger.info(
                "ceremony_integration_disabled",
                message="Skipping ceremony injection (feature flag off)"
            )
            include_ceremonies = False

        # Get base workflows
        workflows = self._select_base_workflows(scale_level)

        # Inject ceremonies if requested
        if include_ceremonies:
            workflows = self._inject_ceremonies(workflows, scale_level)

        return workflows

    def _select_base_workflows(self, scale_level: ScaleLevel) -> List[WorkflowStep]:
        """Select base workflows without ceremonies.

        Args:
            scale_level: Adaptive Agile scale level (0-4)

        Returns:
            List of base WorkflowSteps

        Raises:
            ValueError: If scale_level is invalid
        """
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            return self._level_0_workflows()
        elif scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            return self._level_1_workflows()
        elif scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return self._level_2_workflows()
        elif scale_level == ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            return self._level_3_workflows()
        elif scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            return self._level_4_workflows()
        else:
            raise ValueError(f"Invalid scale level: {scale_level}")

    def _level_0_workflows(self) -> List[WorkflowStep]:
        """Level 0: Chore - Direct implementation.

        Minimal workflow for simple tasks like typos, config changes.
        No planning needed.

        Returns:
            Single implementation workflow
        """
        return [
            WorkflowStep(
                workflow_name="direct-implementation",
                phase="implementation",
                required=True
            )
        ]

    def _level_1_workflows(self) -> List[WorkflowStep]:
        """Level 1: Bug Fix - Quick fix with verification.

        Simple workflow for bug fixes and small changes.
        Analyze, fix, verify.

        Returns:
            Analysis, implementation, verification workflows
        """
        return [
            WorkflowStep(
                workflow_name="analyze-bug",
                phase="analysis",
                required=True
            ),
            WorkflowStep(
                workflow_name="implement-fix",
                phase="implementation",
                required=True,
                depends_on=["analyze-bug"]
            ),
            WorkflowStep(
                workflow_name="verify-fix",
                phase="testing",
                required=True,
                depends_on=["implement-fix"]
            )
        ]

    def _level_2_workflows(self) -> List[WorkflowStep]:
        """Level 2: Small Feature - PRD → Stories → Implementation.

        Basic feature workflow with planning and implementation.
        Suitable for 3-8 story features.

        Returns:
            Planning, implementation, testing workflows
        """
        return [
            WorkflowStep(
                workflow_name="create-prd",
                phase="planning",
                required=True
            ),
            WorkflowStep(
                workflow_name="create-stories",
                phase="planning",
                required=True,
                depends_on=["create-prd"]
            ),
            WorkflowStep(
                workflow_name="implement-stories",
                phase="implementation",
                required=True,
                depends_on=["create-stories"]
            ),
            WorkflowStep(
                workflow_name="test-feature",
                phase="testing",
                required=True,
                depends_on=["implement-stories"]
            )
        ]

    def _level_3_workflows(self) -> List[WorkflowStep]:
        """Level 3: Medium Feature - Full workflow phases.

        Complete workflow with planning, solutioning, implementation.
        Suitable for 12-20 story complex features.

        Returns:
            Full workflow sequence across all phases
        """
        return [
            # Planning Phase
            WorkflowStep(
                workflow_name="create-prd",
                phase="planning",
                required=True
            ),
            WorkflowStep(
                workflow_name="create-epics",
                phase="planning",
                required=True,
                depends_on=["create-prd"]
            ),
            WorkflowStep(
                workflow_name="create-stories",
                phase="planning",
                required=True,
                depends_on=["create-epics"]
            ),
            # Solutioning Phase
            WorkflowStep(
                workflow_name="create-architecture",
                phase="solutioning",
                required=True,
                depends_on=["create-stories"]
            ),
            WorkflowStep(
                workflow_name="create-tech-spec",
                phase="solutioning",
                required=False,  # Optional for level 3
                depends_on=["create-architecture"]
            ),
            # Implementation Phase
            WorkflowStep(
                workflow_name="implement-stories",
                phase="implementation",
                required=True,
                depends_on=["create-architecture"]
            ),
            WorkflowStep(
                workflow_name="code-review",
                phase="implementation",
                required=True,
                depends_on=["implement-stories"]
            ),
            # Testing Phase
            WorkflowStep(
                workflow_name="integration-testing",
                phase="testing",
                required=True,
                depends_on=["code-review"]
            )
        ]

    def _level_4_workflows(self) -> List[WorkflowStep]:
        """Level 4: Greenfield - All phases + extensive planning.

        Complete lifecycle for greenfield applications.
        Suitable for 40+ story projects.

        Returns:
            Comprehensive workflow sequence with all phases
        """
        return [
            # Analysis Phase (Optional)
            WorkflowStep(
                workflow_name="research",
                phase="analysis",
                required=False
            ),
            WorkflowStep(
                workflow_name="product-brief",
                phase="analysis",
                required=False,
                depends_on=["research"]
            ),
            # Planning Phase
            WorkflowStep(
                workflow_name="create-prd",
                phase="planning",
                required=True
            ),
            WorkflowStep(
                workflow_name="create-epics",
                phase="planning",
                required=True,
                depends_on=["create-prd"]
            ),
            WorkflowStep(
                workflow_name="create-stories",
                phase="planning",
                required=True,
                depends_on=["create-epics"]
            ),
            # Solutioning Phase
            WorkflowStep(
                workflow_name="create-architecture",
                phase="solutioning",
                required=True,
                depends_on=["create-stories"]
            ),
            WorkflowStep(
                workflow_name="create-tech-spec",
                phase="solutioning",
                required=True,
                depends_on=["create-architecture"]
            ),
            WorkflowStep(
                workflow_name="design-database",
                phase="solutioning",
                required=True,
                depends_on=["create-tech-spec"]
            ),
            WorkflowStep(
                workflow_name="design-api",
                phase="solutioning",
                required=False,  # Optional
                depends_on=["design-database"]
            ),
            # Implementation Phase
            WorkflowStep(
                workflow_name="implement-stories",
                phase="implementation",
                required=True,
                depends_on=["design-database"]
            ),
            WorkflowStep(
                workflow_name="code-review",
                phase="implementation",
                required=True,
                depends_on=["implement-stories"]
            ),
            WorkflowStep(
                workflow_name="create-tests",
                phase="implementation",
                required=True,
                depends_on=["code-review"]
            ),
            # Testing Phase
            WorkflowStep(
                workflow_name="integration-testing",
                phase="testing",
                required=True,
                depends_on=["create-tests"]
            ),
            WorkflowStep(
                workflow_name="e2e-testing",
                phase="testing",
                required=True,
                depends_on=["integration-testing"]
            )
        ]

    # Ceremony Injection Methods (Story 28.2)

    def _inject_ceremonies(
        self,
        workflows: List[WorkflowStep],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        """Inject ceremony workflows at appropriate points.

        Strategy:
        - Planning: After PRD/epics creation
        - Standup: After implementation workflows
        - Retrospective: After testing/completion

        Args:
            workflows: Base workflow steps
            scale_level: Current scale level

        Returns:
            Enhanced workflow list with ceremonies injected
        """
        if scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            # Level 0-1: No automatic ceremonies (except retro on failure)
            if scale_level == ScaleLevel.LEVEL_1_BUG_FIX and self._should_have_retrospective(scale_level):
                return self._inject_retrospective_only(workflows, scale_level)
            return workflows

        enhanced = []

        for i, workflow in enumerate(workflows):
            enhanced.append(workflow)

            # Inject planning ceremony after PRD/epics
            if workflow.workflow_name in ["create-prd", "create-epics"]:
                if self._should_have_planning(scale_level):
                    planning = self._create_planning_ceremony(
                        scale_level,
                        depends_on=[workflow.workflow_name]
                    )
                    enhanced.append(planning)
                    logger.info(
                        "planning_ceremony_injected",
                        scale_level=scale_level.value,
                        after_workflow=workflow.workflow_name
                    )

            # Inject standup after implementation
            if workflow.workflow_name in ["implement-stories", "story-development"]:
                if self._should_have_standup(scale_level):
                    standup = self._create_standup_ceremony(
                        scale_level,
                        depends_on=[workflow.workflow_name]
                    )
                    enhanced.append(standup)
                    logger.info(
                        "standup_ceremony_injected",
                        scale_level=scale_level.value,
                        after_workflow=workflow.workflow_name
                    )

            # Inject retrospective after testing
            if workflow.workflow_name in ["test-feature", "integration-testing", "code-review"]:
                if self._should_have_retrospective(scale_level):
                    retro = self._create_retrospective_ceremony(
                        scale_level,
                        depends_on=[workflow.workflow_name]
                    )
                    enhanced.append(retro)
                    logger.info(
                        "retrospective_ceremony_injected",
                        scale_level=scale_level.value,
                        after_workflow=workflow.workflow_name
                    )

        return enhanced

    def _inject_retrospective_only(
        self,
        workflows: List[WorkflowStep],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        """Inject only retrospective ceremony for Level 1.

        Args:
            workflows: Base workflow steps
            scale_level: Current scale level

        Returns:
            Workflows with retrospective appended
        """
        if not workflows:
            return workflows

        # Append retrospective after last workflow
        last_workflow = workflows[-1]
        retro = self._create_retrospective_ceremony(
            scale_level,
            depends_on=[last_workflow.workflow_name]
        )
        return workflows + [retro]

    def _should_have_planning(self, scale_level: ScaleLevel) -> bool:
        """Check if planning ceremony should be included.

        Args:
            scale_level: Current scale level

        Returns:
            True if planning ceremony should be injected
        """
        config = self.ceremony_config.get("triggers", {}).get("planning", {})
        level_key = f"level_{scale_level.value}"

        if level_key not in config:
            return False

        return bool(config[level_key].get("required", False))

    def _should_have_standup(self, scale_level: ScaleLevel) -> bool:
        """Check if standup ceremony should be included.

        Args:
            scale_level: Current scale level

        Returns:
            True if standup ceremony should be injected
        """
        if scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return False

        return True  # Conditional based on interval, always available for L2+

    def _should_have_retrospective(self, scale_level: ScaleLevel) -> bool:
        """Check if retrospective ceremony should be included.

        Args:
            scale_level: Current scale level

        Returns:
            True if retrospective ceremony should be injected
        """
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            return False

        # Level 1+: Retrospective available (conditional on triggers)
        return True

    def _create_planning_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create planning ceremony workflow step.

        Args:
            scale_level: Current scale level
            depends_on: List of workflow names this depends on

        Returns:
            Planning ceremony WorkflowStep
        """
        return WorkflowStep(
            workflow_name="planning-ceremony",
            phase="ceremonies",
            required=(scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE),
            depends_on=depends_on
        )

    def _create_standup_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create standup ceremony workflow step.

        Args:
            scale_level: Current scale level
            depends_on: List of workflow names this depends on

        Returns:
            Standup ceremony WorkflowStep
        """
        return WorkflowStep(
            workflow_name="standup-ceremony",
            phase="ceremonies",
            required=False,  # Conditional based on trigger
            depends_on=depends_on
        )

    def _create_retrospective_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create retrospective ceremony workflow step.

        Args:
            scale_level: Current scale level
            depends_on: List of workflow names this depends on

        Returns:
            Retrospective ceremony WorkflowStep
        """
        return WorkflowStep(
            workflow_name="retrospective-ceremony",
            phase="ceremonies",
            required=(scale_level >= ScaleLevel.LEVEL_2_SMALL_FEATURE),
            depends_on=depends_on
        )
