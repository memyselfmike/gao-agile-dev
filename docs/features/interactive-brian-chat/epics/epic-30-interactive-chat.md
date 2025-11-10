# Epic 30: Interactive Brian Chat Interface

**Epic ID**: Epic-30
**Feature**: Interactive Brian Chat Interface
**Duration**: 2 weeks (10 working days)
**Owner**: Amelia (Developer)
**Status**: In Progress (3/7 stories complete, 16/32 points)
**Previous Epic**: Epic 29 (Self-Learning Feedback Loop)
**Story Points**: 32 (16 complete, 16 remaining)

---

## Epic Goal

Transform GAO-Dev from a one-shot CLI tool into an interactive conversational partner by adding a REPL interface where Brian greets users, checks project status, and engages in natural back-and-forth dialogue.

**Success Criteria**:
- `gao-dev start` launches interactive REPL successfully
- Brian greets user with project status summary
- Natural language input works (no memorizing commands)
- Multi-turn conversations supported
- All existing commands accessible via conversation
- Greenfield projects initialized conversationally
- 25+ integration tests passing
- <2 second startup time
- >90% test coverage

---

## Overview

This epic adds the final 5% layer that brings together all capabilities from Epics 22-29 into a unified conversational interface. It leverages:

- **Epic 7.2**: Brian's workflow selection intelligence
- **Epic 26**: ConversationManager for multi-agent dialogues
- **Epic 29**: Self-learning and context augmentation
- **Epic 27**: Full orchestrator integration
- **Epic 20**: Project detection utilities

**Why Essential**: Users need a natural way to interact with GAO-Dev. One-shot commands are cumbersome and require memorizing syntax. An interactive chat makes GAO-Dev accessible, discoverable, and delightful to use.

---

## User Stories (7 stories, 32 points)

### Story 30.1: Brian REPL Command (5 points) - ✅ COMPLETE
**Priority**: P0 (Critical - Foundation)
**Duration**: 1-2 days
**Status**: COMPLETE

**Description**:
Create `gao-dev start` command that launches an interactive REPL (Read-Eval-Print Loop) where users can have ongoing conversations with Brian.

**Acceptance Criteria**:
- ✅ `gao-dev start` command exists and works
- ✅ Infinite while loop accepts user input
- ✅ Exit commands work: `exit`, `quit`, `bye`, Ctrl+C
- ✅ Basic greeting message displayed on startup
- ✅ Farewell message displayed on exit
- ✅ Uses prompt-toolkit for enhanced input (history, arrows)
- ✅ Uses Rich for beautiful formatted output
- ✅ 8+ tests for REPL loop mechanics

**Files**:
- `gao_dev/cli/chat_repl.py` (~200 LOC)
- `gao_dev/cli/commands.py` (add `start` command)
- `tests/cli/test_chat_repl.py` (~150 LOC)

---

### Story 30.2: Project Auto-Detection & Status Check (3 points) - ✅ COMPLETE
**Priority**: P0 (Critical - User needs context)
**Duration**: 1 day
**Status**: COMPLETE

**Description**:
Automatically detect if user is in a GAO-Dev project and display status summary on REPL startup.

**Acceptance Criteria**:
- ✅ Auto-detects `.gao-dev/` in current or parent directories
- ✅ Queries FastContextLoader for project state
- ✅ Displays: project name, epic count, story count, recent commits
- ✅ Detects greenfield projects (no `.gao-dev/`)
- ✅ Formats status beautifully with Rich
- ✅ <2 second detection + status query time
- ✅ 6+ tests for detection and status formatting

**Files**:
- `gao_dev/cli/project_status.py` (~200 LOC)
- `tests/cli/test_project_status.py` (~120 LOC)

---

### Story 30.3: Conversational Brian Integration (8 points) - ✅ COMPLETE
**Priority**: P0 (Critical - Core experience)
**Duration**: 2-3 days
**Status**: COMPLETE

**Description**:
Wrap BrianOrchestrator with conversational interface that parses natural language, analyzes with Brian, and presents results as dialogue.

**Acceptance Criteria**:
- ✅ Parses natural language input (simple keyword matching)
- ✅ Calls `BrianOrchestrator.assess_and_select_workflows()`
- ✅ Formats analysis results conversationally
- ✅ Asks for user confirmation before executing workflows
- ✅ Supports multi-turn clarifications
- ✅ Handles errors gracefully with helpful messages
- ✅ Session context passed to Brian (from ChatSession)
- ✅ 10+ tests for conversational flow

**Files**:
- `gao_dev/orchestrator/conversational_brian.py` (~250 LOC)
- `tests/orchestrator/test_conversational_brian.py` (~180 LOC)

---

### Story 30.4: Command Routing & Execution (5 points)
**Priority**: P1 (High - Access existing features)
**Duration**: 1-2 days

**Description**:
Route user intents to existing CLI commands and wrap outputs conversationally.

**Acceptance Criteria**:
- [ ] Routes to `create_prd`, `create_story`, `implement_story`
- [ ] Routes to `ceremony`, `learning`, `state` commands
- [ ] Wraps outputs with conversational context ("Coordinating with John...")
- [ ] Streams progress updates in real-time
- [ ] Handles command errors gracefully
- [ ] All existing commands work in REPL
- [ ] 8+ tests for command routing

**Files**:
- `gao_dev/cli/command_router.py` (~220 LOC)
- `tests/cli/test_command_router.py` (~150 LOC)

---

### Story 30.5: Session State Management (3 points)
**Priority**: P1 (High - Better UX)
**Duration**: 1 day

**Description**:
Track conversation history and context within a session so Brian remembers what you've discussed.

**Acceptance Criteria**:
- [ ] ChatSession class stores conversation history
- [ ] Context includes: current epic, story, last action
- [ ] History preserved for session duration
- [ ] History cleared on exit
- [ ] Context passed to Brian for better responses
- [ ] Memory limit: last 100 turns to prevent bloat
- [ ] 5+ tests for session state

**Files**:
- `gao_dev/orchestrator/chat_session.py` (~180 LOC)
- `tests/orchestrator/test_chat_session.py` (~120 LOC)

---

### Story 30.6: Greenfield & Brownfield Project Initialization (5 points)
**Priority**: P1 (High - New user experience)
**Duration**: 1-2 days

**Description**:
Guide new users through project setup when no `.gao-dev/` detected, creating structure conversationally. Handle both greenfield (new projects) and brownfield (existing projects without GAO-Dev tracking) scenarios.

**Acceptance Criteria**:
- [ ] Detects when no project exists (greenfield)
- [ ] Detects existing code without `.gao-dev/` (brownfield)
- [ ] Asks for project name conversationally
- [ ] Asks for project type (web, cli, library)
- [ ] Creates `.gao-dev/` directory structure
- [ ] Initializes git repository (if not present)
- [ ] Creates initial documents (README, etc.)
- [ ] For brownfield: Scans existing codebase structure
- [ ] For brownfield: Generates documentation from existing code
- [ ] Smooth onboarding flow for both scenarios
- [ ] 8+ tests for initialization flow (greenfield + brownfield)

**Files**:
- `gao_dev/cli/greenfield_initializer.py` (~200 LOC)
- `tests/cli/test_greenfield_initializer.py` (~130 LOC)

---

### Story 30.7: Testing & Documentation (3 points)
**Priority**: P0 (Critical - Quality assurance)
**Duration**: 1 day

**Description**:
Create comprehensive integration tests and update user documentation.

**Acceptance Criteria**:
- [ ] 25+ integration tests total (across all stories)
- [ ] End-to-end test: New user flow
- [ ] End-to-end test: Feature request flow
- [ ] End-to-end test: Multi-turn conversation
- [ ] Manual QA with 5+ scenarios completed
- [ ] User guide updated with REPL usage
- [ ] Examples added to documentation
- [ ] >90% test coverage achieved

**Files**:
- `tests/cli/test_chat_integration.py` (~250 LOC)
- `docs/features/interactive-brian-chat/USER_GUIDE.md` (new)
- `docs/features/interactive-brian-chat/EXAMPLES.md` (new)
- `README.md` updates

---

## Dependencies

### Upstream Dependencies (All Complete)

- ✅ **Epic 7.2**: BrianOrchestrator with workflow selection
- ✅ **Epic 26**: ConversationManager for multi-agent dialogues
- ✅ **Epic 27**: Full orchestrator integration
- ✅ **Epic 29**: Self-learning and context augmentation
- ✅ **Epic 20**: Project detection utilities
- ✅ **Epic 25**: FastContextLoader for <5ms queries

### Story Dependencies

**Sequential Dependencies**:
- Story 30.1 → Must complete first (foundation)
- Story 30.2 → Depends on 30.1 (needs REPL to display status)
- Story 30.3 → Depends on 30.1, 30.5 (needs REPL and session)
- Story 30.4 → Depends on 30.1, 30.5 (needs REPL and session)
- Story 30.5 → Depends on 30.1 (needs REPL)
- Story 30.6 → Depends on 30.1, 30.2 (needs REPL and detection)
- Story 30.7 → Depends on 30.1-30.6 (tests all components)

**Recommended Order**:
1. 30.1 (REPL foundation)
2. 30.2 (Status) + 30.5 (Session) in parallel
3. 30.3 (Brian conversation)
4. 30.4 (Command routing)
5. 30.6 (Greenfield init)
6. 30.7 (Testing)

---

## Technical Notes

### Architecture Overview

```
┌─────────────────────────────────────────┐
│            ChatREPL (30.1)              │
│  Infinite loop, input/output, Rich UI   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         ChatSession (30.5)              │
│  State, history, intent parsing         │
└─────┬─────────────────────────┬─────────┘
      │                         │
┌─────▼────────────┐   ┌────────▼─────────┐
│ Conversational   │   │ CommandRouter    │
│ Brian (30.3)     │   │   (30.4)         │
└─────┬────────────┘   └────────┬─────────┘
      │                         │
┌─────▼─────────────────────────▼─────────┐
│      Existing Infrastructure            │
│  Brian, GAODevOrchestrator, Workflows   │
└─────────────────────────────────────────┘
```

### New Dependencies

- **prompt-toolkit**: Enhanced REPL with history, autocomplete
  ```bash
  pip install prompt-toolkit
  ```

### Performance Targets

- **Startup**: <2 seconds (project detection + greeting)
- **Response**: <1 second (Brian analysis + formatting)
- **Memory**: <100MB per session
- **Context Load**: <5ms (via FastContextLoader)

---

## Testing Strategy

### Unit Tests (Per Story)

- Story 30.1: 8 tests (REPL mechanics)
- Story 30.2: 6 tests (status detection)
- Story 30.3: 10 tests (conversation flow)
- Story 30.4: 8 tests (command routing)
- Story 30.5: 5 tests (session state)
- Story 30.6: 6 tests (initialization)
- Story 30.7: Integration tests (E2E)

**Total**: 25+ tests across all stories

### Integration Tests (Story 30.7)

**Scenarios**:
1. New user: Start REPL, see greeting, no project detected
2. Existing project: Status displayed correctly
3. Feature request: User asks for feature, Brian analyzes, execution
4. Multi-turn: User refines request through clarifications
5. Command execution: User runs existing commands via REPL
6. Greenfield: Initialize new project conversationally
7. Error handling: Invalid input, helpful error message
8. Graceful exit: User types "exit", sees farewell

### Manual QA (Story 30.7)

**User Scenarios**:
1. **Complete beginner**: Never used GAO-Dev before
2. **Greenfield app**: Build app from scratch in one session
3. **Bug fix**: Report and fix bug in one session
4. **Feature addition**: Add feature to existing project
5. **Exploration**: Ask questions, learn capabilities

---

## Success Metrics

**Completion Criteria**:
- ⏳ All 7 stories complete (32 points) - 3/7 done (16/32 points)
- ✅ `gao-dev start` launches successfully
- ✅ Brian greets user with project status
- ✅ Natural language input works
- [ ] All existing commands accessible
- [ ] Greenfield & brownfield initialization works
- ⏳ 25+ tests passing (baseline tests complete)
- ⏳ >90% test coverage
- ✅ <2 second startup time
- [ ] Manual QA passed (5+ scenarios)

**User Experience**:
- [ ] Users describe it as "natural" and "easy"
- [ ] Reduces onboarding time for new users
- [ ] Increases discoverability of features
- [ ] Makes GAO-Dev more approachable

---

## Risks & Mitigations

### Risk 1: REPL Feels Slow or Unresponsive

**Impact**: High (UX issue)
**Probability**: Medium

**Mitigation**:
- Async operations everywhere
- Show progress indicators
- Stream responses in real-time
- Cache context within session
- Performance tests with large projects

### Risk 2: Conversational Flow Feels Unnatural

**Impact**: High (UX issue)
**Probability**: Medium

**Mitigation**:
- User testing with 5+ developers
- Iterate on Brian's messages
- Keep messages concise (1-2 sentences)
- Rich formatting to separate Brian from output
- Examples in documentation

### Risk 3: Breaking Changes to Existing Commands

**Impact**: Critical
**Probability**: Low

**Mitigation**:
- REPL is additive (doesn't replace commands)
- All existing commands must work unchanged
- Integration tests validate backward compatibility
- Documentation shows both modes

### Risk 4: Session State Leaks or Bugs

**Impact**: Medium
**Probability**: Low

**Mitigation**:
- Clear session on exit
- Stateless command execution
- Tests for state isolation
- Memory limits (last 100 turns)

---

## Epic Timeline

**Week 1**: ✅ COMPLETE
- Monday-Tuesday: Story 30.1 (REPL foundation) - ✅ DONE
- Wednesday: Story 30.2 (Status) + 30.5 (Session) - ✅ 30.2 DONE
- Thursday-Friday: Story 30.3 (Conversational Brian) - ✅ DONE

**Week 2**: ⏳ IN PROGRESS
- Monday: Story 30.4 (Command routing) - ⏳ NEXT
- Tuesday: Story 30.5 (Session state) - PENDING
- Wednesday-Thursday: Story 30.6 (Greenfield & brownfield init) - PENDING
- Friday: Story 30.7 (Testing & docs) - PENDING

**Milestone**: End of Week 2 - Full interactive experience complete (50% done)

---

## References

- [PRD.md](../PRD.md) - Product requirements
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Technical architecture
- [Brian Orchestrator](../../../gao_dev/orchestrator/brian_orchestrator.py) - Existing Brian
- [ConversationManager](../../../gao_dev/orchestrator/conversation_manager.py) - Multi-agent dialogue

---

## Story Files

- [Story 30.1 - Brian REPL Command](../stories/epic-30/story-30.1.md)
- [Story 30.2 - Project Auto-Detection](../stories/epic-30/story-30.2.md)
- [Story 30.3 - Conversational Brian](../stories/epic-30/story-30.3.md)
- [Story 30.4 - Command Routing](../stories/epic-30/story-30.4.md)
- [Story 30.5 - Session State Management](../stories/epic-30/story-30.5.md)
- [Story 30.6 - Greenfield Initialization](../stories/epic-30/story-30.6.md)
- [Story 30.7 - Testing & Documentation](../stories/epic-30/story-30.7.md)

---

**Status**: In Progress (Stories 30.1-30.3 Complete, 16/32 points)
**Next Step**: Story 30.4 - Command Routing (5 pts)
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Stories 30.1-30.3 complete, Story 30.6 expanded for brownfield)
