"""Main orchestrator for GAO-Dev autonomous agents.

The GAODevOrchestrator is a thin facade (~250 LOC) that delegates to specialized services:
- WorkflowExecutionEngine: Workflow execution with variable resolution (Story 22.1)
- ArtifactManager: Artifact detection and registration (Story 22.2)
- AgentCoordinator: Agent lifecycle and coordination (Story 22.3)
- CeremonyOrchestrator: Multi-agent ceremonies (Story 22.4)
- WorkflowCoordinator: Workflow sequence execution
- StoryLifecycleManager: Story and epic lifecycle
- ProcessExecutor: Subprocess execution (Claude CLI)
- QualityGateManager: Artifact validation
- BrianOrchestrator: Complexity assessment and workflow selection

This maintains the Single Responsibility Principle and ensures each component has
a clear, focused purpose. All business logic has been extracted to focused services.
"""

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, List, Any
from datetime import datetime
import structlog
import os

from ..tools import gao_dev_server
from .agent_definitions import AGENT_DEFINITIONS
from .workflow_results import StoryResult, EpicResult, StoryStatus, WorkflowResult
from .brian_orchestrator import (
    BrianOrchestrator,
    WorkflowSequence,
    ScaleLevel,
)
from .workflow_execution_engine import WorkflowExecutionEngine
from .artifact_manager import ArtifactManager
from .agent_coordinator import AgentCoordinator
from .ceremony_orchestrator import CeremonyOrchestrator
from .metadata_extractor import MetadataExtractor
from ..core.config_loader import ConfigLoader
from ..core.workflow_registry import WorkflowRegistry
from ..core.workflow_executor import WorkflowExecutor
from ..core.events.event_bus import EventBus
from ..core.services.workflow_coordinator import WorkflowCoordinator
from ..core.services.story_lifecycle import StoryLifecycleManager
from ..core.services.process_executor import ProcessExecutor
from ..core.services.quality_gate import QualityGateManager
from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.prompt_loader import PromptLoader
from ..core.context.context_persistence import ContextPersistence
from ..core.context.workflow_context import WorkflowContext
from ..core.context.context_api import set_workflow_context, clear_workflow_context
from ..lifecycle.project_lifecycle import ProjectDocumentLifecycle
from ..lifecycle.document_manager import DocumentLifecycleManager

logger = structlog.get_logger()


class GAODevOrchestrator:
    """
    Thin facade orchestrator for GAO-Dev autonomous development (~250 LOC).

    Delegates all business logic to specialized services while maintaining a clean
    public API. This follows the Facade design pattern for simplified access to
    complex subsystems.

    Services (injected via constructor):
    - workflow_execution_engine: Workflow execution with variable resolution (Story 22.1)
    - artifact_manager: Artifact detection and registration (Story 22.2)
    - agent_coordinator: Agent lifecycle and coordination (Story 22.3)
    - ceremony_orchestrator: Multi-agent ceremonies (Story 22.4)
    - workflow_coordinator: Workflow sequence execution
    - story_lifecycle: Story and epic lifecycle
    - process_executor: Subprocess execution (Claude CLI)
    - quality_gate_manager: Artifact validation
    - brian_orchestrator: Complexity assessment and workflow selection

    Usage:
        Use create_default() factory method for normal instantiation.
        Direct constructor is for dependency injection in tests.
    """

    def __init__(
        self,
        project_root: Path,
        workflow_execution_engine: WorkflowExecutionEngine,
        artifact_manager: ArtifactManager,
        agent_coordinator: AgentCoordinator,
        ceremony_orchestrator: CeremonyOrchestrator,
        workflow_coordinator: WorkflowCoordinator,
        story_lifecycle: StoryLifecycleManager,
        process_executor: ProcessExecutor,
        quality_gate_manager: QualityGateManager,
        brian_orchestrator: BrianOrchestrator,
        context_persistence: Optional[ContextPersistence] = None,
        api_key: Optional[str] = None,
        mode: str = "cli",
    ):
        """
        Initialize orchestrator with fully injected services.

        For normal usage, call create_default() factory method instead.

        Args:
            project_root: Root directory of the project
            workflow_execution_engine: Workflow execution service (Story 22.1)
            artifact_manager: Artifact management service (Story 22.2)
            agent_coordinator: Agent coordination service (Story 22.3)
            ceremony_orchestrator: Ceremony orchestration service (Story 22.4)
            workflow_coordinator: Workflow sequence coordinator
            story_lifecycle: Story lifecycle manager
            process_executor: Process execution service
            quality_gate_manager: Quality gate service
            brian_orchestrator: Brian orchestrator for workflow selection
            context_persistence: Optional context persistence service
            api_key: Optional Anthropic API key
            mode: Execution mode - "cli", "benchmark", or "api"
        """
        self.project_root = project_root
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mode = mode

        # Initialize context persistence
        self.context_persistence = context_persistence or ContextPersistence()

        # Store injected services
        self.workflow_execution_engine = workflow_execution_engine
        self.artifact_manager = artifact_manager
        self.agent_coordinator = agent_coordinator
        self.ceremony_orchestrator = ceremony_orchestrator
        self.workflow_coordinator = workflow_coordinator
        self.story_lifecycle = story_lifecycle
        self.process_executor = process_executor
        self.quality_gate_manager = quality_gate_manager
        self.brian_orchestrator = brian_orchestrator

        logger.info(
            "orchestrator_initialized",
            mode=mode,
            project_root=str(project_root),
            services_count=9,
        )

    @property
    def doc_lifecycle(self) -> Optional[DocumentLifecycleManager]:
        """Get the document lifecycle manager from ArtifactManager."""
        return self.artifact_manager.doc_lifecycle

    @doc_lifecycle.setter
    def doc_lifecycle(self, value: Optional[DocumentLifecycleManager]) -> None:
        """Set the document lifecycle manager and update ArtifactManager reference."""
        self.artifact_manager.doc_lifecycle = value

    @classmethod
    def create_default(
        cls,
        project_root: Path,
        api_key: Optional[str] = None,
        mode: str = "cli",
    ) -> "GAODevOrchestrator":
        """
        Create orchestrator with default services.

        Delegates to orchestrator_factory.create_orchestrator() for initialization.
        This is the recommended way to create an orchestrator instance.

        Args:
            project_root: Root directory of the project
            api_key: Optional Anthropic API key
            mode: Execution mode - "cli", "benchmark", or "api"

        Returns:
            Fully initialized GAODevOrchestrator instance

        Example:
            >>> from gao_dev.orchestrator import GAODevOrchestrator
            >>> orch = GAODevOrchestrator.create_default(Path("my-project"))
        """
        from .orchestrator_factory import create_orchestrator

        return create_orchestrator(project_root=project_root, api_key=api_key, mode=mode)

    def close(self) -> None:
        """Close all resources and database connections."""
        if self.doc_lifecycle is not None:
            try:
                self.doc_lifecycle.registry.close()
                logger.debug("document_lifecycle_closed")
            except Exception as e:
                logger.warning("document_lifecycle_close_failed", error=str(e))

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.close()
        return False

    # ========================================================================
    # Public API - High-Level Methods (Delegate to Services)
    # ========================================================================

    async def execute_task(
        self,
        task: str,
        tools: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via AgentCoordinator.

        Delegates to AgentCoordinator.execute_task() which handles ProcessExecutor execution.

        Args:
            task: Task description
            tools: Optional tool list (uses defaults if None)

        Yields:
            Output from agent execution
        """
        async for chunk in self.agent_coordinator.execute_task(
            agent_name="Orchestrator",
            instructions=task,
            tools=tools,
        ):
            yield chunk

    async def create_prd(self, project_name: str) -> AsyncGenerator[str, None]:
        """Create PRD via WorkflowExecutionEngine."""
        result = await self.workflow_execution_engine.execute_task(
            "create_prd", {"project_name": project_name}
        )
        yield f"PRD creation: {result.status.value}"

    async def create_story(
        self, epic: int, story: int, story_title: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Create story via WorkflowExecutionEngine."""
        result = await self.workflow_execution_engine.execute_task(
            "create_story",
            {
                "epic": str(epic),
                "story": str(story),
                "story_title": story_title or "",
                "story_title_part": f" with title '{story_title}'" if story_title else "",
            },
        )
        yield f"Story creation: {result.status.value}"

    async def implement_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """Implement story via WorkflowExecutionEngine."""
        result = await self.workflow_execution_engine.execute_task(
            "implement_story", {"epic": str(epic), "story": str(story)}
        )
        yield f"Story implementation: {result.status.value}"

    async def create_architecture(self, project_name: str) -> AsyncGenerator[str, None]:
        """Create architecture via WorkflowExecutionEngine."""
        result = await self.workflow_execution_engine.execute_task(
            "create_architecture", {"project_name": project_name}
        )
        yield f"Architecture creation: {result.status.value}"

    async def validate_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """Validate story via WorkflowExecutionEngine."""
        result = await self.workflow_execution_engine.execute_task(
            "validate_story", {"epic": str(epic), "story": str(story)}
        )
        yield f"Story validation: {result.status.value}"

    async def assess_and_select_workflows(
        self, initial_prompt: str, force_scale_level: Optional[ScaleLevel] = None
    ) -> WorkflowSequence:
        """
        Use Brian (Engineering Manager) to analyze prompt and select workflows.

        Delegates to BrianOrchestrator to:
        - Assess project complexity (Scale Level 0-4)
        - Determine project type (greenfield, brownfield, etc.)
        - Build appropriate workflow sequence
        - Provide routing rationale

        Args:
            initial_prompt: User's initial request
            force_scale_level: Optional override for scale level (for testing)

        Returns:
            WorkflowSequence with selected workflows and rationale
        """
        logger.info("brian_assessing_prompt", prompt_preview=initial_prompt[:100])

        workflow_sequence = await self.brian_orchestrator.assess_and_select_workflows(
            initial_prompt=initial_prompt, force_scale_level=force_scale_level
        )

        logger.info(
            "brian_workflow_selection_complete",
            scale_level=workflow_sequence.scale_level.value,
            project_type=workflow_sequence.project_type.value,
            workflow_count=len(workflow_sequence.workflows),
        )

        return workflow_sequence

    def get_scale_level_description(self, scale_level: ScaleLevel) -> str:
        """
        Get human-readable description of scale level.

        Delegates to BrianOrchestrator.

        Args:
            scale_level: Scale level enum

        Returns:
            Description string
        """
        return self.brian_orchestrator.get_scale_level_description(scale_level)

    def handle_clarification(
        self, clarifying_questions: List[str], initial_prompt: str
    ) -> Optional[str]:
        """
        Handle clarification when workflow selection is ambiguous.

        Behavior depends on execution mode:
        - CLI mode: Would prompt user interactively (simplified for now)
        - Benchmark mode: Returns None (fail gracefully)
        - API mode: Returns None (caller should handle)

        Args:
            clarifying_questions: List of questions to ask
            initial_prompt: Original user prompt

        Returns:
            Enhanced prompt with clarification, or None if cannot clarify
        """
        logger.info(
            "clarification_needed",
            mode=self.mode,
            questions_count=len(clarifying_questions),
            initial_prompt=initial_prompt[:100],
        )

        # Log questions
        for i, question in enumerate(clarifying_questions, 1):
            logger.info("clarifying_question", number=i, question=question)

        if self.mode == "benchmark":
            logger.warning(
                "clarification_in_benchmark_mode",
                message="Cannot ask clarifying questions in benchmark mode",
            )
            return None
        else:
            logger.info("clarification_mode", message="Clarification handling delegated to caller")
            return None

    async def execute_workflow(
        self,
        initial_prompt: str,
        workflow: Optional[WorkflowSequence] = None,
        commit_after_steps: bool = True,
    ) -> WorkflowResult:
        """Execute workflow sequence with context tracking. Delegates to WorkflowCoordinator."""
        from .workflow_results import WorkflowResult, WorkflowStatus
        from ..core.models.workflow_context import WorkflowContext as OldWorkflowContext
        import uuid

        result = WorkflowResult(
            workflow_name=workflow.workflows[0].name if workflow and workflow.workflows else "auto-select",
            initial_prompt=initial_prompt,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            project_path=str(self.project_root),
        )

        workflow_context = None

        try:
            # Auto-select workflow if not provided
            if workflow is None:
                workflow = await self.assess_and_select_workflows(initial_prompt)
                if not workflow.workflows:
                    result.status = WorkflowStatus.FAILED
                    result.end_time = datetime.now()
                    result.error_message = "Workflow selection requires clarification"
                    return result
                result.workflow_name = f"{workflow.scale_level.name}_sequence"

            # Create workflow context
            workflow_id = str(uuid.uuid4())
            words = initial_prompt.lower().split()[:5]
            filtered = [w for w in words if w not in {"a", "an", "the", "for", "with", "to", "and", "or"}]
            feature = "-".join(filtered[:3]) if filtered else "workflow-execution"
            feature = "".join(c if c.isalnum() or c == "-" else "" for c in feature)[:50]

            workflow_context = WorkflowContext(
                workflow_id=workflow_id,
                epic_num=1,
                story_num=None,
                feature=feature or "workflow-execution",
                workflow_name=result.workflow_name,
                current_phase="initialization",
                status="running",
                metadata={
                    "mode": self.mode,
                    "scale_level": workflow.scale_level.value if workflow.scale_level else None,
                    "project_type": workflow.project_type.value if workflow.project_type else None,
                },
            )

            self.context_persistence.save_context(workflow_context)
            result.context_id = workflow_id
            set_workflow_context(workflow_context)

            # Execute via WorkflowCoordinator
            old_context = OldWorkflowContext(
                initial_prompt=initial_prompt,
                project_root=self.project_root,
                metadata={
                    "mode": self.mode,
                    "scale_level": workflow.scale_level.value,
                    "project_type": workflow.project_type.value,
                    "tracking_context_id": workflow_id,
                },
            )

            coordinator_result = await self.workflow_coordinator.execute_sequence(
                workflow_sequence=workflow, context=old_context
            )

            # Copy results
            result.status = coordinator_result.status
            result.step_results = coordinator_result.step_results
            result.error_message = coordinator_result.error_message
            result.total_artifacts = coordinator_result.total_artifacts

            # Update context
            for step_result in result.step_results:
                for artifact_path in step_result.artifacts_created:
                    workflow_context = workflow_context.add_artifact(artifact_path)

            if result.status != WorkflowStatus.FAILED:
                result.status = WorkflowStatus.COMPLETED
                workflow_context = workflow_context.transition_phase("completed")
                workflow_context = workflow_context.copy_with(status="completed")

            self.context_persistence.update_context(workflow_context)

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            logger.error("workflow_execution_error", error=str(e), exc_info=True)
            if workflow_context:
                workflow_context.metadata["error"] = str(e)
                self.context_persistence.update_context(workflow_context)

        finally:
            result.end_time = datetime.now()
            result.total_artifacts = sum(len(step.artifacts_created) for step in result.step_results)
            clear_workflow_context()

        return result

    async def execute_workflow_sequence_from_prompt(self, initial_prompt: str) -> WorkflowResult:
        """Assess prompt and execute full workflow sequence (main entry point)."""
        workflow_sequence = await self.assess_and_select_workflows(initial_prompt)
        return await self.execute_workflow(initial_prompt=initial_prompt, workflow=workflow_sequence)


