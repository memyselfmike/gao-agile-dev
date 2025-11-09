# Product Requirements Document: Git-Integrated Hybrid Wisdom Architecture

**Feature Name**: Git-Integrated Hybrid Wisdom Architecture
**Version**: 1.0
**Date**: 2025-11-09
**Product Manager**: John
**Status**: Draft

---

## Executive Summary

**Problem**: GAO-Dev needs a high-performance wisdom management system that provides fast context loading (<5ms) for multi-agent operations while maintaining data consistency between files and database.

**Solution**: Implement a hybrid architecture using SQLite for fast state queries and Markdown files for human-readable artifacts, with git commits as atomic transaction boundaries to ensure consistency.

**Impact**:
- 10-20x faster context loading (5ms vs 50-100ms)
- 15x less data transferred (2KB vs 31KB)
- Complete data consistency via git transaction model
- Instant existing project analysis
- Full rollback capability

**Scale**: Epic-level feature (estimated 6 weeks, 6 epics, ~46 stories)

---

## Background & Context

### Current State

GAO-Dev currently relies on file-based document tracking:
- All state stored in Markdown files
- Context loading requires reading 10+ files (50-100ms)
- No fast way to query project state
- Spinning up on existing projects requires scanning all files
- Limited performance for multi-agent ceremonies

### Research Conducted

Three comprehensive analysis documents created:
1. **HYBRID_WISDOM_ARCHITECTURE.md** - Original hybrid design
2. **HYBRID_ARCHITECTURE_RISK_ANALYSIS.md** - Risk analysis (11 categories, 5 critical risks)
3. **GIT_INTEGRATED_HYBRID_ARCHITECTURE.md** - Final solution with git integration
4. **GITMANAGER_AUDIT_AND_ENHANCEMENT.md** - Existing code audit and enhancement plan

**Key Insight**: Git commits provide atomic transaction boundaries that solve all critical consistency risks.

---

## Problem Statement

### User Stories

**As a Product Owner**, I want GAO-Dev to spin up on existing projects instantly, so I can resume work without manual context gathering.

**As Brian (Workflow Coordinator)**, I need fast access to complete epic context (<5ms), so I can coordinate multi-agent ceremonies in real-time without delays.

**As a Developer**, I need confidence that files and database are always in sync, so I don't encounter inconsistent state issues.

**As an Agent (Bob/Amelia/Murat)**, I need precisely the context relevant to my role (2KB), not everything (31KB), so I can respond quickly in ceremonies.

**As a System Administrator**, I need complete rollback capability if migration fails, so existing projects are never left in broken state.

### Pain Points

1. **Slow Context Loading**: Reading 10+ files for epic context takes 50-100ms
2. **Large Context Size**: Agents receive 31KB when they only need 2KB
3. **No Project Status Queries**: Can't quickly answer "What's the current epic progress?"
4. **No Existing Project Support**: Must manually scan all files to understand project state
5. **File-Only Scalability**: Performance degrades as project grows (O(n) file scans)

---

## Goals & Success Criteria

### Primary Goals

1. **Performance**: Epic context loads in <5ms (10-20x improvement)
2. **Precision**: Agents receive <5KB context (15x reduction)
3. **Consistency**: Files and database never out of sync
4. **Rollback**: Full recovery from failed operations
5. **Existing Projects**: Instant analysis of existing projects

### Success Criteria

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Epic context load time | 50-100ms | <5ms | Benchmark timing |
| Context data size | 31KB | <5KB | Payload measurement |
| Data consistency | Manual checking | 100% enforced | Git pre-checks |
| Rollback capability | None | 100% | Transaction tests |
| Existing project analysis | Minutes | <10ms | Database query |
| Test coverage | N/A | >80% | pytest --cov |

### Key Performance Indicators (KPIs)

- **Context Load Performance**: 95th percentile <5ms
- **Multi-Agent Ceremony Duration**: <2 minutes for 5 agents
- **Migration Success Rate**: 100% rollback on failure
- **Data Consistency**: 0 desync issues in production
- **Developer Onboarding**: <1 day to understand system

---

## Scope

### In Scope

**Epic 22: Orchestrator Decomposition & Architectural Refactoring** (Week 1)
- Decompose orchestrator god class (1000+ LOC) into focused services
- Extract WorkflowCoordinator for workflow orchestration
- Extract CeremonyOrchestrator for multi-agent ceremonies
- Extract AgentCoordinator for agent lifecycle
- Zero breaking changes (facade pattern)
- Comprehensive refactoring tests

**Epic 23: GitManager Enhancement** (Week 2, formerly Epic 1)
- Add transaction support methods (is_working_tree_clean, reset_hard, etc.)
- Add branch management methods (delete_branch, enhanced merge)
- Add file history methods (get_last_commit_for_file, etc.)
- Deprecate GitCommitManager
- Comprehensive test suite

**Epic 24: State Tables & Tracker** (Week 3, formerly Epic 2)
- Create database migration 005 (epic_state, story_state, action_items, etc.)
- Implement StateTracker service (EpicStateService, StoryStateService, etc.)
- Implement StateCoordinator facade
- Project-scoped state tracking (.gao-dev/documents.db)
- Unit tests for all state operations

**Epic 25: Git-Integrated State Manager** (Week 4, formerly Epic 3)
- Implement GitIntegratedStateManager with atomic commits
- Implement TransactionManager for file+DB atomicity
- Implement GitMigrationManager with checkpoints
- Implement GitAwareConsistencyChecker
- Implement FastContextLoader service
- Integration tests

**Epic 26: Multi-Agent Ceremonies Architecture** (Week 5, NEW)
- Implement CeremonyOrchestrator for stand-ups, retros, planning
- Implement ConversationManager for multi-agent dialogues
- Ceremony artifacts tracked as documents
- Real-time context loading for ceremonies
- Ceremony integration tests

**Epic 27: Integration & Migration** (Week 6, formerly Epic 4)
- Integrate all services with Orchestrator
- Update CLI commands to use git transactions
- Create migration tools and documentation
- Update CLAUDE.md and architecture docs
- End-to-end tests and validation
- Migration guide for existing projects

### Out of Scope (Future Work)

- Advanced analytics and reporting dashboards
- Database merge conflict resolution (v2 enhancement)
- Performance optimization beyond 5ms target
- Cross-project wisdom sharing
- ML-based learning recommendations

---

## Requirements

### Functional Requirements

#### FR-1: Git Transaction Model
**Priority**: P0 (Critical)
**Description**: Every state change operation creates an atomic git commit

**Acceptance Criteria**:
- ✅ File changes and database changes committed together
- ✅ Operation fails if working tree has uncommitted changes
- ✅ Rollback via git reset --hard on error
- ✅ All operations logged with structured commit messages
- ✅ Commit messages follow conventional commit format

**User Story**: As a developer, I want every state change to be atomic, so files and database can never get out of sync.

---

#### FR-2: State Tracking Tables
**Priority**: P0 (Critical)
**Description**: SQLite database tracks fast-query state

**Acceptance Criteria**:
- ✅ epic_state table tracks epic progress (total, completed, %)
- ✅ story_state table tracks story status (todo, in_progress, done)
- ✅ action_items table tracks ceremony action items
- ✅ ceremony_summaries table tracks ceremony outcomes
- ✅ learning_index table tracks learnings by topic
- ✅ All tables indexed for <5ms query performance

**User Story**: As Brian, I want to query epic progress in <5ms, so I can start ceremonies without delay.

---

#### FR-3: Fast Context Loading
**Priority**: P0 (Critical)
**Description**: Context loads in <5ms with precise data

**Acceptance Criteria**:
- ✅ get_epic_context(epic_num) returns in <5ms
- ✅ Context includes: progress, stories, action items, learnings
- ✅ Context size <5KB JSON
- ✅ Role-based context (agent-specific filtering)
- ✅ Cached when possible, invalidated on changes

**User Story**: As Amelia, I want my ceremony context in <5ms, so I can respond quickly without waiting.

---

#### FR-4: Consistency Enforcement
**Priority**: P0 (Critical)
**Description**: System prevents file-database desynchronization

**Acceptance Criteria**:
- ✅ Operations fail if git working tree not clean
- ✅ Consistency check command detects mismatches
- ✅ Auto-repair command syncs database to files
- ✅ Pre-operation checks validate clean state
- ✅ Post-operation validation confirms consistency

**User Story**: As a developer, I want the system to prevent inconsistency, so I never encounter desync bugs.

---

#### FR-5: Migration Safety
**Priority**: P0 (Critical)
**Description**: Safe migration with full rollback

**Acceptance Criteria**:
- ✅ Migration uses git branch (migration/hybrid-architecture)
- ✅ Phase-by-phase commits (checkpoints)
- ✅ Pre-flight validation before starting
- ✅ Rollback deletes branch and returns to checkpoint
- ✅ Migration report shows success/failure details

**User Story**: As a user, I want migration to be safe with rollback, so my project is never left broken.

---

#### FR-6: Existing Project Support
**Priority**: P1 (High)
**Description**: Analyze existing projects instantly

**Acceptance Criteria**:
- ✅ Query database for current state (<10ms)
- ✅ Return: active epics, current story, pending actions
- ✅ No need to scan/read all files
- ✅ Works on projects with 100+ epics, 1000+ stories
- ✅ Backfill historical data from files + git history

**User Story**: As a product owner, I want to spin up GAO-Dev on existing projects instantly, so I can resume work immediately.

---

### Non-Functional Requirements

#### NFR-1: Performance
- Epic context queries: <5ms (95th percentile)
- Story state updates: <10ms
- Migration backfill: <5 min for 400 stories
- Database size: <50MB for 100 epics

#### NFR-2: Reliability
- Data consistency: 100% (enforced by git)
- Migration rollback: 100% success rate
- Zero data loss on errors
- Graceful degradation if git unavailable

#### NFR-3: Maintainability
- Code coverage: >80%
- Service classes: <200 LOC each
- SOLID principles followed
- Comprehensive logging (structlog)

#### NFR-4: Scalability
- O(1) query performance (indexed)
- Handles 100+ epics, 1000+ stories
- Handles 1000+ learnings
- No performance degradation over time

#### NFR-5: Usability
- Developer onboarding: <1 day
- Clear error messages
- Comprehensive documentation
- Migration guide with examples

---

## User Experience

### Developer Workflow

```bash
# Story creation (atomic git commit)
$ gao-dev create-story --epic 5 --story 3
Creating story 5.3...
[database] Created story_state record
[git] Committed: feat(story-5.3): create story - Implement user auth
Story 5.3 created successfully (commit: a1b2c3d)

# Fast status query
$ gao-dev status
Epic 5: User Authentication
Progress: 30% (3/10 stories complete)
Current story: 5.4 (in_progress)
Active action items: 2
Recent learnings: 3

# Consistency check
$ gao-dev consistency-check
Checking file-database consistency...
[git] Working tree is clean ✓
[check] All documents exist on filesystem ✓
[check] All files registered in database ✓
[check] Epic state matches story counts ✓
Consistency check passed ✓
```

### Multi-Agent Ceremony Experience

```python
# Brian loads context (fast)
context = fast_loader.get_epic_context(epic_num=5)
# <5ms, returns 2KB precise JSON

# Brian coordinates ceremony
async def hold_standup(epic_num):
    context = fast_loader.get_epic_context(epic_num)  # Fast!

    # Each agent gets role-specific context
    bob_context = fast_loader.get_agent_context("bob", epic_num)
    amelia_context = fast_loader.get_agent_context("amelia", epic_num)

    # Ceremony executes efficiently
    # Action items stored in database + files (atomic commit)
```

---

## Technical Considerations

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Transaction Layer                    │
│  (Every operation = atomic git commit)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              GitIntegratedStateManager                      │
│  - create_story() → file + DB + git commit                  │
│  - transition_story() → DB + git commit                     │
│  - hold_ceremony() → files + DB + git commit                │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
         ┌──────────────────┐  ┌──────────────────┐
         │   StateTracker   │  │  FastContextLoader│
         │  (Write State)   │  │   (Read State)    │
         └──────────────────┘  └──────────────────┘
                    │                   │
                    ↓                   ↓
         ┌────────────────────────────────────────┐
         │        SQLite Database                 │
         │  - epic_state                          │
         │  - story_state                         │
         │  - action_items                        │
         │  - ceremony_summaries                  │
         │  - learning_index                      │
         └────────────────────────────────────────┘
```

### Database Schema

**epic_state**: Fast epic progress queries
**story_state**: Fast story status queries
**action_items**: Active action item tracking
**ceremony_summaries**: Ceremony outcomes index
**learning_index**: Topical learning index

All tables indexed for <5ms queries.

### Git Commit Strategy

One commit per operation:
- Story creation → `feat(story-5.3): create story`
- Story transition → `feat(story-5.3): transition to in_progress`
- Story completion → `feat(story-5.3): complete story - 7.5h actual`
- Ceremony → `docs(epic-5): hold stand-up - 3 action items`

### Technology Stack

- **Language**: Python 3.11+
- **Database**: SQLite 3.x (in .gao-dev/documents.db)
- **Version Control**: Git (via GitManager)
- **Logging**: structlog
- **Testing**: pytest, pytest-cov
- **Type Checking**: mypy (strict mode)

---

## Dependencies & Constraints

### Dependencies

**Existing Systems**:
- ✅ DocumentLifecycleManager (documents table, relationships)
- ✅ GitManager (core git operations) - needs enhancement
- ✅ ConfigLoader (configuration management)
- ✅ Orchestrator (agent coordination) - will integrate with new state manager

**New Systems**:
- StateTracker (creates state tables)
- FastContextLoader (reads state)
- GitIntegratedStateManager (coordinates git transactions)

### Constraints

**Technical**:
- SQLite single-writer limitation (mitigated by git serialization)
- Database must be version controlled (.gao-dev/documents.db in git)
- Windows compatibility required (no Unix-specific features)

**Business**:
- No breaking changes to existing APIs
- Backward compatibility during migration
- Must support existing projects (backfill)

**Timeline**:
- Target: 4 weeks (1 epic per week)
- Hard deadline: None (quality over speed)

---

## Risks & Mitigation

### Risk 1: SQLite Concurrency Bottleneck
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Git commit is natural serialization point
- Operations are quick (<100ms)
- If needed, implement write queue

### Risk 2: Database Size Growth
**Likelihood**: Low
**Impact**: Low
**Mitigation**:
- Implement archival strategy in v2
- Prune obsolete learnings
- Monitor database size metrics

### Risk 3: Migration Complexity
**Likelihood**: High
**Impact**: High
**Mitigation**:
- Git branch strategy with rollback
- Phase-by-phase checkpoints
- Comprehensive pre-flight validation
- Dry-run mode for testing

### Risk 4: Developer Onboarding
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Comprehensive documentation
- Clear error messages
- Training materials
- Examples in CLAUDE.md

---

## Release Plan

### Phase 1: Architectural Foundation (Week 1)
**Epic 22: Orchestrator Decomposition**
- Deliverable: Decomposed orchestrator with focused services
- Testing: Refactoring tests, zero-breaking-change validation
- Documentation: Architecture update, service documentation

### Phase 2: Git Enhancement (Week 2)
**Epic 23: GitManager Enhancement**
- Deliverable: Enhanced GitManager with 14 new methods
- Testing: Unit tests, integration tests
- Documentation: API documentation

### Phase 3: State Tracking (Week 3)
**Epic 24: State Tables & Tracker**
- Deliverable: State tables, StateCoordinator + 5 services
- Testing: Unit tests for all state operations
- Documentation: Database schema documentation

### Phase 4: Git Integration (Week 4)
**Epic 25: Git-Integrated State Manager**
- Deliverable: GitIntegratedStateManager, FastContextLoader
- Testing: Integration tests, transaction tests
- Documentation: Architecture documentation

### Phase 5: Ceremonies (Week 5)
**Epic 26: Multi-Agent Ceremonies**
- Deliverable: CeremonyOrchestrator, ConversationManager
- Testing: Ceremony integration tests
- Documentation: Ceremony workflow documentation

### Phase 6: Deployment (Week 6)
**Epic 27: Integration & Migration**
- Deliverable: Full integration, migration tools
- Testing: End-to-end tests, migration tests
- Documentation: Migration guide, updated CLAUDE.md

---

## Open Questions

1. **Q**: Should we implement database merge conflict resolution in v1?
   **A**: No, defer to v2. Git binary merge is sufficient for v1.

2. **Q**: What's the archival strategy for old state data?
   **A**: Defer to v2. Monitor database size first.

3. **Q**: Should we support multiple concurrent ceremonies?
   **A**: No, defer to v2. Sequential ceremonies are acceptable.

4. **Q**: How do we handle very large epics (50+ stories)?
   **A**: Pagination/limiting already designed in FastContextLoader.

---

## Success Metrics

**Launch Criteria** (All must pass):
- ✅ All tests passing (>80% coverage)
- ✅ Epic context loads in <5ms (95th percentile)
- ✅ Migration rollback works 100% of time
- ✅ Consistency checker detects all desync cases
- ✅ Documentation complete and reviewed

**Post-Launch Metrics** (Track for 1 month):
- Context load performance (p50, p95, p99)
- Data consistency issues (target: 0)
- Migration success rate (target: 100%)
- Developer satisfaction survey (target: 8/10)
- Production errors (target: <1 per week)

---

## Appendices

### Appendix A: Analysis Documents
- HYBRID_WISDOM_ARCHITECTURE.md
- HYBRID_ARCHITECTURE_RISK_ANALYSIS.md
- GIT_INTEGRATED_HYBRID_ARCHITECTURE.md
- GITMANAGER_AUDIT_AND_ENHANCEMENT.md

### Appendix B: Related Features
- Epic 10: Prompt & Agent Configuration Abstraction (Complete)
- Epic 18: Workflow Variable Resolution (Complete)
- Epic 20: Project-Scoped Document Lifecycle (Complete)

### Appendix C: Glossary
- **Epic State**: Fast-query table tracking epic progress
- **Story State**: Fast-query table tracking story status
- **Git Transaction**: Atomic commit bundling file + DB changes
- **FastContextLoader**: Service for <5ms context queries
- **StateTracker**: Service maintaining state tables

---

**Document Status**: Ready for Technical Specification
**Next Steps**: Winston to create Technical Specification
**Approval Required**: Technical Lead, Product Owner

---

**Version History**:
- v1.0 (2025-11-09): Initial PRD based on architecture analysis
