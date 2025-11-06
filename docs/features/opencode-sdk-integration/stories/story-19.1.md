# Story 19.1: Add OpenCode SDK Dependency

**Epic**: Epic 19 - OpenCode SDK Integration
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev developer
**I want** the OpenCode Python SDK added as a project dependency
**So that** I can use the SDK's API instead of CLI subprocess calls

---

## Acceptance Criteria

### AC1: SDK Added to Dependencies
- SDK added to `pyproject.toml` with version `^0.1.0a36`
- `pip install -e .` installs SDK without errors
- SDK version is documented as pre-release
- Poetry lock file updated (if using Poetry)

### AC2: SDK Import Verification
- `from opencode_ai import Opencode` imports successfully
- No import errors or warnings
- SDK module accessible from GAO-Dev code

### AC3: Documentation
- Pre-release status documented in comments
- Version compatibility notes added
- Known limitations documented (if any)

### AC4: Dependency Resolution
- No conflicts with existing dependencies
- All existing tests still pass after adding SDK
- CI/CD pipeline installs SDK correctly

---

## Technical Details

### File Structure
```
gao-agile-dev/
├── pyproject.toml           # MODIFIED: Add opencode-ai dependency
├── poetry.lock              # MODIFIED: Update lock file (if using Poetry)
└── requirements.txt         # MODIFIED: Add dependency (if applicable)
```

### Implementation Approach

**Step 1: Add to pyproject.toml**
```toml
[tool.poetry.dependencies]
python = "^3.11"
# ... existing dependencies ...
opencode-ai = "^0.1.0a36"  # Pre-release SDK
```

**Step 2: Update Lock File**
```bash
# If using Poetry
poetry lock --no-update

# If using pip
pip install -e .
```

**Step 3: Verify Installation**
```python
# Test script
from opencode_ai import Opencode

print("OpenCode SDK imported successfully")
print(f"SDK version: {Opencode.__version__ if hasattr(Opencode, '__version__') else 'unknown'}")
```

**Step 4: Document Pre-Release Status**
Add to relevant documentation:
```markdown
## Dependencies

### OpenCode SDK (Pre-Release)
- Version: 0.1.0a36 (alpha)
- Status: Pre-release, may have breaking changes
- Purpose: Python SDK for OpenCode API
- Alternative: OpenCode CLI (fallback)
```

---

## Testing Approach

### Manual Testing
```bash
# Install dependencies
pip install -e .

# Test SDK import
python -c "from opencode_ai import Opencode; print('OK')"

# Verify no import errors
python -c "import opencode_ai; print(dir(opencode_ai))"

# Run existing test suite
pytest
```

### Expected Output
```
OK
['Opencode', '__version__', ...]
...
===== 400+ tests passed =====
```

### Automated Testing
```python
# tests/core/providers/test_opencode_sdk_import.py
"""Test OpenCode SDK import and basic availability."""

def test_opencode_sdk_imports():
    """Verify OpenCode SDK can be imported."""
    try:
        from opencode_ai import Opencode
        assert Opencode is not None
    except ImportError as e:
        pytest.fail(f"Failed to import OpenCode SDK: {e}")

def test_opencode_sdk_available():
    """Verify OpenCode SDK is available for provider use."""
    from opencode_ai import Opencode
    assert hasattr(Opencode, '__init__'), "Opencode class should be instantiable"
```

---

## Dependencies

### Required Packages
- opencode-ai ^0.1.0a36 (NEW)
- Python 3.11+ (existing)
- pip or Poetry (existing)

### Code Dependencies
- None (foundational story)

### External Dependencies
- PyPI access for installing opencode-ai package
- Internet connection for dependency download

---

## Definition of Done

- [x] `opencode-ai` added to `pyproject.toml` with version `^0.1.0a36`
- [x] Lock file updated successfully
- [x] `pip install -e .` completes without errors
- [x] `from opencode_ai import Opencode` imports successfully
- [x] Pre-release status documented in code comments
- [x] All existing tests pass (400+)
- [x] Import test added to test suite
- [x] Code follows existing style (ASCII-only, type hints)
- [x] Committed to git with conventional commit message

---

## Related Stories

**Depends On**: None (foundational story)
**Blocks**:
- Story 19.2 (Implement OpenCodeSDKProvider Core)
- Story 19.3 (Server Lifecycle Management)
- Story 19.4 (Integration Testing and Validation)
- Story 19.5 (Provider Registration and Documentation)

---

## Notes

### Why This Story Matters
This is the foundational story for Epic 19. Without the SDK dependency installed, no other stories can proceed. The SDK provides the Python API interface that will replace the problematic CLI subprocess approach.

### Pre-Release Considerations
The SDK is currently in alpha (0.1.0a36). This means:
- API may change in future releases
- Pin specific version to avoid breaking changes
- Monitor OpenCode SDK releases for updates
- Document any workarounds for alpha issues

### Alternative Approaches Considered
1. **Continue using CLI**: Rejected due to subprocess hanging issues
2. **Direct HTTP API calls**: More work, SDK provides better abstraction
3. **Wait for stable SDK**: Would delay Epic 19 indefinitely

---

## Acceptance Testing

### Test Case 1: SDK Installation
```bash
$ pip install -e .
Processing ...
Successfully installed opencode-ai-0.1.0a36 ...
```
**Expected**: Installation completes successfully

### Test Case 2: SDK Import
```bash
$ python -c "from opencode_ai import Opencode; print('OK')"
OK
```
**Expected**: Import succeeds, prints "OK"

### Test Case 3: Existing Tests Pass
```bash
$ pytest
===== 400+ passed in X.XXs =====
```
**Expected**: All tests pass, no new failures

### Test Case 4: SDK Module Inspection
```bash
$ python -c "import opencode_ai; print(dir(opencode_ai))"
['Opencode', '__version__', ...]
```
**Expected**: SDK exports expected classes and functions

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SDK not available on PyPI | High | Low | Verify package exists before starting |
| Version conflicts | Medium | Low | Test in clean environment first |
| SDK breaking changes | Medium | Medium | Pin exact version, monitor releases |
| Installation fails on CI | Medium | Low | Test CI pipeline after adding dependency |

---

## Implementation Checklist

- [ ] Verify opencode-ai package exists on PyPI
- [ ] Add dependency to pyproject.toml
- [ ] Update lock file (poetry lock or pip install)
- [ ] Test import in clean Python environment
- [ ] Add import test to test suite
- [ ] Document pre-release status
- [ ] Run full test suite
- [ ] Verify CI pipeline still works
- [ ] Create git commit with conventional message

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes
**Estimated Completion**: 2 hours

---

*This story is part of the GAO-Dev OpenCode SDK Integration project.*
