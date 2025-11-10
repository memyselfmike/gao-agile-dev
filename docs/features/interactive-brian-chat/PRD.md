# Product Requirements Document: Interactive Brian Chat Interface

**Feature ID**: interactive-brian-chat
**Version**: 1.0
**Created**: 2025-11-10
**Status**: Planning
**Owner**: Product Team (John)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Goals & Success Criteria](#goals--success-criteria)
4. [User Stories](#user-stories)
5. [Epic Breakdown](#epic-breakdown)
6. [Dependencies](#dependencies)
7. [Timeline](#timeline)
8. [Risks & Mitigations](#risks--mitigations)

---

## Executive Summary

GAO-Dev has built exceptional autonomous development capabilities through Epics 22-29, including:
- Brian agent with self-learning (Epic 29)
- Multi-agent ceremonies (Epic 26)
- Git-integrated hybrid state (Epics 22-27)
- Comprehensive workflow orchestration (Epic 7.2)

However, the system currently operates through **one-shot CLI commands** rather than as a **conversational partner**. Users must know specific commands and can't have natural back-and-forth dialogue with Brian.

**Epic 30** adds the missing 5%: an **interactive REPL chat interface** where Brian becomes a true conversational intermediary between the user and the comprehensive engineering team.

**Vision**: Fire up `gao-dev start`, have Brian greet you, check project status, and engage in natural dialogue about what to work on - all within an infinite while loop that keeps Brian available until you're done.

**Impact**:
- Natural conversation instead of memorizing CLI commands
- Brian guides users through complex decisions
- Seamless project initialization for greenfield projects
- Context-aware suggestions based on project state
- Multi-turn clarifications and refinements

---

## Problem Statement

### Current State

**What Works**:
- ✅ Brian can analyze prompts and select workflows
- ✅ ConversationManager coordinates multi-agent dialogues
- ✅ CeremonyOrchestrator runs team ceremonies
- ✅ Full state management with <5ms context loading
- ✅ Self-learning from past projects
- ✅ Complete git integration

**Critical Gap**:
- ❌ **No interactive chat interface** - All commands are one-shot
- ❌ **No Brian greeting** - Can't start a conversational session
- ❌ **No project auto-detection** - User must know current state
- ❌ **No conversational flow** - Can't have back-and-forth dialogue
- ❌ **Poor discoverability** - Users must know exact command syntax

### Pain Points

**For New Users**:
- Steep learning curve - must learn CLI commands
- No guidance on what to do first
- Can't explore capabilities conversationally
- Intimidating for greenfield projects

**For Experienced Users**:
- Repetitive command typing
- No context from previous commands in session
- Can't have multi-turn refinement conversations
- Must exit and re-run commands to iterate

**For Autonomous Development**:
- Brian can't proactively suggest next steps
- No natural "what should we work on next?" flow
- Breaks immersion when switching between commands

### User Impact

**Without Epic 30**:
```bash
# User must know commands and run them one at a time
$ gao-dev create-prd --name "My Feature"
[Creates PRD, exits]

$ gao-dev create-story --epic 30 --story 1 --title "Story Title"
[Creates story, exits]

$ gao-dev implement-story --epic 30 --story 1
[Implements, exits]

# Cumbersome, not conversational, breaks flow
```

**With Epic 30**:
```bash
$ gao-dev start

Brian: Hello! I'm checking your project status...
Brian: You're in gao-agile-dev with 29 completed epics.
Brian: What would you like to work on today?

You: I want to add a new reporting feature

Brian: Analyzing... This sounds like a Level 2 feature (small, ~5-8 stories).
Brian: Would you like me to create a PRD first, or dive straight into implementation?

You: Let's create a PRD

Brian: Great! Coordinating with John (Product Manager)...
[Creates PRD]
Brian: PRD complete! Ready to break this into stories?

You: Yes

Brian: Coordinating with Bob (Scrum Master)...
[Creates stories]
Brian: I've created 6 stories. Start with story 1?

You: Yes
[... natural flow continues ...]
```

---

## Goals & Success Criteria

### Primary Goals

1. **Conversational Interface**: Natural dialogue with Brian via REPL
2. **Seamless Onboarding**: Automatic project detection and initialization
3. **Context Awareness**: Brian knows project state and suggests next steps
4. **Multi-Turn Dialogue**: Support clarifications and refinements
5. **Unified Experience**: All capabilities accessible through conversation

### Success Criteria

**Conversational Experience**:
- [ ] `gao-dev start` launches interactive REPL with Brian
- [ ] Brian greets user and summarizes project status
- [ ] Users can type natural language prompts
- [ ] Brian responds conversationally, not just output dumps
- [ ] Multi-turn clarifications work seamlessly
- [ ] Exit commands (`exit`, `quit`, `bye`) work gracefully

**Project Auto-Detection**:
- [ ] Automatically detects `.gao-dev/` in current directory or parent
- [ ] Shows summary: epic count, story count, recent commits
- [ ] Detects greenfield projects (no `.gao-dev/`)
- [ ] Offers to initialize new projects conversationally

**Command Integration**:
- [ ] All existing CLI commands accessible via conversation
- [ ] `create-prd`, `create-story`, `implement-story` work in REPL
- [ ] Ceremony commands work in REPL
- [ ] Learning and state commands work in REPL

**User Experience**:
- [ ] <2 second startup time (project detection + greeting)
- [ ] Clear prompts and visual formatting (Rich library)
- [ ] Helpful error messages with suggestions
- [ ] Session history preserved (up/down arrow keys)
- [ ] Ctrl+C gracefully exits with goodbye message

**Testing**:
- [ ] 25+ integration tests for REPL loop
- [ ] Tests for project detection logic
- [ ] Tests for conversation flow
- [ ] Tests for error handling
- [ ] Manual QA with 5+ user scenarios

---

## User Stories

### Epic 30: Interactive Brian Chat Interface

**Story 30.1**: Brian REPL Command (5 points)
- **As a** developer
- **I want** to run `gao-dev start` and enter interactive mode with Brian
- **So that** I can have conversational dialogue instead of one-shot commands

**Story 30.2**: Project Auto-Detection & Status Check (3 points)
- **As a** developer
- **I want** Brian to automatically detect my project and show status on startup
- **So that** I know where I am and what's been done

**Story 30.3**: Conversational Brian Integration (8 points)
- **As a** user
- **I want** to chat naturally with Brian about what I want to build
- **So that** Brian can analyze and recommend workflows conversationally

**Story 30.4**: Command Routing & Execution (5 points)
- **As a** developer
- **I want** all existing CLI commands to work within the chat session
- **So that** I don't lose functionality in interactive mode

**Story 30.5**: Session State Management (3 points)
- **As a** user
- **I want** Brian to remember context within our conversation
- **So that** I don't have to repeat information

**Story 30.6**: Greenfield Project Initialization (5 points)
- **As a** new user
- **I want** Brian to guide me through setting up a new project
- **So that** I can get started quickly without reading docs

**Story 30.7**: Testing & Documentation (3 points)
- **As a** developer
- **I want** comprehensive tests and clear documentation
- **So that** the REPL is reliable and users know how to use it

---

## Epic Breakdown

### Epic 30: Interactive Brian Chat Interface

**Duration**: 2 weeks (32 story points)
**Owner**: Amelia (Developer)
**Dependencies**: Epics 22-29 (all complete)

**Deliverables**:
- Interactive REPL command (`gao-dev start`)
- Project auto-detection and status reporting
- Conversational Brian integration
- Command routing for all existing commands
- Session state management
- Greenfield project initialization flow
- 25+ tests and comprehensive documentation

**Key Components**:
1. `gao_dev/cli/chat_commands.py` - REPL implementation
2. `gao_dev/orchestrator/chat_session.py` - Session state management
3. `gao_dev/cli/project_status.py` - Auto-detection and status
4. `gao_dev/orchestrator/conversational_brian.py` - Conversational wrapper
5. `tests/cli/test_chat_repl.py` - Integration tests

---

## Dependencies

### Technical Dependencies

**Required (All Complete)**:
- ✅ Epic 7.2: Brian agent and workflow selection
- ✅ Epic 26: ConversationManager for multi-agent dialogues
- ✅ Epic 27: Full orchestrator integration
- ✅ Epic 29: Self-learning and context augmentation
- ✅ Project detection utilities (from Epic 20)

**New Dependencies**:
- Python 3.11+ with asyncio support
- Rich library for terminal formatting (already in use)
- Prompt-toolkit for enhanced REPL experience (NEW)

### Feature Dependencies

**Epic 30 builds on**:
- `BrianOrchestrator.assess_and_select_workflows()` (Epic 7.2)
- `ConversationManager` for dialogue flow (Epic 26)
- `FastContextLoader` for project status (Epic 25)
- `GAODevOrchestrator` for command execution (Epic 27)
- Project detection utilities (Epic 20)

**No blockers**: All dependencies are complete and working.

---

## Timeline

**Total Duration**: 2 weeks (32 story points)

### Week 1: Foundation & Core REPL

**Monday-Tuesday**: Story 30.1 - Brian REPL Command (5 pts)
- Basic REPL loop with input/output
- Exit commands (exit, quit, bye)
- Error handling and graceful shutdown
- Basic greeting and farewell

**Wednesday**: Story 30.2 - Project Auto-Detection (3 pts)
- Detect `.gao-dev/` in current/parent directories
- Query project status (epics, stories, commits)
- Format status summary for display
- Detect greenfield projects

**Thursday-Friday + Monday**: Story 30.3 - Conversational Brian (8 pts)
- Parse natural language input
- Call Brian's `assess_and_select_workflows()`
- Present analysis conversationally
- Handle confirmation/rejection flows
- Multi-turn clarifications

**Milestone Week 1**: Basic REPL with Brian conversation working (16 pts complete)

### Week 2: Integration & Polish

**Tuesday-Wednesday**: Story 30.4 - Command Routing (5 pts)
- Route intents to existing CLI commands
- Wrap outputs conversationally
- Stream progress updates
- Handle errors gracefully

**Thursday**: Story 30.5 - Session State (3 pts)
- Track conversation history
- Context memory within session
- Support for multi-turn refinements

**Friday**: Story 30.6 - Greenfield Initialization (5 pts)
- Guide new users through setup
- Create `.gao-dev/` structure
- Initialize git repository
- Set up initial documents

**Monday**: Story 30.7 - Testing & Documentation (3 pts)
- 25+ integration tests
- Update user documentation
- Add examples and demos
- Manual QA

**Milestone Week 2**: Full interactive experience complete and tested (32 pts total)

---

## Risks & Mitigations

### Risk 1: REPL Complexity and Edge Cases

**Impact**: Medium
**Probability**: Medium

**Mitigation**:
- Use proven library (prompt-toolkit) for REPL functionality
- Start with simple loop, add features incrementally
- Comprehensive error handling from day 1
- Test edge cases (Ctrl+C, empty input, long input)

### Risk 2: Conversational Flow Feels Unnatural

**Impact**: High (UX issue)
**Probability**: Medium

**Mitigation**:
- Use rich formatting (colors, panels) to separate Brian from output
- Keep Brian's messages concise and clear
- Add personality but stay professional
- User testing with 5+ developers for feedback
- Iterate based on real usage

### Risk 3: Performance Degradation (Slow Responses)

**Impact**: Medium
**Probability**: Low

**Mitigation**:
- Fast startup (<2s) via FastContextLoader
- Async operations for analysis and execution
- Show progress indicators for long operations
- Cache Brian's context within session
- Performance tests with large projects

### Risk 4: Backward Compatibility with Existing Commands

**Impact**: High (breaking change)
**Probability**: Low

**Mitigation**:
- Keep all existing CLI commands functional
- REPL is additive, doesn't replace commands
- Document migration path for scripts
- Support both modes: interactive and one-shot
- No breaking changes to existing APIs

### Risk 5: User Confusion About Mode (REPL vs Command)

**Impact**: Medium
**Probability**: Medium

**Mitigation**:
- Clear prompts: `Brian: ` vs `$ gao-dev `
- Help command shows available actions
- Easy exit (type "exit" or Ctrl+C)
- Documentation explains both modes clearly
- Examples demonstrate when to use each

### Risk 6: Session State Leaks or Corruption

**Impact**: Medium
**Probability**: Low

**Mitigation**:
- Clear session boundaries (start/exit)
- Stateless command execution (idempotent)
- Session memory only for UI convenience
- Proper cleanup on exit
- Tests for state isolation

---

## Success Metrics

### Quantitative Metrics

**Adoption**:
- Usage rate: % of users who try `gao-dev start`
- Session duration: Average time in interactive mode
- Commands per session: Average number of operations
- Return rate: % of users who use it multiple times

**Performance**:
- Startup time: <2 seconds from command to greeting
- Response time: <1 second for Brian's analysis
- Error rate: <5% of user inputs result in errors

**User Experience**:
- Multi-turn conversations: >30% of sessions have >3 turns
- Exit satisfaction: >90% graceful exits (not Ctrl+C crashes)
- Command discovery: >50% of users discover new commands in REPL

### Qualitative Metrics

**User Satisfaction**:
- "Feels like talking to a real team lead"
- "Easier than remembering CLI commands"
- "Helped me understand what GAO-Dev can do"
- "Made onboarding to my first project smooth"

**System Intelligence**:
- Accurate intent parsing: Brian understands user goals
- Appropriate suggestions: Recommendations make sense
- Clear communication: Messages are easy to understand
- Helpful guidance: Users feel supported, not confused

---

## Acceptance Criteria (Feature-Level)

This feature is **COMPLETE** when:

1. **Interactive REPL**:
   - [ ] `gao-dev start` launches REPL successfully
   - [ ] Infinite loop continues until user exits
   - [ ] Exit commands work: `exit`, `quit`, `bye`, Ctrl+C
   - [ ] 25+ tests passing for REPL functionality

2. **Project Detection**:
   - [ ] Auto-detects `.gao-dev/` in current or parent directories
   - [ ] Shows project summary on startup
   - [ ] Detects greenfield projects and offers initialization
   - [ ] <2 second startup time

3. **Conversational Brian**:
   - [ ] Natural language prompts work
   - [ ] Brian analyzes and responds conversationally
   - [ ] Multi-turn clarifications work
   - [ ] Context preserved within session

4. **Command Integration**:
   - [ ] All existing commands work in REPL
   - [ ] Outputs formatted conversationally
   - [ ] Progress updates streamed in real-time
   - [ ] Error handling with helpful suggestions

5. **Validation**:
   - [ ] End-to-end test: New user creates first project
   - [ ] End-to-end test: Experienced user builds feature in session
   - [ ] End-to-end test: Multi-turn conversation with refinements
   - [ ] Manual QA with 5+ developers - positive feedback

---

## Future Enhancements (Out of Scope)

These are **NOT** included in Epic 30 but could be future work:

1. **Voice Interface**:
   - Voice input/output for hands-free coding
   - Integration with speech recognition APIs

2. **GUI Web Interface**:
   - Browser-based chat interface
   - Rich visualizations and dashboards

3. **Collaborative Sessions**:
   - Multi-user chat sessions
   - Team coordination via Brian

4. **Advanced NLP**:
   - Intent classification with ML models
   - Sentiment analysis for user frustration
   - Proactive suggestions based on patterns

5. **IDE Integration**:
   - VSCode extension with embedded Brian chat
   - JetBrains plugin

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical specification
- [Epic 30](./epics/epic-30-interactive-chat.md) - Epic breakdown
- [Brian Orchestrator](../../gao_dev/orchestrator/brian_orchestrator.py) - Brian implementation (Epic 7.2, 29)
- [ConversationManager](../../gao_dev/orchestrator/conversation_manager.py) - Dialogue management (Epic 26)
- [Project Detection](../../gao_dev/cli/project_detection.py) - Auto-detection utilities (Epic 20)

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial PRD created | John (Product) |

---

**Status**: Ready for Epic Planning and Story Breakdown
**Next Steps**: Create Epic 30 detailed specifications and story files
