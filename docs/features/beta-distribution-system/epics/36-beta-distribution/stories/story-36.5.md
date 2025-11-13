# Story 36.5: GitHub Actions CI Pipeline

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Assignee**: Amelia (Developer)
**Sprint**: Sprint 1 (Week 1)

## User Story
As a developer, I want automated CI pipeline so that every push runs tests and validates code quality

## Acceptance Criteria
- [ ] `.github/workflows/ci.yml` created with matrix strategy
- [ ] Tests run on Ubuntu, Windows, macOS
- [ ] Tests run on Python 3.11 and 3.12
- [ ] Lint with ruff, type check with mypy, format check with black
- [ ] Upload coverage to Codecov
- [ ] Test: Push to branch → CI runs and passes

## Dependencies
**Upstream**: None
**Downstream**: 36.6 (Beta Release Pipeline)

## Risk Level
**Low** - Standard GitHub Actions pattern
