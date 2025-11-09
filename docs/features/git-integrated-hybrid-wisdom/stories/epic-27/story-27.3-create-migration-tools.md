# Story 27.3: Create Migration Tools

**Epic**: Epic 27 - Integration & Migration
**Story ID**: 27.3
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create migration CLI commands: `gao-dev migrate` for migration, `gao-dev consistency-check` for validation, with dry-run mode and rollback support.

---

## Acceptance Criteria

- [ ] `gao-dev migrate` command created
- [ ] `gao-dev consistency-check` command created
- [ ] `--dry-run` flag for migration preview
- [ ] `--rollback` flag for migration undo
- [ ] Migration tested on real projects (at least 2 test projects)
- [ ] Progress reporting during migration
- [ ] 10 migration command tests

---

## Files to Create

- `gao_dev/cli/migration_commands.py` (~200 LOC)
- `tests/cli/test_migration_commands.py` (~180 LOC)

---

## CLI Commands

```bash
# Run migration
gao-dev migrate --dry-run  # Preview only
gao-dev migrate            # Execute migration

# Check consistency
gao-dev consistency-check          # Report issues
gao-dev consistency-check --repair  # Fix issues

# Rollback migration
gao-dev migrate --rollback
```

---

## Testing Strategy

- test_migrate_dry_run()
- test_migrate_creates_tables()
- test_migrate_backfills_epics()
- test_migrate_backfills_stories()
- test_migrate_rollback()
- test_consistency_check_detects_issues()
- test_consistency_check_repair()
- test_migration_on_real_project_1()
- test_migration_on_real_project_2()
- test_migration_progress_reporting()

---

## Definition of Done

- [ ] 10 tests passing
- [ ] Migration tested on 2+ real projects
- [ ] Git commit: "feat(epic-27): add migration CLI commands"

---

**Created**: 2025-11-09
