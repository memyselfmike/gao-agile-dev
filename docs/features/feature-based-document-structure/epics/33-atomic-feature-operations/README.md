# Epic 33: Atomic Feature Operations

**Feature:** Feature-Based Document Structure
**Epic Number:** 33
**Status:** Ready
**Points:** 8
**Timeline:** Week 1.5 (Days 4-7)

---

## Overview

Extend DocumentStructureManager with QA/ folder and README.md generation, then integrate with GitIntegratedStateManager for atomic feature creation. Add user-friendly CLI commands for feature management.

This epic provides the atomic operation layer and user interface, ensuring all feature operations are guaranteed atomic (file + DB + git together or rollback) and accessible via CLI.

## Goals

1. **Enhance DocumentStructureManager**: Add QA/, README.md, auto_commit parameter
2. **Atomic Feature Creation**: GitIntegratedStateManager.create_feature() with rollback
3. **CLI Interface**: User-friendly commands (create-feature, list-features, validate-structure)

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| [33.1](stories/story-33.1.md) | Extend DocumentStructureManager | 2 | Ready |
| [33.2](stories/story-33.2.md) | Extend GitIntegratedStateManager | 4 | Ready |
| [33.3](stories/story-33.3.md) | CLI Commands | 2 | Ready |

**Total:** 8 points

## Dependencies

**Required:**
- Epic 32: State Service Integration (COMPLETE - needs StateCoordinator, services)
- Epic 28: DocumentStructureManager (COMPLETE - base functionality)
- Epic 25: GitIntegratedStateManager (COMPLETE - atomic pattern)

**Blocks:**
- Epic 34: Integration & Variables (can proceed in parallel)

## Key Components

### DocumentStructureManager Enhancements
- QA/ folder creation (all scale levels)
- README.md generation from Jinja2 template
- auto_commit parameter (backward compatible)
- Becomes helper for GitIntegratedStateManager

### GitIntegratedStateManager.create_feature()
- Pre-flight checks (git clean, feature doesn't exist, valid name)
- Atomic operation (file + DB + git together)
- Rollback on error (delete files, rollback DB, reset git)
- Single commit with conventional format

### CLI Commands
- create-feature: Wrap GitIntegratedStateManager.create_feature()
- list-features: Wrap StateCoordinator.list_features()
- validate-structure: Wrap FeaturePathValidator.validate_structure()
- Rich formatted output

## Acceptance Criteria

- [ ] DocumentStructureManager creates QA/ and README.md
- [ ] auto_commit parameter working (true/false)
- [ ] GitIntegratedStateManager.create_feature() atomic
- [ ] Rollback works correctly (no partial state)
- [ ] All 3 CLI commands working
- [ ] Rich formatting for CLI output
- [ ] All 3 stories complete (8 points)
- [ ] 90+ unit test assertions passing (20+50+20)
- [ ] 15+ integration test scenarios passing
- [ ] Performance: feature creation <1s

## Testing Summary

- **Story 33.1:** 20+ assertions (DocumentStructureManager)
- **Story 33.2:** 50+ unit + 15+ integration (GitIntegratedStateManager)
- **Story 33.3:** 20+ CLI scenarios (CLI commands)

**Total:** 90+ unit assertions + 15+ integration scenarios

## Technical Highlights

1. **Atomic Pattern:** Follow Epic 25 pattern exactly (pre-flight, checkpoint, rollback)
2. **Helper Integration:** DocumentStructureManager called with auto_commit=false
3. **All-or-Nothing:** File creation, DB insert, git commit succeed together or roll back
4. **User-Friendly CLI:** Rich formatting, clear errors, helpful suggestions

## Atomic Operation Flow

```
1. Pre-flight checks:
   - Git working tree clean?
   - Feature name valid (kebab-case)?
   - Feature doesn't exist (DB)?
   - Feature folder doesn't exist (filesystem)?

2. Create checkpoint:
   - Note current git HEAD

3. File operations:
   - Call DocumentStructureManager (auto_commit=false)
   - Creates folders and files (no git commit yet)

4. Database insert:
   - Call StateCoordinator.create_feature()
   - Insert feature record

5. Git commit:
   - Single atomic commit with all changes
   - Conventional commit format

6. Rollback on error:
   - Delete feature folder (if created)
   - Delete DB record (if inserted)
   - Git reset --hard to checkpoint
```

## CLI Command Examples

```bash
# Create feature
gao-dev create-feature user-auth --scale-level 3 --description "User authentication"

# List features
gao-dev list-features --status active

# Validate structure
gao-dev validate-structure --feature user-auth
```

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Epic 2 breakdown)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (GitIntegratedStateManager extension)
- **Epic 28:** DocumentStructureManager base implementation
- **Epic 25:** GitIntegratedStateManager atomic pattern
