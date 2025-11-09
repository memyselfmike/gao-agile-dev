"""
WorkflowExecutionEngine - Service for executing workflows with variable resolution.

Extracted from GAODevOrchestrator (Epic 22, Story 22.1) to achieve SOLID principles.

Responsibilities:
- Execute workflows with variable resolution
- Execute generic tasks via workflow prompts
- Handle workflow errors and retries
- Coordinate with WorkflowRegistry, WorkflowExecutor, and PromptLoader
- Return structured workflow results

NOT responsible for:
- High-level orchestration (stays in orchestrator)
- Agent lifecycle management
- Context persistence (handled by orchestrator)
- Subprocess execution (ProcessExecutor)
"""

from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import structlog

from ..core.workflow_registry import WorkflowRegistry
from ..core.workflow_executor import WorkflowExecutor
from ..core.prompt_loader import PromptLoader
from ..core.models.workflow import WorkflowInfo
from .workflow_results import WorkflowResult, WorkflowStatus

logger = structlog.get_logger(__name__)


class WorkflowExecutionEngine:
    """
    Service for executing workflows with variable resolution.

    Single Responsibility: Execute individual workflows and tasks with proper
    variable resolution, template rendering, and error handling.

    This service was extracted from GAODevOrchestrator (Epic 22, Story 22.1) to
    follow the Single Responsibility Principle.

    Responsibilities:
    - Execute workflows with variable resolution
    - Execute generic tasks via task prompts
    - Resolve variables from workflow.yaml, config, and params
    - Render templates with resolved variables
    - Handle workflow execution errors
    - Return structured WorkflowResult objects

    NOT responsible for:
    - Workflow sequence coordination (WorkflowCoordinator)
    - Context management (orchestrator)
    - Agent subprocess execution (ProcessExecutor)
    - Story lifecycle (StoryLifecycleManager)

    Example:
        ```python
        engine = WorkflowExecutionEngine(
            workflow_registry=registry,
            workflow_executor=executor,
            prompt_loader=loader,
            agent_executor=execute_fn
        )

        result = await engine.execute(
            workflow_name="prd",
            params={"project_name": "MyApp"}
        )
        ```
    """

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        workflow_executor: WorkflowExecutor,
        prompt_loader: PromptLoader,
        agent_executor: Optional[callable] = None,
    ):
        """
        Initialize workflow execution engine with injected dependencies.

        Args:
            workflow_registry: Registry to lookup workflows
            workflow_executor: Executor for variable resolution and template rendering
            prompt_loader: Loader for task prompt templates
            agent_executor: Optional callback to execute agent tasks (async generator)
        """
        self.workflow_registry = workflow_registry
        self.workflow_executor = workflow_executor
        self.prompt_loader = prompt_loader
        self.agent_executor = agent_executor

        logger.info(
            "workflow_execution_engine_initialized",
            has_agent_executor=agent_executor is not None,
        )

    async def execute(
        self,
        workflow_name: str,
        params: Dict[str, Any],
        agent_executor: Optional[callable] = None,
    ) -> WorkflowResult:
        """
        Execute workflow with variable resolution.

        This method:
        1. Loads workflow from registry
        2. Resolves variables from params, workflow.yaml, and config
        3. Renders instructions template with resolved variables
        4. Executes workflow via agent executor
        5. Returns structured WorkflowResult

        Args:
            workflow_name: Name of workflow to execute
            params: Parameters for variable resolution
            agent_executor: Optional custom agent executor (overrides instance executor)

        Returns:
            WorkflowResult with execution status and details

        Raises:
            ValueError: If workflow not found or required variables missing
            RuntimeError: If agent executor not available
        """
        result = WorkflowResult(
            workflow_name=workflow_name,
            initial_prompt=params.get("initial_prompt", f"Execute {workflow_name}"),
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
        )

        try:
            # Step 1: Load workflow from registry
            workflow_info = self.workflow_registry.get_workflow(workflow_name)
            if not workflow_info:
                raise ValueError(f"Workflow '{workflow_name}' not found in registry")

            logger.info(
                "workflow_execution_started",
                workflow=workflow_name,
                params_count=len(params),
            )

            # Step 2: Resolve variables
            variables = self.workflow_executor.resolve_variables(workflow_info, params)

            logger.debug(
                "workflow_variables_resolved",
                workflow=workflow_name,
                variables=list(variables.keys()),
            )

            # Step 3: Load and render instructions
            instructions = self._load_instructions(workflow_info)
            rendered_instructions = self.workflow_executor.render_template(
                instructions, variables
            )

            logger.debug(
                "workflow_instructions_rendered",
                workflow=workflow_name,
                instructions_length=len(rendered_instructions),
            )

            # Step 4: Execute via agent executor
            executor = agent_executor or self.agent_executor
            if not executor:
                raise RuntimeError(
                    "No agent executor available. Provide executor in __init__ or execute()."
                )

            output_parts = []
            async for message in executor(workflow_info, **params):
                output_parts.append(message)

            # Step 5: Build successful result
            result.status = WorkflowStatus.COMPLETED
            result.end_time = datetime.now()

            logger.info(
                "workflow_execution_completed",
                workflow=workflow_name,
                duration_seconds=result.duration_seconds,
            )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()

            logger.error(
                "workflow_execution_failed",
                workflow=workflow_name,
                error=str(e),
                exc_info=True,
            )

        return result

    async def execute_task(
        self,
        task_name: str,
        params: Dict[str, Any],
    ) -> WorkflowResult:
        """
        Execute generic task via task prompt template.

        This method:
        1. Loads task prompt template from YAML
        2. Renders template with provided params
        3. Executes as a workflow

        Task prompts are stored in gao_dev/prompts/tasks/ directory
        and define reusable task templates (e.g., create_prd, implement_story).

        Args:
            task_name: Name of task prompt (e.g., "create_prd", "implement_story")
            params: Parameters for template rendering

        Returns:
            WorkflowResult with execution status and details

        Raises:
            ValueError: If task prompt not found
            RuntimeError: If agent executor not available
        """
        result = WorkflowResult(
            workflow_name=f"task:{task_name}",
            initial_prompt=f"Execute task: {task_name}",
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
        )

        try:
            # Step 1: Load task prompt template
            template_path = f"tasks/{task_name}"
            template = self.prompt_loader.load_prompt(template_path)

            if not template:
                raise ValueError(f"Task prompt '{task_name}' not found")

            logger.info(
                "task_execution_started",
                task=task_name,
                params_count=len(params),
            )

            # Step 2: Render template with params
            rendered_prompt = self.prompt_loader.render_prompt(template, params)

            logger.debug(
                "task_prompt_rendered",
                task=task_name,
                prompt_length=len(rendered_prompt),
            )

            # Step 3: Execute via agent executor
            if not self.agent_executor:
                raise RuntimeError("No agent executor available for task execution")

            output_parts = []
            # Execute task by passing rendered prompt directly
            # Note: This is a simplified execution - in practice, we'd use ProcessExecutor
            # For now, we'll create a minimal WorkflowInfo for compatibility
            task_workflow = WorkflowInfo(
                name=task_name,
                description=rendered_prompt,
                phase=-1,  # Task-level, no specific phase
                installed_path=Path("."),  # Not used for tasks
            )

            async for message in self.agent_executor(task_workflow, **params):
                output_parts.append(message)

            # Step 4: Build successful result
            result.status = WorkflowStatus.COMPLETED
            result.end_time = datetime.now()

            logger.info(
                "task_execution_completed",
                task=task_name,
                duration_seconds=result.duration_seconds,
            )

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()

            logger.error(
                "task_execution_failed",
                task=task_name,
                error=str(e),
                exc_info=True,
            )

        return result

    def _load_instructions(self, workflow_info: WorkflowInfo) -> str:
        """
        Load workflow instructions from instructions.md file.

        Args:
            workflow_info: Workflow metadata with installed_path

        Returns:
            Instructions content as string

        Raises:
            FileNotFoundError: If instructions.md not found
        """
        instructions_file = workflow_info.installed_path / "instructions.md"

        if not instructions_file.exists():
            logger.warning(
                "workflow_instructions_not_found",
                workflow=workflow_info.name,
                path=str(instructions_file),
            )
            return workflow_info.description  # Fallback to description

        return instructions_file.read_text(encoding="utf-8")
