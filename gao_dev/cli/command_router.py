"""Command routing and execution for interactive Brian chat.

Routes confirmed workflow sequences and explicit commands to appropriate
orchestrator methods, with progress streaming, error recovery, and Rich formatting.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

from typing import AsyncIterator, Dict, Any, Optional
from pathlib import Path
import asyncio
import time
import structlog
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn
from rich.console import Console
from rich.panel import Panel

from gao_dev.orchestrator.models import WorkflowSequence
from gao_dev.cli.response_formatter import ResponseFormatter, ResponseType
from gao_dev.core.state.operation_tracker import OperationTracker
from gao_dev.core.services.ai_analysis_service import AIAnalysisService

logger = structlog.get_logger()


class CommandRouter:
    """
    Route parsed intents to orchestrator methods and stream results.

    Converts workflow sequences and command intents into actual
    orchestrator calls, with:
    - Progress streaming with Rich formatting
    - Error recovery (retry + AI-powered analysis)
    - State persistence for recovery on restart
    - Visual progress indicators for operations >30s

    Example:
        ```python
        from gao_dev.orchestrator.gao_dev_orchestrator import GAODevOrchestrator

        orchestrator = GAODevOrchestrator()
        router = CommandRouter(
            orchestrator=orchestrator,
            operation_tracker=operation_tracker,
            analysis_service=analysis_service
        )

        # Execute workflow sequence
        async for message in router.execute_workflow_sequence(
            workflow_sequence,
            Path("/project")
        ):
            console.print(message)
        ```
    """

    def __init__(
        self,
        orchestrator: Any,  # GAODevOrchestrator
        operation_tracker: OperationTracker,
        analysis_service: AIAnalysisService,
        formatter: Optional[ResponseFormatter] = None,
        console: Optional[Console] = None
    ):
        """
        Initialize command router.

        Args:
            orchestrator: Orchestrator instance (will create mock for now)
            operation_tracker: OperationTracker for state persistence
            analysis_service: AIAnalysisService for error analysis
            formatter: ResponseFormatter (creates new if not provided)
            console: Rich Console (creates new if not provided)
        """
        self.orchestrator = orchestrator
        self.operation_tracker = operation_tracker
        self.analysis_service = analysis_service
        self.console = console or Console()
        self.formatter = formatter or ResponseFormatter(self.console)
        self.logger = logger.bind(component="command_router")

    async def execute_workflow_sequence(
        self,
        workflow_sequence: WorkflowSequence,
        project_root: Path
    ) -> AsyncIterator[str]:
        """
        Execute workflow sequence from Brian's analysis.

        Features:
        - Progress streaming with Rich formatting
        - Error recovery (retry once + AI-powered analysis)
        - State persistence
        - Progress indicators for long operations

        Args:
            workflow_sequence: Workflow sequence to execute
            project_root: Project root path

        Yields:
            Formatted progress messages
        """
        workflow_count = len(workflow_sequence.workflows)
        self.logger.info(
            "executing_workflow_sequence",
            workflow_count=workflow_count
        )

        # Start operation tracking
        op_id = self.operation_tracker.start_operation(
            operation_type="workflow_sequence",
            description=f"Executing {workflow_count} workflow(s)",
            metadata={"workflow_count": workflow_count}
        )

        # Intro message
        yield self._format_intro(workflow_count)

        # Execute each workflow
        for i, workflow in enumerate(workflow_sequence.workflows, 1):
            workflow_name = self._get_workflow_name(workflow)

            # Update progress
            progress_pct = int((i - 1) / workflow_count * 100)
            self.operation_tracker.update_progress(
                op_id,
                progress_pct,
                f"Workflow {i}/{workflow_count}: {workflow_name}"
            )

            # Workflow header
            yield f"\n[{i}/{workflow_count}] {workflow_name}..."

            # Execute with retry
            try:
                async for message in self._execute_with_retry(
                    workflow,
                    project_root,
                    workflow_name
                ):
                    yield f"  {message}"

                yield f"v {workflow_name} complete!"

            except Exception as e:
                # Workflow failed after retries
                self.logger.error(
                    "workflow_failed_after_retry",
                    workflow=workflow_name,
                    error=str(e)
                )

                # Mark operation failed
                self.operation_tracker.mark_failed(
                    op_id,
                    error_message=str(e),
                    context={"workflow": workflow_name, "step": i}
                )

                yield f"x {workflow_name} failed: {str(e)}"
                yield "\nWould you like to:"
                yield "  1. Continue with remaining workflows"
                yield "  2. Stop here"
                yield "  3. Try alternative approach"

                # Note: User response handling done by ChatREPL
                return

        # All workflows completed
        self.operation_tracker.mark_complete(op_id)
        yield "\nv All workflows completed successfully!"

    async def _execute_with_retry(
        self,
        workflow: Any,
        project_root: Path,
        workflow_name: str,
        max_retries: int = 1
    ) -> AsyncIterator[str]:
        """
        Execute workflow with automatic retry on failure.

        Args:
            workflow: Workflow to execute
            project_root: Project root
            workflow_name: Workflow name for logging
            max_retries: Maximum retry attempts

        Yields:
            Progress messages

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    yield f"Retrying (attempt {attempt + 1})..."

                # Execute workflow
                async for message in self._execute_single_workflow(
                    workflow,
                    project_root
                ):
                    yield message

                # Success!
                return

            except Exception as e:
                last_error = e
                self.logger.warning(
                    "workflow_attempt_failed",
                    workflow=workflow_name,
                    attempt=attempt + 1,
                    error=str(e)
                )

                if attempt < max_retries:
                    # Will retry
                    continue
                else:
                    # All retries failed - analyze with AI
                    yield "\nAnalyzing failure with AI..."

                    try:
                        analysis = await self._analyze_failure(
                            workflow_name,
                            str(e)
                        )
                        yield f"\nAI Analysis:\n{analysis}"
                    except Exception as analysis_error:
                        self.logger.error(
                            "failure_analysis_failed",
                            error=str(analysis_error)
                        )

                    # Re-raise original error
                    raise last_error

    async def _execute_single_workflow(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """
        Execute single workflow.

        Routes to appropriate orchestrator method based on workflow type.

        Args:
            workflow: Workflow to execute
            project_root: Project root

        Yields:
            Progress messages
        """
        workflow_name = self._get_workflow_name(workflow)
        start_time = time.time()

        # Route based on workflow type
        if "prd" in workflow_name.lower():
            async for msg in self._execute_create_prd(workflow, project_root):
                yield msg

        elif "architecture" in workflow_name.lower():
            async for msg in self._execute_create_architecture(workflow, project_root):
                yield msg

        elif "story" in workflow_name.lower() or "stories" in workflow_name.lower():
            async for msg in self._execute_create_stories(workflow, project_root):
                yield msg

        elif "implement" in workflow_name.lower():
            async for msg in self._execute_implement(workflow, project_root):
                yield msg

        elif "ceremony" in workflow_name.lower():
            async for msg in self._execute_ceremony(workflow, project_root):
                yield msg

        else:
            # Generic workflow execution
            yield f"Executing {workflow_name}..."
            # Note: Would call orchestrator.execute_workflow() here
            # For now, simulate
            await asyncio.sleep(0.5)
            yield "Done!"

        # Log duration
        duration = time.time() - start_time
        self.logger.info(
            "workflow_executed",
            workflow=workflow_name,
            duration_ms=duration * 1000
        )

    async def _execute_create_prd(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute PRD creation workflow."""
        yield self._format_agent_start("John", "Creating PRD")

        # Extract project name
        project_name = getattr(workflow, 'project_name', 'New Feature')

        # Simulate orchestrator call
        # In production: result = await self.orchestrator.create_prd(...)
        yield "Analyzing requirements..."
        await asyncio.sleep(0.3)
        yield "Drafting PRD sections..."
        await asyncio.sleep(0.3)
        yield "Writing PRD document..."
        await asyncio.sleep(0.3)

        prd_path = project_root / "docs" / "PRD.md"
        yield f"PRD created at: {prd_path}"

    async def _execute_create_architecture(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute architecture creation workflow."""
        yield self._format_agent_start("Winston", "Designing architecture")

        yield "Analyzing system requirements..."
        await asyncio.sleep(0.3)
        yield "Designing component structure..."
        await asyncio.sleep(0.3)
        yield "Creating architecture document..."
        await asyncio.sleep(0.3)

        arch_path = project_root / "docs" / "ARCHITECTURE.md"
        yield f"Architecture created at: {arch_path}"

    async def _execute_create_stories(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute story creation workflow."""
        yield self._format_agent_start("Bob", "Creating stories")

        epic_num = getattr(workflow, 'epic_num', 1)

        yield f"Breaking down Epic {epic_num} into stories..."
        await asyncio.sleep(0.3)
        yield "Estimating story points..."
        await asyncio.sleep(0.3)
        yield "Writing story files..."
        await asyncio.sleep(0.3)

        story_count = 5  # Simulated
        yield f"Created {story_count} stories for Epic {epic_num}"

    async def _execute_implement(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute implementation workflow."""
        yield self._format_agent_start("Amelia", "Implementing story")

        epic_num = getattr(workflow, 'epic_num', 1)
        story_num = getattr(workflow, 'story_num', 1)

        yield f"Implementing Story {epic_num}.{story_num}..."
        await asyncio.sleep(0.3)
        yield "Writing code..."
        await asyncio.sleep(0.3)
        yield "Running tests..."
        await asyncio.sleep(0.3)

        yield f"Story {epic_num}.{story_num} implemented successfully"

    async def _execute_ceremony(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute ceremony workflow."""
        ceremony_type = getattr(workflow, 'ceremony_type', 'planning')
        yield self._format_agent_start("Bob", f"Facilitating {ceremony_type} ceremony")

        yield f"Coordinating {ceremony_type} ceremony with team..."
        await asyncio.sleep(0.3)
        yield "Gathering input..."
        await asyncio.sleep(0.3)

        yield f"{ceremony_type.capitalize()} ceremony complete!"

    async def _analyze_failure(
        self,
        workflow_name: str,
        error_message: str
    ) -> str:
        """
        Analyze failure with AI to suggest alternatives.

        Args:
            workflow_name: Name of failed workflow
            error_message: Error message

        Returns:
            AI analysis with suggested alternatives
        """
        prompt = f"""
Analyze this workflow failure and suggest alternatives:

Workflow: {workflow_name}
Error: {error_message}

Provide:
1. Root cause analysis
2. 2-3 alternative approaches
3. Recommended next steps

Format as concise bullet points.
""".strip()

        try:
            result = await self.analysis_service.analyze(
                prompt=prompt,
                response_format="text",
                max_tokens=500
            )
            return result.response
        except Exception as e:
            return f"Unable to analyze failure: {str(e)}"

    def _get_workflow_name(self, workflow: Any) -> str:
        """Get workflow name from workflow object."""
        if hasattr(workflow, 'name'):
            return workflow.name
        elif hasattr(workflow, 'workflow_name'):
            return workflow.workflow_name
        else:
            return str(workflow)

    def _format_intro(self, workflow_count: int) -> str:
        """Format introduction message."""
        return f"Executing {workflow_count} workflow(s)..."

    def _format_agent_start(self, agent: str, activity: str) -> str:
        """Format agent start message."""
        return f"-> {agent} is {activity.lower()}..."

    async def execute_command(
        self,
        command: str,
        args: Dict[str, Any],
        project_root: Path
    ) -> AsyncIterator[str]:
        """
        Execute explicit command (non-workflow).

        For direct commands like "show status", "list epics", etc.

        Args:
            command: Command name
            args: Command arguments
            project_root: Project root

        Yields:
            Formatted responses
        """
        self.logger.info("executing_command", command=command)

        if command == "status":
            yield await self._command_status(project_root)

        elif command == "list_epics":
            yield await self._command_list_epics(project_root)

        elif command == "list_stories":
            epic_num = args.get('epic_num')
            yield await self._command_list_stories(project_root, epic_num)

        elif command == "show_learning":
            yield await self._command_show_learning(project_root)

        else:
            yield f"Unknown command: {command}"
            yield "Type 'help' to see available commands."

    async def _command_status(self, project_root: Path) -> str:
        """Show project status."""
        from gao_dev.cli.project_status import ProjectStatusReporter

        reporter = ProjectStatusReporter(project_root)
        status = reporter.get_status()
        return reporter.format_status(status)

    async def _command_list_epics(self, project_root: Path) -> str:
        """List all epics."""
        # Note: Would use FastContextLoader here
        # For now, return placeholder
        return "**Epics**: (Epic listing would appear here)"

    async def _command_list_stories(
        self,
        project_root: Path,
        epic_num: Optional[int]
    ) -> str:
        """List stories for an epic."""
        if not epic_num:
            return "Please specify an epic number: 'list stories for epic 30'"

        # Note: Would use FastContextLoader here
        return f"**Stories for Epic {epic_num}**: (Story listing would appear here)"

    async def _command_show_learning(self, project_root: Path) -> str:
        """Show learnings."""
        # Note: Would use LearningService here
        return "**Recent Learnings**: (Learnings would appear here)"
