# Story 36.10: Health Check System

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a user, I want post-update health checks so that I know my installation is working correctly

## Acceptance Criteria
- [ ] `HealthCheck` class with `run_post_update_check()`
- [ ] Checks: config files, database schema, workflows, agents, git
- [ ] CLI command: `gao-dev health-check` with `--verbose`
- [ ] Test: All checks pass → success message
- [ ] Test: Missing config → detailed error with fix

## Risk Level
**Low** - Validation logic
