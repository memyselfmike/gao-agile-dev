"""
WorkflowCoordinator Service - Coordinates multi-step workflow execution.

Extracted from GAODevOrchestrator (Epic 6, Story 6.1) to achieve SOLID principles.

Responsibilities:
- Execute workflow sequences step-by-step
- Manage workflow context passing
- Publish workflow lifecycle events
- Handle errors with retry logic

NOT responsible for:
- Story lifecycle (StoryLifecycleManager)
- Quality gates (QualityGateManager)
- Subprocess execution (ProcessExecutor)
- High-level orchestration (stays in orchestrator)
"""

import structlog
from typing import Callable, Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio

from ..interfaces.workflow import IWorkflowRegistry
from ..interfaces.agent import IAgentFactory
from ..interfaces.event_bus import IEventBus
from ..events.event_bus import Event

logger = structlog.get_logger()


class WorkflowCoordinator:
    """
    Coordinates execution of workflow sequences.

    Single Responsibility: Execute workflows in sequence order, manage workflow
    context, publish lifecycle events, handle errors and retries.

    This service was extracted from GAODevOrchestrator (Epic 6, Story 6.1) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Execute workflows in sequence order
    - Manage workflow context across steps
    - Publish workflow lifecycle events
    - Handle workflow step failures with retry logic

    NOT responsible for:
    - Story lifecycle management (StoryLifecycleManager)
    - Quality gate validation (QualityGateManager)
    - Subprocess execution (ProcessExecutor)
    - Orchestrator-level logic (stays in orchestrator)

    Example:
        ```python
        coordinator = WorkflowCoordinator(
            workflow_registry=registry,
            agent_factory=factory,
            event_bus=bus,
            max_retries=3
        )

        result = await coordinator.execute_sequence(
            workflow_sequence=sequence,
            context=context
        )
        ```
    """

    def __init__(
        self,
        workflow_registry: IWorkflowRegistry,
        agent_factory: IAgentFactory,
        event_bus: IEventBus,
        agent_executor: Callable,  # Callback to execute agent task
        project_root: Path,
        doc_manager: Optional['DocumentLifecycleManager'] = None,
        workflow_executor: Optional['WorkflowExecutor'] = None,
        max_retries: int = 3,
        # Epic 28.4: Ceremony integration
        ceremony_trigger_engine: Optional['CeremonyTriggerEngine'] = None,
        ceremony_orchestrator: Optional['CeremonyOrchestrator'] = None,
        ceremony_failure_handler: Optional['CeremonyFailureHandler'] = None,
        git_state_manager: Optional['GitIntegratedStateManager'] = None,
        db_path: Optional[Path] = None
    ):
        """
        Initialize coordinator with injected dependencies.

        Args:
            workflow_registry: Registry to lookup workflows
            agent_factory: Factory to create agents (future use)
            event_bus: Event bus for publishing lifecycle events
            agent_executor: Callback function to execute agent tasks
            project_root: Root directory of the project
            doc_manager: Optional document lifecycle manager for tracking artifacts
            workflow_executor: Optional workflow executor for variable resolution (Story 18.1)
            max_retries: Maximum retry attempts for failed workflows (default: 3)
            ceremony_trigger_engine: Optional ceremony trigger engine (Epic 28.4)
            ceremony_orchestrator: Optional ceremony orchestrator (Epic 28.4)
            ceremony_failure_handler: Optional ceremony failure handler (Epic 28.4)
            git_state_manager: Optional git-integrated state manager (Epic 27.1)
            db_path: Optional path to database (for ceremony initialization)
        """
        self.workflow_registry = workflow_registry
        self.agent_factory = agent_factory
        self.event_bus = event_bus
        self.agent_executor = agent_executor
        self.project_root = project_root
        self.doc_manager = doc_manager
        self.workflow_executor = workflow_executor
        self.max_retries = max_retries
        self.db_path = db_path

        # Epic 28.4: Ceremony integration (lazy initialization if not provided)
        self._ceremony_trigger_engine = ceremony_trigger_engine
        self._ceremony_orchestrator = ceremony_orchestrator
        self._ceremony_failure_handler = ceremony_failure_handler
        self.git_state_manager = git_state_manager

        logger.info(
            "workflow_coordinator_initialized",
            max_retries=max_retries,
            project_root=str(project_root),
            has_doc_manager=doc_manager is not None,
            has_workflow_executor=workflow_executor is not None,
            has_ceremony_integration=(
                ceremony_trigger_engine is not None
                and ceremony_orchestrator is not None
                and ceremony_failure_handler is not None
            )
        )

    @property
    def trigger_engine(self):
        """Lazy-initialize CeremonyTriggerEngine if not provided."""
        if self._ceremony_trigger_engine is None and self.db_path is not None:
            from gao_dev.core.services.ceremony_trigger_engine import CeremonyTriggerEngine
            self._ceremony_trigger_engine = CeremonyTriggerEngine(db_path=self.db_path)
        return self._ceremony_trigger_engine

    @property
    def ceremony_orchestrator(self):
        """Lazy-initialize CeremonyOrchestrator if not provided."""
        if self._ceremony_orchestrator is None and self.db_path is not None:
            from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator
            from gao_dev.core.config_loader import ConfigLoader
            config = ConfigLoader()
            self._ceremony_orchestrator = CeremonyOrchestrator(
                config=config,
                db_path=self.db_path,
                project_root=self.project_root,
                git_state_manager=self.git_state_manager
            )
        return self._ceremony_orchestrator

    @property
    def failure_handler(self):
        """Lazy-initialize CeremonyFailureHandler if not provided."""
        if self._ceremony_failure_handler is None:
            from gao_dev.core.services.ceremony_failure_handler import CeremonyFailureHandler
            self._ceremony_failure_handler = CeremonyFailureHandler()
        return self._ceremony_failure_handler

    async def execute_sequence(
        self,
        workflow_sequence: 'WorkflowSequence',
        context: 'WorkflowContext'
    ) -> 'WorkflowResult':
        """
        Execute a sequence of workflows step-by-step.

        Coordinates execution of multiple workflows in order, managing context
        passing, error handling, and event publishing.

        CRITICAL: For story-based workflows (create-story, dev-story, story-done),
        this method implements a proper story loop based on Brian's assessment of
        estimated epics and stories, rather than executing each workflow just once.

        Args:
            workflow_sequence: Sequence of workflows to execute
            context: Execution context with project info and parameters

        Returns:
            WorkflowResult with execution status and artifacts

        Raises:
            WorkflowExecutionError: If sequence fails after max retries
        """
        from ...orchestrator.workflow_results import (
            WorkflowResult,
            WorkflowStatus
        )
        from ...orchestrator.models import PromptAnalysis

        # Initialize result
        result = WorkflowResult(
            workflow_name=(
                workflow_sequence.workflows[0].name
                if workflow_sequence.workflows
                else "empty-sequence"
            ),
            initial_prompt=context.initial_prompt,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            project_path=str(context.project_root) if context.project_root else str(self.project_root)
        )

        try:
            # Validate sequence
            if not workflow_sequence.workflows:
                result.status = WorkflowStatus.FAILED
                result.error_message = "Empty workflow sequence"
                logger.warning("empty_workflow_sequence")
                return result

            # Generate sequence ID for tracking
            sequence_id = f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Publish sequence started event
            self.event_bus.publish(Event(
                type="WorkflowSequenceStarted",
                data={
                    "sequence_id": sequence_id,
                    "workflow_count": len(workflow_sequence.workflows)
                }
            ))

            logger.info(
                "workflow_sequence_started",
                sequence_id=sequence_id,
                workflow_count=len(workflow_sequence.workflows),
                scale_level=workflow_sequence.scale_level.value if workflow_sequence.scale_level else None
            )

            # Separate workflows into setup phase and story phase
            setup_workflows = []
            story_workflows = []

            for workflow_info in workflow_sequence.workflows:
                workflow_name = workflow_info.name.lower()
                if workflow_name in ["create-story", "dev-story", "story-done"]:
                    story_workflows.append(workflow_info)
                else:
                    setup_workflows.append(workflow_info)

            step_number = 1

            # Phase 1: Execute setup workflows (PRD, architecture, tech-spec)
            logger.info(
                "setup_phase_starting",
                setup_workflows=len(setup_workflows)
            )

            for workflow_info in setup_workflows:
                logger.info(
                    "workflow_step_starting",
                    step=step_number,
                    workflow=workflow_info.name,
                    phase="setup"
                )

                # Execute single workflow step
                step_result = await self.execute_workflow(
                    workflow_id=workflow_info.name,
                    workflow_info=workflow_info,
                    step_number=step_number,
                    total_steps=len(workflow_sequence.workflows),  # Total includes all loops
                    context=context
                )

                result.step_results.append(step_result)
                step_number += 1

                # Check for failure
                if step_result.status == "failed":
                    logger.error(
                        "workflow_step_failed",
                        step=workflow_info.name,
                        error=step_result.error_message
                    )
                    result.status = WorkflowStatus.FAILED
                    result.error_message = f"Setup phase failed at {workflow_info.name}: {step_result.error_message}"

                    # Publish sequence failed event
                    self.event_bus.publish(Event(
                        type="WorkflowSequenceFailed",
                        data={
                            "sequence_id": sequence_id,
                            "failed_at_step": step_number - 1,
                            "error": step_result.error_message
                        }
                    ))
                    return result

            logger.info("setup_phase_completed", workflows_executed=len(setup_workflows))

            # Phase 2: Execute story loop (if story workflows exist)
            if story_workflows:
                await self._execute_story_loop(
                    story_workflows=story_workflows,
                    workflow_sequence=workflow_sequence,
                    context=context,
                    result=result,
                    sequence_id=sequence_id,
                    starting_step_number=step_number
                )

            # Mark as completed if all steps succeeded
            if result.status != WorkflowStatus.FAILED:
                result.status = WorkflowStatus.COMPLETED
                result.end_time = datetime.now()

                # Publish sequence completed event
                self.event_bus.publish(Event(
                    type="WorkflowSequenceCompleted",
                    data={
                        "sequence_id": sequence_id,
                        "duration_seconds": (result.end_time - result.start_time).total_seconds(),
                        "total_steps": len(result.step_results)
                    }
                ))

                logger.info(
                    "workflow_sequence_completed",
                    sequence_id=sequence_id,
                    steps=len(result.step_results),
                    duration=(result.end_time - result.start_time).total_seconds()
                )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            logger.error(
                "workflow_sequence_error",
                error=str(e),
                exc_info=True
            )

        finally:
            result.end_time = datetime.now()
            result.total_artifacts = sum(
                len(step.artifacts_created) for step in result.step_results
            )

        return result

    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_info: 'WorkflowInfo',
        step_number: int,
        total_steps: int,
        context: 'WorkflowContext',
        epic: int = 1,
        story: int = 1
    ) -> 'WorkflowStepResult':
        """
        Execute a single workflow step with retry logic.

        Publishes events for workflow step lifecycle. Retries on failure up to
        max_retries times with exponential backoff.

        Args:
            workflow_id: Workflow identifier
            workflow_info: Workflow metadata
            step_number: Current step number in sequence
            total_steps: Total steps in sequence
            context: Execution context
            epic: Epic number for story workflows (default: 1)
            story: Story number for story workflows (default: 1)

        Returns:
            WorkflowStepResult with execution status
        """
        from ...orchestrator.workflow_results import WorkflowStepResult

        step_result = WorkflowStepResult(
            step_name=workflow_info.name,
            agent=self._get_agent_for_workflow(workflow_info),
            status="in_progress",
            start_time=datetime.now()
        )

        # Publish step started event
        self.event_bus.publish(Event(
            type="WorkflowStepStarted",
            data={
                "workflow_id": workflow_id,
                "step_number": step_number,
                "total_steps": total_steps
            }
        ))

        logger.info(
            "workflow_step_started",
            workflow=workflow_id,
            step=step_number,
            agent=step_result.agent
        )

        # Retry loop
        retry_count = 0
        last_error = None

        while retry_count <= self.max_retries:
            try:
                # Execute agent task via callback
                output_parts = []
                async for message in self.agent_executor(workflow_info, epic, story):
                    output_parts.append(message)

                step_result.output = "\n".join(output_parts)
                step_result.status = "success"

                # Publish step completed event
                step_result.end_time = datetime.now()
                self.event_bus.publish(Event(
                    type="WorkflowStepCompleted",
                    data={
                        "workflow_id": workflow_id,
                        "step_number": step_number,
                        "duration_seconds": (
                            step_result.end_time - step_result.start_time
                        ).total_seconds(),
                        "artifacts": step_result.artifacts_created
                    }
                ))

                logger.info(
                    "workflow_step_completed",
                    workflow=workflow_id,
                    agent=step_result.agent,
                    retry_count=retry_count
                )
                break  # Success, exit retry loop

            except Exception as e:
                last_error = e
                retry_count += 1

                logger.warning(
                    "workflow_step_failed_retrying",
                    workflow=workflow_id,
                    retry_count=retry_count,
                    max_retries=self.max_retries,
                    error=str(e)
                )

                # Publish step failed event
                self.event_bus.publish(Event(
                    type="WorkflowStepFailed",
                    data={
                        "workflow_id": workflow_id,
                        "step_number": step_number,
                        "error": str(e),
                        "retry_count": retry_count
                    }
                ))

                if retry_count <= self.max_retries:
                    # Exponential backoff: 2^retry_count seconds
                    backoff_seconds = 2 ** retry_count
                    logger.info(
                        "workflow_retry_backoff",
                        workflow=workflow_id,
                        backoff_seconds=backoff_seconds
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    # Max retries exceeded
                    step_result.status = "failed"
                    step_result.error_message = f"Failed after {self.max_retries} retries: {str(last_error)}"
                    logger.error(
                        "workflow_step_max_retries_exceeded",
                        workflow=workflow_id,
                        max_retries=self.max_retries,
                        error=str(last_error)
                    )

        # Finalize result
        step_result.end_time = datetime.now()
        if step_result.start_time:
            step_result.duration_seconds = (
                step_result.end_time - step_result.start_time
            ).total_seconds()

        return step_result

    async def _execute_story_loop(
        self,
        story_workflows: list,
        workflow_sequence: 'WorkflowSequence',
        context: 'WorkflowContext',
        result: 'WorkflowResult',
        sequence_id: str,
        starting_step_number: int
    ) -> None:
        """
        Execute story loop: create and implement stories until MVP is complete.

        This implements the story loop pattern that existed before Epic 6 refactor.
        After setup phase (PRD, architecture, tech-spec), we loop through creating
        and implementing stories based on Brian's assessment.

        Args:
            story_workflows: List of story workflows (create-story, dev-story, story-done)
            workflow_sequence: Full workflow sequence with scale level and estimated stories
            context: Execution context
            result: WorkflowResult to update with story loop results
            sequence_id: Sequence ID for event tracking
            starting_step_number: Step number to start from (after setup phase)
        """
        from ...orchestrator.workflow_results import WorkflowStatus

        logger.info(
            "story_loop_starting",
            message="Executing story loop - will create and implement stories until MVP complete"
        )

        # Find specific story workflows
        create_story_wf = next((w for w in story_workflows if w.name == "create-story"), None)
        dev_story_wf = next((w for w in story_workflows if w.name == "dev-story"), None)
        story_done_wf = next((w for w in story_workflows if w.name == "story-done"), None)

        if not create_story_wf or not dev_story_wf:
            logger.warning(
                "story_loop_skipped",
                reason="Missing create-story or dev-story workflow"
            )
            return

        # Get estimated story count from workflow sequence
        estimated_stories = getattr(workflow_sequence, 'estimated_stories', 20)
        max_stories = min(estimated_stories, 100)  # Safety limit

        logger.info(
            "story_loop_plan",
            estimated_stories=estimated_stories,
            max_stories=max_stories
        )

        # Execute first story (part of initial sequence)
        step_number = starting_step_number
        current_epic = 1
        story_num = 1

        # Execute initial story workflows (create-story, dev-story, story-done for story 1)
        for workflow_info in story_workflows:
            logger.info(
                "story_loop_iteration",
                iteration=story_num,
                workflow=workflow_info.name,
                epic=current_epic,
                story=story_num
            )

            step_result = await self.execute_workflow(
                workflow_id=workflow_info.name,
                workflow_info=workflow_info,
                step_number=step_number,
                total_steps=max_stories * 3,  # Rough estimate: 3 workflows per story
                context=context,
                epic=current_epic,
                story=story_num
            )

            result.step_results.append(step_result)
            step_number += 1

            # Check for failure
            if step_result.status == "failed":
                logger.error(
                    "story_loop_failed",
                    story=story_num,
                    workflow=workflow_info.name,
                    error=step_result.error_message
                )
                result.status = WorkflowStatus.FAILED
                result.error_message = f"Story loop failed at story {story_num}, workflow {workflow_info.name}: {step_result.error_message}"
                return

        logger.info(
            "story_loop_initial_story_complete",
            story=story_num,
            next_story=story_num + 1
        )

        # Continue with remaining stories (story 2 through max_stories)
        for story_num in range(2, max_stories + 1):
            logger.info(
                "story_loop_next_story",
                story=story_num,
                epic=current_epic,
                total_stories=max_stories
            )

            # Execute create-story workflow
            step_result = await self.execute_workflow(
                workflow_id=create_story_wf.name,
                workflow_info=create_story_wf,
                step_number=step_number,
                total_steps=max_stories * 3,
                context=context,
                epic=current_epic,
                story=story_num
            )
            result.step_results.append(step_result)
            step_number += 1

            if step_result.status == "failed":
                logger.error("story_creation_failed", story=story_num)
                result.status = WorkflowStatus.FAILED
                result.error_message = f"Failed to create story {story_num}"
                return

            # Execute dev-story workflow
            step_result = await self.execute_workflow(
                workflow_id=dev_story_wf.name,
                workflow_info=dev_story_wf,
                step_number=step_number,
                total_steps=max_stories * 3,
                context=context,
                epic=current_epic,
                story=story_num
            )
            result.step_results.append(step_result)
            step_number += 1

            if step_result.status == "failed":
                logger.error("story_development_failed", story=story_num)
                result.status = WorkflowStatus.FAILED
                result.error_message = f"Failed to develop story {story_num}"
                return

            # Execute story-done workflow (if available)
            if story_done_wf:
                step_result = await self.execute_workflow(
                    workflow_id=story_done_wf.name,
                    workflow_info=story_done_wf,
                    step_number=step_number,
                    total_steps=max_stories * 3,
                    context=context,
                    epic=current_epic,
                    story=story_num
                )
                result.step_results.append(step_result)
                step_number += 1

                if step_result.status == "failed":
                    logger.warning(
                        "story_done_failed",
                        story=story_num,
                        message="Story-done failed but continuing"
                    )
                    # Don't fail the entire loop if story-done fails

            logger.info(
                "story_loop_story_complete",
                story=story_num,
                epic=current_epic,
                remaining_stories=max_stories - story_num
            )

        logger.info(
            "story_loop_completed",
            total_stories_implemented=max_stories,
            total_steps=step_number - starting_step_number
        )

    # ========================================================================
    # Epic 28.4: Ceremony Integration
    # ========================================================================

    def _evaluate_ceremony_triggers(self, context: Dict[str, Any]) -> List['CeremonyType']:
        """
        Evaluate which ceremonies should trigger (Epic 28.4).

        Args:
            context: Workflow execution context

        Returns:
            List of ceremony types to execute
        """
        # Skip if ceremony integration not enabled
        if self.trigger_engine is None:
            return []

        from gao_dev.core.services.ceremony_trigger_engine import TriggerContext
        from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel

        # Build trigger context from workflow context
        epic_num = context.get('epic_num', 1)
        scale_level = context.get('scale_level', ScaleLevel.LEVEL_0_CHORE)
        if isinstance(scale_level, str):
            # Convert string to enum if needed
            scale_level = ScaleLevel[scale_level]

        trigger_context = TriggerContext(
            epic_num=epic_num,
            story_num=context.get('story_num'),
            scale_level=scale_level,
            stories_completed=context.get('stories_completed', 0),
            total_stories=context.get('total_stories', 0),
            quality_gates_passed=context.get('quality_gates_passed', True),
            failure_count=context.get('failure_count', 0),
            project_type=context.get('project_type', 'feature'),
            last_standup=context.get('last_standup')
        )

        ceremonies = self.trigger_engine.evaluate_all_triggers(trigger_context)

        if ceremonies:
            logger.info(
                "ceremonies_triggered",
                epic_num=epic_num,
                ceremonies=[c.value for c in ceremonies]
            )

        return ceremonies

    def _execute_ceremonies(
        self,
        ceremonies: List['CeremonyType'],
        context: Dict[str, Any]
    ):
        """
        Execute ceremonies with failure handling (Epic 28.4).

        Implements C3 (atomic transactions) and C9 (failure handling) fixes.

        Args:
            ceremonies: List of ceremony types to execute
            context: Workflow execution context
        """
        # Skip if ceremony orchestrator not available
        if self.ceremony_orchestrator is None:
            logger.warning(
                "ceremonies_skipped_no_orchestrator",
                ceremonies=[c.value for c in ceremonies]
            )
            return

        from gao_dev.orchestrator.ceremony_orchestrator import CeremonyExecutionError
        from gao_dev.core.services.ceremony_failure_handler import CeremonyFailurePolicy

        for ceremony_type in ceremonies:
            try:
                # Execute ceremony with retry
                result = self._execute_ceremony_with_retry(
                    ceremony_type=ceremony_type.value,
                    context=context
                )

                # Success: Reset failure count
                self.failure_handler.reset_failures(
                    ceremony_type.value,
                    context.get('epic_num', 1)
                )

                # Record execution for safety tracking
                self.trigger_engine.record_ceremony_execution(
                    epic_num=context.get('epic_num', 1),
                    ceremony_type=ceremony_type.value,
                    success=True
                )

                # Update context with ceremony results
                self._update_context_with_ceremony(context, result)

            except CeremonyExecutionError as e:
                policy = self.failure_handler.handle_failure(
                    ceremony_type=ceremony_type.value,
                    epic_num=context.get('epic_num', 1),
                    error=e
                )

                if policy == CeremonyFailurePolicy.ABORT:
                    logger.error("workflow_aborted_due_to_ceremony_failure")
                    raise

                elif policy == CeremonyFailurePolicy.CONTINUE:
                    logger.warning(
                        "ceremony_failed_continuing",
                        ceremony_type=ceremony_type.value
                    )
                    # Continue with next ceremony

                elif policy == CeremonyFailurePolicy.SKIP:
                    logger.error(
                        "ceremonies_disabled_for_epic",
                        epic_num=context.get('epic_num', 1)
                    )
                    break  # Stop all future ceremonies

                # RETRY policy handled by _execute_ceremony_with_retry

                # Record failed execution
                self.trigger_engine.record_ceremony_execution(
                    epic_num=context.get('epic_num', 1),
                    ceremony_type=ceremony_type.value,
                    success=False
                )

    def _execute_ceremony_with_retry(
        self,
        ceremony_type: str,
        context: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute ceremony with retry logic (Epic 28.4).

        Args:
            ceremony_type: Type of ceremony
            context: Execution context
            max_retries: Maximum retry attempts

        Returns:
            Ceremony result

        Raises:
            CeremonyExecutionError: If all retries fail
        """
        import time
        from gao_dev.orchestrator.ceremony_orchestrator import CeremonyExecutionError

        for attempt in range(max_retries + 1):
            try:
                # Ceremony execution wrapped in atomic transaction (C3 Fix)
                result = self.ceremony_orchestrator.hold_ceremony(
                    ceremony_type=ceremony_type,
                    epic_num=context.get('epic_num', 1),
                    participants=self._get_participants(ceremony_type),
                    story_num=context.get('story_num'),
                    additional_context=context
                )

                logger.info(
                    "ceremony_executed_successfully",
                    ceremony_type=ceremony_type,
                    epic_num=context.get('epic_num', 1),
                    attempt=attempt + 1
                )

                return result

            except CeremonyExecutionError as e:
                if attempt < max_retries:
                    delay = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        "ceremony_retry",
                        ceremony_type=ceremony_type,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=delay,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "ceremony_failed_all_retries",
                        ceremony_type=ceremony_type,
                        attempts=max_retries + 1
                    )
                    raise

        # Should never reach here, but just in case
        raise CeremonyExecutionError(f"Ceremony {ceremony_type} failed after retries")

    def _update_context_with_ceremony(self, context: Dict[str, Any], result: Dict[str, Any]):
        """Update workflow context with ceremony results (Epic 28.4)."""
        # Store ceremony results for next workflows
        if 'ceremonies' not in context:
            context['ceremonies'] = []

        context['ceremonies'].append({
            'type': result.get('ceremony_type'),
            'id': result.get('ceremony_id'),
            'transcript_path': result.get('transcript_path'),
            'action_items': result.get('action_items', []),
            'learnings': result.get('learnings', [])
        })

        logger.debug(
            "context_updated_with_ceremony",
            ceremony_type=result.get('ceremony_type'),
            ceremony_id=result.get('ceremony_id'),
            action_items_count=len(result.get('action_items', [])),
            learnings_count=len(result.get('learnings', []))
        )

    def _get_participants(self, ceremony_type: str) -> List[str]:
        """Get participant list for ceremony type (Epic 28.4)."""
        participants = {
            'planning': ['John', 'Winston', 'Bob'],
            'standup': ['Bob', 'Amelia', 'Murat'],
            'retrospective': ['John', 'Winston', 'Sally', 'Bob', 'Amelia', 'Murat']
        }
        return participants.get(ceremony_type, ['team'])

    def _get_agent_for_workflow(self, workflow_info: 'WorkflowInfo') -> str:
        """
        Determine which agent should execute a workflow.

        Maps workflow names to agent names based on workflow type.
        This is a temporary mapping until AgentFactory is fully integrated.

        Args:
            workflow_info: Workflow metadata

        Returns:
            Agent name (e.g., "John", "Amelia", "Bob")
        """
        workflow_name_lower = workflow_info.name.lower()

        # Map workflow patterns to agents
        if "prd" in workflow_name_lower:
            return "John"
        elif "architecture" in workflow_name_lower or "tech-spec" in workflow_name_lower:
            return "Winston"
        elif "story" in workflow_name_lower and "create" in workflow_name_lower:
            return "Bob"
        elif "implement" in workflow_name_lower or "dev" in workflow_name_lower:
            return "Amelia"
        elif "test" in workflow_name_lower or "qa" in workflow_name_lower:
            return "Murat"
        elif "ux" in workflow_name_lower or "design" in workflow_name_lower:
            return "Sally"
        elif "brief" in workflow_name_lower or "research" in workflow_name_lower:
            return "Mary"
        else:
            return "Orchestrator"
