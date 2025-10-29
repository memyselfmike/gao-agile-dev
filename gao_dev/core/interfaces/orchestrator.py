"""
Orchestrator interface for GAO-Dev orchestration layer.

This module defines the contract for the main orchestrator that
coordinates workflows, agents, and methodologies.
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, List, Dict, Any


class IOrchestrator(ABC):
    """
    Interface for the main GAO-Dev orchestrator.

    The orchestrator is the top-level component that coordinates:
    - Methodology selection and complexity assessment
    - Workflow sequence execution
    - Agent task execution
    - Quality gate enforcement
    - Event publishing

    This interface allows for multiple orchestrator implementations
    (CLI-based, API-based, multi-tenant, etc.)

    Example:
        ```python
        orchestrator = GAODevOrchestrator(project_root)

        # Execute workflow
        async for message in orchestrator.execute_workflow("create-story"):
            print(message)

        # Execute full story workflow
        result = await orchestrator.execute_story_workflow(epic=1, story=1)
        ```
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the orchestrator.

        Performs setup tasks:
        - Load configuration
        - Initialize registries (agents, workflows, methodologies)
        - Load plugins
        - Set up event bus

        Raises:
            InitializationError: If initialization fails
        """
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        workflow_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowResult':  # Forward reference
        """
        Execute a single workflow.

        Args:
            workflow_name: Name of workflow to execute
            parameters: Optional parameters for the workflow

        Returns:
            WorkflowResult: Result of workflow execution

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            WorkflowExecutionError: If execution fails
        """
        pass

    @abstractmethod
    async def execute_workflow_sequence(
        self,
        sequence: 'WorkflowSequence',  # Forward reference
        context: Optional['WorkflowContext'] = None  # Forward reference
    ) -> 'SequenceResult':  # Forward reference
        """
        Execute a sequence of workflows.

        Workflows are executed in order, with each workflow receiving
        context and artifacts from previous workflows.

        Args:
            sequence: Workflow sequence to execute
            context: Optional execution context

        Returns:
            SequenceResult: Results from all workflows

        Raises:
            SequenceExecutionError: If sequence execution fails
        """
        pass

    @abstractmethod
    async def execute_story_workflow(
        self,
        epic: int,
        story: int,
        story_title: Optional[str] = None
    ) -> 'StoryResult':  # Forward reference
        """
        Execute complete workflow for implementing a story.

        This high-level method handles the entire story lifecycle:
        - Story creation (if needed)
        - Implementation
        - Testing
        - Review

        Args:
            epic: Epic number
            story: Story number
            story_title: Optional story title

        Returns:
            StoryResult: Complete story execution result

        Raises:
            StoryExecutionError: If story workflow fails
        """
        pass

    @abstractmethod
    async def execute_epic_workflow(
        self,
        epic: int
    ) -> 'EpicResult':  # Forward reference
        """
        Execute complete workflow for an epic.

        Executes all stories in the epic sequentially.

        Args:
            epic: Epic number

        Returns:
            EpicResult: Complete epic execution result

        Raises:
            EpicExecutionError: If epic workflow fails
        """
        pass

    @abstractmethod
    async def execute_agent_task(
        self,
        agent_type: str,
        task: str,
        context: Optional['AgentContext'] = None  # Forward reference
    ) -> AsyncGenerator[str, None]:
        """
        Execute a task using a specific agent.

        Args:
            agent_type: Agent type identifier
            task: Task description in natural language
            context: Optional execution context

        Yields:
            str: Progress messages during execution

        Raises:
            AgentNotFoundError: If agent type doesn't exist
            AgentExecutionError: If task execution fails
        """
        pass

    @abstractmethod
    async def assess_project(
        self,
        prompt: str,
        methodology: Optional[str] = None
    ) -> 'ComplexityAssessment':  # Forward reference
        """
        Assess project complexity and recommend workflow.

        Args:
            prompt: User's project description
            methodology: Optional methodology name (defaults to default)

        Returns:
            ComplexityAssessment: Assessment with recommended workflow

        Raises:
            AssessmentError: If assessment fails
        """
        pass

    @abstractmethod
    async def create_project(
        self,
        name: str,
        prompt: str,
        methodology: Optional[str] = None
    ) -> 'Project':  # Forward reference
        """
        Create a new project with complexity assessment.

        Args:
            name: Project name
            prompt: Project description
            methodology: Optional methodology (defaults to default)

        Returns:
            Project: Created project

        Raises:
            ProjectCreationError: If project creation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> 'HealthCheckResult':  # Forward reference
        """
        Perform system health check.

        Checks:
        - All services initialized
        - All registries populated
        - Required tools available
        - Configuration valid

        Returns:
            HealthCheckResult: Health check status

        Raises:
            HealthCheckError: If health check fails
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the orchestrator.

        Performs cleanup:
        - Unload plugins
        - Close connections
        - Save state
        - Clear caches
        """
        pass

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if orchestrator is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        pass

    @property
    @abstractmethod
    def project_root(self) -> 'ProjectPath':  # Forward reference
        """
        Get project root path.

        Returns:
            ProjectPath: Project root path
        """
        pass
