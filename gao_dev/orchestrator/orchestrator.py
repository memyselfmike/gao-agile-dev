"""Main orchestrator for GAO-Dev autonomous agents."""

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, List
from datetime import datetime
import structlog

from ..tools import gao_dev_server
from .agent_definitions import AGENT_DEFINITIONS
from .workflow_results import StoryResult, EpicResult, StoryStatus

logger = structlog.get_logger()


class GAODevOrchestrator:
    """Main orchestrator for GAO-Dev autonomous development team."""

    def __init__(self, project_root: Path):
        """
        Initialize the GAO-Dev orchestrator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root

        # Configure main orchestrator options
        self.options = ClaudeAgentOptions(
            model="claude-sonnet-4",
            mcp_servers={"gao_dev": gao_dev_server},
            agents=AGENT_DEFINITIONS,
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
            cwd=str(project_root),
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

        Args:
            task: Task description

        Yields:
            Message chunks from the agent
        """
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

                # You can add more message type handling here as needed
                # e.g., tool_use, content_block_start, etc.

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
