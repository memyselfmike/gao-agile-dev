# Story 36.8: BackupManager for Pre-Update Safety

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a user, I want automatic backups before updates so that I can recover if something goes wrong

## Acceptance Criteria
- [ ] `BackupManager` class with `create_backup()` and `restore_backup()`
- [ ] Backups in `.gao-dev-backups/backup_YYYYMMDD_HHMMSS/`
- [ ] `backup_metadata.json` includes timestamp, version, file list
- [ ] Old backups cleaned up (keep last 5)
- [ ] Test: Create backup → directory exists
- [ ] Test: Restore backup → original state recovered

## Risk Level
**Low** - File operations
