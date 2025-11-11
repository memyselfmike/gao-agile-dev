# Feature: Feature-Based Document Structure Enhancement

**Status**: Planning (Post-Critical Review - Ready for Implementation)
**Created**: 2025-11-11
**Owner**: Product & Engineering Team

## Overview

This feature transforms GAO-Dev's document organization from inconsistent, ad-hoc folder structures to a rigorously enforced, feature-centric hierarchy. It introduces clear distinctions between MVP (greenfield initial scope) and subsequent features, with standardized folder structures for all documentation.

## The Problem

Current documentation is inconsistent across features:
- No MVP distinction for greenfield projects
- Mix of `docs/PRD.md` (top-level) and `docs/features/{name}/PRD.md` (feature-scoped)
- Some features use `epics.md` (single file), others use `epics/` (folder)
- QA reports scattered across features
- Variable defaults point to top-level locations

## The Solution

Enforce a standard structure for all features:

```
docs/features/
  ├── mvp/                              ← Greenfield initial scope
  │   ├── PRD.md, ARCHITECTURE.md
  │   ├── epics/, stories/, QA/
  │   └── README.md
  │
  └── {feature-name}/                   ← Each feature
      ├── PRD.md, ARCHITECTURE.md
      ├── epics/, stories/, QA/
      └── README.md
```

## Documents

- [PRD v2.0](./PRD.md) - Complete product requirements (60KB) **✅ Post-Critical Review**
- [ARCHITECTURE v3.0](./ARCHITECTURE.md) - Technical design (comprehensive) **✅ State Management Integration**
- [ARCHITECTURE_V3_STATE_INTEGRATION](./ARCHITECTURE_V3_STATE_INTEGRATION.md) - Detailed v3.0 integration specs **✅ NEW**
- [CRITICAL_ANALYSIS](./CRITICAL_ANALYSIS.md) - 67KB critical review (7 critical issues identified)
- [FIXES_SUMMARY](./FIXES_SUMMARY.md) - All fixes documented and applied

## Critical Review Results

**All 7 CRITICAL issues resolved:**
1. ✅ Extension approach (not replacement of DocumentStructureManager)
2. ✅ Git integration (reuses Epic 28's GitManager)
3. ✅ Co-located epic-story structure (epics contain stories)
4. ✅ Per-project features registry (`.gao-dev/documents.db`)
5. ✅ Stateless validator (breaks circular dependencies)
6. ✅ Clear variable naming conventions
7. ✅ WorkflowContext integration (feature_name persistence)

**Scope Reduction:** From 5 epics (40 points, 4 weeks) → **3 epics (25 points, 2 weeks)**

## Epics (Ready to Create)

**Epic Numbers: 32-34** (after Epic 31: Mary Integration)

### Epic 32: State Service Integration (Week 1) - 10 points
1. Story 32.1: Create FeatureStateService (3 pts)
2. Story 32.2: Extend StateCoordinator (2 pts)
3. Story 32.3: Create FeaturePathValidator (2 pts)
4. Story 32.4: Create FeaturePathResolver (3 pts)

### Epic 33: Atomic Feature Operations (Week 1.5) - 8 points
1. Story 33.1: Extend DocumentStructureManager (2 pts)
2. Story 33.2: Extend GitIntegratedStateManager (4 pts)
3. Story 33.3: CLI Commands (2 pts)

### Epic 34: Integration & Variables (Week 2) - 7 points
1. Story 34.1: Schema Migration (2 pts)
2. Story 34.2: Update defaults.yaml (2 pts)
3. Story 34.3: WorkflowExecutor Integration (2 pts)
4. Story 34.4: Testing & Documentation (1 pt)

## Stories

*To be created in epic folders using co-located structure (11 stories total)*

## QA Reports

*No QA artifacts yet (planning phase)*

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| PRD | ✅ Complete | v2.0 (60KB) - Post-critical review |
| Architecture | ✅ Complete | v3.0 (comprehensive) - State management integration |
| V3 Integration Specs | ✅ Complete | ARCHITECTURE_V3_STATE_INTEGRATION.md (detailed) |
| Critical Analysis | ✅ Complete | 67KB analysis, all 7 criticals resolved |
| Fixes Documentation | ✅ Complete | All fixes documented in FIXES_SUMMARY.md |
| Epics | ⏳ Ready | Epic 32-34 defined, ready to create |
| Stories | ⏳ Ready | 11 stories defined, ready to create |
| Implementation | ⏳ Pending | After epic/story files created |

## Key Benefits

1. **Predictable**: Every feature has identical structure
2. **Scalable**: Supports 100+ features without confusion
3. **Discoverable**: README.md in each feature provides index
4. **Integratable**: Cross-references work via standard paths
5. **Enforceable**: CLI scaffolding ensures compliance

## Next Steps

1. ✅ ~~Review PRD~~ - Critical analysis completed, all issues resolved
2. ✅ ~~Create Architecture~~ - v2.0 complete (comprehensive)
3. ✅ ~~Break down epics~~ - 3 epics defined (25 points, 2 weeks)
4. ⏳ **Create epic/story files** - Use co-located structure (next action)
5. ⏳ **Implement** - Build components per story breakdown

## Notes

- This feature **uses the new structure it proposes** (leading by example!)
- Located at: `docs/features/feature-based-document-structure/`
- Demonstrates: PRD.md, README.md, epics/, stories/, QA/ organization
