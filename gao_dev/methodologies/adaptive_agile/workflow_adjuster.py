"""Workflow Adjustment Logic - Apply learnings to workflow sequences.

This module implements the WorkflowAdjuster service which adjusts workflow sequences
based on past learnings with comprehensive safety mechanisms.

Epic: 29 - Self-Learning Feedback Loop
Story: 29.4 - Workflow Adjustment Logic

Design Pattern: Service Layer with Graph-Based Validation
Dependencies: NetworkX, LearningApplicationService, sqlite3, structlog

Safety Mechanisms (C1, C7 fixes):
- C1: Max 3 workflows added per adjustment, max 3 adjustments per epic
- C7: Dependency cycle detection using NetworkX graph algorithms
- Validation before and after adjustments with rollback on failure
"""

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import networkx as nx
import structlog

from gao_dev.core.services.learning_application_service import ScoredLearning
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.lifecycle.exceptions import (
    WorkflowDependencyCycleError,
)

logger = structlog.get_logger()


@dataclass
class WorkflowStep:
    """A workflow step with dependencies.

    Represents a single workflow in a sequence with dependency information
    for graph-based cycle detection and validation.

    Attributes:
        workflow_name: Unique workflow name
        phase: Workflow phase (planning, solutioning, implementation, testing)
        depends_on: List of workflow names this step depends on
        interval: Optional interval for ceremony workflows (e.g., every 3 stories)
        metadata: Additional workflow-specific metadata
    """

    workflow_name: str
    phase: str = "implementation"
    depends_on: List[str] = field(default_factory=list)
    interval: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate workflow step."""
        if not self.workflow_name:
            raise ValueError("workflow_name cannot be empty")
        if self.interval is not None and self.interval < 1:
            raise ValueError(f"interval must be >= 1, got {self.interval}")


class WorkflowAdjuster:
    """
    Service for adjusting workflows based on past learnings with safety mechanisms.

    This service applies learnings to workflow sequences while enforcing:
    - C1 Fix: Adjustment limits (max 3 workflows added, max 3 adjustments per epic)
    - C7 Fix: Dependency cycle detection using NetworkX
    - Validation before and after adjustments
    - Rollback on validation failure

    Example:
        ```python
        adjuster = WorkflowAdjuster(db_path=Path(".gao-dev/documents.db"))

        # Adjust workflows based on learnings
        adjusted = adjuster.adjust_workflows(
            workflows=base_workflows,
            learnings=relevant_learnings,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            epic_num=29
        )
        ```
    """

    # C1 Fix: Adjustment limits
    MAX_WORKFLOWS_ADDED = 3
    MAX_ADJUSTMENTS_PER_EPIC = 3

    def __init__(self, db_path: Path):
        """Initialize workflow adjuster service.

        Args:
            db_path: Path to database for tracking adjustments
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="workflow_adjuster")

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection with transaction handling."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()

    def adjust_workflows(
        self,
        workflows: List[WorkflowStep],
        learnings: List[ScoredLearning],
        scale_level: ScaleLevel,
        epic_num: Optional[int] = None,
    ) -> List[WorkflowStep]:
        """
        Adjust workflows based on learnings with safety checks.

        Safety Mechanisms (C1, C7 fixes):
        - Max 3 workflows added per adjustment
        - Max 3 adjustments per epic
        - Dependency cycle detection
        - Validation before and after adjustments
        - Rollback on validation failure

        Args:
            workflows: Original workflow sequence
            learnings: Relevant learnings with scores
            scale_level: Current scale level
            epic_num: Optional epic number for tracking adjustments

        Returns:
            Adjusted workflow sequence (or original if adjustment fails)
        """
        self.logger.info(
            "adjust_workflows_started",
            workflows_count=len(workflows),
            learnings_count=len(learnings),
            scale_level=scale_level.name,
            epic_num=epic_num,
        )

        # Validate original workflows first
        try:
            self._validate_workflows(workflows, context="original")
        except Exception as e:
            self.logger.error("original_workflows_invalid", error=str(e))
            raise  # Original workflows are broken - cannot proceed

        # Check adjustment limits (C1 fix)
        if epic_num is not None:
            adjustment_count = self._get_adjustment_count_for_epic(epic_num)
            if adjustment_count >= self.MAX_ADJUSTMENTS_PER_EPIC:
                self.logger.warning(
                    "max_adjustments_reached",
                    epic_num=epic_num,
                    adjustment_count=adjustment_count,
                    limit=self.MAX_ADJUSTMENTS_PER_EPIC,
                )
                return workflows  # Return original

            # Log warning at 2 adjustments (approaching limit)
            if adjustment_count == 2:
                self.logger.warning(
                    "approaching_adjustment_limit",
                    epic_num=epic_num,
                    adjustment_count=adjustment_count,
                    limit=self.MAX_ADJUSTMENTS_PER_EPIC,
                )

        # Track workflows added
        workflows_added = 0
        adjusted = workflows.copy()

        # Apply adjustments by category
        for learning in learnings:
            if workflows_added >= self.MAX_WORKFLOWS_ADDED:
                self.logger.warning(
                    "max_workflows_added", workflows_added=workflows_added, limit=self.MAX_WORKFLOWS_ADDED
                )
                break

            category = learning.category

            if category == "quality":
                added = self._apply_quality_learnings(adjusted, [learning])
                workflows_added += len(added)
            elif category == "process":
                added = self._apply_process_learnings(adjusted, [learning])
                workflows_added += len(added)
            elif category == "architectural":
                added = self._apply_architectural_learnings(adjusted, [learning])
                workflows_added += len(added)

        # Validate adjusted workflows (C7 fix)
        try:
            self._validate_workflows(adjusted, context="adjusted")
        except Exception as e:
            self.logger.error("adjusted_workflows_invalid_rolling_back", error=str(e))
            return workflows  # Rollback to original

        # Record adjustments in database
        if epic_num is not None:
            self._record_adjustments(workflows, adjusted, learnings, epic_num)

        self.logger.info(
            "adjust_workflows_completed",
            workflows_added=workflows_added,
            original_count=len(workflows),
            adjusted_count=len(adjusted),
        )

        return adjusted

    def _apply_quality_learnings(
        self, workflows: List[WorkflowStep], learnings: List[ScoredLearning]
    ) -> List[WorkflowStep]:
        """Apply quality learnings to workflow sequence.

        Quality learnings add testing and quality assurance workflows:
        - Low test coverage -> extended-testing, coverage-report
        - Code quality issues -> code-review, static-analysis
        - Integration issues -> integration-testing, end-to-end-testing

        Args:
            workflows: Current workflow sequence
            learnings: Quality learnings to apply

        Returns:
            List of newly added workflows
        """
        added_workflows = []

        for learning in learnings:
            content_lower = learning.learning.lower()

            # Check for test coverage issues
            if "test coverage" in content_lower or "coverage low" in content_lower:
                # Add extended-testing after implementation
                if not self._workflow_exists(workflows, "extended-testing"):
                    new_workflow = WorkflowStep(
                        workflow_name="extended-testing",
                        phase="testing",
                        depends_on=["test-feature"],
                        metadata={
                            "reason": f"Quality learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

                # Add coverage-report after extended-testing
                if not self._workflow_exists(workflows, "coverage-report"):
                    new_workflow = WorkflowStep(
                        workflow_name="coverage-report",
                        phase="testing",
                        depends_on=["extended-testing"],
                        metadata={
                            "reason": f"Quality learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for code quality issues
            if "code quality" in content_lower or "quality issues" in content_lower:
                # Add code-review after implementation
                if not self._workflow_exists(workflows, "code-review"):
                    new_workflow = WorkflowStep(
                        workflow_name="code-review",
                        phase="testing",
                        depends_on=["implement-stories"],
                        metadata={
                            "reason": f"Quality learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for integration issues
            if "integration" in content_lower:
                # Add integration-testing
                if not self._workflow_exists(workflows, "integration-testing"):
                    new_workflow = WorkflowStep(
                        workflow_name="integration-testing",
                        phase="testing",
                        depends_on=["test-feature"],
                        metadata={
                            "reason": f"Quality learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

        self.logger.info(
            "quality_learnings_applied", learnings_count=len(learnings), workflows_added=len(added_workflows)
        )

        return added_workflows

    def _apply_process_learnings(
        self, workflows: List[WorkflowStep], learnings: List[ScoredLearning]
    ) -> List[WorkflowStep]:
        """Apply process learnings to workflow sequence.

        Process learnings modify ceremonies and add process workflows:
        - Communication issues -> increase standup frequency, add ceremony-planning
        - Scope creep -> add scope-review, story-refinement
        - Missed deadlines -> add time-estimation-review

        Args:
            workflows: Current workflow sequence
            learnings: Process learnings to apply

        Returns:
            List of newly added workflows
        """
        added_workflows = []

        for learning in learnings:
            content_lower = learning.learning.lower()

            # Check for communication issues or standup mentions
            if "communication" in content_lower or "standup" in content_lower or "daily" in content_lower:
                # Increase standup frequency (interval: 3 -> 2)
                for workflow in workflows:
                    if workflow.workflow_name == "ceremony-standup" and workflow.interval:
                        if workflow.interval > 1:
                            workflow.interval -= 1
                            self.logger.info(
                                "standup_frequency_increased",
                                new_interval=workflow.interval,
                                learning_id=learning.learning_id,
                            )

                # Add ceremony-planning
                if not self._workflow_exists(workflows, "ceremony-planning"):
                    new_workflow = WorkflowStep(
                        workflow_name="ceremony-planning",
                        phase="planning",
                        depends_on=[],
                        metadata={
                            "reason": f"Process learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for scope creep
            if "scope creep" in content_lower or "scope" in content_lower:
                # Add scope-review mid-epic
                if not self._workflow_exists(workflows, "scope-review"):
                    new_workflow = WorkflowStep(
                        workflow_name="scope-review",
                        phase="planning",
                        depends_on=["create-stories"],
                        metadata={
                            "reason": f"Process learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for missed deadlines
            if "deadline" in content_lower or "timeline" in content_lower:
                # Add time-estimation-review
                if not self._workflow_exists(workflows, "time-estimation-review"):
                    new_workflow = WorkflowStep(
                        workflow_name="time-estimation-review",
                        phase="planning",
                        depends_on=["create-stories"],
                        metadata={
                            "reason": f"Process learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

        self.logger.info(
            "process_learnings_applied", learnings_count=len(learnings), workflows_added=len(added_workflows)
        )

        return added_workflows

    def _apply_architectural_learnings(
        self, workflows: List[WorkflowStep], learnings: List[ScoredLearning]
    ) -> List[WorkflowStep]:
        """Apply architectural learnings to workflow sequence.

        Architectural learnings add architecture review and validation workflows:
        - Architecture drift -> architecture-review, architecture-validation
        - Tech debt -> tech-debt-assessment, refactoring-review
        - Security issues -> security-review, security-testing

        Args:
            workflows: Current workflow sequence
            learnings: Architectural learnings to apply

        Returns:
            List of newly added workflows
        """
        added_workflows = []

        for learning in learnings:
            content_lower = learning.learning.lower()

            # Check for architecture drift
            if "architecture" in content_lower or "drift" in content_lower:
                # Add architecture-review after solutioning
                if not self._workflow_exists(workflows, "architecture-review"):
                    new_workflow = WorkflowStep(
                        workflow_name="architecture-review",
                        phase="solutioning",
                        depends_on=["architecture"],
                        metadata={
                            "reason": f"Architectural learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for tech debt
            if "tech debt" in content_lower or "technical debt" in content_lower:
                # Add tech-debt-assessment
                if not self._workflow_exists(workflows, "tech-debt-assessment"):
                    new_workflow = WorkflowStep(
                        workflow_name="tech-debt-assessment",
                        phase="testing",
                        depends_on=["implement-stories"],
                        metadata={
                            "reason": f"Architectural learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

            # Check for security issues
            if "security" in content_lower:
                # Add security-review after architecture
                if not self._workflow_exists(workflows, "security-review"):
                    new_workflow = WorkflowStep(
                        workflow_name="security-review",
                        phase="solutioning",
                        depends_on=["architecture"],
                        metadata={
                            "reason": f"Architectural learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

                # Add security-testing after implementation
                if not self._workflow_exists(workflows, "security-testing"):
                    new_workflow = WorkflowStep(
                        workflow_name="security-testing",
                        phase="testing",
                        depends_on=["implement-stories"],
                        metadata={
                            "reason": f"Architectural learning: {learning.learning[:100]}",
                            "learning_id": learning.learning_id,
                        },
                    )
                    workflows.append(new_workflow)
                    added_workflows.append(new_workflow)

        self.logger.info(
            "architectural_learnings_applied",
            learnings_count=len(learnings),
            workflows_added=len(added_workflows),
        )

        return added_workflows

    def _detect_dependency_cycles(self, workflows: List[WorkflowStep]) -> List[str]:
        """
        Detect circular dependencies using NetworkX (C7 fix).

        Algorithm:
        1. Build directed graph (workflow -> dependencies)
        2. Use NetworkX simple_cycles() to find all cycles
        3. Raise error if cycles found with clear description

        Example cycle:
        workflow-a depends_on: [workflow-b]
        workflow-b depends_on: [workflow-c]
        workflow-c depends_on: [workflow-a]
        -> Cycle: workflow-a -> workflow-b -> workflow-c -> workflow-a

        Args:
            workflows: List of workflow steps with depends_on

        Returns:
            Empty list if no cycles

        Raises:
            Exception: If cycles detected with cycle descriptions
        """
        # Build directed graph
        G = nx.DiGraph()

        # Add all nodes first
        for wf in workflows:
            G.add_node(wf.workflow_name)

        # Add edges (workflow -> dependency)
        for wf in workflows:
            for dep in wf.depends_on:
                # Check if dependency exists
                if dep not in G:
                    raise WorkflowDependencyCycleError(
                        f"Workflow '{wf.workflow_name}' depends on non-existent workflow '{dep}'"
                    )
                G.add_edge(wf.workflow_name, dep)

        # Find all cycles
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception as e:
            # NetworkX might raise for other graph issues
            raise WorkflowDependencyCycleError(f"Graph analysis error: {e}") from e

        if cycles:
            # Format cycles for error message
            cycle_descriptions = []
            for cycle in cycles:
                cycle_path = " -> ".join(cycle + [cycle[0]])
                cycle_descriptions.append(cycle_path)

            raise WorkflowDependencyCycleError(
                "Dependency cycles detected:\n"
                + "\n".join(f"  - {desc}" for desc in cycle_descriptions),
                cycles=cycle_descriptions,
            )

        return []

    def _validate_workflows(self, workflows: List[WorkflowStep], context: str = "adjusted") -> None:
        """
        Validate workflow list for common issues.

        Checks:
        1. No dependency cycles (C7 fix)
        2. All dependencies exist
        3. No duplicate workflow names
        4. Workflow depth <= 10 (prevents excessive nesting)

        Args:
            workflows: List of workflow steps to validate
            context: Context string for logging (e.g., "original", "adjusted")

        Raises:
            Exception: If validation fails
        """
        self.logger.debug("validating_workflows", context=context, workflows_count=len(workflows))

        # Check 1: Dependency cycles (C7 fix)
        self._detect_dependency_cycles(workflows)

        # Check 2: All dependencies exist
        workflow_names = {wf.workflow_name for wf in workflows}
        for wf in workflows:
            for dep in wf.depends_on:
                if dep not in workflow_names:
                    raise WorkflowDependencyCycleError(
                        f"Workflow '{wf.workflow_name}' depends on non-existent workflow '{dep}'"
                    )

        # Check 3: No duplicates
        if len(workflow_names) != len(workflows):
            duplicates = [
                name
                for name in workflow_names
                if sum(1 for wf in workflows if wf.workflow_name == name) > 1
            ]
            raise WorkflowDependencyCycleError(f"Duplicate workflow names: {duplicates}")

        # Check 4: Workflow depth
        max_depth = self._calculate_max_depth(workflows)
        if max_depth > 10:
            raise WorkflowDependencyCycleError(
                f"Workflow depth {max_depth} exceeds limit of 10"
            )

        self.logger.debug("workflows_validated", context=context, max_depth=max_depth)

    def _calculate_max_depth(self, workflows: List[WorkflowStep]) -> int:
        """
        Calculate maximum dependency depth using NetworkX.

        Uses topological sort to find longest path in DAG.

        Args:
            workflows: List of workflow steps

        Returns:
            Maximum depth (0 if no dependencies or cycles detected)
        """
        G = nx.DiGraph()

        # Build graph (reverse edges for topological sort)
        for wf in workflows:
            G.add_node(wf.workflow_name)
            for dep in wf.depends_on:
                G.add_edge(dep, wf.workflow_name)  # Reverse edge for topological

        try:
            # Longest path in DAG
            if len(G.nodes) == 0:
                return 0
            return nx.dag_longest_path_length(G)
        except nx.NetworkXError:
            # Not a DAG (has cycles) - handled by cycle detection
            return 0

    def _workflow_exists(self, workflows: List[WorkflowStep], workflow_name: str) -> bool:
        """Check if workflow already exists in sequence.

        Args:
            workflows: List of workflow steps
            workflow_name: Workflow name to check

        Returns:
            True if workflow exists, False otherwise
        """
        return any(wf.workflow_name == workflow_name for wf in workflows)

    def _get_adjustment_count_for_epic(self, epic_num: int) -> int:
        """Get number of adjustments already made for this epic (C1 fix).

        Args:
            epic_num: Epic number

        Returns:
            Number of adjustments made for this epic
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT applied_at) FROM workflow_adjustments WHERE epic_num = ?",
                (epic_num,),
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def _record_adjustments(
        self,
        original: List[WorkflowStep],
        adjusted: List[WorkflowStep],
        learnings: List[ScoredLearning],
        epic_num: int,
    ) -> None:
        """Record workflow adjustments in database.

        Args:
            original: Original workflow sequence
            adjusted: Adjusted workflow sequence
            learnings: Learnings that triggered adjustments
            epic_num: Epic number
        """
        original_names = {wf.workflow_name for wf in original}
        adjusted_names = {wf.workflow_name for wf in adjusted}

        # Find added workflows
        added = adjusted_names - original_names

        # Find removed workflows (should be rare)
        removed = original_names - adjusted_names

        # Find modified workflows (e.g., interval changes)
        modified = []
        for original_wf in original:
            for adjusted_wf in adjusted:
                if original_wf.workflow_name == adjusted_wf.workflow_name:
                    if original_wf != adjusted_wf:
                        modified.append(original_wf.workflow_name)

        timestamp = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            # Record added workflows
            for workflow_name in added:
                # Find the workflow in adjusted list to get metadata
                workflow = next((wf for wf in adjusted if wf.workflow_name == workflow_name), None)
                if workflow:
                    learning_id = workflow.metadata.get("learning_id")
                    reason = workflow.metadata.get("reason", "Unknown reason")

                    conn.execute(
                        """
                        INSERT INTO workflow_adjustments
                        (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (epic_num, learning_id, "add", workflow_name, reason, timestamp),
                    )

            # Record removed workflows
            for workflow_name in removed:
                conn.execute(
                    """
                    INSERT INTO workflow_adjustments
                    (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (epic_num, None, "remove", workflow_name, "Removed by adjuster", timestamp),
                )

            # Record modified workflows
            for workflow_name in modified:
                conn.execute(
                    """
                    INSERT INTO workflow_adjustments
                    (epic_num, learning_id, adjustment_type, workflow_name, reason, applied_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (epic_num, None, "modify", workflow_name, "Modified by adjuster", timestamp),
                )

        self.logger.info(
            "adjustments_recorded",
            epic_num=epic_num,
            added=len(added),
            removed=len(removed),
            modified=len(modified),
        )
