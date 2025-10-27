# Story 2.2: Template Variable Detection

**Epic**: Epic 2 - Boilerplate Integration
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev sandbox
**I want** the system to automatically detect template variables in boilerplate files
**So that** I can identify what needs to be substituted for project customization

---

## Acceptance Criteria

### AC1: Variable Detection
- ✅ Detects variables in format `{{variable_name}}`
- ✅ Detects variables in format `__VARIABLE_NAME__`
- ✅ Scans all text files in project
- ✅ Excludes binary files and common ignore patterns
- ✅ Returns list of unique variables found

### AC2: File Type Handling
- ✅ Scans: `.md`, `.json`, `.yaml`, `.yml`, `.txt`, `.py`, `.js`, `.ts`, `.tsx`, `.jsx`
- ✅ Ignores: `.git/`, `node_modules/`, `__pycache__/`, `.env`, binary files
- ✅ Respects `.gitignore` patterns

### AC3: Variable Metadata
- ✅ Returns variable name
- ✅ Returns all file locations where found
- ✅ Returns variable format used
- ✅ Identifies required vs. optional variables

### AC4: Performance
- ✅ Scans large projects (1000+ files) in <5 seconds
- ✅ Uses efficient file walking (not recursive glob)

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/template_scanner.py`

```python
"""Template variable detection in boilerplate projects."""

import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class TemplateVariable:
    """Represents a detected template variable."""
    name: str
    format: str  # 'double_brace' or 'double_underscore'
    locations: List[str]  # File paths where found
    required: bool = True

class TemplateScanner:
    """
    Scans boilerplate projects for template variables.
    """

    # Variable patterns
    DOUBLE_BRACE_PATTERN = re.compile(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}')
    DOUBLE_UNDERSCORE_PATTERN = re.compile(r'__([A-Z_][A-Z0-9_]*)__')

    # File extensions to scan
    TEXT_EXTENSIONS = {
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.py', '.js', '.ts', '.tsx', '.jsx',
        '.html', '.css', '.scss', '.sh', '.bash'
    }

    # Directories to ignore
    IGNORE_DIRS = {
        '.git', 'node_modules', '__pycache__',
        '.venv', 'venv', 'env', '.pytest_cache',
        'dist', 'build', '.next', '.nuxt'
    }

    def scan_project(self, project_path: Path) -> List[TemplateVariable]:
        """
        Scan project for template variables.

        Args:
            project_path: Root directory of boilerplate project

        Returns:
            List of detected template variables with metadata
        """
        pass

    def is_text_file(self, file_path: Path) -> bool:
        """Check if file should be scanned for variables."""
        pass

    def scan_file(self, file_path: Path) -> Set[str]:
        """Scan single file for template variables."""
        pass
```

### Detection Logic

1. **Walk Directory Tree**
   - Use `Path.rglob()` with filters
   - Skip ignored directories
   - Only process text files

2. **Pattern Matching**
   - Apply regex patterns to file contents
   - Extract variable names
   - Track file locations

3. **Deduplication**
   - Merge variables found in multiple files
   - Track all occurrences

---

## Testing Requirements

### Unit Tests

```python
def test_detect_double_brace_variables():
    """Test detection of {{VAR}} format."""
    pass

def test_detect_double_underscore_variables():
    """Test detection of __VAR__ format."""
    pass

def test_ignore_binary_files():
    """Test that binary files are skipped."""
    pass

def test_ignore_node_modules():
    """Test that node_modules is skipped."""
    pass

def test_multiple_occurrences():
    """Test variables found in multiple files."""
    pass

def test_mixed_formats():
    """Test detection of both variable formats."""
    pass
```

### Integration Tests

- Test with real Next.js starter template
- Verify all expected variables found
- Verify performance on large project

---

## Definition of Done

- [ ] TemplateScanner class implemented
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Performance requirements met (<5s for large projects)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Type hints complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 2.1 (boilerplate cloned)
- **Blocks**: Story 2.3 (variable substitution)

---

## Notes

- Consider adding support for custom variable formats in future
- May need to handle variables in binary-adjacent files (package.json, etc.)
- Should document common variable naming conventions

---

*Created as part of Epic 2: Boilerplate Integration*
