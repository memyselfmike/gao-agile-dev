# Story 35.1: Project Setup & Architecture

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.1
**Story Points**: 2
**Owner**: Amelia (Software Developer)
**Dependencies**: None
**Priority**: P0
**Status**: Complete

---

## Description

Create foundational structure for Epic 35 including directory structure, base classes, exceptions, data models, and feature flag. This establishes the architecture for all subsequent stories and ensures proper separation of concerns.

This story focuses on:
- Creating module stubs with type hints and docstrings
- Defining exception hierarchy for error handling
- Creating data models using dataclasses
- Setting up test structure
- Adding feature flag for rollback capability
- Validating import structure (no circular dependencies)

---

## Acceptance Criteria

- [ ] Feature directory created: `docs/features/interactive-provider-selection/`
- [ ] PRD, ARCHITECTURE, and epic breakdown documents exist
- [ ] New module structure created in `gao_dev/cli/`:
  - [ ] `provider_selector.py` (stub with ProviderSelector class)
  - [ ] `interactive_prompter.py` (stub with InteractivePrompter class)
  - [ ] `preference_manager.py` (stub with PreferenceManager class)
  - [ ] `provider_validator.py` (stub with ProviderValidator class)
- [ ] Exception classes defined in `gao_dev/cli/exceptions.py`:
  - [ ] `ProviderSelectionError` (base exception)
  - [ ] `ProviderSelectionCancelled` (user cancelled)
  - [ ] `ProviderValidationFailed` (validation failed)
  - [ ] `PreferenceSaveError` (save failed)
  - [ ] `PreferenceLoadError` (load failed)
- [ ] Data models defined in `gao_dev/cli/models.py`:
  - [ ] `ProviderConfig` (dataclass for provider configuration)
  - [ ] `ProviderPreferences` (dataclass for saved preferences)
  - [ ] `ValidationResult` (dataclass for validation results)
- [ ] Test structure created:
  - [ ] `tests/cli/test_provider_selector.py` (stub with basic imports)
  - [ ] `tests/cli/test_interactive_prompter.py` (stub)
  - [ ] `tests/cli/test_preference_manager.py` (stub)
  - [ ] `tests/cli/test_provider_validator.py` (stub)
- [ ] Feature flag added to `gao_dev/config/defaults.yaml`:
  - [ ] `features.interactive_provider_selection: true`
- [ ] All stubs have:
  - [ ] Complete docstrings (module, class, method level)
  - [ ] Type hints for all parameters and return values
  - [ ] `pass` or `NotImplementedError` for method bodies
- [ ] Import structure validated:
  - [ ] No circular dependencies
  - [ ] All modules import successfully
  - [ ] MyPy passes with no errors in strict mode

---

## Tasks

- [ ] Create feature directory structure
- [ ] Create module stubs with class definitions
  - [ ] Define ProviderSelector class with method signatures
  - [ ] Define InteractivePrompter class with method signatures
  - [ ] Define PreferenceManager class with method signatures
  - [ ] Define ProviderValidator class with method signatures
- [ ] Define exception hierarchy in exceptions.py
  - [ ] Create base ProviderSelectionError
  - [ ] Create specific exception subclasses
  - [ ] Add docstrings explaining when each is raised
- [ ] Define data models with dataclasses
  - [ ] ProviderConfig with all fields
  - [ ] ProviderPreferences with metadata
  - [ ] ValidationResult with success/error fields
- [ ] Create test file stubs
  - [ ] Add basic imports and test class structure
  - [ ] Add placeholder tests (to be filled in implementation stories)
- [ ] Add feature flag to defaults.yaml
  - [ ] Add `features:` section if missing
  - [ ] Add `interactive_provider_selection: true`
  - [ ] Document purpose in comments
- [ ] Validate imports and type hints
  - [ ] Run: `python -c "import gao_dev.cli.provider_selector"`
  - [ ] Run: `python -c "import gao_dev.cli.interactive_prompter"`
  - [ ] Run: `python -c "import gao_dev.cli.preference_manager"`
  - [ ] Run: `python -c "import gao_dev.cli.provider_validator"`
- [ ] Run mypy to ensure type safety
  - [ ] Run: `mypy gao_dev/cli/provider_selector.py --strict`
  - [ ] Run: `mypy gao_dev/cli/interactive_prompter.py --strict`
  - [ ] Run: `mypy gao_dev/cli/preference_manager.py --strict`
  - [ ] Run: `mypy gao_dev/cli/provider_validator.py --strict`
- [ ] Commit changes with atomic commit message

---

## Test Cases

```python
# tests/cli/test_provider_selector.py (stub)
def test_provider_selector_imports():
    """Test that ProviderSelector can be imported."""
    from gao_dev.cli.provider_selector import ProviderSelector
    assert ProviderSelector is not None

# tests/cli/test_interactive_prompter.py (stub)
def test_interactive_prompter_imports():
    """Test that InteractivePrompter can be imported."""
    from gao_dev.cli.interactive_prompter import InteractivePrompter
    assert InteractivePrompter is not None

# tests/cli/test_preference_manager.py (stub)
def test_preference_manager_imports():
    """Test that PreferenceManager can be imported."""
    from gao_dev.cli.preference_manager import PreferenceManager
    assert PreferenceManager is not None

# tests/cli/test_provider_validator.py (stub)
def test_provider_validator_imports():
    """Test that ProviderValidator can be imported."""
    from gao_dev.cli.provider_validator import ProviderValidator
    assert ProviderValidator is not None

def test_exceptions_defined():
    """Test that all custom exceptions are defined."""
    from gao_dev.cli.exceptions import (
        ProviderSelectionError,
        ProviderSelectionCancelled,
        ProviderValidationFailed,
        PreferenceSaveError,
        PreferenceLoadError,
    )
    assert issubclass(ProviderSelectionCancelled, ProviderSelectionError)
    assert issubclass(ProviderValidationFailed, ProviderSelectionError)

def test_data_models_defined():
    """Test that all data models are defined."""
    from gao_dev.cli.models import ProviderConfig, ProviderPreferences, ValidationResult
    assert ProviderConfig is not None
    assert ProviderPreferences is not None
    assert ValidationResult is not None
```

---

## Definition of Done

- [ ] All module files created and committed
- [ ] All exception classes defined with docstrings
- [ ] All data models defined with type hints
- [ ] Test stubs created with basic import tests
- [ ] Feature flag added to defaults.yaml
- [ ] MyPy passes strict mode (0 errors)
- [ ] Import checker validates no circular dependencies
- [ ] All tests pass (stub tests only)
- [ ] Code reviewed and approved
- [ ] Documentation reviewed (docstrings)
- [ ] Commit message follows format: `feat(epic-35): Story 35.1 - Project Setup & Architecture (2 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Feature Flag for Rollback (CRAAP Critical)**:
- Added `features.interactive_provider_selection` flag to defaults.yaml
- Enables production rollback if Epic 35 causes issues
- ChatREPL will check this flag before calling ProviderSelector

### Architecture Decisions

**Module Structure**:
- All provider selection code in `gao_dev/cli/` (closest to usage)
- Data models in separate `models.py` (single source of truth)
- Exceptions in separate `exceptions.py` (reusable across modules)

**Dependency Injection**:
- All classes accept optional dependencies in constructor
- Enables easy testing with mocks
- Avoids tight coupling

**Type Safety**:
- All parameters and returns have type hints
- Use dataclasses for structured data
- MyPy strict mode compliance

### Estimated Effort

**Breakdown**:
- Module stubs: 1 hour (4 classes, basic structure)
- Exceptions: 30 minutes (5 classes with docstrings)
- Data models: 1 hour (3 dataclasses with all fields)
- Test stubs: 30 minutes (4 files with imports)
- Feature flag: 15 minutes
- Validation: 30 minutes (mypy, imports, circular dependency check)
- Documentation: 30 minutes (docstrings)

**Total**: ~4-5 hours (2 story points at upper end, as noted in CRAAP review)

### Dependencies for Next Stories

After this story completes:
- Story 35.2 (PreferenceManager) can begin
- Story 35.3 (ProviderValidator) can begin
- Story 35.4 (InteractivePrompter) can begin

All three can be developed in **parallel** by different developers.

---

**Story Status**: Todo
**Next Action**: Begin implementation
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
