"""
Workflow build strategies implementing the Strategy Pattern.

This module provides concrete implementations of IWorkflowBuildStrategy
for different workflow selection scenarios: scale-level based, project-type
based, and custom workflow sequences.

Story 5.4: Updated to use orchestrator.models instead of brian_orchestrator.
"""

from typing import List, Optional, Dict
import structlog

from ..interfaces.workflow import IWorkflowBuildStrategy, IWorkflowRegistry
from ..models.workflow_context import WorkflowContext
from ..models.workflow import WorkflowInfo
from ...orchestrator.models import (
    ScaleLevel,
    ProjectType,
    WorkflowSequence
)

logger = structlog.get_logger()


class WorkflowStrategyRegistry:
    """
    Registry for workflow build strategies.

    Manages strategy registration and selection based on context.
    Strategies are selected by priority, with highest priority strategies
    that can handle the context being chosen first.
    """

    def __init__(self):
        self._strategies: List[IWorkflowBuildStrategy] = []

    def register_strategy(self, strategy: IWorkflowBuildStrategy) -> None:
        """
        Register a workflow build strategy.

        Args:
            strategy: Strategy to register

        Raises:
            TypeError: If strategy doesn't implement IWorkflowBuildStrategy
        """
        if not isinstance(strategy, IWorkflowBuildStrategy):
            raise TypeError("Strategy must implement IWorkflowBuildStrategy interface")

        self._strategies.append(strategy)
        # Sort by priority (highest first)
        self._strategies.sort(key=lambda s: s.get_priority(), reverse=True)

        logger.info(
            "workflow_strategy_registered",
            strategy=strategy.__class__.__name__,
            priority=strategy.get_priority()
        )

    def get_strategy(self, context: WorkflowContext) -> Optional[IWorkflowBuildStrategy]:
        """
        Get the best strategy for the given context.

        Returns the highest priority strategy that can handle the context.

        Args:
            context: Workflow context

        Returns:
            IWorkflowBuildStrategy if a matching strategy found, None otherwise
        """
        for strategy in self._strategies:
            if strategy.can_handle(context):
                logger.info(
                    "workflow_strategy_selected",
                    strategy=strategy.__class__.__name__,
                    scale_level=context.scale_level,
                    project_type=context.project_type.value if context.project_type else None
                )
                return strategy

        logger.warning("no_workflow_strategy_found", context=context)
        return None

    def list_strategies(self) -> List[str]:
        """
        List all registered strategies.

        Returns:
            List of strategy class names
        """
        return [strategy.__class__.__name__ for strategy in self._strategies]


class CustomWorkflowStrategy(IWorkflowBuildStrategy):
    """
    Strategy for handling explicit custom workflow sequences.

    This strategy has highest priority and is used when the user
    explicitly specifies which workflows to run.
    """

    def __init__(self, workflow_registry: IWorkflowRegistry):
        self.workflow_registry = workflow_registry

    def can_handle(self, context: WorkflowContext) -> bool:
        """Check if context has custom workflows specified."""
        return (
            context.custom_workflows is not None
            and len(context.custom_workflows) > 0
        )

    def build_workflow_sequence(self, context: WorkflowContext) -> WorkflowSequence:
        """Build sequence from custom workflow list."""
        workflows: List[WorkflowInfo] = []

        for workflow_name in context.custom_workflows:
            workflow_info = self.workflow_registry.get_workflow(workflow_name)
            if workflow_info:
                workflows.append(workflow_info)
            else:
                logger.warning(
                    "custom_workflow_not_found",
                    workflow=workflow_name
                )

        return WorkflowSequence(
            scale_level=context.scale_level or ScaleLevel.LEVEL_2,
            workflows=workflows,
            project_type=context.project_type or ProjectType.SOFTWARE,
            routing_rationale="Custom workflow sequence explicitly specified",
            phase_breakdown={"Custom": context.custom_workflows},
            jit_tech_specs=False
        )

    def get_priority(self) -> int:
        """Custom workflows have highest priority."""
        return 100


class ProjectTypeStrategy(IWorkflowBuildStrategy):
    """
    Strategy that routes based on project type.

    Handles special cases like brownfield, game projects, and bug fixes
    that need different workflow sequences regardless of scale.
    """

    def __init__(self, workflow_registry: IWorkflowRegistry):
        self.workflow_registry = workflow_registry

    def can_handle(self, context: WorkflowContext) -> bool:
        """Check if context has special project type."""
        return (
            context.is_brownfield
            or context.is_game_project
            or context.project_type == ProjectType.BUG_FIX
        )

    def build_workflow_sequence(self, context: WorkflowContext) -> WorkflowSequence:
        """Build sequence based on project type."""
        workflows: List[WorkflowInfo] = []
        phase_breakdown: Dict[str, List[str]] = {}

        # Brownfield: Always start with document-project
        if context.is_brownfield:
            doc_workflow = self.workflow_registry.get_workflow("document-project")
            if doc_workflow:
                workflows.append(doc_workflow)
                phase_breakdown["Phase 1: Analysis"] = ["document-project"]

        # Game projects: Use game-specific workflow
        if context.is_game_project:
            gdd_workflow = self.workflow_registry.get_workflow("create-gdd")
            if gdd_workflow:
                workflows.append(gdd_workflow)
                phase_breakdown["Phase 2: Planning"] = ["create-gdd"]

        # Bug fixes: Simple workflow
        if context.project_type == ProjectType.BUG_FIX:
            tech_spec = self.workflow_registry.get_workflow("create-tech-spec")
            dev_story = self.workflow_registry.get_workflow("dev-story")
            if tech_spec:
                workflows.append(tech_spec)
            if dev_story:
                workflows.append(dev_story)
            phase_breakdown["Quick Fix"] = ["create-tech-spec", "dev-story"]

        return WorkflowSequence(
            scale_level=context.scale_level or ScaleLevel.LEVEL_1,
            workflows=workflows,
            project_type=context.project_type or ProjectType.SOFTWARE,
            routing_rationale=f"Project type routing: {context.project_type.value if context.project_type else 'special'}",
            phase_breakdown=phase_breakdown,
            jit_tech_specs=False
        )

    def get_priority(self) -> int:
        """Project type has high priority (but below custom)."""
        return 75


class ScaleLevelStrategy(IWorkflowBuildStrategy):
    """
    Strategy that routes based on BMAD scale level.

    Implements scale-adaptive workflow selection:
    - Level 0: Single atomic change (tech-spec → story)
    - Level 1: Small feature (tech-spec → stories)
    - Level 2: Medium project (PRD → tech-spec → stories)
    - Level 3: Large project (PRD → architecture → JIT tech-specs → stories)
    - Level 4: Enterprise (PRD → architecture → epics → JIT tech-specs → stories)
    """

    def __init__(self, workflow_registry: IWorkflowRegistry):
        self.workflow_registry = workflow_registry

    def can_handle(self, context: WorkflowContext) -> bool:
        """Check if context has scale level."""
        return context.scale_level is not None

    def build_workflow_sequence(self, context: WorkflowContext) -> WorkflowSequence:
        """Build workflow sequence based on scale level."""
        # Convert int scale_level to ScaleLevel enum
        scale_level_value = context.scale_level
        if isinstance(scale_level_value, int):
            scale_level = ScaleLevel(scale_level_value)
        else:
            scale_level = scale_level_value

        workflows: List[WorkflowInfo] = []
        phase_breakdown: Dict[str, List[str]] = {}
        jit_tech_specs = False

        # Level 0: Chore - Single atomic change
        if scale_level == ScaleLevel.LEVEL_0:
            workflows_needed = ["create-tech-spec", "dev-story"]
            for wf_name in workflows_needed:
                wf = self.workflow_registry.get_workflow(wf_name)
                if wf:
                    workflows.append(wf)
            phase_breakdown["Quick Fix"] = workflows_needed

        # Level 1: Small feature
        elif scale_level == ScaleLevel.LEVEL_1:
            workflows_needed = ["create-tech-spec", "create-story", "dev-story"]
            for wf_name in workflows_needed:
                wf = self.workflow_registry.get_workflow(wf_name)
                if wf:
                    workflows.append(wf)
            phase_breakdown["Phase 3: Solutioning"] = ["create-tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story"]

        # Level 2: Medium project
        elif scale_level == ScaleLevel.LEVEL_2:
            workflows_needed = ["create-prd", "create-tech-spec", "create-story", "dev-story"]
            for wf_name in workflows_needed:
                wf = self.workflow_registry.get_workflow(wf_name)
                if wf:
                    workflows.append(wf)
            phase_breakdown["Phase 2: Planning"] = ["create-prd"]
            phase_breakdown["Phase 3: Solutioning"] = ["create-tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story"]

        # Level 3: Large project (JIT tech-specs)
        elif scale_level == ScaleLevel.LEVEL_3:
            workflows_needed = ["create-prd", "create-architecture", "create-story", "dev-story"]
            for wf_name in workflows_needed:
                wf = self.workflow_registry.get_workflow(wf_name)
                if wf:
                    workflows.append(wf)
            phase_breakdown["Phase 2: Planning"] = ["create-prd"]
            phase_breakdown["Phase 3: Solutioning"] = ["create-architecture"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story"]
            jit_tech_specs = True  # Tech specs created just-in-time during stories

        # Level 4: Enterprise (epics + JIT tech-specs)
        elif scale_level == ScaleLevel.LEVEL_4:
            workflows_needed = ["create-prd", "create-architecture", "create-epic", "create-story", "dev-story"]
            for wf_name in workflows_needed:
                wf = self.workflow_registry.get_workflow(wf_name)
                if wf:
                    workflows.append(wf)
            phase_breakdown["Phase 2: Planning"] = ["create-prd", "create-epic"]
            phase_breakdown["Phase 3: Solutioning"] = ["create-architecture"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story"]
            jit_tech_specs = True

        return WorkflowSequence(
            scale_level=scale_level,
            workflows=workflows,
            project_type=context.project_type or ProjectType.SOFTWARE,
            routing_rationale=f"Scale-adaptive routing for Level {scale_level.value}",
            phase_breakdown=phase_breakdown,
            jit_tech_specs=jit_tech_specs
        )

    def get_priority(self) -> int:
        """Scale level has medium priority (default case)."""
        return 50
