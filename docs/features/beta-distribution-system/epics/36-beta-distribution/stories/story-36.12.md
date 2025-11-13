# Story 36.12: Integration Testing & Cross-Platform Validation

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 8
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a developer, I want comprehensive integration tests so that beta releases work across all platforms

## Acceptance Criteria
- [ ] `test_git_url_install_separation()` - Verify complete separation
- [ ] `test_source_directory_detection()` - Error when in source
- [ ] `test_update_preserves_user_state()` - User data preserved
- [ ] `test_migration_rollback_on_failure()` - Rollback works
- [ ] All tests pass on Ubuntu, Windows, macOS
- [ ] Test coverage >90% for new code

## Dependencies
**Upstream**: All previous stories (36.1-36.11)

## Risk Level
**Medium** - Cross-platform testing
