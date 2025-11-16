# Story 39.8: Multi-Agent Chat Switching

**Story Number**: 39.8
**Epic**: 39.3 - Core Observability
**Status**: Complete
**Priority**: MUST HAVE (P0)
**Effort**: S (Small - 2 points)
**Dependencies**: Story 39.7 (Brian Chat Component)

## User Story
As a **user**, I want **to switch between different agents** so that **I can interact with Mary, John, Winston, Sally, Bob, Amelia, or Murat based on my needs**.

## Acceptance Criteria
- [x] AC1: Agent switcher dropdown in top bar (8 agents: Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat)
- [x] AC2: Switching agent takes <100ms
- [x] AC3: Chat history persists per agent (separate contexts)
- [x] AC4: Clear indicator: "You are now chatting with Mary (Business Analyst)"
- [x] AC5: Each agent has distinct avatar/icon
- [x] AC6: Agent-specific prompts loaded from backend config
- [x] AC7: Conversation history cleared when switching (new agent context)
- [x] AC8: Last active agent saved to localStorage
- [x] AC9: Agent descriptions shown in dropdown (role + specialty)
- [x] AC10: Keyboard shortcut to open agent switcher (Cmd+K)

## Technical Context
**Backend**: ChatSession supports multi-agent contexts
**Frontend**: Zustand stores per-agent chat history
**Agents**: Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat
