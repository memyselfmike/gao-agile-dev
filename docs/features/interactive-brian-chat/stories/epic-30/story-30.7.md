# Story 30.7: Testing & Documentation

**Epic**: Epic 30 - Interactive Brian Chat Interface
**Story ID**: 30.7
**Priority**: P0 (Critical - Quality)
**Estimate**: 3 story points
**Duration**: 1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Stories 30.1-30.6 (all implementation complete)

---

## Story Description

Comprehensive testing and documentation for Epic 30. Write integration tests for full user flows, conduct manual QA with real scenarios, update user documentation, create examples and demos, and validate the entire interactive chat experience end-to-end.

This story ensures Epic 30 is production-ready, reliable, and well-documented.

---

## User Story

**As a** developer
**I want** comprehensive tests and clear documentation
**So that** the REPL is reliable and users know how to use it

---

## Acceptance Criteria

- [ ] 15+ integration tests covering full user flows
- [ ] 5+ manual QA scenarios executed and documented
- [ ] User documentation updated with REPL usage
- [ ] Examples created: New user, experienced user, greenfield
- [ ] Demo script for showcasing capabilities
- [ ] All edge cases tested (errors, cancellation, etc.)
- [ ] Performance validated: <2s startup, <1s responses
- [ ] 90%+ test coverage for new code
- [ ] Documentation reviewed and approved
- [ ] Manual QA checklist completed

---

## Files to Create/Modify

### New Files
- `tests/integration/test_chat_flow.py` (~400 LOC)
  - Full conversation flow tests
  - Multi-turn conversation tests
  - Error scenario tests
  - Cancellation tests

- `docs/features/interactive-brian-chat/USER_GUIDE.md` (~300 lines)
  - How to use `gao-dev start`
  - Common workflows
  - Tips and tricks
  - Troubleshooting

- `docs/features/interactive-brian-chat/EXAMPLES.md` (~200 lines)
  - Example conversations
  - Typical scenarios
  - Best practices

- `docs/features/interactive-brian-chat/DEMO_SCRIPT.md` (~150 lines)
  - Demo walkthrough
  - Showcase key features
  - Talking points

### Modified Files
- `README.md` (root) (~30 lines added)
  - Add interactive chat section
  - Link to user guide

- `docs/bmm-workflow-status.md` (~20 lines modified)
  - Update Epic 30 status to "Complete"

---

## Technical Design

### Integration Tests

**Location**: `tests/integration/test_chat_flow.py`

```python
"""Integration tests for interactive chat flows."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from gao_dev.cli.chat_repl import ChatREPL


@pytest.mark.asyncio
async def test_full_feature_request_flow(tmp_path):
    """
    Test complete feature request conversation flow.

    Flow:
    1. User starts REPL
    2. User requests feature
    3. Brian analyzes
    4. User confirms
    5. Workflows execute
    6. User exits
    """
    # Setup project
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    # Mock user inputs
    user_inputs = [
        "I want to build a todo app",  # Feature request
        "yes",                          # Confirmation
        "exit"                          # Exit
    ]

    # Mock Brian orchestrator
    with patch('gao_dev.orchestrator.brian_orchestrator.BrianOrchestrator') as MockBrian:
        mock_brian = MockBrian.return_value
        mock_analysis = MagicMock()
        mock_analysis.scale_level = MagicMock(value=2)
        mock_analysis.rationale = "Small feature"
        mock_analysis.workflows = [MagicMock(name="create_prd")]

        mock_brian.assess_and_select_workflows = AsyncMock(return_value=mock_analysis)

        # Create REPL
        repl = ChatREPL(project_root=tmp_path)

        # Mock prompt_session to return user inputs
        input_iter = iter(user_inputs)
        repl.prompt_session.prompt_async = AsyncMock(
            side_effect=lambda _: next(input_iter)
        )

        # Run REPL (will exit after 3 inputs)
        await repl.start()

        # Assert Brian was called
        mock_brian.assess_and_select_workflows.assert_called_once()


@pytest.mark.asyncio
async def test_multi_turn_conversation(tmp_path):
    """
    Test multi-turn conversation with context.

    Flow:
    1. User: "Build a todo app"
    2. Brian: Analyzes
    3. User: "And add authentication"
    4. Brian: Analyzes with context from turn 1
    """
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    user_inputs = [
        "I want to build a todo app",
        "And then add authentication",
        "exit"
    ]

    with patch('gao_dev.orchestrator.brian_orchestrator.BrianOrchestrator') as MockBrian:
        mock_brian = MockBrian.return_value
        mock_analysis = MagicMock()
        mock_analysis.scale_level = MagicMock(value=2)
        mock_analysis.workflows = []

        mock_brian.assess_and_select_workflows = AsyncMock(return_value=mock_analysis)

        repl = ChatREPL(project_root=tmp_path)

        input_iter = iter(user_inputs)
        repl.prompt_session.prompt_async = AsyncMock(
            side_effect=lambda _: next(input_iter)
        )

        await repl.start()

        # Assert Brian called twice (once per feature request)
        assert mock_brian.assess_and_select_workflows.call_count == 2


@pytest.mark.asyncio
async def test_greenfield_initialization(tmp_path):
    """
    Test greenfield project initialization flow.

    Flow:
    1. Start in empty directory
    2. Brian detects greenfield
    3. User types "init"
    4. Project initialized
    """
    # Empty directory (no .gao-dev/)
    user_inputs = [
        "init",
        "exit"
    ]

    repl = ChatREPL(project_root=tmp_path)

    input_iter = iter(user_inputs)
    repl.prompt_session.prompt_async = AsyncMock(
        side_effect=lambda _: next(input_iter)
    )

    await repl.start()

    # Assert .gao-dev/ created
    assert (tmp_path / ".gao-dev").exists()
    assert (tmp_path / "README.md").exists()


@pytest.mark.asyncio
async def test_error_handling_graceful(tmp_path):
    """
    Test that errors don't crash REPL.

    Flow:
    1. User requests feature
    2. Brian analysis fails
    3. Error displayed
    4. REPL continues
    """
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    user_inputs = [
        "Build something",
        "exit"
    ]

    with patch('gao_dev.orchestrator.brian_orchestrator.BrianOrchestrator') as MockBrian:
        mock_brian = MockBrian.return_value
        mock_brian.assess_and_select_workflows = AsyncMock(
            side_effect=Exception("Analysis failed")
        )

        repl = ChatREPL(project_root=tmp_path)

        input_iter = iter(user_inputs)
        repl.prompt_session.prompt_async = AsyncMock(
            side_effect=lambda _: next(input_iter)
        )

        # Should not raise exception
        await repl.start()


@pytest.mark.asyncio
async def test_ctrl_c_during_execution(tmp_path):
    """
    Test Ctrl+C cancellation during workflow execution.

    Flow:
    1. User confirms workflow execution
    2. Press Ctrl+C during execution
    3. Cancellation message shown
    4. REPL continues
    """
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    user_inputs = [
        "Build app",
        "yes",  # Confirm
        # Ctrl+C happens here (KeyboardInterrupt)
        "exit"
    ]

    with patch('gao_dev.orchestrator.brian_orchestrator.BrianOrchestrator') as MockBrian:
        mock_brian = MockBrian.return_value
        mock_analysis = MagicMock()
        mock_analysis.workflows = [MagicMock(name="long_workflow")]

        mock_brian.assess_and_select_workflows = AsyncMock(return_value=mock_analysis)

        repl = ChatREPL(project_root=tmp_path)

        input_iter = iter(user_inputs)

        # Simulate Ctrl+C on second call
        call_count = 0

        async def mock_prompt(_):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise KeyboardInterrupt()
            return next(input_iter)

        repl.prompt_session.prompt_async = mock_prompt

        # Should handle KeyboardInterrupt gracefully
        await repl.start()


@pytest.mark.asyncio
async def test_help_command(tmp_path):
    """Test help command shows useful information."""
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    user_inputs = ["help", "exit"]

    repl = ChatREPL(project_root=tmp_path)

    input_iter = iter(user_inputs)
    repl.prompt_session.prompt_async = AsyncMock(
        side_effect=lambda _: next(input_iter)
    )

    # Capture output
    from io import StringIO
    from rich.console import Console

    output = StringIO()
    console = Console(file=output, width=120)
    repl.console = console

    await repl.start()

    # Assert help message displayed
    output_text = output.getvalue()
    assert "help" in output_text.lower()
    assert "feature" in output_text.lower() or "build" in output_text.lower()


@pytest.mark.asyncio
async def test_performance_startup_time(tmp_path):
    """Test that startup time is <2 seconds."""
    import time

    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()

    # Mock to exit immediately
    user_inputs = ["exit"]

    repl = ChatREPL(project_root=tmp_path)

    input_iter = iter(user_inputs)
    repl.prompt_session.prompt_async = AsyncMock(
        side_effect=lambda _: next(input_iter)
    )

    # Measure startup time
    start = time.time()
    await repl.start()
    elapsed = time.time() - start

    # Assert <2 seconds (generous for test environment)
    assert elapsed < 2.0
```

### User Guide

**Location**: `docs/features/interactive-brian-chat/USER_GUIDE.md`

```markdown
# Interactive Brian Chat - User Guide

## Overview

The Interactive Brian Chat interface transforms GAO-Dev from a command-line tool into a conversational development partner. Simply run `gao-dev start` and have natural dialogue with Brian, your AI Engineering Manager.

## Getting Started

### Starting the REPL

```bash
$ gao-dev start
```

Brian will greet you and show your project status:

```
Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.

Project: my-awesome-app
Epics: 5 | Stories: 32
Current Epic: Epic 5: User Authentication

Recent Activity:
  - feat(epic-5): Story 5.3 - Login UI Component
  - feat(epic-5): Story 5.2 - JWT Token Service
  - feat(epic-5): Story 5.1 - User Model & Database

Type your requests in natural language, or type 'help' for available commands.
Type 'exit', 'quit', or 'bye' to end the session.
```

### Your First Request

Just type what you want to build:

```
You: I want to add a password reset feature

Brian: Let me analyze that for you...

I've analyzed your request. Here's what I found:

Scale Level: Level 2 - Small feature (1-2 weeks, light planning)
Project Type: feature

Reasoning: This is an enhancement to your existing authentication system

Recommended Workflows:
  1. create_prd
  2. create_stories
  3. implement_stories

Estimated Duration: 1-2 days

Shall I proceed with this plan? (yes/no)
```

Type "yes" to proceed, or "no" to decline.

## Common Workflows

### Building a New Feature

```
You: I want to add email notifications

Brian: [Analyzes...]
Brian: This is a Level 2 feature... Shall I proceed?

You: yes

Brian: Great! I'll coordinate with the team...
Brian: [1/3] create_prd...
Brian: ✓ create_prd complete!
Brian: [2/3] create_stories...
Brian: ✓ create_stories complete!
Brian: [3/3] implement_stories...
Brian: ✓ implement_stories complete!
Brian: 🎉 All workflows completed successfully!
```

### Multi-Turn Conversations

Build on previous requests:

```
You: I want to build a todo app

Brian: [Analyzes todo app...]

You: And then add authentication

Brian: Building on your previous request...
[Analyzes todo app + authentication together]
```

### Getting Help

```
You: help

Brian: I'm here to help you build software! Here's what I can do:

Feature Requests: Just describe what you want to build
  - "I want to add authentication"
  - "Build a todo app with a REST API"

Project Information:
  - "What's the status?" - Current project state

Commands:
  - 'help' - Show this message
  - 'exit', 'quit', 'bye' - End session
```

## Starting a New Project

If you're in a directory without a GAO-Dev project:

```
You: init

Brian: Welcome! Let's set up your new GAO-Dev project.

Creating project structure for 'my-project'...
✓ Project directories created
✓ Git repository initialized
✓ README.md created
✓ .gitignore created
✓ Initial commit created

🎉 Project 'my-project' initialized successfully!

You're all set! What would you like to build first?
```

## Tips & Tricks

### Be Natural

Brian understands natural language:
- "I want to build X"
- "Add feature Y"
- "Fix the bug in Z"
- "Help me with X"

### Use Context

Brian remembers your conversation:
- "And then add X" (builds on previous request)
- "Tell me more about that"
- "What did I just ask for?"

### Cancel Operations

Press Ctrl+C during long operations to cancel.
REPL will continue - you won't lose your session.

### Check History

Use arrow keys (up/down) to recall previous inputs.

## Exiting

Type any of these to exit gracefully:
- `exit`
- `quit`
- `bye`
- Press Ctrl+C

## Troubleshooting

### "No GAO-Dev project detected"

**Solution**: Type `init` to initialize a new project.

### "I'm not sure what you mean"

**Solution**: Rephrase your request more clearly. Try:
- "I want to build [feature]"
- "Help me [action]"

### Slow Responses

**Solution**: First response may be slow (AI analysis). Subsequent responses are faster.

### Errors During Execution

Brian will display the error and suggest next steps.
REPL continues - you can try again or ask for help.

## Advanced Usage

### Direct Commands

While most interactions are conversational, you can also:
- "show status" - Project status
- "list epics" - All epics
- "list stories for epic 5" - Stories for specific epic

### Session Context

Brian tracks:
- Current epic/story you're working on
- Pending confirmations
- Conversation history (last 100 turns)

## Further Reading

- [Examples](./EXAMPLES.md) - Common scenarios
- [Architecture](./ARCHITECTURE.md) - Technical details
- [PRD](./PRD.md) - Feature requirements
```

---

## Manual QA Scenarios

### Scenario 1: New User, First Time

**Goal**: Validate onboarding experience

**Steps**:
1. Create empty directory
2. Run `gao-dev start`
3. Observe greenfield greeting
4. Type `init`
5. Verify project initialized
6. Type "I want to build a todo app"
7. Confirm workflow execution
8. Verify workflows execute
9. Type `exit`

**Success Criteria**:
- [ ] Startup <2 seconds
- [ ] Greenfield message clear
- [ ] Initialization smooth
- [ ] Feature request analyzed correctly
- [ ] Workflows execute without error
- [ ] Exit graceful

---

### Scenario 2: Experienced User, Existing Project

**Goal**: Validate existing project experience

**Steps**:
1. Navigate to gao-agile-dev project
2. Run `gao-dev start`
3. Observe status summary
4. Type "What should I work on next?"
5. Type "I want to add a reporting feature"
6. Confirm execution
7. During execution, press Ctrl+C
8. Verify cancellation
9. Type "help"
10. Type `exit`

**Success Criteria**:
- [ ] Status accurate
- [ ] Question answered helpfully
- [ ] Feature analysis correct
- [ ] Ctrl+C cancels gracefully
- [ ] REPL continues after cancellation
- [ ] Help message useful

---

### Scenario 3: Multi-Turn Refinement

**Goal**: Validate context awareness

**Steps**:
1. Start REPL
2. Type "I want to build a blog"
3. Type "And add comments"
4. Type "Also add user profiles"
5. Confirm final plan
6. Type `exit`

**Success Criteria**:
- [ ] Each turn builds on previous
- [ ] Final analysis includes all 3 features
- [ ] Context preserved throughout
- [ ] Execution plan comprehensive

---

### Scenario 4: Error Handling

**Goal**: Validate graceful error handling

**Steps**:
1. Start REPL
2. Type gibberish: "asdfqwer zxcv"
3. Observe clarification request
4. Type valid request
5. (Simulate failure) - Manual intervention
6. Observe error message
7. Continue with different request
8. Type `exit`

**Success Criteria**:
- [ ] Unclear input handled gracefully
- [ ] Error message helpful
- [ ] REPL never crashes
- [ ] User can recover and continue

---

### Scenario 5: Performance Test

**Goal**: Validate performance targets

**Steps**:
1. Measure startup time (command to greeting)
2. Measure first analysis time
3. Measure subsequent analysis time
4. Check memory usage during session

**Success Criteria**:
- [ ] Startup <2 seconds
- [ ] First analysis <3 seconds (with AI)
- [ ] Subsequent analyses <1 second
- [ ] Memory <100MB during session

---

## Definition of Done

- [ ] 15+ integration tests written and passing
- [ ] 5 manual QA scenarios executed and documented
- [ ] User guide created and reviewed
- [ ] Examples document created
- [ ] Demo script created
- [ ] Root README updated with REPL section
- [ ] bmm-workflow-status.md updated (Epic 30 complete)
- [ ] All tests passing (unit + integration)
- [ ] Test coverage >90% for new code
- [ ] Performance targets validated (<2s startup, <1s responses)
- [ ] Code review completed
- [ ] Git commit: `feat(epic-30): Story 30.7 - Testing & Documentation (3 pts)`
- [ ] Epic 30 marked as COMPLETE

---

## Dependencies

### Internal Dependencies
- All Stories 30.1-30.6 must be complete

### No New External Dependencies

---

## Implementation Notes

### Test Coverage

**Target**: >90% for Epic 30 code

**Measure**:
```bash
pytest --cov=gao_dev.cli.chat_repl --cov=gao_dev.orchestrator.conversational_brian --cov-report=html
```

**Focus Areas**:
- ChatREPL main loop
- ConversationalBrian intent handling
- ChatSession state management
- CommandRouter execution
- GreenfieldInitializer flows

### Manual QA Documentation

**Record**:
- Screenshots of key moments
- Actual output vs expected
- Timing measurements
- User feedback notes

**Store**: In `docs/features/interactive-brian-chat/qa-results.md`

### Demo Script

**Purpose**: Showcase Epic 30 for demos, presentations
**Audience**: Stakeholders, users, developers
**Duration**: 5-10 minutes
**Content**: Highlight key features, wow moments

---

## Manual Testing Checklist

**Core Functionality**:
- [ ] REPL starts and shows greeting
- [ ] Project status detected and displayed
- [ ] Feature requests analyzed correctly
- [ ] Confirmation flow works (yes/no)
- [ ] Workflows execute end-to-end
- [ ] Multi-turn conversations use context
- [ ] Help command shows useful info
- [ ] Exit commands work gracefully

**Error Handling**:
- [ ] Unclear input → Clarification request
- [ ] Analysis failure → Error message, REPL continues
- [ ] Execution failure → Error message, REPL continues
- [ ] Ctrl+C → Cancellation message, REPL continues

**Greenfield**:
- [ ] Detects greenfield projects
- [ ] "init" command initializes project
- [ ] All directories created
- [ ] Git initialized
- [ ] README and .gitignore created

**Performance**:
- [ ] Startup <2 seconds
- [ ] First analysis <3 seconds
- [ ] Subsequent analyses <1 second
- [ ] Memory usage reasonable

**UX**:
- [ ] Formatting beautiful (Rich panels)
- [ ] Messages clear and helpful
- [ ] Progress updates informative
- [ ] Errors actionable

---

## Next Steps

After Story 30.7 is complete:

**Epic 30 is COMPLETE!** 🎉

Update status:
- Mark Epic 30 as "Complete" in bmm-workflow-status.md
- Update sprint-status.yaml
- Create Epic 30 completion retrospective (optional)

---

**Created**: 2025-11-10
**Status**: Ready to Implement
