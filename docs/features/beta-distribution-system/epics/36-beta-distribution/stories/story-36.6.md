# Story 36.6: GitHub Actions Beta Release Pipeline

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 8
**Status**: Ready
**Assignee**: Amelia (Developer)
**Sprint**: Sprint 1 (Week 1)

## User Story
As a developer, I want automatic beta releases on push to main so that testers get updates within minutes

## Acceptance Criteria
- [ ] `.github/workflows/beta-release.yml` created
- [ ] Calculates next version from commits (feat→minor, fix→patch)
- [ ] Adds `-beta.1` suffix to version
- [ ] Generates changelog using git-cliff
- [ ] Creates git tag (e.g., `v0.2.0-beta.1`)
- [ ] Creates GitHub Release with changelog
- [ ] Attaches wheel files to release
- [ ] Test: Push feat commit → New beta version released

## Dependencies
**Upstream**: 36.1 (Dynamic Versioning), 36.3 (Changelog), 36.4 (Build Scripts)
**Downstream**: None

## Risk Level
**Medium** - Workflow orchestration, secrets configuration
