# Story 15.5: Import Existing Data

**Epic:** 15 - State Tracking Database
**Story Points:** 5 | **Priority:** P0 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Import existing sprint-status.yaml and story markdown files into database. One-time migration to transition from file-based to database-backed state tracking.

---

## Acceptance Criteria

### Import Sources
- [ ] Import `docs/sprint-status.yaml` structure
- [ ] Import all story files from `docs/stories/epic-*/story-*.md`
- [ ] Import epic definitions from `docs/features/*/epics.md`
- [ ] Import workflow status from `docs/bmm-workflow-status.md`

### Validation
- [ ] Validate all imported data
- [ ] Check for data consistency (epic exists before stories)
- [ ] Detect duplicate entries
- [ ] Report import errors clearly

### Migration Script
- [ ] CLI command: `gao-dev state import`
- [ ] Dry-run mode (preview without committing)
- [ ] Rollback capability
- [ ] Idempotent (can run multiple times safely)
- [ ] Backup created before migration

### Post-Import
- [ ] Verify data integrity
- [ ] Generate migration report
- [ ] Compare counts (files vs database rows)

**Files to Create:**
- `gao_dev/core/state/importer.py`
- `gao_dev/cli/state_import_commands.py`
- `tests/core/state/test_importer.py`

**Dependencies:** Story 15.3 (Markdown Syncer)

---

## Definition of Done

- [ ] All data imported successfully
- [ ] Validation passing
- [ ] Migration script tested
- [ ] Documentation complete
- [ ] Committed with atomic commit
