# Story 14.1: Checklist YAML Schema

**Epic:** 14 - Checklist Plugin System
**Story Points:** 3
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Define JSON schema for checklist YAML format with validation. This establishes the standard format for all checklists in the system and enables validation, ensuring consistency across core and plugin checklists.

---

## Business Value

This story provides the foundation for the entire checklist system and enables quality gates across all GAO domains:

- **Consistency**: Standard format ensures all checklists structured the same way, enabling predictable processing and rendering
- **Validation**: JSON Schema validates checklists at load time, preventing runtime errors and ensuring data integrity
- **Documentation**: Schema serves as executable documentation for checklist authors, reducing learning curve by 80%
- **Extensibility**: Plugin checklists follow same format as core checklists, enabling seamless integration of domain-specific checklists (legal, ops, research)
- **Quality Gates**: Establishes foundation for automated quality enforcement across story implementation, code review, deployment, and operations
- **Cross-Domain Reusability**: Single checklist format works across dev, ops, legal, research domains (aligned with GAO's multi-team architecture)
- **Version Control**: Schema versioning enables evolution while maintaining backwards compatibility
- **Compliance**: Structured format supports compliance reporting and audit trails (e.g., "Was OWASP checklist executed?")
- **Measurability**: Standardized format enables metrics collection (checklist pass rate, most failed items, compliance trends)

---

## Acceptance Criteria

### JSON Schema Definition
- [ ] JSON Schema file created: `gao_dev/config/schemas/checklist_schema.json`
- [ ] Required fields defined: name, category, version, items
- [ ] Optional fields defined: extends, description, metadata, domain, tags
- [ ] Item fields specified: id, text, severity, category, help_text
- [ ] Schema validation with jsonschema library

### Field Specifications
- [ ] `name`: Unique checklist identifier (string)
- [ ] `category`: Checklist category (enum: testing, code-quality, security, deployment, operations, legal, compliance, research)
- [ ] `version`: Semantic version (pattern: "\\d+\\.\\d+\\.\\d+")
- [ ] `items`: Array of checklist items (min 1 item)
- [ ] `extends`: Parent checklist for inheritance (optional string)
- [ ] `severity`: Item severity (enum: critical, high, medium, low)
- [ ] `metadata`: Extensible object for custom fields

### Example Checklists
- [ ] 3 example checklists created as reference
- [ ] Examples cover different categories (testing, security, deployment)
- [ ] Examples demonstrate inheritance (extends field)
- [ ] Examples validated against schema

### Documentation
- [ ] Checklist authoring guide created
- [ ] Schema field descriptions complete
- [ ] Examples documented with explanations
- [ ] Plugin developer guide references schema

---

## Technical Notes

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GAO-Dev Checklist Schema",
  "type": "object",
  "required": ["checklist"],
  "properties": {
    "checklist": {
      "type": "object",
      "required": ["name", "category", "version", "items"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Unique checklist identifier",
          "minLength": 3,
          "maxLength": 100
        },
        "category": {
          "type": "string",
          "enum": [
            "testing",
            "code-quality",
            "security",
            "deployment",
            "operations",
            "legal",
            "compliance",
            "research"
          ],
          "description": "Primary category for this checklist"
        },
        "version": {
          "type": "string",
          "pattern": "^\\d+\\.\\d+\\.\\d+$",
          "description": "Semantic version (e.g., 1.0.0)"
        },
        "description": {
          "type": "string",
          "description": "Human-readable description of checklist purpose"
        },
        "extends": {
          "type": "string",
          "description": "Parent checklist to inherit from (e.g., 'testing/base-testing-standards')"
        },
        "items": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["id", "text", "severity"],
            "properties": {
              "id": {
                "type": "string",
                "description": "Unique item identifier within checklist",
                "pattern": "^[a-z0-9-]+$"
              },
              "text": {
                "type": "string",
                "description": "Checklist item text",
                "minLength": 10
              },
              "severity": {
                "type": "string",
                "enum": ["critical", "high", "medium", "low"],
                "description": "Importance level of this item"
              },
              "category": {
                "type": "string",
                "description": "Item subcategory (optional)"
              },
              "help_text": {
                "type": "string",
                "description": "Additional guidance for completing this item"
              },
              "references": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Links to documentation or standards"
              }
            }
          }
        },
        "metadata": {
          "type": "object",
          "properties": {
            "domain": {
              "type": "string",
              "enum": ["software-engineering", "operations", "legal", "research", "general"],
              "description": "Target domain for this checklist"
            },
            "applicable_to": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Contexts where this checklist applies (e.g., 'story-implementation', 'code-review')"
            },
            "author": {
              "type": "string",
              "description": "Checklist author"
            },
            "tags": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Tags for categorization and search"
            }
          }
        }
      }
    }
  }
}
```

### Example Checklist: Unit Test Standards

```yaml
# gao_dev/config/checklists/testing/unit-test-standards.yaml

checklist:
  name: "Unit Test Standards"
  category: "testing"
  version: "1.0.0"
  description: "Standards for unit tests in GAO-Dev projects"

  extends: "testing/base-testing-standards"

  items:
    - id: "test-coverage"
      text: "Test coverage is >80% for all new code"
      severity: "high"
      help_text: "Use pytest --cov to measure coverage. Focus on edge cases and error paths."
      references:
        - "https://docs.pytest.org/en/stable/how-to/coverage.html"

    - id: "test-isolation"
      text: "Tests are isolated and do not depend on execution order"
      severity: "critical"
      help_text: "Each test should set up its own fixtures and clean up after itself."

    - id: "test-performance"
      text: "All tests complete in <5 seconds"
      severity: "medium"
      help_text: "Use mocking for external dependencies. Slow tests should be marked with @pytest.mark.slow."

    - id: "test-naming"
      text: "Test names clearly describe what is being tested"
      severity: "low"
      help_text: "Use pattern: test_<function>_<scenario>_<expected_result>"

  metadata:
    domain: "software-engineering"
    applicable_to: ["story-implementation", "code-review", "pr-review"]
    author: "Murat"
    tags: ["testing", "quality", "python"]
```

### Example Checklist: OWASP Top 10

```yaml
# gao_dev/config/checklists/security/owasp-top-10.yaml

checklist:
  name: "OWASP Top 10 Security Checklist"
  category: "security"
  version: "1.0.0"
  description: "Security checklist based on OWASP Top 10 vulnerabilities"

  items:
    - id: "sql-injection"
      text: "All database queries use parameterized statements, no string concatenation"
      severity: "critical"
      help_text: "Use SQLAlchemy or parameterized queries. Never use f-strings or string concatenation with user input."
      references:
        - "https://owasp.org/www-community/attacks/SQL_Injection"

    - id: "xss-prevention"
      text: "All user input is sanitized before rendering in HTML"
      severity: "critical"
      help_text: "Use template engines that auto-escape (Jinja2). Never use innerHTML with user data."

    - id: "authentication"
      text: "Strong authentication implemented (password hashing, MFA support)"
      severity: "high"
      help_text: "Use bcrypt or Argon2 for password hashing. Never store plain text passwords."

    - id: "authorization"
      text: "Authorization checks on all protected resources"
      severity: "high"
      help_text: "Verify user permissions before allowing access to data or actions."

    - id: "secrets-management"
      text: "No secrets in code or version control"
      severity: "critical"
      help_text: "Use environment variables or secret management systems. Add .env to .gitignore."

  metadata:
    domain: "software-engineering"
    applicable_to: ["code-review", "security-review", "deployment"]
    author: "Winston"
    tags: ["security", "owasp", "vulnerabilities"]
```

### Validation Implementation

```python
# gao_dev/core/checklists/schema_validator.py
import jsonschema
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple

class ChecklistSchemaValidator:
    """Validates checklist YAML files against JSON Schema."""

    def __init__(self, schema_path: Path):
        """Initialize validator with schema file."""
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
        self.validator = jsonschema.Draft7Validator(self.schema)

    def validate(self, checklist_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate checklist data against schema.

        Args:
            checklist_data: Parsed checklist dictionary

        Returns:
            (is_valid, error_messages)

        Example:
            validator = ChecklistSchemaValidator(schema_path)
            is_valid, errors = validator.validate(checklist_data)
            if not is_valid:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        errors = []
        for error in self.validator.iter_errors(checklist_data):
            path = '.'.join(str(p) for p in error.path) if error.path else 'root'
            errors.append(f"{path}: {error.message}")

        return (len(errors) == 0, errors)

    def validate_file(self, checklist_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate checklist YAML file.

        Args:
            checklist_path: Path to checklist YAML file

        Returns:
            (is_valid, error_messages)
        """
        try:
            with open(checklist_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self.validate(data)
        except yaml.YAMLError as e:
            return (False, [f"YAML parsing error: {e}"])
        except FileNotFoundError:
            return (False, [f"File not found: {checklist_path}"])
        except Exception as e:
            return (False, [f"Unexpected error: {e}"])

    def validate_directory(self, checklists_dir: Path) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all checklist files in directory.

        Args:
            checklists_dir: Directory containing checklist YAML files

        Returns:
            Dict mapping file path to (is_valid, errors)
        """
        results = {}
        for checklist_file in checklists_dir.rglob("*.yaml"):
            results[str(checklist_file)] = self.validate_file(checklist_file)
        return results
```

**Files to Create:**
- `gao_dev/config/schemas/checklist_schema.json`
- `gao_dev/core/checklists/__init__.py`
- `gao_dev/core/checklists/schema_validator.py`
- `gao_dev/config/checklists/testing/unit-test-standards.yaml` (example)
- `gao_dev/config/checklists/security/owasp-top-10.yaml` (example)
- `gao_dev/config/checklists/deployment/production-readiness.yaml` (example)
- `docs/checklist-authoring-guide.md`
- `tests/core/checklists/test_schema_validator.py`
- `tests/core/checklists/fixtures/valid_checklist.yaml` (test fixture)
- `tests/core/checklists/fixtures/invalid_checklist.yaml` (test fixture)

**Dependencies:**
- None (foundational)

---

## Testing Requirements

### Unit Tests - Schema Validation

**Test Class: TestChecklistSchemaValidator**

1. **Valid Checklist Tests** - Test that well-formed checklists pass validation
   - [ ] Test minimal valid checklist (required fields only)
   - [ ] Test complete valid checklist (all fields populated)
   - [ ] Test checklist with inheritance (extends field)
   - [ ] Test checklist with all severity levels
   - [ ] Test checklist with references array
   - [ ] Test checklist with metadata object

2. **Invalid Checklist Tests** - Test that malformed checklists fail validation
   - [ ] Test missing required fields (name, category, version, items)
   - [ ] Test invalid enum values (category, severity)
   - [ ] Test invalid version pattern (not semver)
   - [ ] Test invalid item ID pattern (uppercase, spaces)
   - [ ] Test empty items array (minItems violation)
   - [ ] Test item text too short (<10 chars)
   - [ ] Test name too short (<3 chars) or too long (>100 chars)

3. **Pattern Validation Tests** - Test regex patterns
   - [ ] Test version pattern accepts: "1.0.0", "2.1.3", "10.20.30"
   - [ ] Test version pattern rejects: "1.0", "v1.0.0", "1.0.0-beta"
   - [ ] Test item ID pattern accepts: "test-coverage", "sql-injection", "item1"
   - [ ] Test item ID pattern rejects: "Test Coverage", "SQL_INJECTION", "item 1"

4. **Array Constraint Tests** - Test array validations
   - [ ] Test items array requires at least 1 item
   - [ ] Test items array can contain multiple items
   - [ ] Test references array is optional
   - [ ] Test tags array is optional

5. **YAML Parsing Tests** - Test file loading
   - [ ] Test valid YAML file loads successfully
   - [ ] Test invalid YAML file raises YAMLError
   - [ ] Test missing file returns appropriate error
   - [ ] Test UTF-8 encoding handled correctly

### Integration Tests

1. **Example Checklist Validation**
   - [ ] All 3 example checklists validate against schema
   - [ ] unit-test-standards.yaml is valid
   - [ ] owasp-top-10.yaml is valid
   - [ ] production-readiness.yaml is valid

2. **Directory Validation**
   - [ ] validate_directory() finds all YAML files recursively
   - [ ] validate_directory() reports valid and invalid files correctly
   - [ ] validate_directory() handles empty directory gracefully

3. **Inheritance Resolution** (prepares for Story 14.2)
   - [ ] Extends field references are syntactically valid
   - [ ] Extends field format is "category/checklist-name"

### Performance Tests

1. **Schema Validation Performance**
   - [ ] Single checklist validation completes in <10ms
   - [ ] Validation of 100 checklists completes in <1 second
   - [ ] Schema loading from file completes in <50ms

2. **Memory Usage**
   - [ ] Schema validator uses <10MB memory
   - [ ] Validation does not leak memory (test 1000 validations)

### Test Coverage Target
- [ ] Line coverage >95% (schema validator is critical path)
- [ ] Branch coverage >90% (all error paths tested)
- [ ] All schema rules have corresponding test case

### Test Fixtures

Create comprehensive test fixtures for validation:

```yaml
# tests/core/checklists/fixtures/valid_minimal.yaml
checklist:
  name: "Minimal Valid Checklist"
  category: "testing"
  version: "1.0.0"
  items:
    - id: "item1"
      text: "This is a valid item with minimum length"
      severity: "low"
```

```yaml
# tests/core/checklists/fixtures/invalid_missing_required.yaml
checklist:
  name: "Invalid Checklist"
  # Missing category (required field)
  version: "1.0.0"
  items:
    - id: "item1"
      text: "This checklist is invalid"
      severity: "low"
```

```yaml
# tests/core/checklists/fixtures/invalid_enum_value.yaml
checklist:
  name: "Invalid Enum Checklist"
  category: "invalid-category"  # Not in enum
  version: "1.0.0"
  items:
    - id: "item1"
      text: "This checklist has invalid enum"
      severity: "super-critical"  # Not in enum
```

---

## Documentation Requirements

### Checklist Authoring Guide

**Location:** `docs/checklist-authoring-guide.md`

Must include:
- [ ] Introduction to checklist system and philosophy
- [ ] Complete field reference with examples
- [ ] Step-by-step guide to creating new checklist
- [ ] Severity level guidelines (when to use critical vs high vs medium vs low)
- [ ] Category selection guide (which category for different use cases)
- [ ] Checklist inheritance patterns (when and how to use extends)
- [ ] Item ID naming conventions (kebab-case, descriptive, unique)
- [ ] Help text best practices (actionable, specific, include references)
- [ ] Metadata usage guide (domain, applicable_to, tags)
- [ ] Common pitfalls and how to avoid them
- [ ] Examples for each category (testing, security, deployment, operations, legal, compliance)
- [ ] Testing your checklist (validation, rendering)
- [ ] Contributing checklists to core library

### Schema Documentation

**Location:** `gao_dev/config/schemas/README.md`

Must include:
- [ ] JSON Schema specification reference
- [ ] All required fields with descriptions and examples
- [ ] All optional fields with descriptions and examples
- [ ] Enum value complete listings
- [ ] Pattern validations explained (version, item ID)
- [ ] Array constraint explanations (minItems, items schema)
- [ ] Nested object schemas (metadata, items)
- [ ] Validation error interpretation guide
- [ ] Schema evolution strategy (versioning, backwards compatibility)

### Plugin Developer Guide Updates

**Location:** `docs/plugin-development-guide.md`

Must add section on checklist plugins:
- [ ] How to provide custom checklists in plugins
- [ ] ChecklistPlugin interface (covered in Story 14.5)
- [ ] Directory structure for plugin checklists
- [ ] Validation requirements for plugin checklists
- [ ] Override behavior (plugin checklists override core)
- [ ] Example plugin with checklists

### API Documentation

**Location:** In code docstrings

Must include:
- [ ] ChecklistSchemaValidator class documentation
- [ ] All method docstrings with Args, Returns, Raises, Examples
- [ ] Type hints for all parameters and return values
- [ ] Usage examples in docstrings

---

## Implementation Details

### Development Approach

1. **Schema-First Design**
   - Create JSON Schema before any implementation code
   - Validate schema against JSON Schema specification (Draft 7)
   - Test schema with example data before writing code

2. **Iterative Example Development**
   - Start with minimal valid example
   - Add complete example with all fields
   - Add category-specific examples (testing, security, deployment)
   - Validate each example as created

3. **Validator Implementation**
   - Implement ChecklistSchemaValidator class
   - Use jsonschema library (standard, well-tested)
   - Add comprehensive error reporting
   - Add directory validation for bulk operations

4. **Testing Strategy**
   - Create test fixtures (valid and invalid checklists)
   - Test all schema rules systematically
   - Test error messages are helpful
   - Performance test with many checklists

5. **Documentation**
   - Write checklist authoring guide
   - Document all schema fields
   - Provide examples for each category
   - Update plugin developer guide

### Schema Design Decisions

**Choice: JSON Schema Draft 7**
- Rationale: Widely supported, mature, good tooling
- Alternative considered: OpenAPI schema
- Decision: JSON Schema is more flexible for validation

**Choice: YAML for Checklists**
- Rationale: Human-readable, supports comments, less verbose than JSON
- Alternative considered: JSON
- Decision: YAML better for human authoring

**Choice: Semantic Versioning for Checklist Versions**
- Rationale: Standard versioning scheme, clear compatibility signals
- Pattern: `\\d+\\.\\d+\\.\\d+` (e.g., "1.0.0")
- Enables future version compatibility checks

**Choice: Kebab-Case for Item IDs**
- Rationale: URL-safe, readable, consistent with common practice
- Pattern: `[a-z0-9-]+`
- Examples: "test-coverage", "sql-injection"

**Choice: Four Severity Levels**
- critical: Must fix before deployment
- high: Should fix before deployment
- medium: Fix in near term
- low: Nice to have, can defer

**Choice: Eight Core Categories**
- testing, code-quality, security, deployment, operations, legal, compliance, research
- Covers all GAO domains (dev, ops, legal, research)
- Extensible via plugins (plugins can add more)

### Integration Points

**With Epic 10 (Prompt Abstraction)**
- Checklist system follows same YAML-based pattern
- Similar validation approach (JSON Schema)
- Consistent with prompt template architecture

**With Epic 12 (Meta-Prompts)**
- Prepares for @checklist: references (Story 13.2)
- Checklist loading similar to prompt loading
- Cache-friendly design

**With Plugin System**
- ChecklistPlugin will extend this schema (Story 14.5)
- Plugin checklists validated same way as core
- Override behavior: plugin checklists can replace core checklists

### Risk Mitigation

**Risk: Schema too restrictive**
- Mitigation: metadata field allows custom extensions
- Mitigation: Validate but don't error on unknown fields (additionalProperties: true in metadata)

**Risk: Performance with many checklists**
- Mitigation: Cache loaded and validated checklists
- Mitigation: Lazy loading (only load when needed)

**Risk: Breaking changes to schema**
- Mitigation: Schema versioning support (future)
- Mitigation: Backwards compatibility testing

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] JSON Schema created and validated against Draft 7
- [ ] ChecklistSchemaValidator implemented
- [ ] 3 example checklists created and validated
- [ ] All examples validate against schema
- [ ] Comprehensive test suite (>95% coverage)
- [ ] All tests passing
- [ ] Documentation complete:
  - [ ] Checklist authoring guide
  - [ ] Schema documentation
  - [ ] API documentation (docstrings)
  - [ ] Plugin developer guide updated
- [ ] Performance benchmarks met (<10ms validation)
- [ ] No regression in existing functionality
- [ ] Code reviewed and approved
- [ ] Committed with atomic commit message:
  ```
  feat(epic-14): implement Story 14.1 - Checklist YAML Schema

  - Create JSON Schema for checklist format (Draft 7)
  - Define required fields (name, category, version, items)
  - Define optional fields (extends, description, metadata, domain, tags)
  - Add field validation (patterns, enums, constraints)
  - Implement ChecklistSchemaValidator with comprehensive error reporting
  - Create 3 example checklists (unit-test-standards, owasp-top-10, production-readiness)
  - Add checklist authoring guide with best practices
  - Add comprehensive test suite (>95% coverage)
  - Validate all examples against schema
  - Document all schema fields and design decisions

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
