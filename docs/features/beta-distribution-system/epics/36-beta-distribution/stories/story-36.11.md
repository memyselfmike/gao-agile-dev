# Story 36.11: Update pyproject.toml Package Configuration

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 3
**Status**: Ready
**Sprint**: Sprint 2 (Week 2)

## User Story
As a developer, I want complete package-data configuration so that all necessary files are included in distributions

## Acceptance Criteria
- [ ] Package-data includes: workflows, configs, templates, migrations, `.gaodev-source`
- [ ] Exclude-package-data excludes: tests, docs, sandbox projects
- [ ] Classifiers updated to "Development Status :: 4 - Beta"
- [ ] Test: Build package, verify files included
- [ ] Test: Verify `.gaodev-source` in package

## Dependencies
**Upstream**: 36.1 (Dynamic Versioning)

## Risk Level
**Low** - Configuration changes
