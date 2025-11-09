# Git-Integrated Hybrid Wisdom Architecture

**Feature Status**: Planning Complete - Ready for Implementation
**Created**: 2025-11-09
**Last Updated**: 2025-11-09 (Aligned with Gap Analysis)
**Owner**: Product Team

---

## ⚠️ IMPORTANT: UPDATED PLAN (Epics 22-27)

This feature was updated on 2025-11-09 to address critical architectural gaps identified during analysis. The plan changed from **4 epics (1-4)** to **6 epics (22-27)** to fix the orchestrator god class FIRST before adding enhancements.

**Key Changes**:
- **Epic 22 added**: Orchestrator Decomposition (MUST BE FIRST) - fixes god class
- **Epic 26 added**: Multi-Agent Ceremonies (essential, not "future work")
- **Epic numbering**: 1-4 → 22-27 (aligned with project epic numbering)
- **Duration**: 4 weeks → 6 weeks
- **Stories**: 30 → 46

**See**: [ALIGNMENT_SUMMARY.md](./ALIGNMENT_SUMMARY.md) for complete details on what changed and why.

---

## Overview

This feature implements a hybrid architecture using SQLite for fast state queries (<5ms) and Markdown files for human-readable artifacts, with git commits as atomic transaction boundaries to ensure consistency.

**Key Benefits**:
- **10-20x faster** context loading (5ms vs 50-100ms)
- **15x less data** transferred (2KB vs 31KB)
- **100% data consistency** via git transaction model
- **Full rollback capability** for safety
- **Instant existing project analysis** via database queries
- **Clean architecture** via orchestrator decomposition (Epic 22)
- **Multi-agent ceremonies** with fast context loading (Epic 26)

---

## Documentation Structure

```
git-integrated-hybrid-wisdom/
├── README.md                          # ← START HERE (this file)
├── PRD.md                             # Product Requirements Document ⭐ AUTHORITATIVE
├── ARCHITECTURE.md                    # Technical Specification ⭐ AUTHORITATIVE
├── ALIGNMENT_SUMMARY.md               # What changed and why ⭐ READ THIS
│
├── epics/                             # Epic breakdown (6 epics: 22-27)
│   ├── OVERVIEW.md                    # Epic summary, timeline, dependencies ⭐
│   ├── epic-22-orchestrator-decomposition.md    # Week 1 (8 stories) 🔴 CRITICAL
│   ├── epic-23-gitmanager-enhancement.md        # Week 2 (8 stories)
│   ├── epic-24-state-tables-tracker.md          # Week 3 (7 stories)
│   ├── epic-25-git-integrated-state-manager.md  # Week 4 (9 stories)
│   ├── epic-26-multi-agent-ceremonies.md        # Week 5 (8 stories) ⭐ NEW
│   └── epic-27-integration-migration.md         # Week 6 (6 stories)
│
├── stories/                           # Story breakdown (46 stories)
│   ├── epic-22/                       # ✅ COMPLETE (8 stories)
│   ├── epic-23/                       # To be created
│   ├── epic-24/                       # To be created
│   ├── epic-25/                       # To be created
│   ├── epic-26/                       # To be created
│   └── epic-27/                       # To be created
│
└── research/                          # 📚 Background research (reference only)
    ├── README.md
    ├── HYBRID_WISDOM_ARCHITECTURE.md
    ├── HYBRID_ARCHITECTURE_RISK_ANALYSIS.md
    ├── GIT_INTEGRATED_HYBRID_ARCHITECTURE.md
    └── GITMANAGER_AUDIT_AND_ENHANCEMENT.md
```

**Also See**: `docs/analysis/` - Comprehensive analysis documents that drove the plan:
- `GAP_ANALYSIS_SUMMARY.md` - Why Epic 22 must be first
- `ORCHESTRATION_ARCHITECTURE_REVIEW.md` - Orchestrator god class analysis
- `MULTI_AGENT_CEREMONIES_ARCHITECTURE.md` - Ceremony architecture
- `WISDOM_MANAGEMENT_INTEGRATION.md` - Document-centric wisdom system

---

## Quick Links

### 🎯 Implementation Documents (USE THESE)

**PRIMARY REFERENCES** (Read in this order):
1. **[ALIGNMENT_SUMMARY](./ALIGNMENT_SUMMARY.md)** ⭐ - What changed and why (READ FIRST)
2. **[PRD](./PRD.md)** ⭐ - Product requirements, 6 epics (22-27), success criteria
3. **[Architecture](./ARCHITECTURE.md)** ⭐ - Technical specification, component design
4. **[Epic Overview](./epics/OVERVIEW.md)** ⭐ - 6 epics, timeline, dependencies, rationale

**EPIC DOCUMENTS**:
- **[Epic 22: Orchestrator Decomposition](./epics/epic-22-orchestrator-decomposition.md)** 🔴 MUST BE FIRST
- **[Epic 23: GitManager Enhancement](./epics/epic-23-gitmanager-enhancement.md)**
- **[Epic 24: State Tables & Tracker](./epics/epic-24-state-tables-tracker.md)**
- **[Epic 25: Git-Integrated State Manager](./epics/epic-25-git-integrated-state-manager.md)**
- **[Epic 26: Multi-Agent Ceremonies](./epics/epic-26-multi-agent-ceremonies.md)** ⭐ Essential
- **[Epic 27: Integration & Migration](./epics/epic-27-integration-migration.md)**

**ANALYSIS DOCUMENTS** (in `docs/analysis/`):
- **[GAP_ANALYSIS_SUMMARY](../../analysis/GAP_ANALYSIS_SUMMARY.md)** - Why plan changed
- **[ORCHESTRATION_ARCHITECTURE_REVIEW](../../analysis/ORCHESTRATION_ARCHITECTURE_REVIEW.md)** - Epic 22 driver
- **[MULTI_AGENT_CEREMONIES_ARCHITECTURE](../../analysis/MULTI_AGENT_CEREMONIES_ARCHITECTURE.md)** - Epic 26 driver

### 📚 Research Documents (Reference Only)
Located in `research/`:
- **[Research Overview](./research/README.md)** - Explains research documents
- Historical design documents (superseded by PRD and Architecture)

---

## Feature Summary

### The Problem

**Two Major Problems Identified**:

1. **Performance Problem** (original focus):
   - Slow context loading: 50-100ms to read 10+ files
   - Large context: Agents receive 31KB when they need 2KB
   - No fast queries: Can't answer "what's epic progress?" quickly
   - No existing project support

2. **Architectural Problem** (discovered in analysis) 🔴 **CRITICAL**:
   - Orchestrator is god class (1,477 LOC)
   - Violates Single Responsibility Principle
   - Mixes 8+ different concerns
   - Makes extension and testing difficult
   - **MUST BE FIXED FIRST** before adding features

### The Solution

**Phase 1: Fix Architecture (Epic 22)** 🔴 **MUST BE FIRST**
- Decompose orchestrator god class (1,477 LOC → <300 LOC)
- Extract 4-5 focused services (<200 LOC each)
- Zero breaking changes (facade pattern)
- **Rationale**: Don't add complexity to broken architecture

**Phase 2-4: Hybrid Architecture (Epics 23-25)**
- **SQLite database** for fast state queries (<5ms)
- **Markdown files** for human-readable documentation
- **Git commits** as atomic transaction boundaries

**Phase 5: Ceremonies (Epic 26)** ⭐ **Essential**
- Multi-agent ceremonies (stand-ups, retros, planning)
- Fast context loading for real-time ceremonies
- Ceremony artifacts tracked as documents
- **Why Essential**: Generates action items, learnings, decisions (core to wisdom)

**Phase 6: Integration (Epic 27)**
- Full system integration
- CLI updates
- Migration tools
- Documentation

### Git Transaction Model

**Core Concept**: Every state change = one atomic git commit
- File changes + database changes committed together
- Rollback via `git reset --hard` on errors
- Full audit trail via git history
- 100% data consistency guaranteed

### Key Components

**Epic 22 (Architectural)**:
1. **WorkflowExecutionEngine** - Workflow execution logic
2. **ArtifactManager** - Artifact detection and registration
3. **AgentCoordinator** - Agent lifecycle management
4. **CeremonyOrchestrator** (foundation) - Ceremony coordination
5. **MetadataExtractor** - Metadata extraction utilities

**Epics 23-25 (Hybrid Architecture)**:
6. **GitManager (Enhanced)** - Transaction support, branch management, file history
7. **StateCoordinator** - Facade for 5 specialized state services
8. **FastContextLoader** - <5ms context queries from database
9. **GitIntegratedStateManager** - Atomic operations via git commits
10. **GitMigrationManager** - Safe migration with checkpoints and rollback

**Epic 26 (Ceremonies)**:
11. **CeremonyOrchestrator (Full)** - Complete ceremony system
12. **ConversationManager** - Multi-agent dialogue management

---

## Timeline & Effort

**Total Duration**: 6 weeks (1 epic per week)
**Total Stories**: 46 stories
**Total Effort**: 184-306 hours (23-38 developer-days)

```
Week 1: Epic 22 - Orchestrator Decomposition (8 stories) 🔴 CRITICAL - MUST BE FIRST
Week 2: Epic 23 - GitManager Enhancement (8 stories)
Week 3: Epic 24 - State Tables & Tracker (7 stories)
Week 4: Epic 25 - Git-Integrated State Manager (9 stories)
Week 5: Epic 26 - Multi-Agent Ceremonies (8 stories) ⭐ Essential
Week 6: Epic 27 - Integration & Migration (6 stories)
```

**Dependencies**: Sequential - each epic requires previous epics to be complete

---

## Why Epic 22 Must Be First

**The Analogy**: "Fix the engine before adding turbochargers"

**The Problem**: Orchestrator is a god class
- 1,477 LOC (should be <300)
- Violates SOLID principles
- Mixes 8 different responsibilities

**The Risk of Wrong Order**:
- ❌ Adding Epics 23-27 on top of broken architecture
- ❌ Technical debt accumulates
- ❌ Harder to refactor later
- ❌ Violates clean architecture

**The Right Order**:
- ✅ Fix architecture FIRST (Epic 22)
- ✅ Then add enhancements (23-27)
- ✅ Clean foundation for all features
- ✅ Zero breaking changes (facade pattern)

**See**: [Gap Analysis Summary](./ALIGNMENT_SUMMARY.md) for complete rationale

---

## Success Criteria

### Performance Targets
- [ ] Epic context loads in <5ms (95th percentile)
- [ ] Agent context loads in <5ms
- [ ] Story operations complete in <100ms (including git commit)
- [ ] Existing project analysis in <10ms

### Quality Targets
- [ ] >80% test coverage (200+ tests)
- [ ] All services <200 LOC (SRP compliance)
- [ ] Zero breaking changes
- [ ] Migration rollback works 100%
- [ ] Orchestrator god class eliminated (<300 LOC)

### Deliverables
- [ ] 46 stories completed across 6 epics
- [ ] Orchestrator decomposed (Epic 22)
- [ ] 5 new database tables (Epic 24)
- [ ] 12+ new services/components
- [ ] Multi-agent ceremonies functional (Epic 26)
- [ ] Migration guide complete
- [ ] Documentation updated (CLAUDE.md, etc.)

---

## Dependencies

### Existing Systems (Required)
- ✅ DocumentLifecycleManager (documents table)
- ✅ GitManager (core operations) - will be enhanced in Epic 23
- ✅ ConfigLoader (configuration)
- ✅ Orchestrator (agent coordination) - will be decomposed in Epic 22

### New Systems (Will Create)

**Epic 22**:
- WorkflowExecutionEngine
- ArtifactManager
- AgentCoordinator
- CeremonyOrchestrator (foundation)
- MetadataExtractor

**Epics 23-25**:
- GitManager (14 new methods)
- StateCoordinator + 5 state services
- FastContextLoader
- GitIntegratedStateManager
- GitMigrationManager
- GitAwareConsistencyChecker

**Epic 26**:
- CeremonyOrchestrator (full implementation)
- ConversationManager

---

## Risks & Mitigations

### Critical Risks (SOLVED)
- ✅ **Orchestrator god class** → Epic 22 (decomposition)
- ✅ **Data consistency** → Git commits bundle file + DB changes
- ✅ **Rollback capability** → Git reset --hard on errors
- ✅ **Migration safety** → Git branch with checkpoints

### Remaining Risks (Managed)
- **SQLite concurrency** → Git serialization is sufficient
- **Database size growth** → Monitor, defer archival to v2
- **Developer onboarding** → Comprehensive documentation
- **Epic 22 refactoring** → Zero-breaking-changes approach mitigates

---

## Epic Sequence & Dependencies

```
Epic 22: Orchestrator Decomposition (FOUNDATION - MUST BE FIRST)
    ↓
    ├─→ Epic 23: GitManager Enhancement
    │       ↓
    │       └─→ Epic 24: State Tables & Tracker
    │               ↓
    │               └─→ Epic 25: Git-Integrated State Manager
    │                       ↓
    │                       ├─→ Epic 26: Multi-Agent Ceremonies
    │                       │       ↓
    └───────────────────────┴──────→ Epic 27: Integration & Migration
```

**Critical Path**: 22 → 23 → 24 → 25 → 26 → 27 (all sequential)

---

## Next Steps

### Completed ✅
1. ✅ Architecture analysis (6 documents in `docs/analysis/`)
2. ✅ Gap analysis (identified Epic 22 need)
3. ✅ PRD and Technical Specification (updated for Epics 22-27)
4. ✅ Epic breakdown (all 6 epics documented)
5. ✅ Epic 22 stories (8 stories created)
6. ✅ Documentation alignment (ALIGNMENT_SUMMARY.md)

### In Progress 📝
7. 📝 **CURRENT**: Create remaining stories (Epics 23-27, 38 stories)

### Upcoming ⏳
8. ⏳ Sprint planning for Epic 22
9. ⏳ Amelia implements Epic 22 stories (Week 1)
10. ⏳ Continue with Epics 23-27 (Weeks 2-6)

---

## Contact & Ownership

**Product Manager**: John
**Technical Architect**: Winston
**Scrum Master**: Bob
**Developer**: Amelia
**QA**: Murat

**Questions?** See:
1. [ALIGNMENT_SUMMARY.md](./ALIGNMENT_SUMMARY.md) - What changed and why
2. [PRD](./PRD.md) - Product requirements
3. [Architecture](./ARCHITECTURE.md) - Technical specification
4. [Gap Analysis](../../analysis/GAP_ANALYSIS_SUMMARY.md) - Why Epic 22 is first

---

## Change Log

**2025-11-09 (v2.0 - MAJOR UPDATE)**:
- 🔴 **CRITICAL**: Updated plan from Epics 1-4 to Epics 22-27
- Added Epic 22 (Orchestrator Decomposition) - MUST BE FIRST
- Added Epic 26 (Multi-Agent Ceremonies) - Essential, not "future work"
- Updated epic numbering (1-4 → 22-27) for project alignment
- Duration: 4 weeks → 6 weeks
- Stories: 30 → 46
- Created ALIGNMENT_SUMMARY.md documenting all changes
- All epics documented with full story summaries
- Epic 22 stories created (8 stories, full detail)
- Status: Ready for Epic 23-27 story creation

**2025-11-09 (v1.0)**:
- Created feature folder structure
- Completed PRD (initial version, 4 epics)
- Completed ARCHITECTURE (initial version, 4 epics)
- Created epic overview
- Status: Superseded by v2.0

---

## Important Notes for Story Creation

**For Bob (Scrum Master)**:

When creating stories for Epics 23-27, use these CURRENT references:
- ✅ `PRD.md` - Updated for Epics 22-27
- ✅ `ARCHITECTURE.md` - Updated for Epics 22-27
- ✅ `epics/OVERVIEW.md` - Updated for 6 epics
- ✅ `epics/epic-22-orchestrator-decomposition.md` through `epic-27-integration-migration.md`
- ✅ `ALIGNMENT_SUMMARY.md` - Why plan changed
- ✅ `stories/epic-22/` - Example of story quality and detail

**DO NOT use**:
- ❌ Old plans referencing Epics 1-4
- ❌ 4-week timeline
- ❌ 30 stories estimate
- ❌ Any documents not updated on 2025-11-09

**All documents are now aligned and current as of 2025-11-09.**

---

**Feature Status**: 📋 **Planning Complete** - Ready for Story Implementation

**Next Milestone**: Complete stories for Epics 23-27 (38 stories)
**Then**: Sprint 1 - Epic 22 Implementation (Week 1)
