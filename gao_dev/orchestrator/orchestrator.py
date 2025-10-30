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
        """
        self.project_root = project_root
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mode = mode

        # Use injected services or create defaults
        if workflow_coordinator is not None:
            self.workflow_coordinator = workflow_coordinator
        if story_lifecycle is not None:
            self.story_lifecycle = story_lifecycle
        if process_executor is not None:
            self.process_executor = process_executor
        if quality_gate_manager is not None:
            self.quality_gate_manager = quality_gate_manager
        if brian_orchestrator is not None:
            self.brian_orchestrator = brian_orchestrator

        # Initialize configuration if services not fully injected
        if not hasattr(self, "brian_orchestrator"):
            self.config_loader = ConfigLoader(project_root)
            self.workflow_registry = WorkflowRegistry(self.config_loader)
            self.workflow_registry.index_workflows()

            brian_persona_path = self.config_loader.get_agents_path() / "brian.md"
            self.brian_orchestrator = BrianOrchestrator(
                workflow_registry=self.workflow_registry,
                api_key=self.api_key,
                brian_persona_path=brian_persona_path if brian_persona_path.exists() else None,
            )

        logger.info(
            "orchestrator_initialized",
            mode=mode,
            project_root=str(project_root),
            services_injected=all([
                hasattr(self, "workflow_coordinator"),
                hasattr(self, "story_lifecycle"),
                hasattr(self, "process_executor"),
                hasattr(self, "quality_gate_manager"),
            ]),
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

        # Find Claude CLI
        from ..core.cli_detector import find_claude_cli
        cli_path = find_claude_cli()

        if mode == "benchmark" and not cli_path:
            raise ValueError(
                "Claude CLI not found. Install Claude Code or set cli_path. "
                "Cannot run in benchmark mode without Claude CLI."
            )

        if cli_path:
            logger.info("claude_cli_detected", path=str(cli_path), mode=mode)

        # Initialize event bus for service communication
        event_bus = EventBus()

        # Initialize services
        workflow_coordinator = WorkflowCoordinator(
            workflow_registry=workflow_registry,
            agent_factory=None,
            event_bus=event_bus,
            agent_executor=cls._execute_agent_task_static,
            project_root=project_root,
            max_retries=3,
        )

        story_lifecycle = StoryLifecycleManager(
            story_repository=None,  # TODO: Add in Story 6.6
            event_bus=event_bus,
        )

        process_executor = ProcessExecutor(
            project_root=project_root,
            cli_path=cli_path,
            api_key=api_key,
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
        task = f"""Use the John agent to create a Product Requirements Document for '{project_name}'.

John should:
1. Use the 'prd' workflow to understand the structure
2. Create a comprehensive PRD.md file
3. Include: Executive Summary, Problem Statement, Goals, Features, Success Metrics
4. Save to docs/PRD.md
5. Commit the file with a conventional commit message
"""
        async for message in self.execute_task(task):
            yield message

    async def create_story(
        self,
        epic: int,
        story: int,
        story_title: Optional[str] = None
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
        title_part = f" with title '{story_title}'" if story_title else ""
        task = f"""Use the Bob agent to create Story {epic}.{story}{title_part}.

Bob should:
1. Ensure the story directory exists for epic {epic}
2. Use the 'create-story' workflow
3. Read the epic definition from docs/epics.md
4. Create story file at docs/stories/epic-{epic}/story-{epic}.{story}.md
5. Include clear acceptance criteria
6. Set status to 'Draft'
7. Commit the story file
"""
        async for message in self.execute_task(task):
            yield message

    async def implement_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """
        Implement a story using the full workflow (Bob → Amelia → Bob).

        Args:
            epic: Epic number
            story: Story number

        Yields:
            Progress messages
        """
        task = f"""Execute the complete story implementation workflow for Story {epic}.{story}.

Coordinate the following agents:

1. **Bob** (Scrum Master):
   - Verify story {epic}.{story} exists and is ready
   - Check story status

2. **Amelia** (Developer):
   - Read the story file
   - Create feature branch: feature/epic-{epic}-story-{story}
   - Use 'dev-story' workflow for implementation guidance
   - Implement all acceptance criteria
   - Write tests
   - Update story status to 'In Progress'
   - Commit implementation

3. **Amelia** (Code Review):
   - Review code quality
   - Ensure tests pass
   - Verify acceptance criteria met
   - Update status to 'Ready for Review'

4. **Bob** (Story Completion):
   - Verify all DoD items completed
   - Merge feature branch
   - Update story status to 'Done'
   - Create final commit

Report progress at each step.
"""
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
        task = f"""Use the Winston agent to create system architecture for '{project_name}'.

Winston should:
1. Read the PRD from docs/PRD.md
2. Use the 'architecture' workflow
3. Create docs/architecture.md with:
   - System context
   - Component diagram
   - Data flow
   - Technology stack
   - Integration patterns
   - Technical risks
4. Commit the architecture document
"""
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

    async def validate_story(
        self,
        epic: int,
        story: int
    ) -> AsyncGenerator[str, None]:
        """
        Validate a story using Murat (QA).

        Args:
            epic: Epic number
            story: Story number

        Yields:
            Progress messages
        """
        task = f"""Use the Murat agent to validate Story {epic}.{story}.

Murat should:
1. Read the story file from docs/stories/epic-{epic}/story-{epic}.{story}.md
2. Verify all acceptance criteria are documented
3. Check that tests exist and pass
4. Verify code coverage meets requirements (target: 80%+)
5. Check code quality (linting, type hints)
6. Report validation results (PASS/FAIL)
7. If FAIL, document what needs to be fixed
"""
        async for message in self.execute_task(task):
            yield message

    async def assess_and_select_workflows(
        self,
        initial_prompt: str,
        force_scale_level: Optional[ScaleLevel] = None
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
        logger.info(
            "brian_assessing_prompt",
            prompt_preview=initial_prompt[:100]
        )

        workflow_sequence = await self.brian_orchestrator.assess_and_select_workflows(
            initial_prompt=initial_prompt,
            force_scale_level=force_scale_level
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
        self,
        clarifying_questions: List[str],
        initial_prompt: str
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
            initial_prompt=initial_prompt[:100]
        )

        # Log questions
        for i, question in enumerate(clarifying_questions, 1):
            logger.info("clarifying_question", number=i, question=question)

        if self.mode == "benchmark":
            logger.warning(
                "clarification_in_benchmark_mode",
                message="Cannot ask clarifying questions in benchmark mode"
            )
            return None
        else:
            logger.info(
                "clarification_mode",
                message="Clarification handling delegated to caller"
            )
            return None

    async def execute_workflow(
        self,
        initial_prompt: str,
        workflow: Optional[WorkflowSequence] = None,
        commit_after_steps: bool = True
    ) -> WorkflowResult:
        """
        Execute complete workflow sequence from initial prompt.

        Delegates to WorkflowCoordinator for execution while handling high-level
        orchestration (workflow selection, clarification).

        Args:
            initial_prompt: User's initial request
            workflow: Optional pre-selected workflow sequence (if None, auto-select)
            commit_after_steps: Whether to commit after each workflow step

        Returns:
            WorkflowResult with execution details and metrics
        """
        from .workflow_results import WorkflowResult, WorkflowStatus

        # Initialize result
        result = WorkflowResult(
            workflow_name=workflow.workflows[0].name if workflow and workflow.workflows else "auto-select",
            initial_prompt=initial_prompt,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            project_path=str(self.project_root) if self.project_root else None
        )

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
                        ["Unable to determine workflow from prompt"],
                        initial_prompt
                    )

                    # If clarification failed
                    result.status = WorkflowStatus.FAILED
                    result.end_time = datetime.now()
                    result.error_message = "Workflow selection requires clarification. " + workflow.routing_rationale
                    logger.warning("workflow_selection_failed", workflows_count=0)
                    return result

                result.workflow_name = f"{workflow.scale_level.name}_sequence"

            logger.info(
                "workflow_execution_started",
                workflow_count=len(workflow.workflows),
                scale_level=workflow.scale_level.value
            )

            # Delegate to WorkflowCoordinator for execution
            from ..core.models.workflow_context import WorkflowContext

            workflow_context = WorkflowContext(
                initial_prompt=initial_prompt,
                project_root=self.project_root,
                metadata={
                    "mode": self.mode,
                    "commit_after_steps": commit_after_steps
                }
            )

            # Execute workflow sequence using WorkflowCoordinator
            coordinator_result = await self.workflow_coordinator.execute_sequence(
                workflow_sequence=workflow,
                context=workflow_context
            )

            # Copy results from coordinator to orchestrator result
            result.status = coordinator_result.status
            result.step_results = coordinator_result.step_results
            result.error_message = coordinator_result.error_message
            result.total_artifacts = coordinator_result.total_artifacts

            # Check if execution failed
            if result.status == WorkflowStatus.FAILED:
                logger.error(
                    "workflow_sequence_failed",
                    error=result.error_message
                )

            # Mark as completed if all steps succeeded
            if result.status != WorkflowStatus.FAILED:
                result.status = WorkflowStatus.COMPLETED
                logger.info(
                    "workflow_execution_completed",
                    steps_completed=len(result.step_results),
                    duration=result.duration_seconds
                )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            logger.error(
                "workflow_execution_error",
                error=str(e),
                exc_info=True
            )

        finally:
            result.end_time = datetime.now()
            result.total_artifacts = sum(
                len(step.artifacts_created) for step in result.step_results
            )

        return result

    async def execute_workflow_sequence_from_prompt(
        self,
        initial_prompt: str
    ) -> WorkflowResult:
        """
        Convenience method: assess prompt and execute full workflow sequence.

        This is the main entry point for autonomous execution from a user prompt.

        Args:
            initial_prompt: User's initial request

        Returns:
            WorkflowResult with complete execution results
        """
        logger.info(
            "autonomous_execution_starting",
            prompt_preview=initial_prompt[:100]
        )

        # Brian assesses and selects workflows
        workflow_sequence = await self.assess_and_select_workflows(initial_prompt)

        # Execute the selected workflow sequence
        result = await self.execute_workflow(
            initial_prompt=initial_prompt,
            workflow=workflow_sequence
        )

        logger.info(
            "autonomous_execution_complete",
            success=result.success,
            duration=result.duration_seconds,
            steps=result.total_steps
        )

        return result

    # ========================================================================
    # Static Helper Methods
    # ========================================================================

    @staticmethod
    async def _execute_agent_task_static(
        workflow_info: "WorkflowInfo",
        epic: int = 1,
        story: int = 1
    ) -> AsyncGenerator[str, None]:
        """
        Static helper for executing agent tasks (used by WorkflowCoordinator).

        This is a placeholder for actual agent execution logic.
        In practice, this would be replaced with the actual agent executor.

        Args:
            workflow_info: Workflow metadata
            epic: Epic number for story workflows
            story: Story number for story workflows

        Yields:
            Output from agent execution
        """
        logger.debug(
            "executing_agent_task",
            workflow=workflow_info.name,
            epic=epic,
            story=story
        )
        # Actual implementation would execute the appropriate agent
        # For now, this is a placeholder
        yield "Task execution would happen here"

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
