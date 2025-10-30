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
from typing import Callable
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
        max_retries: int = 3
    ):
        """
        Initialize coordinator with injected dependencies.

        Args:
            workflow_registry: Registry to lookup workflows
            agent_factory: Factory to create agents (future use)
            event_bus: Event bus for publishing lifecycle events
            agent_executor: Callback function to execute agent tasks
            project_root: Root directory of the project
            max_retries: Maximum retry attempts for failed workflows (default: 3)
        """
        self.workflow_registry = workflow_registry
        self.agent_factory = agent_factory
        self.event_bus = event_bus
        self.agent_executor = agent_executor
        self.project_root = project_root
        self.max_retries = max_retries

        logger.info(
            "workflow_coordinator_initialized",
            max_retries=max_retries,
            project_root=str(project_root)
        )

    async def execute_sequence(
        self,
        workflow_sequence: 'WorkflowSequence',
        context: 'WorkflowContext'
    ) -> 'WorkflowResult':
        """
        Execute a sequence of workflows step-by-step.

        Coordinates execution of multiple workflows in order, managing context
        passing, error handling, and event publishing.

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
                workflow_count=len(workflow_sequence.workflows)
            )

            # Execute workflows step by step
            for i, workflow_info in enumerate(workflow_sequence.workflows, 1):
                logger.info(
                    "workflow_step_starting",
                    step=i,
                    total=len(workflow_sequence.workflows),
                    workflow=workflow_info.name
                )

                # Execute single workflow step
                step_result = await self.execute_workflow(
                    workflow_id=workflow_info.name,
                    workflow_info=workflow_info,
                    step_number=i,
                    total_steps=len(workflow_sequence.workflows),
                    context=context
                )

                result.step_results.append(step_result)

                # Check for failure
                if step_result.status == "failed":
                    logger.error(
                        "workflow_step_failed",
                        step=workflow_info.name,
                        error=step_result.error_message
                    )
                    result.status = WorkflowStatus.FAILED
                    result.error_message = f"Step {i} failed: {step_result.error_message}"

                    # Publish sequence failed event
                    self.event_bus.publish(Event(
                        type="WorkflowSequenceFailed",
                        data={
                            "sequence_id": sequence_id,
                            "failed_at_step": i,
                            "error": step_result.error_message
                        }
                    ))
                    break

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
