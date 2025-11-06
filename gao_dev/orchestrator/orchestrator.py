"""Main orchestrator for GAO-Dev autonomous agents.

The GAODevOrchestrator is a thin facade that delegates to specialized services:
- WorkflowCoordinator: Workflow execution
- StoryLifecycleManager: Story and epic lifecycle
- ProcessExecutor: Subprocess execution (Claude CLI)
- QualityGateManager: Artifact validation
- BrianOrchestrator: Complexity assessment and workflow selection

This maintains the Single Responsibility Principle and ensures each component has
a clear, focused purpose.
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
from ..core.config_loader import ConfigLoader
from ..core.workflow_registry import WorkflowRegistry
from ..core.events.event_bus import EventBus
from ..core.services.workflow_coordinator import WorkflowCoordinator
from ..core.services.story_lifecycle import StoryLifecycleManager
from ..core.services.process_executor import ProcessExecutor
from ..core.services.quality_gate import QualityGateManager
from ..core.prompt_loader import PromptLoader
from ..core.context.context_persistence import ContextPersistence
from ..core.context.workflow_context import WorkflowContext
from ..core.context.context_api import set_workflow_context, clear_workflow_context
from ..lifecycle.project_lifecycle import ProjectDocumentLifecycle
from ..lifecycle.document_manager import DocumentLifecycleManager

logger = structlog.get_logger()


class GAODevOrchestrator:
    """
    Thin facade orchestrator for GAO-Dev autonomous development.

    Delegates all business logic to specialized services while maintaining a clean
    public API. This follows the Facade design pattern for simplified access to
    complex subsystems.

    Services:
    - workflow_coordinator: Executes workflow sequences
    - story_lifecycle: Manages story and epic lifecycle
    - process_executor: Executes external processes (Claude CLI)
    - quality_gate_manager: Validates workflow artifacts
    - brian_orchestrator: Analyzes complexity and selects workflows
    """

    def __init__(
        self,
        project_root: Path,
        api_key: Optional[str] = None,
        mode: str = "cli",
        workflow_coordinator: Optional[WorkflowCoordinator] = None,
        story_lifecycle: Optional[StoryLifecycleManager] = None,
        process_executor: Optional[ProcessExecutor] = None,
        quality_gate_manager: Optional[QualityGateManager] = None,
        brian_orchestrator: Optional[BrianOrchestrator] = None,
        context_persistence: Optional[ContextPersistence] = None,
    ):
        """
        Initialize the GAO-Dev orchestrator with injected services.

        For normal usage, call create_default() instead of this constructor directly.

        Args:
            project_root: Root directory of the project
            api_key: Optional Anthropic API key for Brian's analysis
            mode: Execution mode - "cli", "benchmark", or "api"
            workflow_coordinator: Optional custom WorkflowCoordinator
            story_lifecycle: Optional custom StoryLifecycleManager
            process_executor: Optional custom ProcessExecutor
            quality_gate_manager: Optional custom QualityGateManager
            brian_orchestrator: Optional custom BrianOrchestrator
            context_persistence: Optional custom ContextPersistence
        """
        self.project_root = project_root
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mode = mode

        # Initialize context persistence (always needed)
        self.context_persistence = context_persistence or ContextPersistence()

        # Initialize project-scoped document lifecycle
        self.doc_lifecycle: Optional[DocumentLifecycleManager] = None
        try:
            self.doc_lifecycle = ProjectDocumentLifecycle.initialize(self.project_root)
            logger.info(
                "document_lifecycle_initialized",
                project_root=str(self.project_root),
                db_path=str(ProjectDocumentLifecycle.get_db_path(self.project_root))
            )
        except Exception as e:
            logger.warning(
                "document_lifecycle_initialization_failed",
                project_root=str(self.project_root),
                error=str(e),
                message="Orchestrator will continue without document lifecycle tracking"
            )

        # CRITICAL FIX: Initialize missing services automatically
        # Check if any services are missing - if so, initialize all of them
        any_service_missing = (
            workflow_coordinator is None
            or story_lifecycle is None
            or process_executor is None
            or quality_gate_manager is None
            or brian_orchestrator is None
        )

        if any_service_missing:
            # Initialize all services using the same logic as create_default()
            # This ensures benchmarks can call GAODevOrchestrator() directly
            self._initialize_default_services(
                workflow_coordinator,
                story_lifecycle,
                process_executor,
                quality_gate_manager,
                brian_orchestrator,
            )
        else:
            # All services provided, use them directly
            self.workflow_coordinator = workflow_coordinator
            self.story_lifecycle = story_lifecycle
            self.process_executor = process_executor
            self.quality_gate_manager = quality_gate_manager
            self.brian_orchestrator = brian_orchestrator

        # Update workflow_coordinator with doc_manager if it was initialized
        if hasattr(self, 'workflow_coordinator') and self.workflow_coordinator:
            self.workflow_coordinator.doc_manager = self.doc_lifecycle

        logger.info(
            "orchestrator_initialized",
            mode=mode,
            project_root=str(project_root),
            has_doc_lifecycle=self.doc_lifecycle is not None,
            services_injected=all(
                [
                    hasattr(self, "workflow_coordinator"),
                    hasattr(self, "story_lifecycle"),
                    hasattr(self, "process_executor"),
                    hasattr(self, "quality_gate_manager"),
                ]
            ),
        )

    def _initialize_default_services(
        self,
        workflow_coordinator: Optional[WorkflowCoordinator],
        story_lifecycle: Optional[StoryLifecycleManager],
        process_executor: Optional[ProcessExecutor],
        quality_gate_manager: Optional[QualityGateManager],
        brian_orchestrator: Optional[BrianOrchestrator],
    ) -> None:
        """
        Initialize default service instances for any missing services.

        This is called by __init__ when services are not fully injected,
        allowing benchmarks and tests to use GAODevOrchestrator() directly.

        Args:
            workflow_coordinator: Optional injected coordinator
            story_lifecycle: Optional injected lifecycle manager
            process_executor: Optional injected executor
            quality_gate_manager: Optional injected quality manager
            brian_orchestrator: Optional injected Brian orchestrator
        """
        # Initialize configuration (needed by all services)
        self.config_loader = ConfigLoader(self.project_root)
        self.workflow_registry = WorkflowRegistry(self.config_loader)
        self.workflow_registry.index_workflows()

        # Initialize PromptLoader for task prompts
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt_loader = PromptLoader(
            prompts_dir=prompts_dir, config_loader=self.config_loader, cache_enabled=True
        )

        # Find Claude CLI if needed
        from ..core.cli_detector import find_claude_cli

        cli_path = find_claude_cli()

        if self.mode == "benchmark" and not cli_path:
            raise ValueError(
                "Claude CLI not found. Install Claude Code or set cli_path. "
                "Cannot run in benchmark mode without Claude CLI."
            )

        if cli_path:
            logger.info("claude_cli_detected", path=str(cli_path), mode=self.mode)

        # Initialize event bus for service communication
        event_bus = EventBus()

        # Initialize ProcessExecutor first (needed before WorkflowCoordinator)
        self.process_executor = process_executor or ProcessExecutor(
            project_root=self.project_root,
            cli_path=cli_path,
            api_key=self.api_key,
        )

        # Initialize or use provided services
        self.workflow_coordinator = workflow_coordinator or WorkflowCoordinator(
            workflow_registry=self.workflow_registry,
            agent_factory=None,
            event_bus=event_bus,
            agent_executor=self._execute_agent_task_static,  # Now self.process_executor exists
            project_root=self.project_root,
            doc_manager=self.doc_lifecycle,  # Pass document lifecycle manager
            max_retries=3,
        )

        self.story_lifecycle = story_lifecycle or StoryLifecycleManager(
            story_repository=None,
            event_bus=event_bus,
        )

        self.quality_gate_manager = quality_gate_manager or QualityGateManager(
            project_root=self.project_root,
            event_bus=event_bus,
        )

        # Initialize Brian orchestrator
        brian_persona_path = self.config_loader.get_agents_path() / "brian.md"
        self.brian_orchestrator = brian_orchestrator or BrianOrchestrator(
            workflow_registry=self.workflow_registry,
            api_key=self.api_key,
            brian_persona_path=brian_persona_path if brian_persona_path.exists() else None,
        )

    @classmethod
    def create_default(
        cls,
        project_root: Path,
        api_key: Optional[str] = None,
        mode: str = "cli",
    ) -> "GAODevOrchestrator":
        """
        Create orchestrator with default service configuration.

        Factory method that sets up all services with standard dependencies.

        Args:
            project_root: Root directory of the project
            api_key: Optional Anthropic API key
            mode: Execution mode - "cli", "benchmark", or "api"

        Returns:
            Fully initialized GAODevOrchestrator instance

        Raises:
            ValueError: If Claude CLI required but not found (benchmark mode)
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        # Initialize configuration
        config_loader = ConfigLoader(project_root)
        workflow_registry = WorkflowRegistry(config_loader)
        workflow_registry.index_workflows()

        # Get provider from environment (default: claude-code)
        provider_name = os.getenv("AGENT_PROVIDER", "claude-code").lower()
        logger.info("agent_provider_selected", provider=provider_name, mode=mode)

        # Initialize event bus for service communication
        event_bus = EventBus()

        # Initialize ProcessExecutor with provider (new API)
        process_executor = ProcessExecutor(
            project_root=project_root,
            provider_name=provider_name,
            provider_config={"api_key": api_key} if api_key else None,
        )

        # Create agent executor closure that captures process_executor
        # This will be used by WorkflowCoordinator to execute agent tasks
        async def agent_executor_closure(
            workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1
        ) -> AsyncGenerator[str, None]:
            """Closure that executes agent tasks via ProcessExecutor."""
            # Load workflow instructions from instructions.md
            # Ensure installed_path is a Path object (defensive coding for serialization)
            installed_path = (
                Path(workflow_info.installed_path)
                if isinstance(workflow_info.installed_path, str)
                else workflow_info.installed_path
            )
            instructions_file = installed_path / "instructions.md"
            if instructions_file.exists():
                task_prompt = instructions_file.read_text(encoding="utf-8")
            else:
                # Fallback to workflow description if no instructions.md
                task_prompt = workflow_info.description
                logger.warning(
                    "workflow_missing_instructions",
                    workflow=workflow_info.name,
                    path=str(instructions_file),
                )

            # Replace placeholders for story workflows
            if "{epic}" in task_prompt:
                task_prompt = task_prompt.replace("{epic}", str(epic))
            if "{story}" in task_prompt:
                task_prompt = task_prompt.replace("{story}", str(story))

            logger.info(
                "executing_workflow_via_closure",
                workflow=workflow_info.name,
                epic=epic,
                story=story,
                prompt_length=len(task_prompt),
            )

            # Execute via ProcessExecutor
            async for output in process_executor.execute_agent_task(task=task_prompt, timeout=None):
                yield output

        # Initialize services
        workflow_coordinator = WorkflowCoordinator(
            workflow_registry=workflow_registry,
            agent_factory=None,
            event_bus=event_bus,
            agent_executor=agent_executor_closure,
            project_root=project_root,
            doc_manager=None,  # Orchestrator will update this after doc_lifecycle initialization
            max_retries=3,
        )

        story_lifecycle = StoryLifecycleManager(
            story_repository=None,  # TODO: Add in Story 6.6
            event_bus=event_bus,
        )

        quality_gate_manager = QualityGateManager(
            project_root=project_root,
            event_bus=event_bus,
        )

        # Initialize Brian
        brian_persona_path = config_loader.get_agents_path() / "brian.md"
        brian_orchestrator = BrianOrchestrator(
            workflow_registry=workflow_registry,
            api_key=api_key,
            brian_persona_path=brian_persona_path if brian_persona_path.exists() else None,
        )

        # Create and return orchestrator instance
        return cls(
            project_root=project_root,
            api_key=api_key,
            mode=mode,
            workflow_coordinator=workflow_coordinator,
            story_lifecycle=story_lifecycle,
            process_executor=process_executor,
            quality_gate_manager=quality_gate_manager,
            brian_orchestrator=brian_orchestrator,
        )

    def get_document_manager(self) -> Optional[DocumentLifecycleManager]:
        """
        Get the project-scoped document lifecycle manager.

        Returns:
            DocumentLifecycleManager instance or None if not initialized

        Example:
            >>> orchestrator = GAODevOrchestrator(project_root=Path("my-project"))
            >>> doc_manager = orchestrator.get_document_manager()
            >>> if doc_manager:
            ...     doc_manager.registry.register_document("PRD.md", "product-requirements")
        """
        return self.doc_lifecycle

    # ========================================================================
    # Public API - Thin Delegation Methods
    # ========================================================================

    async def execute_task(self, task: str) -> AsyncGenerator[str, None]:
        """
        Execute a task using the orchestrator.

        Delegates to ProcessExecutor in benchmark mode, or uses SDK client in CLI mode.

        Args:
            task: Task description

        Yields:
            Message chunks from the agent
        """
        if self.mode == "benchmark":
            # Delegate to ProcessExecutor service
            async for chunk in self.process_executor.execute_agent_task(task):
                yield chunk
        else:
            raise NotImplementedError(
                "CLI mode requires setup. Use create_default() factory method."
            )

    async def create_prd(self, project_name: str) -> AsyncGenerator[str, None]:
        """
        Create a PRD using John (Product Manager).

        Args:
            project_name: Name of the project

        Yields:
            Progress messages
        """
        # Load prompt template from YAML
        template = self.prompt_loader.load_prompt("tasks/create_prd")
        task = self.prompt_loader.render_prompt(template, {"project_name": project_name})

        async for message in self.execute_task(task):
            yield message

    async def create_story(
        self, epic: int, story: int, story_title: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Create a user story using Bob (Scrum Master).

        Args:
            epic: Epic number
            story: Story number
            story_title: Optional story title

        Yields:
            Progress messages
        """
        # Load prompt template from YAML
        template = self.prompt_loader.load_prompt("tasks/create_story")
        title_part = f" with title '{story_title}'" if story_title else ""
        task = self.prompt_loader.render_prompt(
            template,
            {
                "epic": str(epic),
                "story": str(story),
                "story_title": story_title or "",
                "story_title_part": title_part,
            },
        )

        async for message in self.execute_task(task):
            yield message

    async def implement_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """
        Implement a story using the full workflow (Bob -> Amelia -> Bob).

        Args:
            epic: Epic number
            story: Story number

        Yields:
            Progress messages
        """
        # Load prompt template from YAML
        template = self.prompt_loader.load_prompt("tasks/implement_story")
        task = self.prompt_loader.render_prompt(template, {"epic": str(epic), "story": str(story)})

        async for message in self.execute_task(task):
            yield message

    async def create_architecture(self, project_name: str) -> AsyncGenerator[str, None]:
        """
        Create system architecture using Winston (Architect).

        Args:
            project_name: Name of the project

        Yields:
            Progress messages
        """
        # Load prompt template from YAML
        template = self.prompt_loader.load_prompt("tasks/create_architecture")
        task = self.prompt_loader.render_prompt(template, {"project_name": project_name})

        async for message in self.execute_task(task):
            yield message

    async def run_health_check(self) -> AsyncGenerator[str, None]:
        """
        Run system health check.

        Yields:
            Health check results
        """
        task = "Run the health_check tool and report the results."
        async for message in self.execute_task(task):
            yield message

    async def validate_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """
        Validate a story using Murat (QA).

        Args:
            epic: Epic number
            story: Story number

        Yields:
            Progress messages
        """
        # Load prompt template from YAML
        template = self.prompt_loader.load_prompt("tasks/validate_story")
        task = self.prompt_loader.render_prompt(template, {"epic": str(epic), "story": str(story)})

        async for message in self.execute_task(task):
            yield message

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
        """
        Execute complete workflow sequence from initial prompt with automatic context tracking.

        Delegates to WorkflowCoordinator for execution while handling high-level
        orchestration (workflow selection, clarification). Automatically creates and
        manages WorkflowContext throughout the workflow lifecycle.

        Args:
            initial_prompt: User's initial request
            workflow: Optional pre-selected workflow sequence (if None, auto-select)
            commit_after_steps: Whether to commit after each workflow step

        Returns:
            WorkflowResult with execution details, metrics, and context_id
        """
        from .workflow_results import WorkflowResult, WorkflowStatus
        import uuid

        # Initialize result
        result = WorkflowResult(
            workflow_name=(
                workflow.workflows[0].name if workflow and workflow.workflows else "auto-select"
            ),
            initial_prompt=initial_prompt,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            project_path=str(self.project_root) if self.project_root else None,
        )

        # Create WorkflowContext for this execution
        workflow_context = None

        try:
            # Step 1: Select workflow sequence if not provided
            if workflow is None:
                logger.info("workflow_auto_select", prompt=initial_prompt)
                workflow = await self.assess_and_select_workflows(initial_prompt)

                if not workflow.workflows:
                    # Workflow selection needs clarification
                    logger.info("workflow_selection_needs_clarification")

                    # Handle clarification based on mode
                    enhanced_prompt = self.handle_clarification(
                        ["Unable to determine workflow from prompt"], initial_prompt
                    )

                    # If clarification failed
                    result.status = WorkflowStatus.FAILED
                    result.end_time = datetime.now()
                    result.error_message = (
                        "Workflow selection requires clarification. " + workflow.routing_rationale
                    )
                    logger.warning("workflow_selection_failed", workflows_count=0)
                    return result

                result.workflow_name = f"{workflow.scale_level.name}_sequence"

            # Step 2: Create WorkflowContext for this execution
            workflow_id = str(uuid.uuid4())
            workflow_context = WorkflowContext(
                workflow_id=workflow_id,
                epic_num=1,  # Default to epic 1 (can be overridden by metadata)
                story_num=None,  # Will be set by story workflows
                feature=self._extract_feature_name(initial_prompt),
                workflow_name=result.workflow_name,
                current_phase="initialization",
                status="running",
                metadata={
                    "mode": self.mode,
                    "commit_after_steps": commit_after_steps,
                    "scale_level": workflow.scale_level.value if workflow.scale_level else None,
                    "project_type": workflow.project_type.value if workflow.project_type else None,
                    "estimated_stories": getattr(workflow, 'estimated_stories', None),
                    "estimated_epics": getattr(workflow, 'estimated_epics', None),
                    "routing_rationale": getattr(workflow, 'routing_rationale', None),
                },
            )

            # Persist initial context to database
            version = self.context_persistence.save_context(workflow_context)
            result.context_id = workflow_id

            logger.info(
                "workflow_context_created",
                workflow_id=workflow_id,
                version=version,
                feature=workflow_context.feature,
            )

            # Set thread-local context for agent access
            set_workflow_context(workflow_context)

            logger.info(
                "workflow_execution_started",
                workflow_count=len(workflow.workflows),
                scale_level=workflow.scale_level.value,
                context_id=workflow_id,
            )

            # Step 3: Transition to planning phase
            workflow_context = workflow_context.transition_phase("planning")
            self.context_persistence.update_context(workflow_context)
            set_workflow_context(workflow_context)  # Update thread-local

            # Delegate to WorkflowCoordinator for execution
            # Note: WorkflowCoordinator expects the old-style WorkflowContext from models.workflow_context
            # We'll pass metadata but also update our tracking context
            from ..core.models.workflow_context import WorkflowContext as OldWorkflowContext

            old_workflow_context = OldWorkflowContext(
                initial_prompt=initial_prompt,
                project_root=self.project_root,
                metadata={
                    "mode": self.mode,
                    "commit_after_steps": commit_after_steps,
                    "scale_level": workflow.scale_level.value,
                    "project_type": workflow.project_type.value,
                    "estimated_stories": workflow.estimated_stories,
                    "estimated_epics": workflow.estimated_epics,
                    "routing_rationale": workflow.routing_rationale,
                    "tracking_context_id": workflow_id,  # Link to our tracking context
                },
            )

            # Execute workflow sequence using WorkflowCoordinator
            coordinator_result = await self.workflow_coordinator.execute_sequence(
                workflow_sequence=workflow, context=old_workflow_context
            )

            # Copy results from coordinator to orchestrator result
            result.status = coordinator_result.status
            result.step_results = coordinator_result.step_results
            result.error_message = coordinator_result.error_message
            result.total_artifacts = coordinator_result.total_artifacts

            # Step 4: Update context with artifacts from execution
            for step_result in result.step_results:
                for artifact_path in step_result.artifacts_created:
                    workflow_context = workflow_context.add_artifact(artifact_path)

            # Check if execution failed
            if result.status == WorkflowStatus.FAILED:
                logger.error("workflow_sequence_failed", error=result.error_message)
                # Mark context as failed
                workflow_context = workflow_context.copy_with(
                    status="failed",
                    current_phase="failed",
                )
                workflow_context.metadata["error"] = result.error_message
                self.context_persistence.update_context(workflow_context)
                set_workflow_context(workflow_context)

            # Note: Story loop logic is now handled by WorkflowCoordinator._execute_story_loop()
            # during execute_sequence(). No additional logic needed here.

            # Mark as completed if all steps succeeded
            if result.status != WorkflowStatus.FAILED:
                result.status = WorkflowStatus.COMPLETED

                # Transition context to completed phase
                workflow_context = workflow_context.transition_phase("completed")
                workflow_context = workflow_context.copy_with(status="completed")
                self.context_persistence.update_context(workflow_context)
                set_workflow_context(workflow_context)

                logger.info(
                    "workflow_execution_completed",
                    steps_completed=len(result.step_results),
                    duration=result.duration_seconds,
                    context_id=workflow_id,
                )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            logger.error("workflow_execution_error", error=str(e), exc_info=True)

            # Mark context as failed if it was created
            if workflow_context is not None:
                workflow_context = workflow_context.copy_with(
                    status="failed",
                    current_phase="failed",
                )
                workflow_context.metadata["error"] = str(e)
                workflow_context.metadata["exception_type"] = type(e).__name__
                self.context_persistence.update_context(workflow_context)

        finally:
            result.end_time = datetime.now()
            result.total_artifacts = sum(
                len(step.artifacts_created) for step in result.step_results
            )

            # Clear thread-local context
            clear_workflow_context()

            logger.debug(
                "workflow_context_cleared",
                context_id=workflow_context.workflow_id if workflow_context else None,
            )

        return result

    async def execute_workflow_sequence_from_prompt(self, initial_prompt: str) -> WorkflowResult:
        """
        Convenience method: assess prompt and execute full workflow sequence.

        This is the main entry point for autonomous execution from a user prompt.

        Args:
            initial_prompt: User's initial request

        Returns:
            WorkflowResult with complete execution results
        """
        logger.info("autonomous_execution_starting", prompt_preview=initial_prompt[:100])

        # Brian assesses and selects workflows
        workflow_sequence = await self.assess_and_select_workflows(initial_prompt)

        # Execute the selected workflow sequence
        result = await self.execute_workflow(
            initial_prompt=initial_prompt, workflow=workflow_sequence
        )

        logger.info(
            "autonomous_execution_complete",
            success=result.success,
            duration=result.duration_seconds,
            steps=result.total_steps,
        )

        return result

    # ========================================================================
    # Agent Execution Bridge
    # ========================================================================

    async def _execute_agent_task_static(
        self, workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task via ProcessExecutor (used by WorkflowCoordinator).

        This method bridges the WorkflowCoordinator's agent_executor callback
        to the ProcessExecutor service. It loads the workflow instructions from
        instructions.md and delegates execution to ProcessExecutor.

        Args:
            workflow_info: Workflow metadata containing path to instructions
            epic: Epic number for story workflows
            story: Story number for story workflows

        Yields:
            Output from agent execution via Claude CLI

        Raises:
            ProcessExecutionError: If Claude CLI execution fails
            ValueError: If Claude CLI not found
        """
        logger.debug("executing_agent_task", workflow=workflow_info.name, epic=epic, story=story)

        # Load workflow instructions from instructions.md
        # Ensure installed_path is a Path object (defensive coding for serialization)
        installed_path = (
            Path(workflow_info.installed_path)
            if isinstance(workflow_info.installed_path, str)
            else workflow_info.installed_path
        )
        instructions_file = installed_path / "instructions.md"
        if instructions_file.exists():
            task_prompt = instructions_file.read_text(encoding="utf-8")
        else:
            # Fallback to workflow description if no instructions.md
            task_prompt = workflow_info.description
            logger.warning(
                "workflow_missing_instructions",
                workflow=workflow_info.name,
                path=str(instructions_file),
            )

        # Replace placeholders if this is a story workflow
        # Support both single {epic} and double {{epic_num}} brace formats
        replacements = {
            "{epic}": str(epic),
            "{story}": str(story),
            "{{epic_num}}": str(epic),
            "{{story_num}}": str(story),
            "{{dev_story_location}}": "docs/stories",  # Default story location
        }

        for placeholder, value in replacements.items():
            if placeholder in task_prompt:
                task_prompt = task_prompt.replace(placeholder, value)

        logger.info(
            "executing_workflow_via_process_executor",
            workflow=workflow_info.name,
            agent=self._get_agent_for_workflow(workflow_info),
            epic=epic,
            story=story,
            prompt_length=len(task_prompt),
        )

        # Execute via ProcessExecutor
        async for output in self.process_executor.execute_agent_task(
            task=task_prompt, timeout=None  # Use default timeout from ProcessExecutor
        ):
            yield output

    def _get_agent_for_workflow(self, workflow_info: "WorkflowInfo") -> str:
        """
        Determine which agent should execute a workflow.

        Maps workflow names to agent names based on workflow type.
        This is used by tests and is delegated to WorkflowCoordinator for
        actual execution.

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
            # Default to orchestrator
            return "Orchestrator"

    def _extract_feature_name(self, prompt: str) -> str:
        """
        Extract feature name from initial prompt for context tracking.

        This is a simple extraction that takes the first few words
        or falls back to a generic name. Can be enhanced with NLP later.

        Args:
            prompt: Initial user prompt

        Returns:
            Feature name string (kebab-case)
        """
        # Simple extraction: take first 3-5 words, convert to kebab-case
        words = prompt.lower().split()[:5]
        # Remove common stop words
        stop_words = {"a", "an", "the", "for", "with", "to", "and", "or"}
        filtered_words = [w for w in words if w not in stop_words]

        if not filtered_words:
            return "workflow-execution"

        # Join with hyphens, limit length
        feature_name = "-".join(filtered_words[:3])
        # Remove special characters
        feature_name = "".join(c if c.isalnum() or c == "-" else "" for c in feature_name)
        return feature_name[:50] or "workflow-execution"
