# GAO-Dev Checklist Library

Comprehensive library of 25 quality checklists for software development, security, deployment, and operations.

## Overview

The GAO-Dev checklist library provides machine-readable, reusable checklists that ensure consistency and quality across all development workflows. All checklists are defined in YAML format, validated against a JSON schema, and can be loaded programmatically by agents or used manually by developers.

## Quick Start

```python
from gao_dev.core.checklists.checklist_loader import ChecklistLoader
from pathlib import Path

# Initialize loader
loader = ChecklistLoader(
    [Path("gao_dev/config/checklists")],
    Path("gao_dev/config/schemas/checklist_schema.json")
)

# Load a checklist
checklist = loader.load_checklist("testing/unit-test-standards")

# Render as markdown
markdown = loader.render_checklist(checklist)
print(markdown)
```

## Categories

### Testing (4 checklists)

#### base-testing-standards.yaml
**Extends:** None
**Items:** 4
**Use When:** Base for all testing checklists (inherited by others)

Foundation testing standards applicable to all test types.

**Key Items:**
- Tests exist for all new functionality (critical)
- All tests pass before committing (critical)
- Tests are well-documented (low)
- Tests are maintainable and follow DRY principle (medium)

#### unit-test-standards.yaml
**Extends:** testing/base-testing-standards
**Items:** 12
**Use When:** Implementing or reviewing unit tests

**Key Items:**
- Test coverage >80% for all new code (high)
- Tests are isolated and do not depend on execution order (critical)
- All tests complete in <5 seconds (medium)
- External dependencies are properly mocked (high)

**Usage:**
```bash
# Load programmatically
loader.load_checklist("testing/unit-test-standards")
```

#### integration-test-standards.yaml
**Extends:** testing/base-testing-standards
**Items:** 12
**Use When:** Implementing or reviewing integration tests

**Key Items:**
- Integration tests cover interactions between multiple components (high)
- Database setup and teardown are properly managed (critical)
- API contracts are tested (high)
- Environment is isolated from production (critical)

#### e2e-test-standards.yaml
**Extends:** testing/base-testing-standards
**Items:** 12
**Use When:** Implementing or reviewing end-to-end tests

**Key Items:**
- Critical user flows are tested end-to-end (critical)
- Browser automation is properly configured (high)
- Tests run in staging environment (high)
- Tests are reliable and not flaky (high)

---

### Code Quality (5 checklists)

#### solid-principles.yaml
**Items:** 7
**Use When:** Code review, architecture review, refactoring

Verifies adherence to SOLID principles in code design.

**Key Items:**
- Each class has a single, well-defined responsibility (high)
- Subtypes can be substituted for base types (high)
- High-level modules depend on abstractions (high)
- No 'God classes' with too many responsibilities (critical)

#### clean-code.yaml
**Items:** 8
**Use When:** Code review, story implementation, refactoring

Clean code practices and maintainability standards.

**Key Items:**
- Code follows DRY principle (high)
- Variables, functions, and classes have meaningful names (high)
- Functions are small and focused (<50 lines) (medium)
- Error handling is explicit and informative (high)

#### python-standards.yaml
**Items:** 8
**Use When:** Code review for Python code

Python-specific coding standards and best practices.

**Key Items:**
- Code follows PEP 8 style guide (medium)
- All public functions and classes have docstrings (high)
- Use context managers for resource management (high)
- Imports are organized and clean (low)

#### type-safety.yaml
**Items:** 8
**Use When:** Code review to ensure proper type annotations

Type hints and type safety standards for Python code.

**Key Items:**
- All public functions have type hints (critical)
- Avoid using 'Any' type (high)
- Code passes mypy in strict mode (high)
- Use generic types for collections (high)

#### refactoring.yaml
**Items:** 8
**Use When:** Code review, technical debt assessment

Identifies code smells and refactoring opportunities.

**Key Items:**
- No God classes (>300 lines) (critical)
- No significant code duplication (high)
- Functions have reasonable cyclomatic complexity (<10) (high)
- No deeply nested structures (>3 levels) (medium)

---

### Security (4 checklists)

#### owasp-top-10.yaml
**Items:** 10
**Use When:** Code review, security review, deployment

Security checklist based on OWASP Top 10 vulnerabilities.

**Key Items:**
- All database queries use parameterized statements (critical)
- All user input is sanitized before rendering (critical)
- No secrets in code or version control (critical)
- Strong authentication implemented (high)

**References:**
- https://owasp.org/www-community/attacks/SQL_Injection
- https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

#### secure-coding.yaml
**Items:** 8
**Use When:** Code review, security review, story implementation

Secure coding practices and vulnerability prevention.

**Key Items:**
- All user input is validated (critical)
- Output is properly encoded for context (critical)
- No command injection vulnerabilities (critical)
- Deserialization of untrusted data is avoided (critical)

#### secrets-management.yaml
**Items:** 8
**Use When:** Code review, security audit, deployment

Best practices for managing secrets and credentials.

**Key Items:**
- No secrets hardcoded in source code (critical)
- No secrets in version control history (critical)
- Secrets loaded from environment variables or secret management (high)
- Secrets are not logged or printed (critical)

#### api-security.yaml
**Items:** 9
**Use When:** API development, security review, code review

Security best practices for REST APIs and web services.

**Key Items:**
- Rate limiting is implemented (critical)
- Authentication uses secure tokens (critical)
- Authorization checks on all endpoints (critical)
- API only accepts HTTPS requests (critical)

**References:**
- https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html

---

### Deployment (4 checklists)

#### production-readiness.yaml
**Items:** Varies
**Use When:** Production deployment

Production deployment readiness checklist (created in Story 14.2).

#### rollout-checklist.yaml
**Items:** 8
**Use When:** Feature deployment, release planning

Ensures safe feature rollouts to production.

**Key Items:**
- Feature flags implemented for gradual rollout (high)
- Rollback plan documented and tested (critical)
- Monitoring and alerts configured (critical)
- Changes are backward compatible (critical)

#### database-migration.yaml
**Items:** 8
**Use When:** Database schema changes, data migrations

Safety checklist for database migrations.

**Key Items:**
- Migrations are reversible (critical)
- Migration tested in staging with production-like data (critical)
- Database backup taken before migration (critical)
- Application code compatible with old and new schema (critical)

#### configuration-management.yaml
**Items:** 8
**Use When:** Deployment, environment setup

Configuration management and environment setup checklist.

**Key Items:**
- Configuration is environment-specific (critical)
- Secrets managed via secret management system (critical)
- Configuration files are version controlled (high)
- Configuration validation on startup (high)

---

### Operations (4 checklists)

#### incident-response.yaml
**Items:** 8
**Use When:** Production incidents and outages

Guides incident response and resolution.

**Key Items:**
- Incident detected through monitoring (high)
- Incident communication started (critical)
- Mitigation actions started (critical)
- Postmortem scheduled within 48 hours (medium)

**References:**
- https://sre.google/sre-book/monitoring-distributed-systems/
- https://sre.google/sre-book/postmortem-culture/

#### change-management.yaml
**Items:** 8
**Use When:** Production changes, maintenance

Process checklist for managing changes to production systems.

**Key Items:**
- Change approved by stakeholders (high)
- Impact assessment completed (critical)
- Change tested in non-production environment (critical)
- Rollback plan documented (critical)

#### monitoring-setup.yaml
**Items:** 8
**Use When:** New service deployment, monitoring configuration

Comprehensive monitoring and observability checklist.

**Key Items:**
- Application metrics instrumented (critical)
- Structured logging configured (high)
- Alert thresholds configured (critical)
- Runbooks created for common alerts (high)

**References:**
- https://sre.google/sre-book/monitoring-distributed-systems/
- https://sre.google/sre-book/service-level-objectives/

#### disaster-recovery.yaml
**Items:** 8
**Use When:** DR planning and testing

Disaster recovery preparedness checklist.

**Key Items:**
- Backup procedures documented and automated (critical)
- Backup restoration tested regularly (critical)
- RTO and RPO defined (high)
- DR plan documented and accessible (critical)

**References:**
- https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/backup-and-restore.html

---

### General/Workflow (4 checklists)

#### code-review.yaml
**Items:** 8
**Use When:** Code review, PR review

Comprehensive code review checklist.

**Key Items:**
- Code logic is correct and handles edge cases (critical)
- Tests provide adequate coverage (high)
- Code follows quality standards (high)
- No obvious security vulnerabilities (critical)

#### pr-review.yaml
**Items:** 9
**Use When:** Pull request review before merging

Pull request review and merge checklist.

**Key Items:**
- PR has clear description (high)
- Tests added for new functionality (critical)
- All CI tests passing (critical)
- Code reviewed by at least one team member (critical)

#### documentation.yaml
**Items:** 8
**Use When:** Story implementation, documentation review

Documentation completeness and quality checklist.

**Key Items:**
- README.md exists with setup instructions (high)
- API documentation complete and up-to-date (high)
- All public functions/classes have docstrings (high)
- Architecture diagrams document system design (medium)

**References:**
- https://keepachangelog.com/

#### story-implementation.yaml
**Items:** 10
**Use When:** Story development to ensure completeness

Comprehensive checklist for implementing user stories.

**Key Items:**
- All acceptance criteria met (critical)
- All tests pass (critical)
- Test coverage >80% for new code (high)
- Code follows quality standards (high)

---

## Severity Levels

Checklists use four severity levels to prioritize items:

| Severity | Description | Example |
|----------|-------------|---------|
| **critical** | Deployment blockers, must fix | No SQL injection, migrations are reversible |
| **high** | Should fix before deployment | Test coverage >80%, health checks implemented |
| **medium** | Fix in near term | Functions <50 lines, no code duplication |
| **low** | Nice to have, can defer | Test names follow convention, comments are clear |

## Inheritance

Some checklists extend others to avoid duplication:

```
testing/base-testing-standards (parent)
  |
  +-- testing/unit-test-standards (child)
  +-- testing/integration-test-standards (child)
  +-- testing/e2e-test-standards (child)
```

When a checklist extends another:
- Child inherits all items from parent
- Child can override parent items (same ID)
- Child can add new items
- Metadata is merged (child overrides parent)

## Integration with Workflows

### Story Implementation Workflow

Use these checklists during story implementation:

```yaml
checklists:
  - testing/unit-test-standards       # Verify tests exist and pass
  - code-quality/clean-code           # Check code quality
  - code-quality/python-standards     # Python-specific standards
  - code-quality/type-safety          # Type hints
  - security/secure-coding            # Security checks
  - general/story-implementation      # Overall completeness
```

### Code Review Workflow

Use these checklists during code review:

```yaml
checklists:
  - general/code-review               # Comprehensive review
  - testing/unit-test-standards       # Verify tests
  - security/secure-coding            # Security review
```

### Deployment Workflow

Use these checklists before deployment:

```yaml
checklists:
  - deployment/production-readiness   # Ready for production
  - deployment/configuration-management # Config is correct
  - operations/monitoring-setup       # Monitoring configured
```

## CLI Usage

```bash
# List all checklists
gao-dev checklist list

# Show checklist details
gao-dev checklist show testing/unit-test-standards

# Validate a checklist file
gao-dev checklist validate gao_dev/config/checklists/testing/unit-test-standards.yaml

# Run checklist against code
gao-dev checklist run testing/unit-test-standards --story 14.3
```

## Creating Custom Checklists

See the [Checklist Authoring Guide](authoring-guide.md) for details on creating custom checklists.

### Basic Structure

```yaml
checklist:
  name: "My Custom Checklist"
  category: "testing"  # testing, code-quality, security, deployment, operations
  version: "1.0.0"
  description: "Brief description of checklist purpose"

  # Optional: Extend another checklist
  extends: "testing/base-testing-standards"

  items:
    - id: "my-item-1"
      text: "Clear, actionable item text"
      severity: "high"  # critical, high, medium, low
      help_text: "Guidance on how to complete this item"
      references:
        - "https://example.com/docs"

  metadata:
    domain: "software-engineering"
    applicable_to: ["story-implementation", "code-review"]
    author: "Your Name"
    tags: ["testing", "quality"]
```

## Plugin Integration

Plugins can provide custom checklists. Place checklist YAML files in your plugin directory:

```
my-plugin/
  checklists/
    my-category/
      custom-checklist.yaml
```

The ChecklistLoader will discover and load these automatically.

## Performance

- Single checklist load time: <10ms
- All 25 checklists load time: <1 second
- Checklists are cached after first load

## Validation

All checklists are validated against the JSON schema at:
- `gao_dev/config/schemas/checklist_schema.json`

To validate all checklists:

```python
from gao_dev.core.checklists.schema_validator import ChecklistSchemaValidator
from pathlib import Path

validator = ChecklistSchemaValidator(Path("gao_dev/config/schemas/checklist_schema.json"))
results = validator.validate_directory(Path("gao_dev/config/checklists"))

for file_path, (is_valid, errors) in results.items():
    if not is_valid:
        print(f"Invalid: {file_path}")
        for error in errors:
            print(f"  - {error}")
```

## Statistics

- **Total Checklists:** 25
- **Testing:** 4 (base + unit + integration + e2e)
- **Code Quality:** 5 (SOLID + clean-code + python + type-safety + refactoring)
- **Security:** 4 (OWASP + secure-coding + secrets + API)
- **Deployment:** 4 (production-readiness + rollout + DB migration + config)
- **Operations:** 4 (incident + change + monitoring + DR)
- **General:** 4 (code-review + PR-review + documentation + story)

## References

- [OWASP Top 10](https://owasp.org/www-top-ten/)
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [PEP 8](https://peps.python.org/pep-0008/)

## Contributing

To add a new checklist:

1. Create YAML file in appropriate category directory
2. Follow naming convention: `kebab-case.yaml`
3. Validate against schema
4. Add to this catalog
5. Write tests in `tests/core/checklists/`
6. Submit PR

## Support

For questions or issues with checklists:
- File an issue in the GAO-Dev repository
- Contact the GAO-Dev team
- See documentation at `docs/checklists/`
