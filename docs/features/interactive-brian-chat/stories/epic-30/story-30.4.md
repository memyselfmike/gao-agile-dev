# Story 30.4: Command Routing & Execution

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.4
**Priority**: P0 (Critical - Execution)
**Estimate**: 11 story points (updated from 5 - includes Critical 2, 3, HIGH 4)
**Duration**: 2-3 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.3 (Conversational Brian), Story 30.5 (Session State), Epic 15 (StateTracker), Epic 21 (AIAnalysisService)

---

## Story Description

Implement command routing to execute workflows and commands after Brian's analysis and user confirmation. Convert confirmed workflow sequences into actual orchestrator calls, stream progress updates conversationally, and wrap outputs beautifully.

This story connects conversational analysis (Story 30.3) to actual execution, making the REPL functional end-to-end.

---

## User Story

**As a** developer
**I want** all existing CLI commands to work within the chat session
**So that** I don't lose functionality in interactive mode

---

## Acceptance Criteria

### Core Routing (Original)
- [ ] CommandRouter maps all existing CLI commands to orchestrator methods
- [ ] Routes: create_prd, create_architecture, create_story, implement_story, ceremony, learning, state
- [ ] Command arguments extracted and validated before execution
- [ ] Unknown commands return helpful error with suggestions
- [ ] Multi-workflow sequences execute in order

### Rich CLI Formatting (Critical 2)
- [ ] Each agent has distinct color scheme (Brian=green, John=blue, Winston=magenta, Sally=cyan, Bob=yellow, Amelia=bright_cyan, Murat=bright_yellow, Mary=bright_magenta)
- [ ] Response type system implemented with 11 types: intro, commentary, conclusion, question, agent_start, agent_progress, agent_output, agent_complete, error, warning, success
- [ ] Proper indentation hierarchy: Brian at left margin, agent work indented
- [ ] Rich Panels for important messages (Brian's analysis, errors)
- [ ] Visual symbols: → (start), • (progress), ✓ (success), ✗ (error), ⚠ (warning)

### Progress Tracking (Critical 2)
- [ ] Operations >30s show spinner with elapsed time
- [ ] Progress updates stream in real-time
- [ ] Current agent and activity visible during execution
- [ ] Spinner stops on completion/error
- [ ] Rich Progress library with SpinnerColumn and TimeElapsedColumn

### Error Recovery (Critical 2)
- [ ] Automatic retry once on first failure
- [ ] AI-powered failure analysis after second failure (using AIAnalysisService from Epic 21)
- [ ] Alternative approaches suggested based on error type
- [ ] User prompted to choose next action after failure
- [ ] Clear error messages with recovery options

### State Persistence (Critical 2)
- [ ] Active operations persisted to database immediately on start
- [ ] Operation progress updates saved to StateTracker (Epic 15)
- [ ] Artifacts tracked as they're created
- [ ] Failed operations marked with error details
- [ ] Completed operations archived with metrics

### Recovery on Startup (Critical 2)
- [ ] REPL checks for interrupted operations on startup
- [ ] User presented with recovery options: resume/start fresh/view completed
- [ ] Resumed operations continue from last known state
- [ ] Cancelled operations marked in history

### AI-Powered Help System (Critical 3)
- [ ] "help" command detected and routed to HelpSystem
- [ ] AI analyzes help query to understand user intent (using AIAnalysisService)
- [ ] Project context gathered via StateTracker (epic count, story count, current state)
- [ ] Context-aware help response generated based on project state
- [ ] Targeted, actionable guidance provided (NOT generic lists)
- [ ] Specific next steps suggested based on project state
- [ ] Help rendered in Rich Panel with formatting
- [ ] Examples work: "help" in greenfield, "help" in active project, "help with ceremonies", "help I'm stuck"

### AI-Powered Subcommand Routing (HIGH 4)
- [ ] Subcommand parser using AIAnalysisService
- [ ] Handles natural language variations for commands
- [ ] Extracts command structure: (command, subcommand, args)
- [ ] Supported commands with subcommands:
  - ceremony: list, show, run (with type: planning/standup/review/retrospective)
  - learning: list, show, apply
  - state: show (with epic/story identifiers)
  - story: list, show, status
  - epic: list, show, status
- [ ] Argument extraction from natural language (epic numbers, story identifiers, learning IDs, ceremony types)
- [ ] Falls back gracefully if parsing fails (ask user to clarify)

### Integration with Existing Systems
- [ ] Uses StateTracker (Epic 15) for operation persistence
- [ ] Uses DocumentLifecycle (Epic 12) for artifact tracking
- [ ] Uses AIAnalysisService (Epic 21) for failure analysis, help intelligence, and subcommand parsing
- [ ] Uses GAODevOrchestrator (Epic 27) for command execution

### Testing
- [ ] Unit tests for CommandRouter routing logic
- [ ] Unit tests for response type formatting
- [ ] Unit tests for help intent detection
- [ ] Unit tests for context-aware help generation
- [ ] Unit tests for subcommand parsing with various natural language inputs
- [ ] Integration tests for error recovery flow
- [ ] Integration tests for state persistence
- [ ] Integration tests for recovery on restart
- [ ] Integration tests for help system with various project states
- [ ] Integration test: "list ceremonies for epic 1" → correct routing
- [ ] Manual QA: Create PRD, kill process mid-execution, restart, verify recovery
- [ ] Manual QA: Trigger failure, verify retry → analysis → alternatives flow
- [ ] Manual QA: Try "help" in greenfield project, verify guidance
- [ ] Manual QA: Try "help" in active project, verify context-aware suggestions

### Performance
- [ ] Response formatting overhead <5ms
- [ ] State persistence overhead <10ms per update
- [ ] Recovery check on startup <100ms
- [ ] Help query analysis <1s

---

## Files to Create/Modify

### New Files
- `gao_dev/cli/command_router.py` (~400 LOC)
  - `CommandRouter` class
  - Route intents to orchestrator methods
  - Stream progress updates
  - Format outputs conversationally

- `tests/cli/test_command_router.py` (~300 LOC)
  - Tests for command routing
  - Tests for progress streaming
  - Tests for error handling
  - Tests for cancellation

### Modified Files
- `gao_dev/orchestrator/conversational_brian.py` (~50 LOC modified)
  - Integrate CommandRouter for execution
  - Replace execution placeholder with real routing

- `gao_dev/cli/chat_repl.py` (~20 LOC modified)
  - Handle Ctrl+C during execution gracefully
  - Show cancellation message

---

## Technical Design

### CommandRouter Class

**Location**: `gao_dev/cli/command_router.py`

```python
"""Command routing and execution for interactive chat."""

from typing import AsyncIterator, Dict, Any, Optional
from pathlib import Path
import asyncio
import structlog

from gao_dev.orchestrator.gao_dev_orchestrator import GAODevOrchestrator
from gao_dev.core.models.workflow_sequence import WorkflowSequence

logger = structlog.get_logger()


class CommandRouter:
    """
    Route parsed intents to orchestrator methods and stream results.

    Converts workflow sequences and command intents into actual
    orchestrator calls, streaming progress updates conversationally.
    """

    def __init__(self, orchestrator: GAODevOrchestrator):
        """
        Initialize router.

        Args:
            orchestrator: GAODevOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = logger.bind(component="command_router")

    async def execute_workflow_sequence(
        self,
        workflow_sequence: WorkflowSequence,
        project_root: Path
    ) -> AsyncIterator[str]:
        """
        Execute workflow sequence from Brian's analysis.

        Args:
            workflow_sequence: Workflow sequence to execute
            project_root: Project root path

        Yields:
            Conversational progress updates
        """
        self.logger.info(
            "executing_workflow_sequence",
            workflow_count=len(workflow_sequence.workflows)
        )

        yield f"Executing {len(workflow_sequence.workflows)} workflow(s)..."

        for i, workflow in enumerate(workflow_sequence.workflows, 1):
            workflow_name = workflow.name if hasattr(workflow, 'name') else str(workflow)

            yield f"\n[{i}/{len(workflow_sequence.workflows)}] {workflow_name}..."

            try:
                # Execute workflow via orchestrator
                async for message in self._execute_single_workflow(
                    workflow,
                    project_root
                ):
                    yield f"  {message}"

                yield f"✓ {workflow_name} complete!"

            except Exception as e:
                self.logger.exception("workflow_failed", workflow=workflow_name, error=str(e))
                yield f"✗ {workflow_name} failed: {str(e)}"
                yield "Would you like to continue with remaining workflows? (yes/no)"
                # NOTE: Cancellation handling would be done by ChatREPL
                return

        yield "\n🎉 All workflows completed successfully!"

    async def _execute_single_workflow(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """
        Execute single workflow.

        Args:
            workflow: Workflow to execute
            project_root: Project root

        Yields:
            Progress messages
        """
        # Route to appropriate orchestrator method based on workflow type
        workflow_name = workflow.name if hasattr(workflow, 'name') else str(workflow)

        if "prd" in workflow_name.lower():
            async for msg in self._execute_create_prd(workflow, project_root):
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
            # Use orchestrator's generic workflow executor
            await self.orchestrator.execute_workflow(workflow, project_root)
            yield "Done!"

    async def _execute_create_prd(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute PRD creation workflow."""
        yield "Coordinating with John (Product Manager)..."

        try:
            # Extract project name from workflow or use default
            project_name = getattr(workflow, 'project_name', 'New Feature')

            # Call orchestrator
            result = await self.orchestrator.create_prd(
                name=project_name,
                project_root=project_root
            )

            # Format result
            prd_path = result.get('prd_path', 'Unknown')
            yield f"PRD created at: {prd_path}"

        except Exception as e:
            yield f"PRD creation failed: {str(e)}"
            raise

    async def _execute_create_stories(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute story creation workflow."""
        yield "Coordinating with Bob (Scrum Master)..."

        try:
            # Extract epic number or use default
            epic_num = getattr(workflow, 'epic_num', None)

            if not epic_num:
                yield "Error: Epic number required for story creation"
                raise ValueError("Epic number not provided")

            # Call orchestrator
            result = await self.orchestrator.create_stories_for_epic(
                epic_num=epic_num,
                project_root=project_root
            )

            # Format result
            story_count = result.get('story_count', 0)
            yield f"Created {story_count} stories for Epic {epic_num}"

        except Exception as e:
            yield f"Story creation failed: {str(e)}"
            raise

    async def _execute_implement(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute implementation workflow."""
        yield "Coordinating with Amelia (Developer)..."

        try:
            # Extract epic and story numbers
            epic_num = getattr(workflow, 'epic_num', None)
            story_num = getattr(workflow, 'story_num', None)

            if not epic_num or not story_num:
                yield "Error: Epic and story numbers required"
                raise ValueError("Epic/story numbers not provided")

            # Call orchestrator
            async for message in self.orchestrator.implement_story(
                epic_num=epic_num,
                story_num=story_num,
                project_root=project_root
            ):
                yield message

        except Exception as e:
            yield f"Implementation failed: {str(e)}"
            raise

    async def _execute_ceremony(
        self,
        workflow: Any,
        project_root: Path
    ) -> AsyncIterator[str]:
        """Execute ceremony workflow."""
        ceremony_type = getattr(workflow, 'ceremony_type', 'unknown')
        yield f"Coordinating {ceremony_type} ceremony with the team..."

        try:
            # Call ceremony orchestrator
            result = await self.orchestrator.hold_ceremony(
                ceremony_type=ceremony_type,
                project_root=project_root
            )

            yield f"{ceremony_type.capitalize()} ceremony complete!"

        except Exception as e:
            yield f"Ceremony failed: {str(e)}"
            raise

    async def execute_command(
        self,
        command: str,
        args: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """
        Execute explicit command (non-workflow).

        For direct commands like "show status", "list epics", etc.

        Args:
            command: Command name
            args: Command arguments

        Yields:
            Conversational responses
        """
        self.logger.info("executing_command", command=command)

        if command == "status":
            yield await self._command_status(args)

        elif command == "list_epics":
            yield await self._command_list_epics(args)

        elif command == "list_stories":
            yield await self._command_list_stories(args)

        elif command == "show_learning":
            yield await self._command_show_learning(args)

        else:
            yield f"Unknown command: {command}"
            yield "Type 'help' to see available commands."

    async def _command_status(self, args: Dict[str, Any]) -> str:
        """Show project status."""
        # Use ProjectStatusReporter from Story 30.2
        from gao_dev.cli.project_status import ProjectStatusReporter

        reporter = ProjectStatusReporter()
        status = reporter.get_status()
        return reporter.format_status(status)

    async def _command_list_epics(self, args: Dict[str, Any]) -> str:
        """List all epics."""
        from gao_dev.core.state.fast_context_loader import FastContextLoader

        project_root = args.get('project_root', Path.cwd())
        db_path = project_root / ".gao-dev" / "documents.db"

        context_loader = FastContextLoader(db_path)
        epics = context_loader.get_epics()

        if not epics:
            return "No epics found in this project."

        lines = ["**Epics**:"]
        for epic in epics:
            status = epic.get('status', 'unknown')
            lines.append(f"  - Epic {epic['epic_num']}: {epic['title']} [{status}]")

        return "\n".join(lines)

    async def _command_list_stories(self, args: Dict[str, Any]) -> str:
        """List stories for an epic."""
        epic_num = args.get('epic_num')
        if not epic_num:
            return "Please specify an epic number: 'list stories for epic 30'"

        from gao_dev.core.state.fast_context_loader import FastContextLoader

        project_root = args.get('project_root', Path.cwd())
        db_path = project_root / ".gao-dev" / "documents.db"

        context_loader = FastContextLoader(db_path)
        stories = context_loader.get_stories_for_epic(epic_num)

        if not stories:
            return f"No stories found for Epic {epic_num}."

        lines = [f"**Stories for Epic {epic_num}**:"]
        for story in stories:
            status = story.get('status', 'unknown')
            lines.append(
                f"  - Story {story['epic_num']}.{story['story_num']}: "
                f"{story['title']} [{status}]"
            )

        return "\n".join(lines)

    async def _command_show_learning(self, args: Dict[str, Any]) -> str:
        """Show learnings."""
        # Use LearningService from Epic 29
        from gao_dev.core.services.learning_service import LearningService

        project_root = args.get('project_root', Path.cwd())
        learning_service = LearningService(project_root / ".gao-dev" / "documents.db")

        learnings = learning_service.get_learnings(limit=5)

        if not learnings:
            return "No learnings recorded yet."

        lines = ["**Recent Learnings**:"]
        for learning in learnings:
            lines.append(f"  - {learning['title']}: {learning['lesson'][:100]}...")

        return "\n".join(lines)
```

### ConversationalBrian Integration

**Location**: `gao_dev/orchestrator/conversational_brian.py` (modify)

```python
class ConversationalBrian:
    """Conversational wrapper around BrianOrchestrator."""

    def __init__(
        self,
        brian_orchestrator: BrianOrchestrator,
        command_router: CommandRouter  # NEW: Add router
    ):
        """Initialize conversational Brian."""
        self.brian = brian_orchestrator
        self.command_router = command_router  # NEW
        self.intent_parser = IntentParser()
        self.logger = logger.bind(component="conversational_brian")

    async def _handle_confirmation(
        self,
        intent: Intent,
        context: ConversationContext
    ) -> AsyncIterator[str]:
        """Handle confirmation response."""
        if not context.pending_confirmation:
            yield "I'm not sure what you're confirming. What would you like to do?"
            return

        if intent.is_positive:
            # User confirmed - EXECUTE!
            yield "Great! I'll coordinate with the team to get started..."

            # NEW: Actually execute workflows
            async for message in self.command_router.execute_workflow_sequence(
                context.pending_confirmation,
                Path(context.project_root)
            ):
                yield message

            # Clear pending confirmation
            context.pending_confirmation = None

        else:
            # User declined
            yield "No problem! Let me know if you'd like to try a different approach."
            context.pending_confirmation = None
```

### ChatREPL Enhancement

**Location**: `gao_dev/cli/chat_repl.py` (modify)

```python
class ChatREPL:
    """Interactive REPL for conversational chat with Brian."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize ChatREPL with full orchestration stack."""
        self.project_root = project_root or Path.cwd()
        # ... (existing initialization)

        # NEW: Create orchestrator and router
        from gao_dev.orchestrator.gao_dev_orchestrator import GAODevOrchestrator
        from gao_dev.cli.command_router import CommandRouter

        self.orchestrator = GAODevOrchestrator()
        self.command_router = CommandRouter(self.orchestrator)

        # Conversational Brian with router
        brian_orchestrator = BrianOrchestrator()
        self.conversational_brian = ConversationalBrian(
            brian_orchestrator,
            self.command_router  # Pass router
        )

        # ... (rest of initialization)

    async def start(self) -> None:
        """Start interactive REPL loop."""
        # ... (existing greeting)

        while True:
            try:
                user_input = await self.prompt_session.prompt_async("You: ")
                # ... (existing exit check)

                # Handle input (now with real execution)
                await self._handle_input(user_input)

            except KeyboardInterrupt:
                # NEW: Handle Ctrl+C during execution
                self.logger.info("keyboard_interrupt_during_execution")
                self.console.print("\n[yellow]Operation cancelled by user[/yellow]")
                # Continue loop (don't exit)
                continue

            except Exception as e:
                # ... (existing error handling)
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/cli/test_command_router.py`

**Test Cases**:

1. **test_execute_workflow_sequence**
   - Workflow sequence → All workflows execute in order
   - Progress messages yielded for each workflow

2. **test_execute_create_prd**
   - PRD workflow → Orchestrator.create_prd() called
   - Success message includes PRD path

3. **test_execute_create_stories**
   - Story workflow → Orchestrator.create_stories_for_epic() called
   - Success message includes story count

4. **test_execute_implement**
   - Implementation workflow → Orchestrator.implement_story() called
   - Progress messages streamed

5. **test_workflow_failure_handling**
   - Workflow fails → Error message yielded
   - Asks user if want to continue

6. **test_execute_command_status**
   - Command "status" → Status displayed
   - Uses ProjectStatusReporter

7. **test_execute_command_list_epics**
   - Command "list_epics" → Epic list displayed
   - Uses FastContextLoader

8. **test_command_not_found**
   - Unknown command → Helpful error message
   - Suggests "help"

**Example Test**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from gao_dev.cli.command_router import CommandRouter


@pytest.mark.asyncio
async def test_execute_workflow_sequence():
    """Test executing workflow sequence."""
    # Mock orchestrator
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_prd = AsyncMock(return_value={"prd_path": "/test/prd.md"})

    # Create router
    router = CommandRouter(mock_orchestrator)

    # Mock workflow sequence
    mock_workflow = MagicMock()
    mock_workflow.name = "create_prd"

    mock_sequence = MagicMock()
    mock_sequence.workflows = [mock_workflow]

    # Execute
    messages = []
    async for message in router.execute_workflow_sequence(
        mock_sequence,
        Path("/test/project")
    ):
        messages.append(message)

    # Assert
    assert len(messages) >= 3
    assert "Executing 1 workflow" in messages[0]
    assert "create_prd" in messages[1]
    assert "complete" in messages[-1].lower()


@pytest.mark.asyncio
async def test_workflow_failure_handling():
    """Test handling workflow failures."""
    # Mock orchestrator that fails
    mock_orchestrator = MagicMock()
    mock_orchestrator.create_prd = AsyncMock(side_effect=Exception("PRD creation failed"))

    router = CommandRouter(mock_orchestrator)

    # Mock workflow
    mock_workflow = MagicMock()
    mock_workflow.name = "create_prd"

    mock_sequence = MagicMock()
    mock_sequence.workflows = [mock_workflow]

    # Execute
    messages = []
    async for message in router.execute_workflow_sequence(mock_sequence, Path("/test")):
        messages.append(message)

    # Assert failure message
    assert any("failed" in msg.lower() for msg in messages)
    assert any("continue" in msg.lower() for msg in messages)
```

---

## Definition of Done

- [ ] Code written and follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] 10+ unit tests written and passing
- [ ] Integration test: Workflow execution end-to-end
- [ ] Manual testing: Commands work in REPL
- [ ] Progress streaming works smoothly
- [ ] Errors handled gracefully
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.4 - Command Routing & Execution (5 pts)`
- [ ] Documentation updated (inline docstrings)

---

## Dependencies

### Internal Dependencies
- Story 30.3 (ConversationalBrian must exist)
- GAODevOrchestrator (Epic 27)
- FastContextLoader (Epic 25)
- LearningService (Epic 29)

### No New External Dependencies

---

## Implementation Notes

### Streaming Progress Updates

**Pattern**:
- Use `async for` to yield messages incrementally
- User sees progress in real-time
- Don't wait for entire operation to complete

**Example**:
```python
async for message in router.execute_workflow_sequence(...):
    console.print(message)  # Shows immediately
```

### Error Handling Strategy

**Levels**:
1. **Workflow-level errors**: Catch, report, ask to continue
2. **Command-level errors**: Catch, suggest alternatives
3. **Unexpected errors**: Catch, log, display user-friendly message

**Never crash the REPL on execution errors.**

### Cancellation Handling

**Ctrl+C During Execution**:
- Catch KeyboardInterrupt in REPL loop
- Display "Operation cancelled by user"
- Continue REPL (don't exit)
- Clean up any partial work

**Future Enhancement**: Support for explicit "cancel" command

### Command vs Workflow Routing

**Workflows** (from Brian analysis):
- Multi-step sequences (PRD → Stories → Implementation)
- Routed via `execute_workflow_sequence()`

**Commands** (explicit user requests):
- Single operations ("show status", "list epics")
- Routed via `execute_command()`

---

## Manual Testing Checklist

- [ ] Run `gao-dev start`
- [ ] Type: "I want to add a feature"
- [ ] Brian analyzes, type: "yes"
  - [ ] Workflows execute
  - [ ] Progress messages stream
  - [ ] Success message at end
- [ ] Type: "show status"
  - [ ] Status displayed
- [ ] Type: "list epics"
  - [ ] Epic list displayed
- [ ] During long operation, press Ctrl+C
  - [ ] Operation cancelled
  - [ ] REPL continues (doesn't exit)
- [ ] Type command that will fail (e.g., invalid epic)
  - [ ] Error message clear
  - [ ] REPL continues
  - [ ] Suggestion provided

---

## Next Steps

After Story 30.4 is complete:

**Story 30.5**: Enhance session state for multi-turn context memory
**Story 30.6**: Add greenfield project initialization flow

---

**Created**: 2025-11-10
**Status**: Ready to Implement
