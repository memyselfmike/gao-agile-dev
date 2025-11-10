# Interactive Brian Chat Interface

**Epics**: 30 (Chat REPL) + 31 (Full Mary Integration)
**Status**: In Progress (3/7 stories complete, 16/32 points)
**Story Points**: 32 (Epic 30) + 25 (Epic 31) = 57 points (~3.5 weeks)
**Owner**: Amelia (Developer)

---

## Overview

Epic 30 adds the final 5% layer that brings together all capabilities from Epics 22-29 into a unified **conversational interface**. Users can now chat with Brian interactively instead of memorizing CLI commands.

### What You Get

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
[... natural conversation continues ...]
```

**Key Features**:
- ✅ Natural language interaction - No memorizing commands
- ✅ Project auto-detection - Brian knows where you are
- ✅ Multi-turn conversations - Refine and clarify
- ✅ All existing commands accessible - Full feature parity
- ✅ Greenfield initialization - Guide new projects
- ✅ Beautiful terminal UI - Rich formatting

---

## Quick Start

### Prerequisites

- GAO-Dev installed (Epics 22-29 complete)
- Python 3.11+
- New dependency: `prompt-toolkit`

### Installation

```bash
# Install new dependency
pip install prompt-toolkit

# Verify installation
gao-dev --version
```

### Usage

```bash
# Start interactive chat
gao-dev start

# Or specify project directory
gao-dev start --project /path/to/project
```

### Exit

```bash
# Any of these work:
You: exit
You: quit
You: bye

# Or press Ctrl+C
```

---

## Documentation

### Core Documents

- **[PRD.md](./PRD.md)** - Product requirements, user stories, success criteria
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical design, component architecture, data flows
- **[epics/epic-30-interactive-chat.md](./epics/epic-30-interactive-chat.md)** - Epic breakdown, story overview

### Story Files

All 7 stories are documented in `stories/epic-30/`:

1. **[Story 30.1](./stories/epic-30/story-30.1.md)** - Brian REPL Command (5 pts) - ✅ COMPLETE
   - Foundation: Infinite loop, input/output, exit handling

2. **[Story 30.2](./stories/epic-30/story-30.2.md)** - Project Auto-Detection (3 pts) - ✅ COMPLETE
   - Auto-detect `.gao-dev/`, display project status on startup

3. **[Story 30.3](./stories/epic-30/story-30.3.md)** - Conversational Brian (8 pts) - ✅ COMPLETE
   - Natural language → Brian analysis → Conversational responses

4. **[Story 30.4](./stories/epic-30/story-30.4.md)** - Command Routing (5 pts) - ⏳ NEXT
   - Route intents to existing commands, stream progress

5. **[Story 30.5](./stories/epic-30/story-30.5.md)** - Session State (3 pts)
   - Remember conversation history and context

6. **[Story 30.6](./stories/epic-30/story-30.6.md)** - Greenfield & Brownfield Init (5 pts)
   - Guide new users through project setup (new or existing)

7. **[Story 30.7](./stories/epic-30/story-30.7.md)** - Testing & Docs (3 pts)
   - 25+ integration tests, user guide, examples

---

## Architecture

### Component Overview

```
┌──────────────────────────────────────┐
│      ChatREPL (Story 30.1)           │
│  Infinite loop, Rich UI, Exit logic  │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│    ChatSession (Story 30.5)          │
│  History, context, intent parsing    │
└───────┬───────────────────┬──────────┘
        │                   │
┌───────▼────────┐  ┌───────▼──────────┐
│Conversational  │  │  CommandRouter   │
│Brian (30.3)    │  │    (30.4)        │
└───────┬────────┘  └───────┬──────────┘
        │                   │
┌───────▼───────────────────▼──────────┐
│  Existing Infrastructure             │
│  Brian, GAODevOrchestrator, Workflows│
└──────────────────────────────────────┘
```

### Key Components

**ChatREPL** (`gao_dev/cli/chat_repl.py`):
- Infinite while loop for input/output
- prompt-toolkit for enhanced input (history, arrows)
- Rich for beautiful formatting
- Graceful exit handling

**ChatSession** (`gao_dev/orchestrator/chat_session.py`):
- Session state management
- Conversation history tracking
- Intent parsing and routing
- Context preservation

**ConversationalBrian** (`gao_dev/orchestrator/conversational_brian.py`):
- Wrapper around BrianOrchestrator
- Natural language → analysis → dialogue
- Multi-turn confirmation flows

**ProjectStatusReporter** (`gao_dev/cli/project_status.py`):
- Auto-detect `.gao-dev/` in current/parent directories
- Query project status (epics, stories, commits)
- Format status for display

**CommandRouter** (`gao_dev/cli/command_router.py`):
- Route intents to existing CLI commands
- Stream progress updates
- Wrap outputs conversationally

**GreenfieldInitializer** (`gao_dev/cli/greenfield_initializer.py`):
- Guide new users through project setup
- Handle both greenfield (new) and brownfield (existing) projects
- Create `.gao-dev/` structure
- Initialize git and docs

---

## Implementation Timeline

### Week 1: Foundation & Core (16 pts) - ✅ COMPLETE

**Monday-Tuesday**: Story 30.1 (5 pts) - ✅ DONE
- Basic REPL loop working
- Exit commands functional
- Rich formatting in place

**Wednesday**: Story 30.2 (3 pts) - ✅ DONE
- Project detection working
- Status displayed on startup

**Thursday-Monday**: Story 30.3 (8 pts) - ✅ DONE
- Natural language input → Brian analysis
- Conversational responses
- Multi-turn flow

**Milestone Week 1**: ✅ ACHIEVED - Can chat with Brian and get workflow recommendations

### Week 2: Integration & Polish (16 pts)

**Tuesday-Wednesday**: Story 30.4 (5 pts)
- All commands work in REPL
- Progress streaming
- Error handling

**Thursday**: Story 30.5 (3 pts)
- Session history working
- Context preserved

**Friday**: Story 30.6 (5 pts)
- Greenfield & brownfield init flow
- New user onboarding + existing project GAO-Dev tracking

**Monday**: Story 30.7 (3 pts)
- 25+ tests passing
- Documentation complete
- Manual QA done

**Milestone Week 2**: Full interactive experience complete and validated

---

## Success Criteria

### Technical

- [ ] `gao-dev start` launches successfully (<2s startup)
- [ ] Brian greets with project status
- [ ] Natural language input works
- [ ] Multi-turn conversations supported
- [ ] All existing commands accessible
- [ ] Greenfield initialization works
- [ ] 25+ tests passing (>90% coverage)
- [ ] No regressions in existing functionality

### User Experience

- [ ] Feels natural and conversational
- [ ] Easy for new users (no docs required)
- [ ] Fast and responsive (<1s for Brian analysis)
- [ ] Helpful error messages
- [ ] Beautiful terminal formatting
- [ ] Graceful exit (no crashes)

### Validation

- [ ] End-to-end test: New user creates first project
- [ ] End-to-end test: Experienced user builds feature
- [ ] End-to-end test: Multi-turn conversation with refinements
- [ ] Manual QA: 5+ developer scenarios - positive feedback

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

### Integration Tests

**Scenarios**:
1. New user: Start REPL, no project detected, initialize new
2. Existing project: Status displayed, feature request executed
3. Multi-turn: User refines request through clarifications
4. Command execution: User runs existing commands via REPL
5. Error handling: Invalid input, helpful error message
6. Graceful exit: User types "exit", sees farewell

### Manual QA

**User Scenarios**:
1. Complete beginner (first time using GAO-Dev)
2. Greenfield app (build from scratch in one session)
3. Bug fix (report and fix in one session)
4. Feature addition (add to existing project)
5. Exploration (ask questions, learn capabilities)

---

## Dependencies

### Upstream (All Complete ✅)

- **Epic 7.2**: BrianOrchestrator with workflow selection
- **Epic 26**: ConversationManager for multi-agent dialogues
- **Epic 27**: Full orchestrator integration
- **Epic 29**: Self-learning and context augmentation
- **Epic 20**: Project detection utilities
- **Epic 25**: FastContextLoader for <5ms queries

### New Dependencies

**Python Package**:
- `prompt-toolkit>=3.0.43` - Enhanced REPL

```bash
pip install prompt-toolkit
```

**No breaking changes**: All existing CLI commands continue to work.

---

## Benefits

### For New Users

- **No learning curve**: Just type what you want in natural language
- **Guided onboarding**: Brian walks you through setup
- **Discoverability**: Learn features through conversation
- **No docs required**: Brian explains as you go

### For Experienced Users

- **Faster workflow**: No typing full commands
- **Context preserved**: Session remembers what you're doing
- **Multi-turn refinement**: Clarify and iterate easily
- **Less context switching**: Stay in one session

### For GAO-Dev Project

- **Accessibility**: Makes GAO-Dev approachable for everyone
- **Adoption**: Lower barrier to entry → more users
- **Feedback**: Conversations reveal user needs
- **Showcase**: Demonstrates autonomous capabilities beautifully

---

## Risks & Mitigations

### Risk 1: REPL Feels Slow

**Mitigation**: Async operations, streaming updates, <1s response target

### Risk 2: Conversation Feels Unnatural

**Mitigation**: User testing, iterate on messages, Rich formatting

### Risk 3: Breaking Changes

**Mitigation**: REPL is additive, all existing commands still work

### Risk 4: Session State Bugs

**Mitigation**: Clear state on exit, stateless execution, tests

---

## Future Enhancements (Beyond Epic 30)

1. **Advanced NLP**: ML-based intent classification, entity extraction
2. **Voice Interface**: Speech recognition for hands-free coding
3. **Web UI**: Browser-based chat interface with visualizations
4. **Collaborative**: Multi-user sessions for team coordination
5. **IDE Integration**: VSCode/JetBrains plugins with embedded chat
6. **Proactive AI**: Brian suggests next steps without prompting

---

## References

### Internal

- [GAO-Dev Project Guide (CLAUDE.md)](../../../CLAUDE.md)
- [BMAD Workflow Status](../../../bmm-workflow-status.md)
- [Brian Orchestrator](../../../gao_dev/orchestrator/brian_orchestrator.py)
- [ConversationManager](../../../gao_dev/orchestrator/conversation_manager.py)

### External

- [prompt-toolkit Documentation](https://python-prompt-toolkit.readthedocs.io/)
- [Rich Documentation](https://rich.readthedocs.io/)

---

## Getting Help

### During Implementation

- Review story files for detailed technical guidance
- Check ARCHITECTURE.md for component design
- Reference existing ConversationManager (Epic 26)
- Ask in team chat or create GitHub issue

### For Users (Post-Implementation)

```bash
# In REPL
You: help

# Get command list
You: what can you do?

# Ask questions
You: how do I create a PRD?
```

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-10 | 1.0 | Initial documentation created | Amelia (Developer) |
| 2025-11-10 | 1.1 | Updated with Stories 30.1-30.3 complete, Story 30.6 expanded for brownfield | Bob (Scrum Master) |

---

**Status**: In Progress (Stories 30.1-30.3 Complete, 16/32 points done)
**Next Step**: Story 30.4 - Command Routing (5 pts)
**Progress**: 50% complete (Week 1 milestone achieved)
**Contact**: Amelia (Developer) for questions
