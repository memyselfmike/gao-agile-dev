# Story 36.4: Build Scripts & Package Validation

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Assignee**: Amelia (Developer)
**Sprint**: Sprint 1 (Week 1)

## User Story
As a developer, I want automated build scripts so that creating release packages is fast, consistent, and validated

## Acceptance Criteria
- [ ] `scripts/bump_version.py` calculates MAJOR, MINOR, PATCH correctly
- [ ] `scripts/build.sh` cleans, builds wheel, validates with twine
- [ ] `scripts/pre_release_check.sh` runs tests, type checks, git validation
- [ ] `scripts/install_local.sh` builds and installs locally
- [ ] All scripts executable and have clear output
- [ ] Test: `./scripts/build.sh` produces valid wheel in `dist/`

## Dependencies
**Upstream**: 36.1 (Dynamic Versioning)
**Downstream**: 36.6 (Beta Release Pipeline)

## Risk Level
**Low** - Standard build scripts, bash automation
