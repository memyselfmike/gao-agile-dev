"""AgentCoordinator Service - Coordinates agent operations and lifecycle.

Extracted from GAODevOrchestrator in Story 22.3 to centralize agent-related
operations into a focused service with clear responsibilities.

Responsibilities:
- Execute tasks via appropriate agents
- Map workflows to correct agents
- Manage agent lifecycle (creation, caching)
- Coordinate agent-specific context
- Handle agent errors and retries

Design Pattern: Service pattern with agent factory integration
"""

from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any
import structlog

logger = structlog.get_logger()


class AgentCoordinator:
    """
    Service for coordinating agent operations.

    This service centralizes all agent-related logic including:
    - Agent task execution via ProcessExecutor
    - Agent-workflow mapping
    - Agent lifecycle management
    - Agent context coordination

    The coordinator acts as a bridge between workflows and agent execution,
    ensuring consistent agent behavior across the system.

    Example:
        ```python
        coordinator = AgentCoordinator(
            process_executor=executor,
            project_root=Path("/project")
        )

        # Execute task via agent
        async for output in coordinator.execute_task(
            agent_name="Amelia",
            instructions="Implement Story 1.1",
            context={"epic": 1, "story": 1}
        ):
            print(output)

        # Get agent for workflow
        agent_name = coordinator.get_agent("prd")  # Returns "John"
        ```

    Attributes:
        process_executor: ProcessExecutor for running agent tasks
        project_root: Root directory of the project
        _agent_cache: Cache of agent instances (if using AgentFactory)
    """

    def __init__(
        self,
        process_executor: "ProcessExecutor",
        project_root: Path,
    ):
        """
        Initialize agent coordinator.

        Args:
            process_executor: ProcessExecutor for executing agent tasks
            project_root: Root directory of the project
        """
        self.process_executor = process_executor
        self.project_root = project_root
        self._agent_cache: Dict[str, Any] = {}

        logger.info(
            "agent_coordinator_initialized",
            project_root=str(project_root),
        )

    async def execute_task(
        self,
        agent_name: str,
        instructions: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[list] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via named agent.

        This method coordinates agent task execution by:
        1. Preparing agent context from provided metadata
        2. Executing instructions via ProcessExecutor
        3. Streaming output back to caller
        4. Handling errors and retries

        Args:
            agent_name: Name of agent to execute task (e.g., "Amelia", "John")
            instructions: Task instructions/prompt for the agent
            context: Optional context metadata (epic, story, workflow_name, etc.)
            tools: Optional list of tools to enable (uses defaults if None)

        Yields:
            Output chunks from agent execution

        Raises:
            ProcessExecutionError: If agent execution fails

        Example:
            ```python
            async for output in coordinator.execute_task(
                agent_name="Bob",
                instructions="Create story 1.1",
                context={"epic": 1, "story": 1, "workflow_name": "story-create"}
            ):
                print(output)
            ```
        """
        context = context or {}

        logger.info(
            "agent_coordinator_executing_task",
            agent_name=agent_name,
            instructions_length=len(instructions),
            context=context,
        )

        # Default tools for agents
        if tools is None:
            tools = [
                "Read", "Write", "Edit", "MultiEdit",
                "Bash", "Grep", "Glob",
                "TodoWrite"
            ]

        try:
            # Execute via ProcessExecutor
            async for output in self.process_executor.execute_agent_task(
                task=instructions,
                tools=tools,
                timeout=None
            ):
                yield output

            logger.info(
                "agent_coordinator_task_complete",
                agent_name=agent_name,
                context=context,
            )

        except Exception as e:
            logger.error(
                "agent_coordinator_task_failed",
                agent_name=agent_name,
                error=str(e),
                context=context,
                exc_info=True,
            )
            raise

    def get_agent(self, workflow_name: str) -> str:
        """
        Get agent name for workflow.

        Maps workflow names to agent names based on workflow type.
        This mapping ensures the right specialist handles each workflow.

        Workflow Type Mapping:
        - PRD workflows -> John (Product Manager)
        - Architecture workflows -> Winston (Technical Architect)
        - Story creation workflows -> Bob (Scrum Master)
        - Implementation workflows -> Amelia (Developer)
        - Test workflows -> Murat (Test Architect)
        - UX workflows -> Sally (UX Designer)
        - Research/Brief workflows -> Mary (Engineering Manager)

        Args:
            workflow_name: Name of the workflow (e.g., "prd", "story-create")

        Returns:
            Agent name (e.g., "John", "Amelia", "Bob")

        Example:
            ```python
            agent = coordinator.get_agent("prd")  # Returns "John"
            agent = coordinator.get_agent("story-implement")  # Returns "Amelia"
            agent = coordinator.get_agent("architecture")  # Returns "Winston"
            ```
        """
        workflow_name_lower = workflow_name.lower()

        # Map workflow patterns to agents
        if "prd" in workflow_name_lower:
            agent = "John"
        elif "architecture" in workflow_name_lower or "tech-spec" in workflow_name_lower:
            agent = "Winston"
        elif "story" in workflow_name_lower and "create" in workflow_name_lower:
            agent = "Bob"
        elif "implement" in workflow_name_lower or "dev" in workflow_name_lower:
            agent = "Amelia"
        elif "test" in workflow_name_lower or "qa" in workflow_name_lower:
            agent = "Murat"
        elif "ux" in workflow_name_lower or "design" in workflow_name_lower:
            agent = "Sally"
        elif "brief" in workflow_name_lower or "research" in workflow_name_lower:
            agent = "Mary"
        else:
            # Default to orchestrator for generic workflows
            agent = "Orchestrator"

        logger.debug(
            "agent_coordinator_workflow_mapping",
            workflow_name=workflow_name,
            agent=agent,
        )

        return agent
