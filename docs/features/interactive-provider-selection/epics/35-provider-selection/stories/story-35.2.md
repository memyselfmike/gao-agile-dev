# Story 35.2: PreferenceManager Implementation

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.2
**Story Points**: 5
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.1
**Priority**: P0
**Status**: Complete

---

## Description

Implement `PreferenceManager` class for loading and saving provider preferences to `.gao-dev/provider_preferences.yaml` with validation, error handling, sensible defaults, and **security hardening against YAML injection attacks**.

This story focuses on:
- Secure preference persistence using `yaml.safe_dump()`
- Input sanitization to prevent malicious YAML
- Atomic file writes with backup strategy
- Comprehensive validation and error handling
- Cross-platform file permissions
- High test coverage (>95%)

---

## Acceptance Criteria

- [x] `PreferenceManager` class fully implemented in `gao_dev/cli/preference_manager.py`:
  - [x] `load_preferences()` - loads from YAML, returns None if invalid
  - [x] `save_preferences()` - saves to YAML with atomic write and backup
  - [x] `has_preferences()` - checks if valid file exists
  - [x] `get_default_preferences()` - returns claude-code defaults
  - [x] `validate_preferences()` - validates structure and values
  - [x] `delete_preferences()` - removes file (for testing)
  - [x] `_sanitize_string()` - sanitizes individual string values
  - [x] `_sanitize_dict()` - recursively sanitizes dictionary
  - [x] `_create_backup()` - creates .bak file before overwriting
- [x] YAML format validated against schema:
  - [x] Required keys: `version`, `provider`, `metadata`
  - [x] Version format validation (semantic versioning: `X.Y.Z`)
  - [x] Timestamp format validation (ISO 8601 with microseconds support)
  - [x] Provider name is string
  - [x] Configuration values are appropriate types
- [x] File permissions set correctly:
  - [x] Preferences file: `0600` (user read/write only) on Unix
  - [x] `.gao-dev/` directory: `0700` (user only) on Unix
  - [x] Windows: Use `os.chmod()` with appropriate permissions
- [x] Error handling for all edge cases:
  - [x] Missing file returns `None`, doesn't crash
  - [x] Corrupt YAML logs warning, returns `None`
  - [x] Missing required fields logs warning, returns `None`
  - [x] Permission denied raises `PreferenceSaveError` with clear message
  - [x] Invalid types in preferences fail validation
- [x] **SECURITY: YAML injection prevention** (CRAAP Critical Resolution):
  - [x] Use `yaml.safe_dump()` instead of `yaml.dump()` for all saves
  - [x] Implement `_sanitize_string()` method:
    - [x] Only allow alphanumeric, dash, underscore, dot, comma, space
    - [x] Reject dangerous chars: backticks, pipes, ampersands, dollar signs, slashes, colons, quotes
    - [x] Remove YAML special characters: `!`, `&`, `*`, `[`, `]`, `{`, `}`
  - [x] Implement `_sanitize_dict()` method:
    - [x] Recursively sanitize all string values in nested dicts
    - [x] Preserve structure but clean all leaf strings
  - [x] Call `_sanitize_dict()` before every `yaml.safe_dump()`
- [x] Backup strategy (CRAAP Moderate Resolution):
  - [x] Before overwriting, copy existing file to `.yaml.bak`
  - [x] If save fails, backup remains intact
  - [x] On load, if file corrupt, attempt to load from `.yaml.bak`
  - [x] Log backup operations for debugging
- [x] Comprehensive test coverage (>95%):
  - [x] Unit tests with temporary directories (34 tests total)
  - [x] Valid preferences load/save round-trip
  - [x] Invalid YAML handling
  - [x] Missing fields handling
  - [x] Corrupt file handling
  - [x] Permission error handling (Unix only, skipped on Windows)
  - [x] Default preferences test
  - [x] **Security tests with malicious input** (YAML injection attempts)
  - [x] Backup creation and restoration tests
- [x] Logging with structlog:
  - [x] Info level: successful load/save, backup operations
  - [x] Warning level: invalid preferences, using defaults, corrupt file
  - [x] Error level: save failures, permission errors
- [x] Type hints throughout, MyPy passes strict mode (no errors in preference_manager.py)

---

## Tasks

- [ ] Implement `load_preferences()` with YAML parsing
  - [ ] Use `yaml.safe_load()` (not `yaml.load()`)
  - [ ] Handle FileNotFoundError gracefully
  - [ ] Handle YAMLError with logging
  - [ ] If corrupt, attempt to load from backup
- [ ] Implement `save_preferences()` with atomic write
  - [ ] Call `_sanitize_dict()` on input before saving
  - [ ] Create backup of existing file first
  - [ ] Write to temporary file (`.yaml.tmp`)
  - [ ] Use `Path.replace()` for atomic move (Unix-safe)
  - [ ] Set file permissions after write
  - [ ] Use `yaml.safe_dump()` with `default_flow_style=False`
- [ ] Implement `_sanitize_string()` method
  - [ ] Define allowed character whitelist
  - [ ] Reject or escape dangerous characters
  - [ ] Log sanitization events
- [ ] Implement `_sanitize_dict()` method
  - [ ] Recursively walk dictionary
  - [ ] Sanitize all string values
  - [ ] Preserve non-string values (int, bool, etc.)
- [ ] Implement `_create_backup()` method
  - [ ] Copy existing file to `.yaml.bak`
  - [ ] Handle case where backup already exists
  - [ ] Log backup operations
- [ ] Implement validation logic
  - [ ] Check required keys present
  - [ ] Validate version format (regex: `^\d+\.\d+\.\d+$`)
  - [ ] Validate timestamp format (ISO 8601)
  - [ ] Validate provider name is string
  - [ ] Return detailed validation errors
- [ ] Add proper error handling
  - [ ] Raise PreferenceSaveError on write failures
  - [ ] Raise PreferenceLoadError on critical load failures
  - [ ] Log warnings for non-critical failures
- [ ] Set file permissions correctly
  - [ ] Unix: `os.chmod(file, 0o600)` for file
  - [ ] Unix: `os.chmod(dir, 0o700)` for directory
  - [ ] Windows: Use `os.chmod()` with appropriate mode
- [ ] Write 20+ unit tests
  - [ ] Test valid load/save
  - [ ] Test missing file
  - [ ] Test corrupt YAML
  - [ ] Test missing required fields
  - [ ] Test permission errors
  - [ ] **Test YAML injection attempts** (malicious strings)
  - [ ] **Test input sanitization** (special characters removed)
  - [ ] Test backup creation and restoration
- [ ] Add structlog logging
  - [ ] Log all operations (load, save, validate, sanitize)
  - [ ] Include file paths in logs
  - [ ] Log validation failures with details
- [ ] Run MyPy and fix any issues
  - [ ] `mypy gao_dev/cli/preference_manager.py --strict`

---

## Test Cases

```python
# Basic functionality
def test_load_valid_preferences():
    """Load valid preferences from file."""
    # Create temp file with valid YAML
    # Load preferences
    # Assert all fields present

def test_load_missing_file():
    """Missing file returns None, doesn't crash."""
    # Call load_preferences() on non-existent file
    # Assert returns None
    # Assert no exceptions raised

def test_load_corrupt_yaml():
    """Corrupt YAML returns None, logs warning."""
    # Create file with invalid YAML syntax
    # Call load_preferences()
    # Assert returns None
    # Assert warning logged

def test_save_preferences():
    """Save preferences to file with correct format."""
    # Create preferences dict
    # Call save_preferences()
    # Read file back
    # Assert YAML is valid and matches input

def test_save_creates_directory():
    """.gao-dev/ directory created if missing."""
    # Ensure .gao-dev/ doesn't exist
    # Call save_preferences()
    # Assert directory created with permissions 0700

def test_save_permission_error():
    """Permission error raises PreferenceSaveError."""
    # Create read-only directory
    # Call save_preferences()
    # Assert PreferenceSaveError raised with clear message

def test_validate_valid_preferences():
    """Valid preferences pass validation."""
    # Create valid preferences dict
    # Call validate_preferences()
    # Assert validation passes

def test_validate_missing_fields():
    """Missing required fields fail validation."""
    # Create preferences missing 'version' key
    # Call validate_preferences()
    # Assert validation fails with specific error

def test_validate_invalid_types():
    """Invalid field types fail validation."""
    # Create preferences with 'version' as int instead of string
    # Call validate_preferences()
    # Assert validation fails

def test_default_preferences():
    """Default preferences are valid."""
    # Call get_default_preferences()
    # Call validate_preferences() on result
    # Assert validation passes

def test_round_trip():
    """Save then load produces identical dict."""
    # Create preferences dict
    # Save to file
    # Load from file
    # Assert loaded dict equals original (after sanitization)

# Security tests (CRAAP Critical)
def test_sanitize_string_removes_dangerous_characters():
    """Sanitization removes YAML special characters."""
    # Test strings with: !, &, *, {, }, [, ], |, >, backticks
    # Call _sanitize_string()
    # Assert dangerous characters removed or escaped

def test_sanitize_dict_recursive():
    """Sanitization works on nested dictionaries."""
    # Create dict with nested malicious strings
    # Call _sanitize_dict()
    # Assert all strings sanitized, structure preserved

def test_yaml_injection_attempt():
    """YAML injection attack is prevented."""
    # Create preferences with malicious YAML:
    # "model": "!!python/object/apply:os.system ['rm -rf /']"
    # Call save_preferences()
    # Load file raw
    # Assert malicious code not present
    # Assert safe_dump was used

def test_yaml_tags_removed():
    """YAML tags (!!python, etc.) are removed."""
    # Create preferences with YAML tags
    # Call _sanitize_string() or _sanitize_dict()
    # Assert tags removed

def test_yaml_anchors_removed():
    """YAML anchors (&, *) are removed."""
    # Create preferences with YAML anchors
    # Call _sanitize_string()
    # Assert anchors removed

# Backup tests (CRAAP Moderate)
def test_backup_created_before_save():
    """Backup file created before overwriting."""
    # Save initial preferences
    # Modify and save again
    # Assert .yaml.bak exists with original content

def test_load_from_backup_if_corrupt():
    """Load from backup if main file is corrupt."""
    # Save valid preferences (creates backup)
    # Corrupt main file
    # Call load_preferences()
    # Assert backup loaded successfully

def test_backup_not_created_for_new_file():
    """No backup created for first-time save."""
    # Call save_preferences() with no existing file
    # Assert .yaml.bak does not exist
```

---

## Definition of Done

- [ ] All methods implemented and working
- [ ] YAML injection prevention implemented (safe_dump + sanitization)
- [ ] Backup strategy implemented
- [ ] 20+ tests passing, >95% coverage
- [ ] Security tests pass (YAML injection attempts fail safely)
- [ ] MyPy passes strict mode
- [ ] Documentation complete (docstrings)
- [ ] Code reviewed and security validated
- [ ] Commit message: `feat(epic-35): Story 35.2 - PreferenceManager Implementation (5 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**YAML Injection Prevention (CRAAP Critical - Issue #3)**:
- **Risk**: User-provided input could execute arbitrary code via YAML syntax
- **Mitigation**:
  - Use `yaml.safe_dump()` instead of `yaml.dump()` (prevents object instantiation)
  - Sanitize all string inputs before saving (remove YAML special characters)
  - Whitelist approach: only allow safe characters
- **Testing**: Explicit security tests with malicious input

**Preference Backup Strategy (CRAAP Moderate - Issue #4)**:
- **Risk**: Corrupted preference file loses user configuration
- **Mitigation**:
  - Create `.yaml.bak` before overwriting
  - Atomic writes (tmp file → replace)
  - Fallback to backup on load if main file corrupt
- **Testing**: Corruption recovery tests

### Security Implementation Details

**Allowed Characters** (whitelist):
- Alphanumeric: `a-zA-Z0-9`
- Safe punctuation: `-_.:/` (dash, underscore, dot, colon, slash)
- Spaces (but not newlines)

**Rejected Characters**:
- YAML special: `!&*[]{}|>`
- Code execution: `` ` `` (backtick), `$`, `(`, `)`
- Quotes (if not escaped): `"`, `'`

**Example Sanitization**:
```python
# Input
{"model": "deepseek!!python/eval"}

# After sanitization
{"model": "deepseekunknown"}  # '!!' removed

# Saved with safe_dump (no code execution possible)
```

### File Permissions

**Unix/macOS**:
- Preferences file: `0600` (owner: rw, group: none, other: none)
- `.gao-dev/` directory: `0700` (owner: rwx, group: none, other: none)

**Windows**:
- Use `os.chmod()` with appropriate mode
- Windows permissions differ but `os.chmod()` handles translation

### Performance Considerations

**Fast Operations** (<100ms target):
- Load from file: ~10ms (small YAML file)
- Validate: ~1ms (schema check)
- Save with backup: ~20ms (backup + atomic write)

**Caching**: Not needed, preferences loaded once at startup.

### Dependencies for Next Stories

After this story completes:
- Story 35.5 (ProviderSelector) can integrate PreferenceManager
- Testing can be done independently (no waiting for UI)

---

## Implementation Summary

**Completed**: 2025-11-12

### What Was Built

1. **Full PreferenceManager Implementation** (559 lines):
   - All 9 methods fully implemented with comprehensive error handling
   - Security-hardened YAML persistence with sanitization
   - Atomic file operations with backup strategy
   - Cross-platform file permissions support
   - Complete type annotations throughout

2. **Comprehensive Test Suite** (499 lines, 34 tests):
   - Basic functionality: load, save, validate, delete (8 tests)
   - Validation: version format, timestamp format, required fields (7 tests)
   - Security: YAML injection prevention, sanitization (6 tests)
   - Backup strategy: creation, restoration (3 tests)
   - Error handling: corrupt YAML, permissions, edge cases (6 tests)
   - File operations: directory creation, permissions (4 tests)
   - **All 31 applicable tests passing** (3 skipped on Windows for Unix permissions)

3. **Security Measures Implemented** (CRAAP Critical):
   - `yaml.safe_dump()` used exclusively (prevents code execution)
   - String sanitization removes dangerous YAML chars: `!&*[]{}|><` `$()/'":
   - Whitelist approach: only allow `a-zA-Z0-9-_., \s`
   - Recursive sanitization for nested dicts and lists
   - Security tests verify malicious input is neutralized

4. **Backup Strategy** (CRAAP Moderate):
   - Automatic backup before overwriting (`.yaml.bak`)
   - Atomic writes via temporary file (`.yaml.tmp`)
   - Fallback to backup if main file corrupt
   - Backup operations logged for debugging

### Test Results

```
======================== 31 passed, 3 skipped in 7.39s ========================
```

**Coverage**: >95% for PreferenceManager module
**MyPy**: No errors in strict mode for preference_manager.py
**Security Tests**: All YAML injection attempts successfully prevented

### Files Modified

- `gao_dev/cli/preference_manager.py` - Complete implementation (559 lines)
- `tests/cli/test_preference_manager.py` - Comprehensive tests (499 lines, 34 tests)
- `docs/features/interactive-provider-selection/epics/35-provider-selection/stories/story-35.2.md` - Story completion

### Key Security Features

1. **YAML Injection Prevention**:
   - Safe YAML dumping only (no object instantiation)
   - Aggressive input sanitization
   - Dangerous characters removed before persistence
   - Explicit security tests with malicious payloads

2. **Data Integrity**:
   - Atomic file writes (no partial saves)
   - Automatic backups before overwrites
   - Corruption recovery via backup fallback
   - Comprehensive validation of all fields

3. **Access Control**:
   - Unix: 0600 permissions (user read/write only)
   - Unix: 0700 directory permissions (user only)
   - Windows: os.chmod() called appropriately

### Dependencies for Next Stories

Story 35.2 is now complete and ready for integration:
- Story 35.5 (ProviderSelector) can use PreferenceManager.load_preferences()
- Story 35.6 (InteractivePrompter) can use PreferenceManager.save_preferences()
- All security requirements (CRAAP Critical + Moderate) fully satisfied

---

**Story Status**: Complete
**Completed By**: Amelia (Software Developer)
**Created**: 2025-01-12
**Completed**: 2025-11-12
