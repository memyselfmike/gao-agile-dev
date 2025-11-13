# Story 36.7: VersionManager for Compatibility Checking

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a user, I want automatic version compatibility checks so that updates don't break my project

## Acceptance Criteria
- [ ] `VersionManager` class with `check_compatibility()` method
- [ ] Stores version in `.gao-dev/version.txt`
- [ ] Returns CompatibilityResult with status: compatible, needs_migration, incompatible
- [ ] Test: New project → initialize
- [ ] Test: Old compatible version → needs_migration
- [ ] Integration: `gao-dev start` checks compatibility

## Risk Level
**Low** - Version comparison logic
