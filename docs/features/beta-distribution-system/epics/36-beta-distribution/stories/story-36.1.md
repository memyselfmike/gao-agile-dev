# Story 36.1: Dynamic Versioning with setuptools-scm

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 3
**Status**: Done
**Assignee**: Amelia (Developer)
**Sprint**: Sprint 1 (Week 1)
**Completed**: 2025-11-13

---

## User Story

As a developer, I want automatic version calculation from git tags so that I never have to manually update pyproject.toml

---

## Description

Configure setuptools-scm to derive package version from git tags, eliminating manual version updates. This is the foundation for automated versioning - git tags become the single source of truth for all version information.

---

## Technical Context

- Update `pyproject.toml` to use dynamic versioning
- Add setuptools-scm to build dependencies
- Configure version scheme (post-release) and local scheme (node-and-date)
- Test that version is correctly derived from git tags
- **Files**: `pyproject.toml`, `scripts/bump_version.py`

---

## Acceptance Criteria

- [x] `pyproject.toml` configured with `dynamic = ["version"]`
- [x] `[tool.setuptools_scm]` section added with correct schemes
- [x] `scripts/bump_version.py` calculates semantic versions correctly
- [x] Test: Tag repo with `v0.1.0-beta.1` → package version matches
- [x] Test: Build package → version in wheel filename is correct
- [x] Test: No manual version field in pyproject.toml
- [x] Documentation: Comment in pyproject.toml explaining dynamic versioning

---

## Testing Notes

```bash
# Test version calculation
python scripts/bump_version.py 0.1.0 minor  # → 0.2.0
python scripts/bump_version.py 0.1.0 patch  # → 0.1.1

# Test setuptools-scm
git tag v0.1.0-beta.1
python -m build
# Check dist/ for correct version
```

---

## Implementation Steps

1. Update `pyproject.toml`:
   - Remove static `version = "1.0.0"` line
   - Add `dynamic = ["version"]` to `[project]`
   - Add `[tool.setuptools_scm]` section with schemes
   - Update `build-system.requires` to include `setuptools-scm>=8.0`

2. Verify `scripts/bump_version.py` exists and works

3. Test version derivation:
   - Create test tag
   - Build package
   - Verify version in wheel filename

4. Add documentation comment explaining dynamic versioning

---

## Dependencies

**Upstream**: None (foundational story)
**Downstream**: 36.4 (Build Scripts), 36.6 (Beta Release Pipeline)

---

## Risk Level

**Low** - Industry-standard tool, well-documented, widely used

---

## Definition of Done

- [x] Code changes committed and pushed
- [x] All acceptance criteria met
- [x] Tests pass locally (20/20 tests passing)
- [ ] CI pipeline passes (pending push)
- [ ] Code reviewed and approved (pending review)
- [x] Documentation updated (comments in pyproject.toml)
- [x] Story marked as complete in tracking
