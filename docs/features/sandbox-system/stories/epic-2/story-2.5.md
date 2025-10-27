# Story 2.5: Boilerplate Validation

**Epic**: Epic 2 - Boilerplate Integration
**Status**: Draft
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Completed**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev sandbox
**I want** boilerplate integration validated after setup
**So that** I can be confident the sandbox project is ready to use

---

## Acceptance Criteria

### AC1: Structure Validation
- ✅ Verifies expected directories exist
- ✅ Verifies key files present (package.json, README, etc.)
- ✅ Checks for template residue (unsubstituted variables)
- ✅ Reports any structural issues

### AC2: Dependency Validation
- ✅ Verifies dependencies installed successfully
- ✅ Checks node_modules or venv exists
- ✅ Validates lockfiles are present
- ✅ Reports any missing dependencies

### AC3: Configuration Validation
- ✅ Verifies config files valid (JSON, YAML)
- ✅ Checks for common configuration issues
- ✅ Validates environment setup
- ✅ Reports configuration errors

### AC4: Health Check
- ✅ Runs basic health check command if available
- ✅ Verifies project can be built/compiled
- ✅ Checks for immediate errors
- ✅ Reports overall project health

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/boilerplate_validator.py`

```python
"""Boilerplate integration validation."""

from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    """Severity of validation issue."""
    ERROR = "error"  # Critical issue, project won't work
    WARNING = "warning"  # Non-critical issue
    INFO = "info"  # Informational message

@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: ValidationLevel
    category: str  # 'structure', 'dependencies', 'config', 'health'
    message: str
    fix_suggestion: Optional[str] = None

@dataclass
class ValidationReport:
    """Complete validation report."""
    passed: bool
    issues: List[ValidationIssue]
    warnings_count: int
    errors_count: int

class BoilerplateValidator:
    """
    Validates boilerplate integration completeness and correctness.
    """

    def validate_project(self, project_path: Path) -> ValidationReport:
        """
        Run complete validation on sandbox project.

        Args:
            project_path: Root directory of sandbox project

        Returns:
            ValidationReport with all issues found
        """
        pass

    def validate_structure(self, project_path: Path) -> List[ValidationIssue]:
        """Validate directory structure and key files."""
        pass

    def validate_dependencies(self, project_path: Path) -> List[ValidationIssue]:
        """Validate dependencies installed correctly."""
        pass

    def validate_configuration(self, project_path: Path) -> List[ValidationIssue]:
        """Validate configuration files."""
        pass

    def run_health_check(self, project_path: Path) -> List[ValidationIssue]:
        """Run project-specific health checks."""
        pass

    def check_for_template_residue(self, project_path: Path) -> List[str]:
        """Find any unsubstituted template variables."""
        pass
```

### Validation Checks

**Structure Validation**:
- [ ] `package.json` or `pyproject.toml` exists
- [ ] `README.md` exists
- [ ] `src/` or equivalent directory exists
- [ ] `.gitignore` exists
- [ ] No `.git` directory conflicts

**Dependency Validation**:
- [ ] `node_modules/` exists if Node project
- [ ] `.venv/` or `venv/` exists if Python project
- [ ] Lockfile present and valid
- [ ] No missing peer dependencies

**Configuration Validation**:
- [ ] JSON files valid (parse without errors)
- [ ] YAML files valid (parse without errors)
- [ ] No syntax errors in config files
- [ ] Required environment variables documented

**Health Check**:
- [ ] Can run `npm run build` or equivalent (if defined)
- [ ] Can import main module (Python)
- [ ] No immediate runtime errors
- [ ] TypeScript compiles (if applicable)

### Validation Report Format

```
================================================================================
 Boilerplate Validation Report
 Project: todo-app-baseline-run-001
================================================================================

Structure: OK
  ✅ All required directories present
  ✅ Key files detected: package.json, README.md, .gitignore

Dependencies: OK
  ✅ node_modules/ exists (pnpm)
  ✅ pnpm-lock.yaml present
  ⚠️  Peer dependency warning: react@18.x expected, 17.x found

Configuration: OK
  ✅ package.json valid
  ✅ tsconfig.json valid
  ⚠️  .env.example present but .env missing

Health Check: OK
  ✅ TypeScript compilation successful
  ✅ No build errors

================================================================================
Summary: 2 warnings, 0 errors
Status: READY ✅
================================================================================
```

---

## Testing Requirements

### Unit Tests

```python
def test_detect_missing_directory():
    """Test detection of missing required directory."""
    pass

def test_detect_unsubstituted_variable():
    """Test detection of template residue."""
    pass

def test_validate_json_syntax():
    """Test JSON validation."""
    pass

def test_dependency_check_node():
    """Test Node dependency validation."""
    pass

def test_dependency_check_python():
    """Test Python dependency validation."""
    pass

def test_health_check_failure():
    """Test health check error detection."""
    pass
```

### Integration Tests

- Test with properly set up Next.js project
- Test with missing dependencies
- Test with configuration errors
- Test with unsubstituted variables

---

## Definition of Done

- [ ] BoilerplateValidator class implemented
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] All validation checks working
- [ ] Clear, actionable error messages
- [ ] Integrated with sandbox init flow
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Type hints complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Stories 2.1, 2.2, 2.3, 2.4
- **Blocks**: None (completes Epic 2)

---

## Notes

- Validation should be fast (<5 seconds)
- Consider adding --strict mode for stricter validation
- Should provide fix suggestions when possible
- May evolve based on common issues found

---

*Created as part of Epic 2: Boilerplate Integration*
**Completed**: 2025-10-27
