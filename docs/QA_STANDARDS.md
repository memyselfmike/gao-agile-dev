# Quality Assurance Standards - GAO-Dev

**Version**: 1.0.0
**Last Updated**: 2025-10-27
**Applies To**: All GAO-Dev code

---

## Overview

This document defines the quality standards for GAO-Dev codebase. All code must meet these standards before being considered production-ready.

**Source**: Adapted from BMAD MCP QA validation system

---

## Quality Checklist (14 Criteria)

All modules must pass **14/14** criteria:

### 1. DRY Principle (Don't Repeat Yourself)
**Criterion**: No code duplication

**Check**: `dry-001`
- ❌ **FAIL**: > 5 repeated code patterns
- ⚠️ **WARNING**: 1-5 repeated patterns
- ✅ **PASS**: 0 repeated patterns

**How to Fix**:
- Extract common code into helper methods
- Create base classes for shared functionality
- Use composition over duplication

**Example**:
```python
# ❌ BAD - Repeated pattern
def method_a(self):
    try:
        result = do_something()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def method_b(self):
    try:
        result = do_something_else()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ✅ GOOD - Extract helper
def _execute_safely(self, func):
    try:
        result = func()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def method_a(self):
    return self._execute_safely(do_something)

def method_b(self):
    return self._execute_safely(do_something_else)
```

---

### 2. Magic Numbers
**Criterion**: No hardcoded numeric literals

**Check**: `dry-002`
- ❌ **FAIL**: > 10 magic numbers
- ⚠️ **WARNING**: 1-10 magic numbers
- ✅ **PASS**: 0 magic numbers (all extracted to named constants)

**How to Fix**:
- Extract numbers to module-level constants
- Use ALL_CAPS naming for constants
- Group related constants together

**Example**:
```python
# ❌ BAD - Magic numbers
def process_data(self, data):
    if len(data) > 100:
        return data[:50]
    timeout = 30
    retries = 3

# ✅ GOOD - Named constants
MAX_DATA_LENGTH = 100
DATA_PREVIEW_LENGTH = 50
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

def process_data(self, data):
    if len(data) > MAX_DATA_LENGTH:
        return data[:DATA_PREVIEW_LENGTH]
    timeout = DEFAULT_TIMEOUT_SECONDS
    retries = MAX_RETRIES
```

---

### 3. Type Safety - Any Types
**Criterion**: No `Any` type usage

**Check**: `type-003`
- ❌ **FAIL**: > 5 uses of `Any`
- ⚠️ **WARNING**: 1-5 uses of `Any`
- ✅ **PASS**: 0 uses of `Any`

**How to Fix**:
- Use specific types (`str`, `int`, `List[str]`, etc.)
- Create TypedDict for complex structures
- Use Union types for multiple possibilities
- Use type aliases for clarity

**Example**:
```python
# ❌ BAD - Any type
from typing import Any, Dict

def process_data(data: Dict[str, Any]) -> Any:
    return data.get("value")

# ✅ GOOD - Specific types
from typing import Dict, Union, TypedDict

class DataStructure(TypedDict):
    value: str
    count: int
    optional_field: Optional[str]

ValueType = Union[str, int, None]

def process_data(data: DataStructure) -> ValueType:
    return data.get("value")
```

---

### 4. Function Length
**Criterion**: Functions should be focused and readable

**Check**: `func-004`
- ❌ **FAIL**: > 50 lines
- ⚠️ **WARNING**: 30-50 lines
- ✅ **PASS**: < 30 lines

**How to Fix**:
- Extract helper methods
- Break complex logic into steps
- Use single responsibility principle

---

### 5. Module Size
**Criterion**: Modules should be manageable

**Check**: `module-005`
- ❌ **FAIL**: > 500 lines
- ⚠️ **WARNING**: 300-500 lines
- ✅ **PASS**: < 300 lines

**How to Fix**:
- Split large modules into smaller ones
- Group related functionality
- Use clear module boundaries

---

### 6. Cyclomatic Complexity
**Criterion**: Functions should have low complexity

**Check**: `complexity-006`
- ❌ **FAIL**: Complexity > 15
- ⚠️ **WARNING**: Complexity 10-15
- ✅ **PASS**: Complexity < 10

**How to Fix**:
- Extract complex conditionals into methods
- Use early returns
- Simplify nested logic

---

### 7. Documentation - Docstrings
**Criterion**: All public methods documented

**Check**: `doc-007`
- ❌ **FAIL**: < 50% have docstrings
- ⚠️ **WARNING**: 50-90% have docstrings
- ✅ **PASS**: > 90% have docstrings

**Example**:
```python
def execute_workflow(self, workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a GAO-Dev workflow with parameters.

    Args:
        workflow: Workflow information object
        params: Parameters for workflow execution

    Returns:
        Dictionary containing execution results with keys:
        - success: bool
        - instructions: str
        - template: str (if applicable)
        - output_file: str (if applicable)

    Raises:
        ValueError: If required parameters are missing
        FileNotFoundError: If workflow files not found
    """
```

---

### 8. Type Hints
**Criterion**: All function signatures typed

**Check**: `type-008`
- ❌ **FAIL**: < 50% have type hints
- ⚠️ **WARNING**: 50-90% have type hints
- ✅ **PASS**: > 90% have type hints

---

### 9. Error Handling
**Criterion**: Comprehensive error handling

**Check**: `error-009`
- ❌ **FAIL**: Bare except or missing error handling
- ⚠️ **WARNING**: Some error handling but not comprehensive
- ✅ **PASS**: All potential errors handled with specific exceptions

**Example**:
```python
# ❌ BAD - Bare except
try:
    do_something()
except:
    pass

# ✅ GOOD - Specific exceptions
try:
    do_something()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return default_value
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise
```

---

### 10. Naming Conventions
**Criterion**: Follow PEP 8 naming

**Check**: `naming-010`
- ✅ Classes: `PascalCase`
- ✅ Functions/methods: `snake_case`
- ✅ Constants: `ALL_CAPS`
- ✅ Private members: `_leading_underscore`

---

### 11. Import Organization
**Criterion**: Imports organized and clean

**Check**: `import-011`
- ✅ Standard library first
- ✅ Third-party next
- ✅ Local imports last
- ✅ No unused imports
- ✅ No wildcard imports

**Example**:
```python
# Standard library
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import click
import structlog
from anthropic import Anthropic

# Local
from ..core import ConfigLoader, WorkflowRegistry
from .models import WorkflowInfo
```

---

### 12. Single Responsibility Principle
**Criterion**: Classes/functions have one clear purpose

**Check**: `srp-012`
- ❌ **FAIL**: God objects, classes doing too much
- ⚠️ **WARNING**: Some mixed responsibilities
- ✅ **PASS**: Clear single responsibility

---

### 13. Dependency Injection
**Criterion**: Don't create dependencies, inject them

**Check**: `di-013`
- ✅ Dependencies passed as parameters
- ✅ No global state
- ✅ Testable design

**Example**:
```python
# ❌ BAD - Create dependencies
class Manager:
    def __init__(self):
        self.config = ConfigLoader()  # Hard dependency
        self.db = Database()          # Hard dependency

# ✅ GOOD - Inject dependencies
class Manager:
    def __init__(self, config: ConfigLoader, db: Database):
        self.config = config  # Injected
        self.db = db          # Injected
```

---

### 14. Test Coverage
**Criterion**: Comprehensive test coverage

**Check**: `test-014`
- ❌ **FAIL**: < 50% coverage
- ⚠️ **WARNING**: 50-80% coverage
- ✅ **PASS**: > 80% coverage

---

## Quality Scoring

### Module Score Calculation

Score = (Checks Passed / 14) × 100

| Score | Grade | Status |
|-------|-------|--------|
| 14/14 (100%) | A+ | ✅ Excellent |
| 13/14 (93%) | A | ✅ Good |
| 12/14 (86%) | B | ⚠️ Acceptable |
| 11/14 (79%) | C | ⚠️ Needs Improvement |
| < 11/14 (< 79%) | F | ❌ Unacceptable |

### Minimum Standards

**For Production**: All modules must score **12/14 or higher** (86%+)

**Critical Violations** (Auto-fail):
- More than 10 DRY violations
- More than 10 magic numbers
- More than 5 Any types
- Missing docstrings on public API
- Bare except clauses

---

## SOLID Principles

All GAO-Dev code must follow SOLID principles:

### S - Single Responsibility Principle
- Each class/function has ONE reason to change
- If you can describe it with "and", it's doing too much

### O - Open/Closed Principle
- Open for extension, closed for modification
- Use inheritance, composition, or plugins

### L - Liskov Substitution Principle
- Subtypes must be substitutable for base types
- Don't break contracts in subclasses

### I - Interface Segregation Principle
- Many specific interfaces better than one general
- Don't force clients to depend on unused methods

### D - Dependency Inversion Principle
- Depend on abstractions, not concrete implementations
- High-level modules shouldn't depend on low-level modules

---

## Clean Architecture Principles

### Layers
```
┌─────────────────────────────────┐
│   Presentation (CLI, UI)        │  # Depends on ↓
├─────────────────────────────────┤
│   Application (Use Cases)       │  # Depends on ↓
├─────────────────────────────────┤
│   Domain (Business Logic)       │  # Independent
├─────────────────────────────────┤
│   Infrastructure (DB, File I/O) │  # Depends on Domain
└─────────────────────────────────┘
```

**Rules**:
- Inner layers don't depend on outer layers
- Dependencies point inward
- Domain layer is pure business logic

---

## Code Review Checklist

Before merging:
- [ ] All 14 QA criteria pass
- [ ] Tests written and passing (> 80% coverage)
- [ ] Type hints on all functions
- [ ] Docstrings on public API
- [ ] No DRY violations
- [ ] No magic numbers
- [ ] No `Any` types
- [ ] SOLID principles followed
- [ ] Clean architecture maintained
- [ ] Code reviewed by at least one person
- [ ] Commit messages follow convention
- [ ] Documentation updated

---

## Automated QA Tools

### Type Checking
```bash
mypy gao_dev/ --strict
```

### Linting
```bash
ruff check gao_dev/
```

### Formatting
```bash
black gao_dev/ --line-length 100
```

### Testing
```bash
pytest tests/ --cov=gao_dev --cov-report=html
```

### Complexity Analysis
```bash
radon cc gao_dev/ -a
```

---

## Refactoring Guidelines

### When to Refactor

**Immediate** (before continuing):
- Fails critical violations (DRY > 10, magic numbers > 10)
- Missing type hints on public API
- No error handling

**Soon** (next sprint):
- Score < 12/14
- Multiple SOLID violations
- Test coverage < 80%

**Later** (backlog):
- Score 12-13/14 but could be improved
- Minor style issues
- Documentation gaps

### Refactoring Process

1. **Write Tests First**: Ensure current behavior captured
2. **Refactor Incrementally**: Small, testable changes
3. **Validate Continuously**: Tests must pass after each change
4. **Review Before/After**: Ensure improvement, no regression

---

## Quality Metrics to Track

For each module, track over time:
- QA score (out of 14)
- DRY violations count
- Magic numbers count
- Any type usage count
- Test coverage percentage
- Cyclomatic complexity average
- Lines of code

**Goal**: Trend toward higher scores and lower violations

---

## Examples from Codebase

### Good Example: state_manager.py (13/14)
- Clear helper methods
- No magic numbers
- Type-safe
- Good error handling
- Single responsibility per method

### Needs Improvement Example: server.py (11/14)
- Too many DRY violations
- God object pattern
- Needs refactoring into smaller modules

---

## Enforcement

### Pre-commit Hooks
- Run mypy (type checking)
- Run ruff (linting)
- Run black (formatting)

### CI/CD Pipeline
- Run full test suite
- Generate coverage report
- Fail if coverage < 80%
- Run QA validator
- Fail if critical violations

### Code Review
- Reviewer checks QA standards
- Use QA checklist
- Block merge if standards not met

---

**Remember**: Quality is not optional. It's faster to write quality code the first time than to refactor later.

---

*This document is adapted from BMAD MCP QA validation system and tailored for GAO-Dev.*
