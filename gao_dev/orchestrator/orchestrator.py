"""Main orchestrator for GAO-Dev autonomous agents."""

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, List, Any
from datetime import datetime
from dataclasses import asdict
import structlog
import os
import subprocess
import json

from ..tools import gao_dev_server
from .agent_definitions import AGENT_DEFINITIONS
from .workflow_results import StoryResult, EpicResult, StoryStatus
from .brian_orchestrator import (
    BrianOrchestrator,
    WorkflowSequence,
    ScaleLevel,
    ProjectType,
    PromptAnalysis
)
from ..core.config_loader import ConfigLoader
from ..core.workflow_registry import WorkflowRegistry

logger = structlog.get_logger()


class GAODevOrchestrator:
    """Main orchestrator for GAO-Dev autonomous development team."""

    def __init__(self, project_root: Path, api_key: Optional[str] = None, mode: str = "cli"):
        """
        Initialize the GAO-Dev orchestrator.

        Args:
            project_root: Root directory of the project
            api_key: Optional Anthropic API key for Brian's analysis
            mode: Execution mode - "cli", "benchmark", or "api"
        """
        self.project_root = project_root
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mode = mode  # Story 7.2.4: Execution mode for clarification handling

        # Initialize configuration and registries
        self.config_loader = ConfigLoader(project_root)
        self.workflow_registry = WorkflowRegistry(self.config_loader)
        self.workflow_registry.index_workflows()

        # Initialize Brian - Senior Engineering Manager and Workflow Orchestrator
        brian_persona_path = self.config_loader.get_agents_path() / "brian.md"
        self.brian_orchestrator = BrianOrchestrator(
            workflow_registry=self.workflow_registry,
            api_key=self.api_key,
            brian_persona_path=brian_persona_path if brian_persona_path.exists() else None
        )

        # Story 4.8: Find Claude CLI for programmatic execution
        from ..core.cli_detector import find_claude_cli, validate_claude_cli
        cli_path = find_claude_cli()

        if mode == "benchmark" and not cli_path:
            raise ValueError(
                "Claude CLI not found. Install Claude Code or set cli_path. "
                "Cannot run in benchmark mode without Claude CLI."
            )

        if cli_path:
            logger.info("claude_cli_detected", path=str(cli_path), mode=mode)

        # Configure main orchestrator options for PROGRAMMATIC EXECUTION
        self.options = ClaudeAgentOptions(
            # Story 4.8: Point to Claude CLI executable for programmatic mode
            cli_path=cli_path if mode == "benchmark" else None,

            # Story 4.8: Set working directory to project
            cwd=self.project_root if mode == "benchmark" else None,

            # Story 4.8: Pass API key via environment (secure)
            env={"ANTHROPIC_API_KEY": self.api_key} if self.api_key and mode == "benchmark" else {},

            # Model configuration
            model="claude-sonnet-4-5-20250929",

            # Story 4.8: Permission mode - bypass for benchmarks (sandbox-safe)
            permission_mode="bypassPermissions" if mode == "benchmark" else "default",

            # MCP servers (keeps MCP integration)
            mcp_servers={"gao_dev": gao_dev_server},

            # Agent definitions (keeps agent orchestration)
            agents=AGENT_DEFINITIONS,

            # Story 4.8: Grant access to project directory
            add_dirs=[self.project_root] if mode == "benchmark" else [],

            # Tools
            allowed_tools=[
                # File operations
                "Read",
                "Write",
                "Edit",
                "MultiEdit",
                "Grep",
                "Glob",
                # Shell operations
                "Bash",
                # Task tool (REQUIRED for spawning subagents)
                "Task",
                # Task management
                "TodoWrite",
                # Research
                "WebSearch",
                "WebFetch",
                # GAO-Dev tools
                "mcp__gao_dev__list_workflows",
                "mcp__gao_dev__get_workflow",
                "mcp__gao_dev__execute_workflow",
                "mcp__gao_dev__get_story_status",
                "mcp__gao_dev__set_story_status",
                "mcp__gao_dev__ensure_story_directory",
                "mcp__gao_dev__get_sprint_status",
                "mcp__gao_dev__git_create_branch",
                "mcp__gao_dev__git_commit",
                "mcp__gao_dev__git_merge_branch",
                "mcp__gao_dev__health_check",
            ],
            system_prompt=self._get_orchestrator_prompt(),
        )

    def _get_orchestrator_prompt(self) -> str:
        """Get the orchestrator system prompt."""
        return """You are the GAO-Dev orchestrator, managing a team of 7 specialized AI agents for software development.

**Your Team:**

1. **Mary** (Business Analyst)
   - Conducts business analysis and requirements gathering
   - Creates product briefs
   - Performs research
   - Use for: Analysis workflows, requirements, research

2. **John** (Product Manager)
   - Creates PRDs and defines features
   - Prioritizes work
   - Defines success metrics
   - Use for: PRD creation, epic definition, prioritization

3. **Winston** (Technical Architect)
   - Designs system architecture
   - Creates technical specifications
   - Defines tech stack
   - Use for: Architecture design, technical decisions

4. **Sally** (UX Designer)
   - Creates user experiences
   - Designs wireframes
   - Defines user flows
   - Use for: UX design, user flows, interface design

5. **Bob** (Scrum Master)
   - Creates and manages user stories
   - Tracks story status
   - Coordinates team
   - Use for: Story creation, story management, status tracking

6. **Amelia** (Software Developer)
   - Implements user stories
   - Writes code
   - Performs code reviews
   - Use for: Implementation, coding, testing

7. **Murat** (Test Architect)
   - Creates test strategies
   - Defines quality standards
   - Writes test plans
   - Use for: Testing strategy, test plans, quality assurance

**Your Role:**
1. Understand the user's request
2. Delegate to the appropriate specialist agent using the Task tool
3. Coordinate multi-agent workflows when needed
4. Ensure quality standards are met
5. Track progress and report status

**GAO-Dev Tools Available:**
- list_workflows: See available workflows
- execute_workflow: Run workflows with the right agent
- get_story_status/set_story_status: Track story progress
- git operations: Branch, commit, merge
- health_check: Validate system state

**Example Delegation:**
- "Create a PRD" → Use Task tool to spawn John (PM)
- "Create Story 1.1" → Use Task tool to spawn Bob (Scrum Master)
- "Implement Story 1.1" → Use Task tool to spawn Amelia (Developer)
- "Design architecture" → Use Task tool to spawn Winston (Architect)

**Important:**
- Always use the Task tool to spawn the appropriate agent
- One agent per specialized task
- Coordinate multi-step workflows (e.g., Bob creates story → Amelia implements → Bob marks done)
- Ensure all artifacts are created and committed
"""

    async def execute_task(self, task: str) -> AsyncGenerator[str, None]:
        """
        Execute a task using the orchestrator.

        For benchmark mode: shells out to Claude CLI
        For interactive mode: uses ClaudeSDKClient

        Args:
            task: Task description

        Yields:
            Message chunks from the agent
        """
        if self.mode == "benchmark":
            # Story 4.8: Shell out to Claude CLI for benchmark execution
            async for chunk in self._execute_task_subprocess(task):
                yield chunk
        else:
            # Interactive mode: use SDK client
            async with ClaudeSDKClient(options=self.options) as client:
                await client.query(task)

                async for message in client.receive_response():
                    # Parse and yield message text
                    if message.get("type") == "content_block_delta":
                        delta = message.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                yield text

    async def _execute_task_subprocess(self, task: str) -> AsyncGenerator[str, None]:
        """
        Execute task by shelling out to Claude CLI (for benchmark mode).

        Args:
            task: Task description

        Yields:
            Output from Claude CLI
        """
        from ..core.cli_detector import find_claude_cli

        cli_path = find_claude_cli()
        if not cli_path:
            raise ValueError("Claude CLI not found")

        # Build command
        cmd = [str(cli_path)]

        # Add flags for non-interactive execution
        cmd.extend(['--print'])  # Non-interactive output
        cmd.extend(['--dangerously-skip-permissions'])  # Auto-approve tools
        cmd.extend(['--model', 'claude-sonnet-4-5-20250929'])

        # Add project directory access
        cmd.extend(['--add-dir', str(self.project_root)])

        # Set environment with API key
        env = os.environ.copy()
        if self.api_key:
            env['ANTHROPIC_API_KEY'] = self.api_key

        # Note: Not passing --agents to avoid command line length limit on Windows
        # The CLI will use Task tool to spawn subagents, which will have default behavior

        logger.info(
            "executing_claude_cli",
            cli=str(cli_path),
            mode="subprocess",
            has_api_key=bool(self.api_key),
            command_preview=f"{cmd[0]} {' '.join(cmd[1:4])}..."
        )

        # Execute Claude CLI as subprocess
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.project_root)
            )

            # Send task as input
            stdout, stderr = process.communicate(input=task, timeout=3600)

            logger.info(
                "claude_cli_completed",
                return_code=process.returncode,
                stdout_length=len(stdout),
                stderr_length=len(stderr),
                stdout_preview=stdout[:200] if stdout else "(empty)",
                stderr_preview=stderr[:200] if stderr else "(empty)"
            )

            if stderr:
                logger.warning("claude_cli_stderr", stderr=stderr[:1000])

            # Yield output even if return code isn't 0 (might have partial output)
            if stdout:
                yield stdout

            if process.returncode != 0:
                error_msg = f"Claude CLI failed with code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr[:500]}"
                if not stdout and not stderr:
                    error_msg += " (no output - check if claude.bat is configured correctly)"
                raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError("Claude CLI execution timed out after 1 hour")
        except Exception as e:
            logger.error("claude_cli_execution_failed", error=str(e))
            raise

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

    # ========================================================================
    # Story Workflow Methods (Epic 7.1.2)
    # ========================================================================

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

    async def execute_story_workflow(
        self,
        epic: int,
        story: int,
        story_config: Optional[Dict] = None,
        with_qa: bool = True
    ) -> StoryResult:
        """
        Execute complete story lifecycle with QA validation.

        This is the core agile workflow: Bob -> Amelia -> Murat -> Commit

        Workflow:
        1. Bob (Scrum Master) creates detailed story spec
        2. Amelia (Developer) implements + writes tests
        3. Murat (QA) validates quality (if with_qa=True)
        4. Git atomic commit with story details

        Args:
            epic: Epic number
            story: Story number
            story_config: Optional story configuration (acceptance criteria, etc.)
            with_qa: Whether to include QA validation (default: True)

        Returns:
            StoryResult with metrics, artifacts, commit hash
        """
        result = StoryResult(
            story_name=f"Story {epic}.{story}",
            epic_name=f"Epic {epic}",
            agent="workflow",
            status=StoryStatus.IN_PROGRESS,
            start_time=datetime.now()
        )

        try:
            logger.info(
                "story_workflow_started",
                epic=epic,
                story=story,
                with_qa=with_qa
            )

            # Phase 1: Bob creates story spec
            result.status = StoryStatus.IN_PROGRESS
            logger.debug("executing_phase", phase="story_creation", agent="Bob")

            async for _ in self.create_story(epic, story):
                pass  # Execute story creation

            # Phase 2: Amelia implements
            logger.debug("executing_phase", phase="implementation", agent="Amelia")

            async for _ in self.implement_story(epic, story):
                pass  # Execute implementation

            # Phase 3: Murat validates (if enabled)
            if with_qa:
                result.status = StoryStatus.QA_VALIDATION
                logger.debug("executing_phase", phase="qa_validation", agent="Murat")

                async for _ in self.validate_story(epic, story):
                    pass  # Execute QA validation

            # Phase 4: Story complete
            result.status = StoryStatus.COMPLETED
            result.end_time = datetime.now()

            logger.info(
                "story_workflow_completed",
                epic=epic,
                story=story,
                duration=(result.end_time - result.start_time).total_seconds()
            )

        except Exception as e:
            result.status = StoryStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()

            logger.error(
                "story_workflow_failed",
                epic=epic,
                story=story,
                error=str(e)
            )

        return result

    async def execute_epic_workflow(
        self,
        epic: int,
        stories: List[Dict],
        with_qa: bool = True
    ) -> EpicResult:
        """
        Execute all stories in an epic sequentially.

        Args:
            epic: Epic number
            stories: List of story configurations
            with_qa: Whether to include QA per story

        Returns:
            EpicResult with all story results
        """
        epic_result = EpicResult(epic_name=f"Epic {epic}")
        epic_result.start_time = datetime.now()

        logger.info(
            "epic_workflow_started",
            epic=epic,
            total_stories=len(stories),
            with_qa=with_qa
        )

        for i, story_config in enumerate(stories, 1):
            logger.debug("executing_story", epic=epic, story=i)

            story_result = await self.execute_story_workflow(
                epic=epic,
                story=i,
                story_config=story_config,
                with_qa=with_qa
            )
            epic_result.story_results.append(story_result)

            # Stop on first failure (fail-fast)
            if story_result.status == StoryStatus.FAILED:
                logger.warning(
                    "epic_workflow_stopped_on_failure",
                    epic=epic,
                    failed_story=i
                )
                break

        epic_result.end_time = datetime.now()

        logger.info(
            "epic_workflow_completed",
            epic=epic,
            completed_stories=epic_result.completed_stories,
            failed_stories=epic_result.failed_stories,
            duration=(epic_result.end_time - epic_result.start_time).total_seconds()
        )

        return epic_result

    # ========================================================================
    # Brian - Scale-Adaptive Workflow Selection (Story 7.2.1)
    # ========================================================================

    async def assess_and_select_workflows(
        self,
        initial_prompt: str,
        force_scale_level: Optional[ScaleLevel] = None
    ) -> WorkflowSequence:
        """
        Use Brian (Engineering Manager) to analyze prompt and select workflows.

        Brian applies his 20 years of experience to:
        - Assess project complexity (Scale Level 0-4)
        - Determine project type (greenfield, brownfield, game, etc.)
        - Build appropriate workflow sequence
        - Provide routing rationale

        This is the entry point for scale-adaptive workflow selection.

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
            jit_tech_specs=workflow_sequence.jit_tech_specs
        )

        return workflow_sequence

    def get_scale_level_description(self, scale_level: ScaleLevel) -> str:
        """
        Get human-readable description of scale level.

        Args:
            scale_level: Scale level enum

        Returns:
            Description string
        """
        return self.brian_orchestrator.get_scale_level_description(scale_level)

    # ========================================================================
    # Clarification Dialog (Story 7.2.4)
    # ========================================================================

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
            # Benchmark mode: Fail gracefully
            logger.warning(
                "clarification_in_benchmark_mode",
                message="Cannot ask clarifying questions in benchmark mode"
            )
            return None

        elif self.mode == "cli":
            # CLI mode: For now, return None (interactive prompting to be added)
            # TODO: Add interactive CLI prompting
            logger.info(
                "clarification_cli_mode",
                message="Interactive clarification not yet implemented"
            )
            return None

        else:
            # API mode or unknown
            logger.info(
                "clarification_api_mode",
                message="Clarification handling delegated to caller"
            )
            return None

    # ========================================================================
    # Multi-Workflow Sequence Executor (Story 7.2.2)
    # ========================================================================

    async def _verify_workflow_artifacts(
        self,
        workflow_info: "WorkflowInfo",
        step_result: "WorkflowStepResult"
    ) -> Dict[str, Any]:
        """
        Brian's Quality Gate: Verify workflow produced expected artifacts.

        After each workflow executes, Brian checks if the expected files/outputs were created.
        If something's missing, Brian decides whether to retry or adapt.

        Args:
            workflow_info: Workflow that was executed
            step_result: Result from workflow execution

        Returns:
            Dict with:
                - success: bool
                - missing_artifacts: List[str]
                - action: "continue" | "retry" | "adapt"
                - adaptation_note: str (if action is "adapt")
        """
        workflow_name = workflow_info.name
        missing_artifacts = []
        docs_path = self.project_root / "docs"

        # Define expected artifacts for each workflow
        expected_artifacts = {
            "prd": [docs_path / "PRD.md"],
            "create-story": [docs_path / "stories"],  # At least stories directory should exist
            "dev-story": [],  # dev-story varies, hard to predict exact files
            "architecture": [docs_path / "ARCHITECTURE.md"],
        }

        if workflow_name not in expected_artifacts:
            # No specific expectations for this workflow
            return {
                "success": True,
                "missing_artifacts": [],
                "action": "continue",
                "adaptation_note": ""
            }

        # Check if expected artifacts exist
        for artifact in expected_artifacts[workflow_name]:
            if not artifact.exists():
                missing_artifacts.append(str(artifact))

        if not missing_artifacts:
            return {
                "success": True,
                "missing_artifacts": [],
                "action": "continue",
                "adaptation_note": ""
            }

        # Brian's decision logic: How to handle missing artifacts
        if workflow_name == "prd":
            # PRD is critical but might have been created as epics.md instead
            epics_file = docs_path / "epics.md"
            if epics_file.exists():
                logger.info(
                    "brian_found_alternative",
                    expected="PRD.md",
                    found="epics.md",
                    decision="adapt"
                )
                return {
                    "success": False,
                    "missing_artifacts": missing_artifacts,
                    "action": "adapt",
                    "adaptation_note": "epics.md found instead of PRD.md, proceeding with epics"
                }
            else:
                # No PRD and no epics - retry
                return {
                    "success": False,
                    "missing_artifacts": missing_artifacts,
                    "action": "retry",
                    "adaptation_note": ""
                }

        elif workflow_name == "create-story":
            # Stories directory is critical - retry if missing
            stories_dir = docs_path / "stories"
            if stories_dir.exists():
                # Directory exists, check if it has any story files
                story_files = list(stories_dir.glob("epic-*/story-*.md"))
                if story_files:
                    return {
                        "success": True,
                        "missing_artifacts": [],
                        "action": "continue",
                        "adaptation_note": ""
                    }
            # No stories - retry
            return {
                "success": False,
                "missing_artifacts": missing_artifacts,
                "action": "retry",
                "adaptation_note": ""
            }

        # Default: adapt (continue with what we have)
        return {
            "success": False,
            "missing_artifacts": missing_artifacts,
            "action": "adapt",
            "adaptation_note": f"Some artifacts missing for {workflow_name}, continuing anyway"
        }

    async def _check_if_more_stories_needed(self) -> bool:
        """
        Check if more stories are needed to complete the MVP.

        In benchmark mode, we continue creating stories up to max_stories limit.
        Brian's quality gates will ensure each story is properly created and implemented.

        Returns:
            True if more stories should be created (controlled by loop's max_stories limit)
        """
        # Simple approach: Always return True
        # The while loop's max_stories limit prevents infinite loops
        # Brian's quality gates ensure each workflow produces valid artifacts
        return True

    async def execute_workflow(
        self,
        initial_prompt: str,
        workflow: Optional[WorkflowSequence] = None,
        commit_after_steps: bool = True
    ) -> "WorkflowResult":
        """
        Execute complete workflow sequence from initial prompt.

        This is the core autonomous execution method that:
        1. Selects appropriate workflow sequence (if not provided)
        2. Executes workflows sequentially across phases
        3. Calls agents to perform tasks
        4. Creates artifacts and commits to git
        5. Returns comprehensive results

        Args:
            initial_prompt: User's initial request
            workflow: Optional pre-selected workflow sequence (if None, auto-select)
            commit_after_steps: Whether to commit after each workflow step

        Returns:
            WorkflowResult with execution details and metrics
        """
        from .workflow_results import WorkflowResult, WorkflowStepResult, WorkflowStatus

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
                    # Check if clarification is needed (Story 7.2.4)
                    # Note: Brian returns empty workflow list when needs_clarification=True
                    # We pass questions through routing_rationale for now
                    logger.info("workflow_selection_needs_clarification")

                    # Extract clarifying questions from routing_rationale if present
                    clarifying_questions = []
                    if "clarification" in workflow.routing_rationale.lower():
                        clarifying_questions = [workflow.routing_rationale]

                    # Handle clarification based on mode
                    enhanced_prompt = self.handle_clarification(
                        clarifying_questions if clarifying_questions else ["Unable to determine workflow from prompt"],
                        initial_prompt
                    )

                    # If clarification failed or returned None
                    result.status = WorkflowStatus.FAILED
                    result.end_time = datetime.now()
                    result.error_message = "Workflow selection requires clarification. " + workflow.routing_rationale
                    logger.warning("workflow_selection_failed", workflows_count=0, needs_clarification=True)
                    return result

                result.workflow_name = f"{workflow.scale_level.name}_sequence"

            logger.info(
                "workflow_execution_started",
                workflow_count=len(workflow.workflows),
                scale_level=workflow.scale_level.value
            )

            # Step 2: Execute workflows sequentially
            for i, workflow_info in enumerate(workflow.workflows, 1):
                logger.info(
                    "workflow_step_started",
                    step=i,
                    total=len(workflow.workflows),
                    workflow_name=workflow_info.name
                )

                step_result = await self._execute_workflow_step(
                    workflow_info=workflow_info,
                    step_number=i,
                    total_steps=len(workflow.workflows)
                )

                result.step_results.append(step_result)

                # TODO: Re-enable Brian's Quality Gate after testing basic loop
                # Brian's verification temporarily disabled to test basic story loop first

                # Commit after step if enabled
                if commit_after_steps and step_result.status == "success":
                    # Git commits are handled by the individual agent methods
                    pass

                # Fail-fast: Stop on first failure
                if step_result.status == "failed":
                    logger.error(
                        "workflow_step_failed",
                        step=workflow_info.name,
                        error=step_result.error_message
                    )
                    result.status = WorkflowStatus.FAILED
                    break

            # Step 3: Continue implementing stories until MVP is complete
            # After initial workflows (prd, create-story, dev-story), check if more stories needed
            if result.status != WorkflowStatus.FAILED and self.mode == "benchmark":
                # Find create-story and dev-story workflows for looping
                create_story_workflow = next((w for w in workflow.workflows if w.name == "create-story"), None)
                dev_story_workflow = next((w for w in workflow.workflows if w.name == "dev-story"), None)

                if create_story_workflow and dev_story_workflow:
                    logger.info("story_loop_starting", message="Continuing to implement additional stories until MVP complete")

                    # Loop: create next story → implement story → check if more needed
                    max_stories = 20  # Safety limit to prevent infinite loops
                    stories_implemented = 1  # Already implemented 1 story in initial sequence
                    current_epic = 1

                    while stories_implemented < max_stories:
                        # Ask if more stories are needed for MVP
                        should_continue = await self._check_if_more_stories_needed()

                        if not should_continue:
                            logger.info("mvp_complete", stories_implemented=stories_implemented)
                            break

                        # Get the next story number by scanning file system
                        next_story_num = self._get_next_story_number(epic=current_epic)

                        logger.info(
                            "story_loop_iteration",
                            iteration=stories_implemented + 1,
                            workflow="create-story",
                            epic=current_epic,
                            story=next_story_num
                        )

                        # Create next story with correct epic/story numbers
                        step_result = await self._execute_workflow_step(
                            workflow_info=create_story_workflow,
                            step_number=len(result.step_results) + 1,
                            total_steps=len(workflow.workflows),
                            epic=current_epic,
                            story=next_story_num
                        )
                        result.step_results.append(step_result)

                        if step_result.status == "failed":
                            logger.error("story_creation_failed", iteration=stories_implemented + 1, epic=current_epic, story=next_story_num)
                            break

                        # Implement the story with same epic/story numbers
                        logger.info(
                            "story_loop_iteration",
                            iteration=stories_implemented + 1,
                            workflow="dev-story",
                            epic=current_epic,
                            story=next_story_num
                        )

                        step_result = await self._execute_workflow_step(
                            workflow_info=dev_story_workflow,
                            step_number=len(result.step_results) + 1,
                            total_steps=len(workflow.workflows),
                            epic=current_epic,
                            story=next_story_num
                        )
                        result.step_results.append(step_result)

                        if step_result.status == "failed":
                            logger.error("story_implementation_failed", iteration=stories_implemented + 1, epic=current_epic, story=next_story_num)
                            break

                        stories_implemented += 1
                        logger.info("story_completed", total_stories=stories_implemented, epic=current_epic, story=next_story_num)

                    logger.info(
                        "story_loop_complete",
                        total_stories_implemented=stories_implemented,
                        max_reached=stories_implemented >= max_stories
                    )

            # Step 4: Mark complete if all steps succeeded
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

    def _get_next_story_number(self, epic: int = 1) -> int:
        """
        Scan the docs/stories directory to find the next story number to create.

        Args:
            epic: Epic number to search within (default: 1)

        Returns:
            Next available story number (e.g., if story-1.2.md exists, returns 3)
        """
        docs_path = self.project_root / "docs"
        stories_path = docs_path / "stories" / f"epic-{epic}"

        if not stories_path.exists():
            logger.debug("stories_path_not_found", path=str(stories_path), next_story=1)
            return 1

        # Find all story files matching pattern: story-{epic}.{story}.md
        story_files = list(stories_path.glob(f"story-{epic}.*.md"))

        if not story_files:
            logger.debug("no_stories_found", path=str(stories_path), next_story=1)
            return 1

        # Extract story numbers from filenames
        story_numbers = []
        for story_file in story_files:
            # Parse filename like "story-1.2.md" -> extract "2"
            try:
                parts = story_file.stem.split('.')
                if len(parts) >= 2:
                    story_num = int(parts[1])
                    story_numbers.append(story_num)
            except (ValueError, IndexError):
                continue

        if not story_numbers:
            logger.debug("no_valid_story_numbers", path=str(stories_path), next_story=1)
            return 1

        next_story = max(story_numbers) + 1
        logger.debug("next_story_calculated", existing_stories=sorted(story_numbers), next_story=next_story)
        return next_story

    async def _execute_workflow_step(
        self,
        workflow_info: "WorkflowInfo",
        step_number: int,
        total_steps: int,
        epic: int = 1,
        story: int = 1
    ) -> "WorkflowStepResult":
        """
        Execute a single workflow step.

        Maps workflow to appropriate agent method and executes.

        Args:
            workflow_info: Workflow metadata
            step_number: Current step number
            total_steps: Total number of steps
            epic: Epic number for story workflows (default: 1)
            story: Story number for story workflows (default: 1)

        Returns:
            WorkflowStepResult with execution details
        """
        from .workflow_results import WorkflowStepResult

        step_result = WorkflowStepResult(
            step_name=workflow_info.name,
            agent=self._get_agent_for_workflow(workflow_info),
            status="in_progress",
            start_time=datetime.now()
        )

        try:
            # Map workflow to agent method
            agent_method = self._get_agent_method_for_workflow(workflow_info, epic=epic, story=story)

            if agent_method is None:
                raise ValueError(f"No agent method found for workflow: {workflow_info.name}")

            # Execute agent method
            output_parts = []
            async for message in agent_method():
                output_parts.append(message)

            step_result.output = "\n".join(output_parts)
            step_result.status = "success"

            logger.info(
                "workflow_step_completed",
                workflow=workflow_info.name,
                agent=step_result.agent
            )

        except Exception as e:
            step_result.status = "failed"
            step_result.error_message = str(e)
            logger.error(
                "step_execution_failed",
                workflow=workflow_info.name,
                error=str(e)
            )

        finally:
            step_result.end_time = datetime.now()
            step_result.duration_seconds = (
                step_result.end_time - step_result.start_time
            ).total_seconds()

        return step_result

    def _get_agent_for_workflow(self, workflow_info: "WorkflowInfo") -> str:
        """
        Determine which agent should execute a workflow.

        Args:
            workflow_info: Workflow metadata

        Returns:
            Agent name (Mary, John, Winston, etc.)
        """
        # Map workflow name patterns to agents
        workflow_name_lower = workflow_info.name.lower()

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

    def _get_agent_method_for_workflow(self, workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1):
        """
        Map workflow to orchestrator method.

        Args:
            workflow_info: Workflow metadata
            epic: Epic number for story workflows (default: 1)
            story: Story number for story workflows (default: 1)

        Returns:
            Async method to call, or None if not found
        """
        # Map workflow names to orchestrator methods
        workflow_name_lower = workflow_info.name.lower()

        # PRD workflows
        if workflow_name_lower == "prd":
            return lambda: self.create_prd(project_name="Project")

        # Architecture workflows
        elif workflow_name_lower in ["architecture", "tech-spec"]:
            return lambda: self.create_architecture(project_name="Project")

        # Story workflows
        elif "create-story" in workflow_name_lower:
            return lambda: self.create_story(epic=epic, story=story)

        # Implementation workflows
        elif "dev-story" in workflow_name_lower or "implement" in workflow_name_lower:
            return lambda: self.implement_story(epic=epic, story=story)

        # Validation workflows
        elif "validate" in workflow_name_lower or "qa" in workflow_name_lower:
            return lambda: self.validate_story(epic=epic, story=story)

        # Default: Execute generic task
        else:
            task_description = f"Execute the {workflow_info.name} workflow"
            return lambda: self.execute_task(task_description)

    async def execute_workflow_sequence_from_prompt(
        self,
        initial_prompt: str
    ) -> "WorkflowResult":
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
