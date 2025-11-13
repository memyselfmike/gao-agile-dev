# Story 36.9: Migration Transaction Safety

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 8
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a user, I want database migrations to be atomic so that failed updates roll back automatically

## Acceptance Criteria
- [ ] `MigrationRunner` with transaction-based migrations
- [ ] Creates backup before migration
- [ ] Records migrations in `schema_version` table
- [ ] On error: Rollback transaction, restore backup
- [ ] Test: All migrations succeed → version updated
- [ ] Test: One migration fails → all rolled back

## Dependencies
**Upstream**: 36.8 (BackupManager)

## Risk Level
**Medium** - Transaction handling, error recovery
