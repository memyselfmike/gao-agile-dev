# Story 36.2: Source Repository Detection & Prevention

**Epic**: 36 - Beta Distribution and Update Management System
**Story Points**: 5
**Status**: Ready
**Assignee**: Amelia (Developer)
**Sprint**: Sprint 1 (Week 1)

---

## User Story

As a user, I want clear errors when running from GAO-Dev source directory so that I never accidentally operate on the wrong repository

---

## Description

Implement source repository detection to prevent the critical repo confusion problem. Add checks to `project_detection.py` that identify GAO-Dev's source repository and raise clear, actionable errors with installation/usage instructions.

This solves the core problem where beta testers clone GAO-Dev and run commands from the source directory, causing git operations to affect GAO-Dev's repo instead of their project.

---

## Technical Context

- Create `.gaodev-source` marker file in repo root
- Update `gao_dev/cli/project_detection.py` with `_is_gaodev_source_repo()` check
- Add `GAODevSourceDirectoryError` exception with helpful message
- Update package-data in pyproject.toml to include `.gaodev-source`
- **Files**: `.gaodev-source`, `gao_dev/cli/project_detection.py`, `pyproject.toml`

---

## Acceptance Criteria

- [ ] `.gaodev-source` marker file created with explanation comment
- [ ] `_is_gaodev_source_repo()` checks for distinctive markers:
  - `.gaodev-source`
  - `gao_dev/orchestrator/orchestrator.py`
  - `docs/bmm-workflow-status.md`
- [ ] `detect_project_root()` raises `GAODevSourceDirectoryError` when in source repo
- [ ] Error message includes:
  - Problem explanation
  - Correct installation command
  - Correct usage command
- [ ] Test: Running `gao-dev start` from source directory → clear error
- [ ] Test: Running from user project → works correctly
- [ ] Test: Running with `--project /path/to/user/project` → works
- [ ] `.gaodev-source` included in package-data (appears in installed package)

---

## Test Scenarios

### Scenario 1: Source Directory Detection
```bash
cd /path/to/gao-agile-dev  # GAO-Dev source repo
gao-dev start
# Expected: GAODevSourceDirectoryError with clear instructions
```

### Scenario 2: User Project Works
```bash
cd ~/my-project
gao-dev start
# Expected: Normal startup
```

### Scenario 3: Explicit Project Flag
```bash
gao-dev start --project ~/my-project
# Expected: Normal startup
```

### Scenario 4: Marker in Package
```bash
pip install ./dist/gao_dev-*.whl
python -c "import importlib.resources; print(importlib.resources.files('gao_dev').joinpath('.gaodev-source').exists())"
# Expected: True
```

---

## Implementation Steps

1. Create `.gaodev-source` marker file:
   ```
   # GAO-Dev Source Repository Marker
   # This file identifies the GAO-Dev source repository.
   # Do not run gao-dev commands from this directory.
   ```

2. Update `gao_dev/cli/project_detection.py`:
   - Add `GAODevSourceDirectoryError` exception class
   - Add `_is_gaodev_source_repo(path: Path) -> bool` function
   - Update `detect_project_root()` to call check early
   - Provide helpful error message

3. Update `pyproject.toml`:
   - Add `.gaodev-source` to package-data

4. Write unit tests:
   - Test source repo detection
   - Test user project detection
   - Test error messages

---

## Error Message Format

```
[E001] Running from GAO-Dev Source Directory

GAO-Dev must be installed via pip and run from your project directory.

Installation:
  pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

Usage:
  cd /path/to/your/project
  gao-dev start

Alternative:
  gao-dev start --project /path/to/your/project

Documentation: https://docs.gao-dev.com/errors/E001
Support: https://github.com/memyselfmike/gao-agile-dev/issues/new
```

---

## Dependencies

**Upstream**: None
**Downstream**: 36.12 (Integration Tests)

---

## Risk Level

**Low** - Simple file checks, clear error messages, straightforward implementation

---

## Definition of Done

- [ ] Code changes committed and pushed
- [ ] All acceptance criteria met
- [ ] Tests pass (unit tests for detection logic)
- [ ] CI pipeline passes
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Story marked as complete in tracking
