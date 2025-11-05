# Checklist Authoring Guide

## Introduction

Checklists are a core component of the GAO-Dev quality gates system. They provide structured, repeatable validation criteria for various stages of the development lifecycle. This guide explains how to create, validate, and contribute checklists to the GAO-Dev system.

### Philosophy

Checklists in GAO-Dev follow these principles:

1. **Actionable**: Every item should be specific and actionable
2. **Measurable**: Items should have clear pass/fail criteria
3. **Contextual**: Checklists apply to specific contexts (story implementation, code review, deployment)
4. **Severity-aware**: Items are prioritized by severity (critical, high, medium, low)
5. **Educational**: Help text guides users on how to satisfy each item
6. **Reusable**: Checklists can inherit from other checklists to promote consistency

---

## Quick Start

### Creating Your First Checklist

1. **Choose a category**: Select from testing, code-quality, security, deployment, operations, legal, compliance, or research
2. **Create YAML file**: Place in `gao_dev/config/checklists/<category>/<name>.yaml`
3. **Define required fields**: name, category, version, items
4. **Add checklist items**: Each with id, text, and severity
5. **Validate**: Run validator to ensure schema compliance

### Minimal Example

```yaml
checklist:
  name: "My First Checklist"
  category: "testing"
  version: "1.0.0"
  items:
    - id: "basic-test"
      text: "All basic tests are passing"
      severity: "high"
```

---

## Field Reference

### Required Fields

#### `name` (string)
- **Description**: Unique identifier for the checklist
- **Constraints**: 3-100 characters
- **Example**: "Unit Test Standards", "OWASP Top 10 Security Checklist"
- **Best Practice**: Use descriptive names that clearly indicate the checklist's purpose

#### `category` (enum)
- **Description**: Primary category for organizing checklists
- **Valid Values**:
  - `testing` - Test-related checklists
  - `code-quality` - Code quality and style checklists
  - `security` - Security-focused checklists
  - `deployment` - Deployment and release checklists
  - `operations` - Operational readiness checklists
  - `legal` - Legal compliance checklists
  - `compliance` - Regulatory compliance checklists
  - `research` - Research validation checklists
- **Best Practice**: Choose the most specific category; use metadata.domain for cross-domain checklists

#### `version` (string)
- **Description**: Semantic version number
- **Pattern**: Must match `\d+\.\d+\.\d+` (e.g., "1.0.0")
- **Examples**: "1.0.0", "2.3.1", "10.0.5"
- **Best Practice**:
  - Increment MAJOR for breaking changes
  - Increment MINOR for new items
  - Increment PATCH for text corrections

#### `items` (array)
- **Description**: List of checklist items
- **Constraints**: Must have at least 1 item
- **See**: Item Fields section below

### Optional Fields

#### `description` (string)
- **Description**: Human-readable description of the checklist's purpose
- **Example**: "Standards for unit tests in GAO-Dev projects"
- **Best Practice**: Explain when and why to use this checklist

#### `extends` (string)
- **Description**: Parent checklist to inherit from
- **Format**: "category/checklist-name"
- **Example**: "testing/base-testing-standards"
- **Best Practice**: Use inheritance to avoid duplication and maintain consistency
- **Note**: Inheritance resolution implemented in Story 14.2

#### `metadata` (object)
- **Description**: Extensible metadata for categorization and context
- **Fields**:
  - `domain` (enum): software-engineering, operations, legal, research, general
  - `applicable_to` (array): Contexts where checklist applies
  - `author` (string): Checklist author
  - `tags` (array): Tags for search and categorization
- **Example**:
  ```yaml
  metadata:
    domain: "software-engineering"
    applicable_to: ["story-implementation", "code-review"]
    author: "Murat"
    tags: ["testing", "quality", "python"]
  ```

---

## Item Fields

Each checklist item has the following structure:

### Required Item Fields

#### `id` (string)
- **Description**: Unique identifier within the checklist
- **Pattern**: Must match `[a-z0-9-]+` (lowercase, numbers, hyphens only)
- **Examples**: "test-coverage", "sql-injection", "item1"
- **Invalid**: "Test Coverage", "SQL_INJECTION", "item 1"
- **Best Practice**: Use descriptive kebab-case identifiers

#### `text` (string)
- **Description**: The checklist item text shown to users
- **Constraints**: Minimum 10 characters
- **Example**: "Test coverage is >80% for all new code"
- **Best Practice**: Write clear, actionable statements; use specific criteria when possible

#### `severity` (enum)
- **Description**: Importance level of the item
- **Valid Values**:
  - `critical` - Must fix before deployment; system will fail/be insecure without it
  - `high` - Should fix before deployment; significant quality/security impact
  - `medium` - Fix in near term; moderate quality impact
  - `low` - Nice to have; can defer without significant impact
- **Best Practice**: See Severity Level Guidelines section below

### Optional Item Fields

#### `category` (string)
- **Description**: Item subcategory for grouping
- **Example**: "unit-tests", "integration-tests", "authentication"
- **Best Practice**: Use for organizing items within large checklists

#### `help_text` (string)
- **Description**: Additional guidance for completing the item
- **Example**: "Use pytest --cov to measure coverage. Focus on edge cases and error paths."
- **Best Practice**: Provide actionable guidance; include tool commands or reference materials

#### `references` (array of strings)
- **Description**: Links to documentation, standards, or resources
- **Example**:
  ```yaml
  references:
    - "https://docs.pytest.org/en/stable/how-to/coverage.html"
    - "https://owasp.org/www-community/attacks/SQL_Injection"
  ```
- **Best Practice**: Link to official documentation and authoritative sources

---

## Severity Level Guidelines

### When to Use Each Severity Level

#### Critical
- **Definition**: Must fix before deployment; failure creates security risk or system failure
- **Examples**:
  - No secrets in version control
  - SQL injection prevention
  - All database migrations tested and reversible
  - Tests are isolated (no interdependencies)
- **Impact if Skipped**: Security breach, data loss, system outage

#### High
- **Definition**: Should fix before deployment; significant quality or security impact
- **Examples**:
  - Test coverage >80%
  - Authorization checks on protected resources
  - Performance benchmarks meet SLA
  - Monitoring and alerting configured
- **Impact if Skipped**: Quality degradation, potential security issues, poor user experience

#### Medium
- **Definition**: Fix in near term; moderate quality impact
- **Examples**:
  - All tests complete in <5 seconds
  - Error messages don't expose sensitive info
  - Feature flags configured
  - Documentation complete
- **Impact if Skipped**: Technical debt accumulates, maintainability decreases

#### Low
- **Definition**: Nice to have; can defer without significant impact
- **Examples**:
  - Test names follow naming convention
  - Code comments are up to date
  - Incident response procedures documented
- **Impact if Skipped**: Minor inconvenience, cosmetic issues

---

## Category Selection Guide

### Testing
- **Use For**: Test coverage, test quality, test performance, test organization
- **Examples**: Unit test standards, integration test checklist, E2E test requirements
- **Typical Contexts**: story-implementation, code-review, pre-deployment

### Code-Quality
- **Use For**: Code style, maintainability, architecture, refactoring
- **Examples**: Python code standards, TypeScript best practices, clean architecture checklist
- **Typical Contexts**: code-review, pr-review, architecture-review

### Security
- **Use For**: Vulnerability prevention, secure coding, authentication, authorization
- **Examples**: OWASP Top 10, API security, secrets management
- **Typical Contexts**: code-review, security-review, deployment

### Deployment
- **Use For**: Production readiness, release procedures, deployment validation
- **Examples**: Production readiness checklist, deployment runbook, rollback plan
- **Typical Contexts**: deployment, production-release, go-live

### Operations
- **Use For**: Monitoring, alerting, incident response, system health
- **Examples**: SRE checklist, monitoring setup, incident response procedures
- **Typical Contexts**: post-deployment, operations, on-call

### Legal
- **Use For**: Terms of service, privacy policies, licensing, contracts
- **Examples**: GDPR compliance, privacy policy review, licensing audit
- **Typical Contexts**: legal-review, compliance-review, contract-signing

### Compliance
- **Use For**: Regulatory compliance, audit requirements, industry standards
- **Examples**: SOC2 compliance, HIPAA requirements, PCI-DSS checklist
- **Typical Contexts**: compliance-review, audit, certification

### Research
- **Use For**: Research methodology, experiment validation, data analysis
- **Examples**: Experiment design checklist, data quality validation, research ethics
- **Typical Contexts**: research-proposal, experiment-review, publication-review

---

## Checklist Inheritance

### When to Use Inheritance

Use the `extends` field to inherit from parent checklists when:
1. Creating specialized versions of general checklists (e.g., Python tests extending base testing standards)
2. Building domain-specific variants (e.g., legal team extending base compliance checklist)
3. Avoiding duplication across related checklists

### Inheritance Format

```yaml
checklist:
  name: "Child Checklist"
  category: "testing"
  version: "1.0.0"
  extends: "testing/parent-checklist"  # category/name format
  items:
    # Child items (merged with parent items)
```

### Inheritance Resolution (Story 14.2)

- Child items are merged with parent items
- Child items can override parent items with same ID
- Child severity can be stricter than parent (e.g., parent=medium, child=high)
- Circular inheritance is detected and rejected

---

## Best Practices

### Item Writing Guidelines

1. **Be Specific**: "Test coverage >80%" is better than "Good test coverage"
2. **Be Actionable**: Include what to do, not just what to check
3. **Include Context**: Use help_text to explain why the item matters
4. **Provide Resources**: Link to documentation, tools, or examples
5. **Use Consistent Language**: Imperative mood ("Ensure...", "Verify...") or declarative ("Tests pass")

### Example: Poor vs. Good Items

**Poor Item:**
```yaml
- id: "tests"
  text: "Tests are good"
  severity: "medium"
```

**Good Item:**
```yaml
- id: "test-coverage"
  text: "Test coverage is >80% for all new code"
  severity: "high"
  help_text: "Use pytest --cov to measure coverage. Focus on edge cases and error paths."
  references:
    - "https://docs.pytest.org/en/stable/how-to/coverage.html"
```

### Checklist Organization

1. **Order by Severity**: Place critical items first
2. **Group Related Items**: Use category field for grouping
3. **Limit Checklist Size**: 5-15 items per checklist is ideal; use inheritance for larger sets
4. **One Concern Per Checklist**: Don't mix security and testing in one checklist

### Versioning Strategy

1. **Start at 1.0.0**: Initial release version
2. **Increment PATCH (1.0.1)**: Typo fixes, clarifications, help text improvements
3. **Increment MINOR (1.1.0)**: New items added, non-breaking changes
4. **Increment MAJOR (2.0.0)**: Items removed, severity changes, breaking changes

---

## Common Pitfalls

### 1. Vague Items
**Problem**: "Code quality is acceptable"
**Solution**: "Code passes Ruff linting with zero errors"

### 2. Incorrect Severity
**Problem**: Marking "Update README" as critical
**Solution**: Use low severity for documentation unless it's critical compliance docs

### 3. Invalid Item IDs
**Problem**: "Test_Coverage" or "test coverage"
**Solution**: "test-coverage" (lowercase, hyphens only)

### 4. Missing Help Text
**Problem**: Item text only, no guidance
**Solution**: Add help_text with specific commands or procedures

### 5. Wrong Version Format
**Problem**: "1.0" or "v1.0.0"
**Solution**: "1.0.0" (semantic version without prefix)

### 6. Empty Items Array
**Problem**: Creating a checklist with no items
**Solution**: Every checklist must have at least 1 item

### 7. Item Text Too Short
**Problem**: "Tests pass"
**Solution**: "All unit tests pass with >80% coverage" (minimum 10 characters)

---

## Testing Your Checklist

### Validation

Use the ChecklistSchemaValidator to validate your checklist:

```python
from pathlib import Path
from gao_dev.core.checklists import ChecklistSchemaValidator

schema_path = Path("gao_dev/config/schemas/checklist_schema.json")
validator = ChecklistSchemaValidator(schema_path)

checklist_path = Path("gao_dev/config/checklists/testing/my-checklist.yaml")
is_valid, errors = validator.validate_file(checklist_path)

if is_valid:
    print("Checklist is valid!")
else:
    for error in errors:
        print(f"Validation error: {error}")
```

### Automated Validation

Run validation on all checklists in a directory:

```python
results = validator.validate_directory(Path("gao_dev/config/checklists"))

for file_path, (is_valid, errors) in results.items():
    if not is_valid:
        print(f"{file_path}:")
        for error in errors:
            print(f"  - {error}")
```

---

## Example Checklists

### Example 1: Testing Checklist

```yaml
checklist:
  name: "Unit Test Standards"
  category: "testing"
  version: "1.0.0"
  description: "Standards for unit tests in GAO-Dev projects"

  items:
    - id: "test-coverage"
      text: "Test coverage is >80% for all new code"
      severity: "high"
      help_text: "Use pytest --cov to measure coverage."
      references:
        - "https://docs.pytest.org/en/stable/how-to/coverage.html"

    - id: "test-isolation"
      text: "Tests are isolated and do not depend on execution order"
      severity: "critical"
      help_text: "Each test should set up its own fixtures."

  metadata:
    domain: "software-engineering"
    applicable_to: ["story-implementation", "code-review"]
    author: "Murat"
    tags: ["testing", "quality"]
```

### Example 2: Security Checklist

```yaml
checklist:
  name: "API Security Checklist"
  category: "security"
  version: "1.0.0"
  description: "Security requirements for REST APIs"

  items:
    - id: "authentication-required"
      text: "All API endpoints require authentication except public endpoints"
      severity: "critical"
      help_text: "Use JWT tokens or API keys. Document public endpoints."

    - id: "rate-limiting"
      text: "Rate limiting is configured on all API endpoints"
      severity: "high"
      help_text: "Prevent abuse with rate limiting. Use 1000 req/hour for authenticated users."

    - id: "input-validation"
      text: "All API inputs are validated against a schema"
      severity: "high"
      help_text: "Use Pydantic models or JSON Schema for validation."

  metadata:
    domain: "software-engineering"
    applicable_to: ["code-review", "security-review"]
    author: "Winston"
    tags: ["security", "api", "rest"]
```

### Example 3: Deployment Checklist

```yaml
checklist:
  name: "Production Deployment Checklist"
  category: "deployment"
  version: "1.0.0"
  description: "Pre-deployment validation for production releases"

  items:
    - id: "all-tests-passing"
      text: "All tests are passing in CI/CD pipeline"
      severity: "critical"
      help_text: "Check CI dashboard. All unit, integration, and E2E tests must pass."

    - id: "database-migrations-tested"
      text: "Database migrations tested and reversible"
      severity: "critical"
      help_text: "Test migrations in staging. Document rollback procedure."

    - id: "monitoring-configured"
      text: "Monitoring and alerting are configured"
      severity: "high"
      help_text: "Set up application metrics and alerts. Configure on-call rotation."

    - id: "rollback-plan"
      text: "Rollback plan documented and tested"
      severity: "high"
      help_text: "Document rollback steps. Test in staging environment."

  metadata:
    domain: "software-engineering"
    applicable_to: ["deployment", "production-release"]
    author: "Winston"
    tags: ["deployment", "production", "release"]
```

---

## Contributing Checklists

### To Core Library

1. **Create Checklist**: Follow this guide to create a well-formed checklist
2. **Validate**: Ensure it passes schema validation
3. **Document**: Add clear description and help text
4. **Submit PR**: Submit pull request with checklist file
5. **Review**: Checklist will be reviewed for quality and applicability

### Via Plugins

For domain-specific or organization-specific checklists:

1. **Create Plugin**: Develop a checklist plugin (see Plugin Developer Guide)
2. **Add Checklists**: Place YAML files in plugin's checklists directory
3. **Register**: Plugin system automatically discovers and loads checklists
4. **Override**: Plugin checklists can override core checklists

---

## Advanced Topics

### Custom Metadata Fields

The metadata object supports custom fields for specialized use cases:

```yaml
metadata:
  domain: "legal"
  author: "Legal Team"
  tags: ["gdpr", "privacy"]

  # Custom fields
  jurisdiction: "EU"
  last_reviewed: "2025-01-15"
  review_frequency: "quarterly"
```

### Multi-Domain Checklists

For checklists that apply across domains:

```yaml
metadata:
  domain: "general"
  applicable_to: ["story-implementation", "deployment", "operations"]
```

### Conditional Items (Future)

Story 14.3 will add support for conditional items:

```yaml
items:
  - id: "conditional-item"
    text: "Item that only applies in certain contexts"
    severity: "high"
    conditions:
      when: "context.environment == 'production'"
```

---

## Schema Reference

### JSON Schema Location

`gao_dev/config/schemas/checklist_schema.json`

### Validation Tools

- **ChecklistSchemaValidator**: Python class for validation
- **validate_file()**: Validate single YAML file
- **validate_directory()**: Validate all YAML files in directory
- **validate()**: Validate parsed checklist data

### Error Messages

Common validation errors and solutions:

| Error | Solution |
|-------|----------|
| "Missing required property 'name'" | Add name field to checklist |
| "'category' is not one of ['testing', ...]" | Use valid category enum value |
| "does not match pattern '^\\d+\\.\\d+\\.\\d+$'" | Use semantic version format (e.g., "1.0.0") |
| "'id' does not match pattern '^[a-z0-9-]+$'" | Use lowercase kebab-case for item IDs |
| "is too short" | Ensure text is at least 10 characters |
| "[] is too short" | Add at least one item to items array |

---

## FAQ

**Q: Can I have multiple checklists with the same name?**
A: No, checklist names should be unique. Use category and metadata to differentiate similar checklists.

**Q: How do I know which severity to use?**
A: See Severity Level Guidelines section. When in doubt, use high for quality/security items, medium for best practices.

**Q: Can I use custom categories?**
A: No, use one of the 8 predefined categories. Use metadata.domain and tags for additional categorization.

**Q: What if my item text is less than 10 characters?**
A: Expand it to be more descriptive. "Tests pass" → "All unit tests pass successfully"

**Q: Can I reference other checklists?**
A: Yes, use the extends field. Full inheritance resolution comes in Story 14.2.

**Q: How do I add checklist to a plugin?**
A: See Plugin Developer Guide for checklist plugin instructions (Story 14.5).

---

## Resources

- **JSON Schema**: `gao_dev/config/schemas/checklist_schema.json`
- **Example Checklists**: `gao_dev/config/checklists/`
- **Validator Code**: `gao_dev/core/checklists/schema_validator.py`
- **Tests**: `tests/core/checklists/test_schema_validator.py`
- **Plugin Guide**: `docs/plugin-development-guide.md`

---

## Changelog

### Version 1.0.0 (Story 14.1)
- Initial checklist authoring guide
- JSON Schema definition
- Field reference and examples
- Best practices and common pitfalls
- Validation instructions
