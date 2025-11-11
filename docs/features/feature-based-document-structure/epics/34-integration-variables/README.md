# Epic 34: Integration & Variables

**Feature:** Feature-Based Document Structure
**Epic Number:** 34
**Status:** Ready
**Points:** 7
**Timeline:** Week 2 (Days 8-10)

---

## Overview

Complete the feature-based structure with database migration, updated variable defaults, WorkflowExecutor integration, and comprehensive testing. Ensures all workflows use co-located paths and provides migration guide for existing projects.

This epic finalizes the system integration, updating all configuration and providing comprehensive end-to-end validation.

## Goals

1. **Database Migration**: features table with triggers and audit trail
2. **Variable Defaults**: Update defaults.yaml with co-located epic-story paths
3. **WorkflowExecutor Integration**: Use FeaturePathResolver, pass WorkflowContext
4. **Documentation & Testing**: E2E tests, migration guide, CLAUDE.md updates

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| [34.1](stories/story-34.1.md) | Schema Migration | 2 | Ready |
| [34.2](stories/story-34.2.md) | Update defaults.yaml | 2 | Ready |
| [34.3](stories/story-34.3.md) | WorkflowExecutor Integration | 2 | Ready |
| [34.4](stories/story-34.4.md) | Testing & Documentation | 1 | Ready |

**Total:** 7 points

## Dependencies

**Required:**
- Epic 32: State Service Integration (COMPLETE - needs FeaturePathResolver)
- Epic 33: Atomic Feature Operations (COMPLETE - needs CLI for migration)
- Epic 18: WorkflowExecutor (COMPLETE - base functionality)

**Blocks:**
- None (final epic in feature)

## Key Components

### Schema Migration
- features table creation
- Indexes for performance
- Triggers (auto-timestamps, audit trail)
- features_audit table
- Idempotent and rollback-capable

### defaults.yaml Updates
- All paths feature-scoped
- Co-located epic-story structure
- Clear naming convention (_location, _folder, _overview)
- Backward compatibility (legacy_* paths)

### WorkflowExecutor Integration
- FeaturePathResolver integration
- WorkflowContext passed to resolver
- 6-level feature_name resolution
- Fallback to legacy paths

### Testing & Documentation
- End-to-end test suite (5+ scenarios)
- Migration guide
- CLAUDE.md updates
- CLI help text

## Acceptance Criteria

- [ ] Migration script creates features table with triggers
- [ ] defaults.yaml has all co-located paths
- [ ] WorkflowExecutor resolves feature_name intelligently
- [ ] E2E tests cover greenfield, feature creation, validation
- [ ] Migration guide comprehensive
- [ ] CLAUDE.md updated with feature commands
- [ ] All 4 stories complete (7 points)
- [ ] 50+ test assertions passing
- [ ] No regressions in existing functionality

## Testing Summary

- **Story 34.1:** Migration tests (fresh DB, existing DB, idempotency, rollback, triggers)
- **Story 34.2:** Validation tests (30+ assertions - path resolution, naming, compatibility)
- **Story 34.3:** Integration tests (15+ cases - all priority levels, context persistence)
- **Story 34.4:** E2E tests (5+ scenarios - greenfield, flow, validation, concurrency, recovery)

**Total:** 50+ test assertions across all levels

## Technical Highlights

1. **Database Safety:** Idempotent migration with rollback capability
2. **Audit Trail:** All feature changes logged to features_audit table
3. **Co-Located Paths:** Epics contain their stories (intuitive navigation)
4. **Context Persistence:** feature_name set once, persists across workflow steps
5. **Backward Compatible:** Legacy paths available, no breaking changes

## Migration Flow

```
1. Run migration:
   gao-dev migrate

2. Create features for existing work:
   gao-dev create-feature mvp --scope mvp

3. Migrate documents:
   mv docs/PRD.md docs/features/mvp/PRD.md
   mv docs/ARCHITECTURE.md docs/features/mvp/ARCHITECTURE.md

4. Validate structure:
   gao-dev validate-structure --feature mvp

5. Fix any violations:
   (add missing files/folders as reported)
```

## Variable Examples

**Before (Legacy):**
```yaml
prd_location: "docs/PRD.md"
epic_location: "docs/epics.md"
story_folder: "docs/stories"
```

**After (Feature-Based):**
```yaml
prd_location: "docs/features/{{feature_name}}/PRD.md"
epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"
story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"
story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"
```

## End-to-End Test Scenarios

1. **Greenfield MVP Creation**
   - Create MVP feature → verify structure → validate compliance

2. **Feature → Epic → Story Flow**
   - Create feature → create epic (linked) → create story (co-located)

3. **Validation**
   - Test compliant feature → test non-compliant feature

4. **Concurrency**
   - Create 3 features concurrently → verify thread safety

5. **Error Recovery**
   - Trigger error → verify rollback → verify no partial state

## Documentation Deliverables

1. **MIGRATION_GUIDE.md**: Step-by-step migration instructions
2. **USER_GUIDE.md**: How to use feature-based structure
3. **CLAUDE.md updates**: New commands, updated structure diagrams
4. **CLI help text**: Comprehensive examples for all commands

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Epic 3 breakdown)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Complete integration)
- **Epic 18:** WorkflowExecutor base implementation
- **Epic 20:** Per-project database pattern
