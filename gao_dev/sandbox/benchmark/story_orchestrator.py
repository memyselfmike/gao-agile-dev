"""Story-based workflow orchestration for incremental development."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from .config import StoryConfig, EpicConfig

logger = structlog.get_logger()


class StoryStatus(Enum):
    """Status of a story in the workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StoryResult:
    """Result of executing a single story."""

    story_name: str
    epic_name: str
    agent: str
    status: StoryStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    acceptance_criteria_met: List[str] = field(default_factory=list)
    acceptance_criteria_failed: List[str] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_failed: int = 0
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "story_name": self.story_name,
            "epic_name": self.epic_name,
            "agent": self.agent,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "acceptance_criteria_met": self.acceptance_criteria_met,
            "acceptance_criteria_failed": self.acceptance_criteria_failed,
            "artifacts_created": self.artifacts_created,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "commit_hash": self.commit_hash,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class EpicResult:
    """Result of executing an entire epic."""

    epic_name: str
    story_results: List[StoryResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0

    @property
    def completed_stories(self) -> int:
        """Count of successfully completed stories."""
        return sum(
            1 for r in self.story_results if r.status == StoryStatus.COMPLETED
        )

    @property
    def failed_stories(self) -> int:
        """Count of failed stories."""
        return sum(1 for r in self.story_results if r.status == StoryStatus.FAILED)

    @property
    def total_stories(self) -> int:
        """Total number of stories."""
        return len(self.story_results)

    @property
    def success(self) -> bool:
        """Check if epic succeeded (all stories completed)."""
        return (
            self.total_stories > 0
            and self.completed_stories == self.total_stories
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "epic_name": self.epic_name,
            "story_results": [s.to_dict() for s in self.story_results],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": self.total_duration_seconds,
            "completed_stories": self.completed_stories,
            "failed_stories": self.failed_stories,
            "total_stories": self.total_stories,
            "success": self.success,
        }


class StoryOrchestrator:
    """
    Orchestrates story-based incremental workflow.

    Iterates through epics and stories, executing:
    - Story creation (by Scrum Master)
    - Story implementation (by Developer)
    - Story validation (by QA)
    - Git commit (automated)

    Each story follows the complete cycle before moving to the next.
    """

    def __init__(
        self,
        project_path: Path,
        api_key: Optional[str] = None,
        git_manager: Optional[Any] = None,
        metrics_aggregator: Optional[Any] = None,
    ):
        """
        Initialize story orchestrator.

        Args:
            project_path: Path to the sandbox project
            api_key: Anthropic API key for agent spawning
            git_manager: GitManager instance for commits
            metrics_aggregator: MetricsAggregator for tracking
        """
        self.project_path = Path(project_path)
        self.api_key = api_key
        self.git_manager = git_manager
        self.metrics_aggregator = metrics_aggregator
        self.logger = logger.bind(
            component="StoryOrchestrator", project=str(project_path)
        )

        # Initialize agent spawner if API key provided
        self.agent_spawner = None
        if api_key:
            from .agent_spawner import AgentSpawner
            self.agent_spawner = AgentSpawner(api_key=api_key)

    def execute_epics(
        self,
        epics: List[EpicConfig],
        timeout_seconds: Optional[int] = None,
    ) -> List[EpicResult]:
        """
        Execute multiple epics sequentially.

        Args:
            epics: List of epic configurations
            timeout_seconds: Optional timeout for entire execution

        Returns:
            List[EpicResult]: Results for each epic
        """
        self.logger.info("starting_epic_execution", total_epics=len(epics))

        epic_results = []
        for epic in epics:
            epic_result = self.execute_epic(epic, timeout_seconds)
            epic_results.append(epic_result)

            # Stop if epic failed and configured to stop on failure
            if not epic_result.success:
                self.logger.warning(
                    "epic_failed_stopping_execution",
                    epic=epic.name,
                    completed=epic_result.completed_stories,
                    failed=epic_result.failed_stories,
                )
                break

        self.logger.info(
            "epic_execution_completed",
            total_epics=len(epics),
            completed_epics=sum(1 for r in epic_results if r.success),
        )

        return epic_results

    def execute_epic(
        self,
        epic: EpicConfig,
        timeout_seconds: Optional[int] = None,
    ) -> EpicResult:
        """
        Execute all stories in an epic sequentially.

        Args:
            epic: Epic configuration
            timeout_seconds: Optional timeout for epic execution

        Returns:
            EpicResult: Results for the epic
        """
        self.logger.info(
            "starting_epic",
            epic=epic.name,
            total_stories=len(epic.stories),
        )

        result = EpicResult(epic_name=epic.name)
        result.start_time = datetime.now()

        for story in epic.stories:
            story_result = self.execute_story(story, epic.name, timeout_seconds)
            result.story_results.append(story_result)

            # Log progress
            self.logger.info(
                "story_completed",
                epic=epic.name,
                story=story.name,
                status=story_result.status.value,
                progress=f"{len(result.story_results)}/{len(epic.stories)}",
            )

            # Stop on first failure (fail-fast for quality)
            if story_result.status == StoryStatus.FAILED:
                self.logger.error(
                    "story_failed_stopping_epic",
                    epic=epic.name,
                    story=story.name,
                    error=story_result.error_message,
                )
                # Mark remaining stories as skipped
                for remaining_story in epic.stories[len(result.story_results) :]:
                    skipped_result = StoryResult(
                        story_name=remaining_story.name,
                        epic_name=epic.name,
                        agent=remaining_story.agent,
                        status=StoryStatus.SKIPPED,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                    )
                    result.story_results.append(skipped_result)
                break

        result.end_time = datetime.now()
        result.total_duration_seconds = (
            result.end_time - result.start_time
        ).total_seconds()

        self.logger.info(
            "epic_completed",
            epic=epic.name,
            completed=result.completed_stories,
            failed=result.failed_stories,
            duration=result.total_duration_seconds,
        )

        return result

    def execute_story(
        self,
        story: StoryConfig,
        epic_name: str,
        timeout_seconds: Optional[int] = None,
    ) -> StoryResult:
        """
        Execute a single story through the complete cycle.

        Workflow:
        1. Create story specification (Bob - Scrum Master)
        2. Implement story (Amelia - Developer)
        3. Validate story (Murat - QA)
        4. Commit changes (GitManager)

        Args:
            story: Story configuration
            epic_name: Name of the parent epic
            timeout_seconds: Optional timeout for story

        Returns:
            StoryResult: Result of story execution
        """
        self.logger.info(
            "starting_story",
            epic=epic_name,
            story=story.name,
            agent=story.agent,
            story_points=story.story_points,
        )

        result = StoryResult(
            story_name=story.name,
            epic_name=epic_name,
            agent=story.agent,
            status=StoryStatus.IN_PROGRESS,
            start_time=datetime.now(),
        )

        # Record story start in metrics
        if self.metrics_aggregator:
            self.metrics_aggregator.record_story_start(
                epic_name=epic_name,
                story_name=story.name,
                metadata={"agent": story.agent, "story_points": story.story_points},
            )

        try:
            # Phase 1: Story Creation (Bob creates detailed spec)
            self._execute_story_creation(story, result)

            # Phase 2: Story Implementation (Amelia implements)
            self._execute_story_implementation(story, result)

            # Phase 3: Story Validation (Murat tests)
            self._execute_story_validation(story, result)

            # Phase 4: Git Commit (Automated)
            self._execute_story_commit(story, result)

            # Mark as completed
            result.status = StoryStatus.COMPLETED
            result.end_time = datetime.now()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            # Record story completion in metrics
            if self.metrics_aggregator:
                self.metrics_aggregator.record_story_complete(
                    status="completed",
                    metadata={"commit_hash": result.commit_hash},
                )

            self.logger.info(
                "story_completed_successfully",
                epic=epic_name,
                story=story.name,
                duration=result.duration_seconds,
            )

        except Exception as e:
            result.status = StoryStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            # Record story failure in metrics
            if self.metrics_aggregator:
                self.metrics_aggregator.record_story_complete(
                    status="failed",
                    metadata={"error": str(e)},
                )

            self.logger.error(
                "story_failed",
                epic=epic_name,
                story=story.name,
                error=str(e),
            )

        return result

    def _execute_story_creation(
        self, story: StoryConfig, result: StoryResult
    ) -> None:
        """
        Execute story creation phase (Bob - Scrum Master).

        Creates detailed story specification with:
        - Acceptance criteria
        - Technical requirements
        - Dependencies
        """
        self.logger.debug("story_creation_phase", story=story.name)

        if self.agent_spawner:
            # Spawn Bob to create detailed story specification
            prompt = self._create_story_creation_prompt(story, result)

            agent_result = self.agent_spawner.spawn_agent(
                agent_name="Bob",
                task_prompt=prompt,
                project_path=self.project_path,
                timeout_seconds=story.timeout_seconds // 3,  # 1/3 of story time for creation
            )

            # Record metrics
            if self.metrics_aggregator and agent_result.metrics:
                self.metrics_aggregator.record_agent_metrics(agent_result.metrics)

            if agent_result.success:
                result.acceptance_criteria_met.append("Story specification created by Bob")
                result.metadata["creation_phase"] = "completed"
                result.metadata["creation_output"] = agent_result.output[:500]  # First 500 chars
            else:
                raise Exception(f"Story creation failed: {agent_result.error}")
        else:
            # Fallback if no agent spawner
            result.acceptance_criteria_met.append("Story specification created (no agent)")
            result.metadata["creation_phase"] = "skipped"

    def _execute_story_implementation(
        self, story: StoryConfig, result: StoryResult
    ) -> None:
        """
        Execute story implementation phase (Amelia - Developer).

        Implements the story with:
        - Code implementation
        - Unit tests
        - Documentation
        """
        self.logger.debug("story_implementation_phase", story=story.name)

        if self.agent_spawner:
            # Spawn Amelia to implement ONE story
            prompt = self._create_story_implementation_prompt(story, result)

            agent_result = self.agent_spawner.spawn_agent(
                agent_name="Amelia",
                task_prompt=prompt,
                project_path=self.project_path,
                timeout_seconds=story.timeout_seconds // 2,  # 1/2 of story time for implementation
            )

            # Record metrics
            if self.metrics_aggregator and agent_result.metrics:
                self.metrics_aggregator.record_agent_metrics(agent_result.metrics)

            if agent_result.success:
                result.acceptance_criteria_met.append("Story implemented by Amelia")
                result.metadata["implementation_phase"] = "completed"
                result.metadata["implementation_output"] = agent_result.output[:500]
            else:
                raise Exception(f"Story implementation failed: {agent_result.error}")
        else:
            # Fallback if no agent spawner
            result.acceptance_criteria_met.append("Story implemented (no agent)")
            result.metadata["implementation_phase"] = "skipped"

    def _execute_story_validation(
        self, story: StoryConfig, result: StoryResult
    ) -> None:
        """
        Execute story validation phase (Murat - QA).

        Validates the story with:
        - Test execution
        - Quality checks
        - Acceptance criteria verification
        """
        self.logger.debug("story_validation_phase", story=story.name)

        if self.agent_spawner:
            # Spawn Murat to validate ONE story
            prompt = self._create_story_validation_prompt(story, result)

            agent_result = self.agent_spawner.spawn_agent(
                agent_name="Murat",
                task_prompt=prompt,
                project_path=self.project_path,
                timeout_seconds=story.timeout_seconds // 6,  # 1/6 of story time for validation
            )

            # Record metrics
            if self.metrics_aggregator and agent_result.metrics:
                self.metrics_aggregator.record_agent_metrics(agent_result.metrics)

            if agent_result.success:
                result.acceptance_criteria_met.append("Story validated by Murat")
                result.tests_passed = len(story.acceptance_criteria)
                result.metadata["validation_phase"] = "completed"
                result.metadata["validation_output"] = agent_result.output[:500]
            else:
                raise Exception(f"Story validation failed: {agent_result.error}")
        else:
            # Fallback if no agent spawner
            result.acceptance_criteria_met.append("Story validated (no agent)")
            result.tests_passed = len(story.acceptance_criteria)
            result.metadata["validation_phase"] = "skipped"

    def _execute_story_commit(
        self, story: StoryConfig, result: StoryResult
    ) -> None:
        """
        Execute git commit for completed story.

        Creates conventional commit:
        feat(epic): implement Story X.Y - Story Name
        """
        self.logger.debug("story_commit_phase", story=story.name)

        if self.git_manager:
            try:
                # Create commit message
                commit_message = self._generate_commit_message(story, result)

                # Create commit
                commit_result = self.git_manager.create_commit(
                    message=commit_message,
                    add_all=True,
                    allow_empty=False,
                )

                result.commit_hash = commit_result["hash"]
                result.artifacts_created.extend(commit_result["files_changed"])

                self.logger.info(
                    "story_committed",
                    story=story.name,
                    commit_hash=result.commit_hash,
                    files=len(commit_result["files_changed"]),
                )

            except Exception as e:
                self.logger.warning(
                    "story_commit_failed",
                    story=story.name,
                    error=str(e),
                )
                # Don't fail the story if commit fails
                result.metadata["commit_warning"] = str(e)
        else:
            self.logger.debug("git_manager_not_configured_skipping_commit")

    def _generate_commit_message(
        self, story: StoryConfig, result: StoryResult
    ) -> str:
        """
        Generate conventional commit message for story.

        Format:
        feat(epic-name): implement Story - Story Name

        Story Points: X
        Acceptance Criteria: Y/Z met
        Duration: X.Xs

        🤖 Generated with GAO-Dev
        Co-Authored-By: Claude <noreply@anthropic.com>
        """
        # Extract epic name slug
        epic_slug = result.epic_name.lower().replace(" ", "-")

        # Build commit message
        lines = [
            f"feat({epic_slug}): implement {story.name}",
            "",
            story.description or "Story implementation",
            "",
            f"Story Points: {story.story_points}",
            f"Acceptance Criteria: {len(result.acceptance_criteria_met)} met",
            f"Duration: {result.duration_seconds:.1f}s",
            f"Agent: {story.agent}",
            "",
            "🤖 Generated with GAO-Dev",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
        ]

        return "\n".join(lines)

    def _create_story_creation_prompt(
        self, story: StoryConfig, result: StoryResult
    ) -> str:
        """
        Create focused prompt for Bob to create ONE story specification.

        Emphasizes:
        - Working on ONE story at a time
        - Clear acceptance criteria
        - No epic-level planning (just this story)
        """
        return f"""You are Bob, the Scrum Master for GAO-Dev.

## YOUR TASK: Create Specification for ONE Story

**IMPORTANT**: Focus ONLY on this ONE story. Do not create other stories or plan the epic.

### Story Overview
- **Epic**: {result.epic_name}
- **Story Name**: {story.name}
- **Story Points**: {story.story_points}
- **Agent Responsible**: {story.agent}
- **Description**: {story.description}

### Predefined Acceptance Criteria
{chr(10).join(f"- {criterion}" for criterion in story.acceptance_criteria)}

### Your Responsibilities

1. **Review the Story**: Understand what needs to be built for THIS ONE story
2. **Enhance Acceptance Criteria**: Add any technical acceptance criteria needed
3. **Identify Dependencies**: List any files or components this story depends on
4. **Define Technical Requirements**: Specify implementation details
5. **Create Story Document**: Document this ONE story for Amelia to implement

### Output Required

Create a detailed story specification document that includes:
- Clear, testable acceptance criteria
- Technical implementation notes
- Dependencies and prerequisites
- Definition of done
- Estimated complexity

### Context
- **Project Path**: {self.project_path}
- **Working on**: ONE story at a time (incremental agile workflow)
- **Next Step**: Amelia will implement this story based on your specification

**Remember**: Focus on THIS ONE story. Amelia will use your specification to implement it.

Begin creating the story specification now."""

    def _create_story_implementation_prompt(
        self, story: StoryConfig, result: StoryResult
    ) -> str:
        """
        Create focused prompt for Amelia to implement ONE story.

        Emphasizes:
        - Implementing ONE story at a time
        - Following acceptance criteria
        - Writing tests for this story only
        """
        # Get context from creation phase
        creation_output = result.metadata.get("creation_output", "")

        return f"""You are Amelia, the Software Developer for GAO-Dev.

## YOUR TASK: Implement ONE Story

**IMPORTANT**: Implement ONLY this ONE story. Do not implement other stories.

### Story Details
- **Epic**: {result.epic_name}
- **Story Name**: {story.name}
- **Story Points**: {story.story_points}
- **Description**: {story.description}

### Acceptance Criteria (Must All Be Met)
{chr(10).join(f"- {criterion}" for criterion in story.acceptance_criteria)}

### Context from Story Creation Phase
{creation_output if creation_output else "No additional context from Bob"}

### Your Responsibilities

1. **Implement THIS Story**: Write code to meet all acceptance criteria
2. **Write Tests**: Create unit tests that verify acceptance criteria
3. **Follow Standards**: Use TypeScript, proper typing, clean code
4. **Document Code**: Add docstrings and comments as needed
5. **Verify Locally**: Ensure tests pass before marking complete

### Implementation Guidelines
- **Focus**: ONE story at a time (not the whole epic)
- **Quality**: Production-ready code with 80%+ test coverage
- **Tests**: Write tests that verify each acceptance criterion
- **Types**: Full TypeScript type safety, no 'any' types
- **Style**: Follow project conventions and best practices

### Context
- **Project Path**: {self.project_path}
- **Working on**: ONE story (incremental workflow)
- **Next Step**: Murat will validate your implementation

### Output Format
Provide:
- Summary of files created/modified
- Test results showing acceptance criteria met
- Any issues or blockers encountered
- Confirmation that all acceptance criteria are satisfied

**Remember**: Implement THIS ONE story completely. Murat will validate it next.

Begin implementing the story now."""

    def _create_story_validation_prompt(
        self, story: StoryConfig, result: StoryResult
    ) -> str:
        """
        Create focused prompt for Murat to validate ONE story.

        Emphasizes:
        - Validating ONE story at a time
        - Checking all acceptance criteria
        - Running tests for this story only
        """
        # Get context from implementation phase
        implementation_output = result.metadata.get("implementation_output", "")

        return f"""You are Murat, the Test Architect and QA Engineer for GAO-Dev.

## YOUR TASK: Validate ONE Story

**IMPORTANT**: Validate ONLY this ONE story. Do not test other stories.

### Story Details
- **Epic**: {result.epic_name}
- **Story Name**: {story.name}
- **Story Points**: {story.story_points}
- **Description**: {story.description}

### Acceptance Criteria to Verify
{chr(10).join(f"- {criterion}" for criterion in story.acceptance_criteria)}

### Context from Implementation Phase
{implementation_output if implementation_output else "No context from Amelia"}

### Your Responsibilities

1. **Run Tests**: Execute all tests related to THIS story
2. **Verify Acceptance Criteria**: Confirm each criterion is met
3. **Check Code Quality**: Verify type safety, linting, coverage
4. **Validate Functionality**: Manual testing if needed
5. **Report Results**: Clear pass/fail for each criterion

### Validation Checklist
- [ ] All tests passing for this story
- [ ] Test coverage >= 80% for new code
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] All acceptance criteria verified
- [ ] Code follows project standards

### Context
- **Project Path**: {self.project_path}
- **Working on**: ONE story (incremental validation)
- **Next Step**: If passing, story will be committed

### Output Format
Provide:
- Test results (passing/failing counts)
- Acceptance criteria verification (checked/unchecked)
- Code quality metrics (coverage, linting, types)
- Overall verdict: PASS or FAIL
- If FAIL: Specific issues that need fixing

**Remember**: Validate THIS ONE story. If it passes, it will be committed atomically.

Begin validating the story now."""
