"""Workflow selector for Adaptive Agile Methodology.

Selects appropriate workflows based on scale level.

Story 5.2: Extracted from brian_orchestrator.py
"""

from typing import List

from gao_dev.core.models.methodology import WorkflowStep
from .scale_levels import ScaleLevel


class WorkflowSelector:
    """Selects Adaptive Agile workflows based on scale level.

    Implements scale-adaptive workflow selection strategy where different
    scale levels get different workflow sequences.

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import (
            ScaleLevel,
            WorkflowSelector
        )

        selector = WorkflowSelector()
        workflows = selector.select_workflows(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        # Returns: Planning + Implementation + Testing workflows
        ```
    """

    def select_workflows(self, scale_level: ScaleLevel) -> List[WorkflowStep]:
        """Select workflows for given scale level.

        Args:
            scale_level: Adaptive Agile scale level (0-4)

        Returns:
            List of WorkflowSteps in execution order

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
