# Epic 27: Integration & Migration

**Epic ID**: Epic-GHW-27
**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Duration**: Week 6 (5 days)
**Owner**: Amelia (Developer) + Bob (Scrum Master)
**Status**: Planning
**Previous Epic**: All Epics 22-26

---

## Epic Goal

Integrate all services with orchestrator, update CLI commands, create migration tools, and complete documentation.

**Success Criteria**:
- Full orchestrator integration complete
- CLI commands updated to use git transactions
- Migration tools tested on real projects
- Documentation complete (CLAUDE.md, migration guide)
- 15+ E2E tests passing
- >80% overall test coverage
- All performance targets met

---

## Overview

This is the final epic that brings everything together and enables full production deployment.

### Key Deliverables

1. **Orchestrator Integration**: All services integrated
2. **CLI Updates**: Commands use git transactions
3. **Migration Tools**: Safe migration for existing projects
4. **Documentation**: Complete user and developer docs
5. **E2E Tests**: Full workflow validation
6. **Performance Validation**: All targets met

---

## User Stories (6 stories)

### Story 27.1: Integrate All Services with Orchestrator
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Integrate all services (Epics 22-26) with the main orchestrator.

**Acceptance Criteria**:
- [ ] WorkflowExecutionEngine integrated
- [ ] ArtifactManager integrated
- [ ] AgentCoordinator integrated
- [ ] GitIntegratedStateManager integrated
- [ ] CeremonyOrchestrator integrated
- [ ] All integrations tested
- [ ] 10 integration tests

---

### Story 27.2: Update CLI Commands
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Update CLI commands to use git-integrated state manager.

**Acceptance Criteria**:
- [ ] create_prd uses git transactions
- [ ] create_story uses git transactions
- [ ] implement_story uses git transactions
- [ ] All commands create atomic commits
- [ ] CLI tests updated
- [ ] 8 CLI tests

---

### Story 27.3: Create Migration Tools
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Create migration tools and CLI commands for existing projects.

**Acceptance Criteria**:
- [ ] gao-dev migrate command
- [ ] gao-dev consistency-check command
- [ ] Migration dry-run mode
- [ ] Rollback support
- [ ] Migration tested on real projects
- [ ] 10 migration tests

---

### Story 27.4: End-to-End Tests
**Priority**: P0 (Critical)
**Estimate**: 8 hours

**Description**:
Create comprehensive E2E tests for complete workflows.

**Acceptance Criteria**:
- [ ] E2E: Create epic to completion
- [ ] E2E: Ceremony with context loading
- [ ] E2E: Existing project migration
- [ ] E2E: Error recovery and rollback
- [ ] E2E: Multi-story workflow
- [ ] 15 E2E tests

---

### Story 27.5: Performance Validation
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Validate all performance targets are met.

**Acceptance Criteria**:
- [ ] Epic context <5ms (p95)
- [ ] Agent context <5ms (p95)
- [ ] Story creation <100ms
- [ ] Story transition <50ms
- [ ] Database size acceptable
- [ ] 10 performance benchmarks

---

### Story 27.6: Documentation & Migration Guide
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Complete all documentation for production release.

**Acceptance Criteria**:
- [ ] Update CLAUDE.md with new architecture
- [ ] Migration guide complete
- [ ] API documentation complete
- [ ] Troubleshooting guide
- [ ] Examples and tutorials

**Files**:
- CLAUDE.md (update)
- docs/features/git-integrated-hybrid-wisdom/MIGRATION_GUIDE.md (new)
- docs/features/git-integrated-hybrid-wisdom/API.md (new)
- docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md (new)

---

## Dependencies

**Upstream**: All previous epics (22-26)

**Downstream**: None (final epic)

---

## Technical Notes

### Integration Points

1. **Orchestrator → Services**:
   - Facade delegates to all services
   - No direct service coupling

2. **CLI → Orchestrator**:
   - Commands use orchestrator facade
   - Git transactions automatic

3. **Migration → All Services**:
   - Migration uses GitMigrationManager
   - Backfills all state tables
   - Validates consistency

---

## Testing Strategy

**Integration Tests**: 10

**CLI Tests**: 8

**Migration Tests**: 10

**E2E Tests**: 15

**Performance Benchmarks**: 10

**Total**: 53+ tests

---

## Success Metrics

- [ ] All integrations complete
- [ ] CLI commands updated
- [ ] Migration tools working
- [ ] 53+ tests passing
- [ ] >80% overall coverage
- [ ] All performance targets met
- [ ] Documentation complete

---

## Launch Checklist

**Pre-Launch**:
- [ ] All 200+ tests passing
- [ ] Performance targets validated
- [ ] Migration tested on 3+ real projects
- [ ] Documentation reviewed
- [ ] Zero breaking changes confirmed

**Post-Launch**:
- [ ] Monitor performance metrics
- [ ] Track migration success rate
- [ ] Collect user feedback
- [ ] Address issues promptly

---

**Epic Status**: Planning (Awaiting all previous epics)
**Next Step**: Complete Epics 22-26 first
**Created**: 2025-11-09
