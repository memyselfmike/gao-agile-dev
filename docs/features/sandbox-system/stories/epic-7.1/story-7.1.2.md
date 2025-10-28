# Story 7.1.2: Move Story Workflow to Core Orchestrator

**Epic**: 7.1 - Integration & Architecture Fix
**Story Points**: 5
**Priority**: P0 - Critical
**Status**: Ready
**Owner**: Amelia (Developer)

## User Story

As a GAO-Dev architect
I want story-based workflows in the core orchestrator
So that incremental development with QA-as-you-go is a core feature, not a sandbox-only capability

## Context

**Current Architecture Problem**:
- Story-by-story workflow (Bob → Amelia → Murat → Commit) is in `gao_dev/sandbox/benchmark/story_orchestrator.py`
- This should be a CORE workflow, not benchmark-specific
- StoryOrchestrator still uses removed AgentSpawner (Epic 7.1 removed it)
- Story-based benchmarks fail: `No module named 'gao_dev.sandbox.benchmark.agent_spawner'`

**Key Insight**: Story-by-story incremental development with QA validation IS the core agile workflow for GAO-Dev.

## Problem

1. Story workflow buried in sandbox (wrong location)
2. StoryOrchestrator uses AgentSpawner (removed in Epic 7)
3. CLI can't use story workflows (not accessible)
4. QA-as-you-go treated as special case, should be default

## Goal

Refactor architecture to make story-based workflow a core feature of GAODevOrchestrator.

## Acceptance Criteria

### Code Changes
- [ ] Add `execute_story_workflow()` method to GAODevOrchestrator
- [ ] Add `execute_epic_workflow()` method to GAODevOrchestrator
- [ ] Story workflow uses GAODevOrchestrator, not AgentSpawner
- [ ] StoryOrchestrator either removed or made thin wrapper
- [ ] All references to AgentSpawner removed/updated

### Functionality
- [ ] Can execute single story: Bob → Amelia → Murat → Commit
- [ ] Can execute full epic (loop through all stories)
- [ ] QA validation happens per story (Murat after Amelia)
- [ ] Atomic git commits per story
- [ ] Existing CLI commands still work (backwards compatible)

### Testing
- [ ] Unit tests for new orchestrator methods
- [ ] Integration test for story workflow
- [ ] Benchmark can use new core methods

## Technical Design

### Add to GAODevOrchestrator

```python
# gao_dev/orchestrator/orchestrator.py

class GAODevOrchestrator:
    """Main orchestrator for GAO-Dev autonomous development team."""

    # ... existing methods ...

    async def execute_story_workflow(
        self,
        epic: int,
        story: int,
        story_config: Optional[Dict] = None,
        with_qa: bool = True
    ) -> StoryResult:
        """
        Execute complete story lifecycle with QA validation.

        Workflow:
        1. Bob (Scrum Master) → Create detailed story spec
        2. Amelia (Developer) → Implement + write tests
        3. Murat (QA) → Validate, run tests, check quality (if with_qa=True)
        4. Git → Atomic commit with story details

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
            # Phase 1: Bob creates story spec
            await self._execute_story_creation(epic, story, result)

            # Phase 2: Amelia implements
            await self._execute_story_implementation(epic, story, result)

            # Phase 3: Murat validates (if enabled)
            if with_qa:
                await self._execute_story_qa(epic, story, result)

            # Phase 4: Git commit
            await self._execute_story_commit(epic, story, result)

            result.status = StoryStatus.COMPLETED
            result.end_time = datetime.now()

        except Exception as e:
            result.status = StoryStatus.FAILED
            result.error_message = str(e)

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

        for i, story_config in enumerate(stories, 1):
            story_result = await self.execute_story_workflow(
                epic=epic,
                story=i,
                story_config=story_config,
                with_qa=with_qa
            )
            epic_result.story_results.append(story_result)

            # Stop on first failure (fail-fast)
            if story_result.status == StoryStatus.FAILED:
                break

        epic_result.end_time = datetime.now()
        return epic_result

    async def _execute_story_creation(self, epic, story, result):
        """Phase 1: Bob creates story spec."""
        # Use existing create_story() method
        async for message in self.create_story(epic, story):
            pass  # Collect output

    async def _execute_story_implementation(self, epic, story, result):
        """Phase 2: Amelia implements."""
        # Use existing implement_story() method
        async for message in self.implement_story(epic, story):
            pass  # Collect output

    async def _execute_story_qa(self, epic, story, result):
        """Phase 3: Murat validates."""
        # NEW: Add QA validation method
        task = f"""Use Murat (QA) to validate Story {epic}.{story}.

        Murat should:
        1. Read the story file
        2. Run all tests (npm test, pytest, etc.)
        3. Check code coverage (target: 80%+)
        4. Validate acceptance criteria met
        5. Check code quality (linting, types)
        6. Report pass/fail with details
        """
        async for message in self.execute_task(task):
            pass  # Collect QA output

    async def _execute_story_commit(self, epic, story, result):
        """Phase 4: Create atomic git commit."""
        # Create commit with story details
        commit_message = f"feat(story-{epic}.{story}): implement {result.story_name}"
        # Use git manager to commit
```

### Update Benchmark Runner

```python
# gao_dev/sandbox/benchmark/runner.py

def _execute_story_based_workflow(self, project, result):
    """Execute story-based workflow using core orchestrator."""

    # Use core GAODevOrchestrator, not StoryOrchestrator
    orchestrator = GAODevOrchestrator(project_root=project_path)

    for epic_config in self.config.epics:
        epic_result = asyncio.run(
            orchestrator.execute_epic_workflow(
                epic=epic_config.number,
                stories=epic_config.stories,
                with_qa=True  # QA-as-you-go!
            )
        )

        # Record metrics
        result.epic_results.append(epic_result)
```

### Remove/Deprecate StoryOrchestrator

**Option A**: Remove entirely (use core orchestrator)
**Option B**: Make thin wrapper for benchmark-specific metrics

```python
# Option B: Thin wrapper
class StoryOrchestrator:
    """Thin wrapper around core orchestrator for benchmark metrics."""

    def __init__(self, orchestrator: GAODevOrchestrator):
        self.orchestrator = orchestrator
        self.metrics = MetricsAggregator()

    async def execute_epic(self, epic_config):
        result = await self.orchestrator.execute_epic_workflow(
            epic=epic_config.number,
            stories=epic_config.stories
        )
        self.metrics.record_epic(result)
        return result
```

## Testing Strategy

1. **Unit Tests**: Test new orchestrator methods in isolation
2. **Integration Test**: Run story workflow end-to-end
3. **Benchmark Test**: Run simple-story-test.yaml
4. **CLI Test**: Verify existing commands still work

## Migration Path

1. Add new methods to GAODevOrchestrator
2. Update benchmark runner to use new methods
3. Test with simple-story-test.yaml
4. Deprecate old StoryOrchestrator
5. Update documentation

## Dependencies

- Story 7.1.1 must be complete (phase-based working)
- Requires GAODevOrchestrator (already exists)
- Requires git integration (already exists)

## Risks

- Large refactoring - test thoroughly
- May break existing benchmarks temporarily
- Need to ensure backwards compatibility

## Definition of Done

- [ ] Code refactored and tested
- [ ] Story workflow in core orchestrator
- [ ] AgentSpawner references removed
- [ ] Tests passing
- [ ] simple-story-test.yaml works
- [ ] Code committed atomically
- [ ] Story status updated to Done

## Notes

This is the key architectural fix that makes story-by-story incremental development a core GAO-Dev feature, not a sandbox-only capability.

**Impact**: After this story, the CLI can use story workflows directly, enabling true incremental autonomous development.
