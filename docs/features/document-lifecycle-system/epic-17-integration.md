# Epic 17: Context System Integration

**Feature:** Document Lifecycle & Context Management
**Priority:** P0 (Critical - Makes Epic 16 Functional)
**Estimated Duration:** 2-3 weeks
**Story Points:** 34 points
**Dependencies:** Epic 12 (Document Lifecycle), Epic 15 (State Database), Epic 16 (Context Persistence Layer)

---

## Overview

Epic 16 delivered a well-architected Context Persistence Layer with comprehensive tests (257 passing), but it exists in isolation. Epic 17 integrates the context system into the GAO-Dev ecosystem, making it functional and usable by agents, workflows, and users.

**Problem**: Epic 16 components are not connected to existing systems:
- Document loading is a stub (returns None)
- Database tables are fragmented across multiple DBs
- Not wired into orchestrator or workflows
- Agents cannot use the Context API
- No CLI access for users

**Solution**: Create integration stories that connect Epic 16 to Epic 12, Epic 15, orchestrator, agents, and CLI.

---

## Success Criteria

- ✅ Documents load correctly from DocumentLifecycleManager (Epic 12)
- ✅ All context tables in single unified database with Epic 15
- ✅ Workflows automatically create and persist WorkflowContext
- ✅ Agents can access context via AgentContextAPI
- ✅ Users can query/manage context via CLI
- ✅ End-to-end tests verify full integration
- ✅ Migration system handles schema upgrades
- ✅ Performance validated (<50ms operations)
- ✅ Documentation updated with working examples

---

## Epic Breakdown

### Story 17.1: Document Loading Integration (Epic 12)
**Points:** 5 | **Priority:** P0

**Goal**: Implement actual document loading via DocumentLifecycleManager

**Tasks**:
- Integrate WorkflowContext with DocumentLifecycleManager
- Implement `_load_document()` method with path resolution
- Map doc_type to DocumentType enum
- Handle document not found gracefully
- Update AgentContextAPI default loader
- Add integration tests with Epic 12

**Acceptance Criteria**:
- [ ] `context.get_prd()` returns actual PRD content
- [ ] `context.get_architecture()` returns actual architecture
- [ ] `context.get_epic_definition()` returns actual epic
- [ ] `context.get_story_definition()` returns actual story
- [ ] Document not found returns None (not error)
- [ ] Integration tests with DocumentLifecycleManager pass
- [ ] Examples in documentation work with real documents

**Files to Modify**:
- `gao_dev/core/context/workflow_context.py`
- `gao_dev/core/context/context_api.py`
- `tests/integration/test_context_document_loading.py` (new)

---

### Story 17.2: Database Unification (Epic 15)
**Points:** 5 | **Priority:** P0

**Goal**: Unify all context tables into single database with Epic 15 StateTracker

**Tasks**:
- Create unified database configuration
- Update all context modules to use shared DB path
- Fix foreign key references between tables
- Ensure workflow_context references workflow_executions
- Ensure context_usage references documents table
- Add database migration for existing installations
- Update initialization code

**Acceptance Criteria**:
- [ ] Single `gao_dev.db` contains all tables (state, context, documents)
- [ ] Foreign keys between tables validated
- [ ] ContextPersistence uses same DB as StateTracker
- [ ] ContextUsageTracker uses same DB
- [ ] ContextLineageTracker uses same DB
- [ ] Migration script moves data from old DBs
- [ ] Integration tests verify FK constraints work
- [ ] No orphaned data in separate databases

**Files to Modify**:
- `gao_dev/core/config.py` (add unified DB path)
- `gao_dev/core/context/context_persistence.py`
- `gao_dev/core/context/context_usage_tracker.py`
- `gao_dev/core/context/context_lineage.py`
- `gao_dev/core/state/state_tracker.py`
- `gao_dev/core/context/migrations/003_unify_database.sql` (new)

---

### Story 17.3: Orchestrator Integration
**Points:** 8 | **Priority:** P0

**Goal**: Wire WorkflowContext into GAODevOrchestrator lifecycle

**Tasks**:
- Create WorkflowContext at workflow start
- Persist context after each phase
- Pass context through workflow steps
- Update context with decisions/artifacts
- Transition context phases with workflow phases
- Handle workflow failures (mark context as failed)
- Add context to workflow results

**Acceptance Criteria**:
- [ ] Orchestrator creates WorkflowContext for each workflow execution
- [ ] Context persisted to database at workflow start
- [ ] Context updated after each workflow phase
- [ ] Decisions recorded in context
- [ ] Artifacts recorded in context
- [ ] Failed workflows mark context as failed
- [ ] WorkflowResult includes context_id
- [ ] Integration tests verify full workflow with context
- [ ] Benchmark workflows show context tracking

**Files to Modify**:
- `gao_dev/orchestrator/orchestrator.py`
- `gao_dev/orchestrator/workflow_results.py`
- `gao_dev/core/workflow_executor.py`
- `tests/integration/test_orchestrator_context.py` (new)

---

### Story 17.4: Agent Prompt Integration
**Points:** 5 | **Priority:** P0

**Goal**: Update agent prompts to use AgentContextAPI

**Tasks**:
- Update story_orchestrator prompts to set WorkflowContext
- Update implement_story prompt to use AgentContextAPI
- Update validate_story prompt to access context
- Add context references to agent YAML configs
- Update prompt templates with context API examples
- Test agents can access epic/architecture via API
- Document context API usage patterns

**Acceptance Criteria**:
- [ ] Story orchestrator sets WorkflowContext before agent calls
- [ ] Agents can call `get_workflow_context()` in prompts
- [ ] Agents can access `context.get_epic_definition()`
- [ ] Agents can access `context.get_architecture()`
- [ ] Agents can access `context.get_coding_standards()`
- [ ] Context usage tracked for lineage
- [ ] Agent YAML configs reference context API
- [ ] Integration tests verify agents access context
- [ ] Documentation shows agent usage examples

**Files to Modify**:
- `gao_dev/config/prompts/story_orchestrator/*.yaml`
- `gao_dev/config/prompts/tasks/implement_story.yaml`
- `gao_dev/config/prompts/tasks/validate_story.yaml`
- `gao_dev/config/agents/*.yaml` (add context API references)
- `tests/integration/test_agent_context_access.py` (new)

---

### Story 17.5: CLI Commands for Context Management
**Points:** 5 | **Priority:** P1

**Goal**: Add CLI commands for users to query and manage context

**Tasks**:
- Create `gao-dev context` command group
- Add `gao-dev context show <workflow-id>` (show context details)
- Add `gao-dev context list` (list recent contexts)
- Add `gao-dev context history <epic> <story>` (show context versions)
- Add `gao-dev context lineage <epic>` (show document lineage)
- Add `gao-dev context stats` (cache/usage statistics)
- Add `gao-dev context clear-cache` (clear context cache)
- Rich output formatting

**Acceptance Criteria**:
- [ ] `gao-dev context show <id>` displays context details
- [ ] `gao-dev context list` shows recent workflow contexts
- [ ] `gao-dev context history` shows all versions for story
- [ ] `gao-dev context lineage` generates lineage report
- [ ] `gao-dev context stats` shows cache hit rate, usage counts
- [ ] `gao-dev context clear-cache` clears ContextCache
- [ ] All commands support --json output
- [ ] Rich formatting with tables and colors
- [ ] Help text and examples for all commands
- [ ] Unit tests for all CLI commands

**Files to Create**:
- `gao_dev/cli/context_commands.py`
- `tests/cli/test_context_commands.py`

**Files to Modify**:
- `gao_dev/cli/commands.py` (register context commands)

---

### Story 17.6: Migration System
**Points:** 3 | **Priority:** P1

**Goal**: Implement database migration runner for schema upgrades

**Tasks**:
- Create MigrationRunner class
- Add schema_version table for tracking
- Implement up/down migration support
- Auto-detect and apply pending migrations
- Add rollback capability
- Create migration for database unification
- Update initialization to run migrations

**Acceptance Criteria**:
- [ ] `schema_version` table tracks applied migrations
- [ ] MigrationRunner detects pending migrations
- [ ] Migrations applied in order automatically
- [ ] Rollback support for last N migrations
- [ ] `gao-dev db migrate` CLI command
- [ ] `gao-dev db rollback` CLI command
- [ ] `gao-dev db status` shows migration status
- [ ] Migration logs show applied migrations with timestamps
- [ ] Integration tests verify migration up/down
- [ ] Existing databases migrated successfully

**Files to Create**:
- `gao_dev/core/context/migrations/runner.py`
- `gao_dev/core/context/migrations/003_unify_database.sql`
- `tests/core/context/test_migration_runner.py`

---

### Story 17.7: End-to-End Integration Tests
**Points:** 3 | **Priority:** P0

**Goal**: Comprehensive integration tests verifying full system

**Tasks**:
- Test full workflow with context (create PRD → implement story)
- Test document loading through entire stack
- Test context persistence across workflow phases
- Test lineage tracking from PRD → Architecture → Story → Code
- Test cache effectiveness (hit rates)
- Test concurrent workflow executions
- Validate performance claims (<50ms operations)
- Test failure scenarios (DB locked, documents missing)

**Acceptance Criteria**:
- [ ] E2E test: Create PRD, workflow loads it via context
- [ ] E2E test: Implement story, context tracks document usage
- [ ] E2E test: Generate lineage report showing document flow
- [ ] E2E test: Cache hit rate >80% for repeated document access
- [ ] E2E test: Concurrent workflows don't interfere
- [ ] E2E test: Missing documents handled gracefully
- [ ] Performance test: Document load <50ms (p95)
- [ ] Performance test: Context save <50ms (p95)
- [ ] Performance test: Lineage query <100ms (p95)
- [ ] All E2E tests pass consistently

**Files to Create**:
- `tests/integration/test_context_e2e.py`
- `tests/performance/test_context_performance.py`

---

## Story Dependencies

```
Story 17.1 (Document Loading) ─┐
                               ├─→ Story 17.3 (Orchestrator)
Story 17.2 (Database Unify)   ─┘        │
                                        ├─→ Story 17.4 (Agent Prompts)
Story 17.6 (Migrations)        ─────────┤
                                        │
Story 17.5 (CLI Commands)      ─────────┤
                                        │
                                        └─→ Story 17.7 (E2E Tests)
```

**Critical Path**: 17.1 → 17.2 → 17.3 → 17.4 → 17.7

**Parallel Work Possible**:
- Story 17.5 (CLI) can be done alongside 17.3/17.4
- Story 17.6 (Migrations) can be done alongside 17.1/17.2

---

## Recommended Sprint Breakdown

### Sprint 1 (Week 1): Foundation
- Story 17.1: Document Loading (5 pts)
- Story 17.2: Database Unification (5 pts)
- **Total: 10 points**
- **Goal**: Core integrations working

### Sprint 2 (Week 2): System Integration
- Story 17.3: Orchestrator Integration (8 pts)
- Story 17.6: Migration System (3 pts)
- **Total: 11 points**
- **Goal**: Workflows use context

### Sprint 3 (Week 3): User Access & Validation
- Story 17.4: Agent Prompt Integration (5 pts)
- Story 17.5: CLI Commands (5 pts)
- Story 17.7: E2E Tests (3 pts)
- **Total: 13 points**
- **Goal**: System complete and validated

---

## Total Effort Summary

| Story | Points | Duration | Priority |
|-------|--------|----------|----------|
| 17.1: Document Loading | 5 | 1 week | P0 |
| 17.2: Database Unification | 5 | 1 week | P0 |
| 17.3: Orchestrator Integration | 8 | 1.5 weeks | P0 |
| 17.4: Agent Prompt Integration | 5 | 1 week | P0 |
| 17.5: CLI Commands | 5 | 1 week | P1 |
| 17.6: Migration System | 3 | 0.5 weeks | P1 |
| 17.7: E2E Integration Tests | 3 | 0.5 weeks | P0 |
| **TOTAL** | **34 points** | **2-3 weeks** | - |

---

## Risks & Mitigations

### Risk 1: Epic 12 Not Complete
**Likelihood:** Medium | **Impact:** Critical

**Mitigation**:
- Verify Epic 12 DocumentLifecycleManager is stable
- Create mock DocumentLifecycleManager for testing
- Document exact Epic 12 dependencies needed

### Risk 2: Database Migration Breaks Existing Data
**Likelihood:** Medium | **Impact:** High

**Mitigation**:
- Backup database before migration
- Extensive testing of migration scripts
- Rollback capability required
- Dry-run mode to preview changes

### Risk 3: Performance Degradation
**Likelihood:** Low | **Impact:** Medium

**Mitigation**:
- Performance tests as acceptance criteria
- Benchmark before/after integration
- Optimize hot paths identified in profiling
- Cache aggressively

### Risk 4: Breaking Changes to Existing Workflows
**Likelihood:** Low | **Impact:** Critical

**Mitigation**:
- Backwards compatibility tests
- Feature flags for gradual rollout
- Extensive integration testing
- Rollback plan if issues found

---

## Success Metrics

### Functional Metrics
- ✅ All 7 stories complete with >80% test coverage
- ✅ 100% of integration tests passing
- ✅ All Epic 16 components wired into system
- ✅ Agents successfully use Context API
- ✅ CLI commands functional

### Performance Metrics
- ✅ Document load <50ms (p95)
- ✅ Context save <50ms (p95)
- ✅ Lineage query <100ms (p95)
- ✅ Cache hit rate >80%

### Quality Metrics
- ✅ Zero regression bugs in existing features
- ✅ No database corruption issues
- ✅ All foreign key constraints validated
- ✅ Documentation accurate and complete

---

## Post-Epic 17 State

**What Will Work**:
1. ✅ Workflows automatically create and persist context
2. ✅ Agents access PRD/Architecture/Epic via Context API
3. ✅ Document lineage tracked from PRD → Code
4. ✅ Users query context via CLI
5. ✅ Single unified database for all GAO-Dev state
6. ✅ Migration system handles schema upgrades
7. ✅ Full end-to-end validation

**Production Ready**: **100%**
- ✅ All integrations complete
- ✅ All tests passing
- ✅ Documentation accurate
- ✅ Performance validated
- ✅ Migration path established

---

## Next Steps

After Epic 17, the Context System will be fully operational. Future enhancements could include:

- **Epic 18**: Meta-Prompt System (use context in @doc: references)
- **Epic 19**: Advanced Context Features (AI-powered context suggestions, auto-tagging)
- **Epic 20**: Context Analytics (usage patterns, optimization recommendations)

---

**Epic Owner**: TBD
**Start Date**: TBD
**Target Completion**: 3 weeks from start
**Status**: PROPOSED

---

**Dependencies Summary**:
- **Requires**: Epic 12 (complete), Epic 15 (complete), Epic 16 (complete)
- **Blocks**: Meta-Prompt System, Advanced Context Features
- **Integrates With**: All existing GAO-Dev components
