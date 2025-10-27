# Story 2.3: Variable Substitution Engine

**Epic**: Epic 2 - Boilerplate Integration
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev sandbox
**I want** template variables automatically substituted with project-specific values
**So that** boilerplate projects are properly customized for each sandbox project

---

## Acceptance Criteria

### AC1: Variable Substitution
- ✅ Substitutes `{{variable_name}}` format
- ✅ Substitutes `__VARIABLE_NAME__` format
- ✅ Handles both formats in same file
- ✅ Performs case-sensitive replacement
- ✅ Updates all occurrences in all files

### AC2: Value Sources
- ✅ Uses project name from sandbox metadata
- ✅ Uses user-provided values from config
- ✅ Uses default values for common variables
- ✅ Prompts for missing required variables
- ✅ Validates values before substitution

### AC3: File Handling
- ✅ Preserves file encoding (UTF-8)
- ✅ Maintains file permissions
- ✅ Preserves line endings (LF/CRLF)
- ✅ Creates backup before substitution (optional)

### AC4: Safety & Validation
- ✅ Validates substitution values (alphanumeric, hyphens, underscores)
- ✅ Prevents empty substitutions
- ✅ Reports any unsubstituted variables
- ✅ Rollback capability on error

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/template_substitutor.py`

```python
"""Template variable substitution engine."""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SubstitutionResult:
    """Result of variable substitution operation."""
    files_modified: int
    variables_substituted: int
    unsubstituted_variables: List[str]
    errors: List[str]

class TemplateSubstitutor:
    """
    Performs template variable substitution in boilerplate projects.
    """

    # Common default variables
    DEFAULT_VARIABLES = {
        'PROJECT_NAME': None,  # Required
        'PROJECT_DESCRIPTION': 'A GAO-Dev sandbox project',
        'AUTHOR': 'GAO-Dev',
        'LICENSE': 'MIT',
        'YEAR': '2025',
    }

    def substitute_variables(
        self,
        project_path: Path,
        variables: Dict[str, str],
        create_backup: bool = False,
    ) -> SubstitutionResult:
        """
        Substitute template variables in project files.

        Args:
            project_path: Root directory of project
            variables: Dictionary mapping variable names to values
            create_backup: Whether to backup files before substitution

        Returns:
            SubstitutionResult with operation details

        Raises:
            SubstitutionError: If substitution fails
        """
        pass

    def substitute_in_file(
        self,
        file_path: Path,
        variables: Dict[str, str],
    ) -> int:
        """
        Substitute variables in a single file.

        Returns:
            Number of substitutions made
        """
        pass

    def validate_value(self, value: str) -> bool:
        """Validate substitution value format."""
        pass

    def rollback_substitution(self, project_path: Path) -> bool:
        """Rollback substitution using backups."""
        pass
```

### Substitution Logic

1. **Prepare Variables**
   - Merge user values with defaults
   - Validate all values
   - Check for required variables

2. **File Processing**
   - Read file content
   - Apply regex replacements
   - Write back to file

3. **Error Handling**
   - Track unsubstituted variables
   - Rollback on critical error
   - Report comprehensive results

### Common Variables

| Variable | Source | Example | Required |
|----------|--------|---------|----------|
| `PROJECT_NAME` | Sandbox name | `todo-app-001` | Yes |
| `PROJECT_DESCRIPTION` | User input | `Todo application` | No |
| `AUTHOR` | Config | `Mike` | No |
| `LICENSE` | Config/default | `MIT` | No |
| `YEAR` | Current year | `2025` | No |
| `REPO_URL` | Generated | `https://github.com/...` | No |

---

## Testing Requirements

### Unit Tests

```python
def test_substitute_double_brace():
    """Test {{VAR}} substitution."""
    pass

def test_substitute_double_underscore():
    """Test __VAR__ substitution."""
    pass

def test_multiple_variables_same_file():
    """Test multiple variables in one file."""
    pass

def test_missing_required_variable():
    """Test error on missing required variable."""
    pass

def test_invalid_value_rejected():
    """Test invalid characters rejected."""
    pass

def test_preserves_encoding():
    """Test UTF-8 encoding preserved."""
    pass

def test_rollback_on_error():
    """Test rollback functionality."""
    pass
```

### Integration Tests

- Test with real Next.js starter
- Verify all variables substituted correctly
- Test with missing variables
- Test with special characters

---

## Definition of Done

- [ ] TemplateSubstitutor class implemented
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Error handling comprehensive
- [ ] Rollback functionality working
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Type hints complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 2.2 (variable detection)
- **Blocks**: Story 2.4 (dependency installation)

---

## Notes

- Consider adding dry-run mode to preview changes
- May need to handle variables in filenames (future)
- Should log all substitutions for audit trail

---

*Created as part of Epic 2: Boilerplate Integration*
