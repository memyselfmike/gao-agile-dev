# Story 14.3: Core Checklist Library

**Epic:** 14 - Checklist Plugin System
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Create 20+ core checklists covering testing, code quality, security, deployment, and operations. Convert existing qa-comprehensive.md to YAML format and create focused, reusable checklists. This comprehensive library provides immediate value across all GAO-Dev workflows and serves as reference implementations for plugin developers.

---

## Business Value

This story delivers immediate, tangible value across the entire GAO-Dev ecosystem:

- **Quality Gates**: Automated quality enforcement at story implementation, code review, and deployment stages
- **Knowledge Codification**: Captures best practices from existing qa-comprehensive.md in machine-readable format
- **Consistency**: All teams use same quality standards, reducing variation and improving reliability
- **Onboarding**: New developers/agents learn standards from checklists, reducing ramp-up time by 60%
- **Compliance**: Security and deployment checklists ensure regulatory compliance (OWASP, production readiness)
- **Reusability**: Focused checklists can be mixed and matched for different contexts (story implementation uses testing + code-quality + security)
- **Extensibility**: Serves as reference implementation for plugin developers creating domain-specific checklists
- **Measurability**: Structured checklists enable metrics (which items fail most often, compliance trends over time)
- **Cross-Domain**: Covers dev, ops, security, compliance - aligned with GAO's multi-team vision

**Strategic Impact:**
- Enables autonomous quality enforcement (agents can self-check before submitting)
- Prepares for Epic 12 Meta-Prompts (@checklist: references)
- Foundation for quality metrics dashboard (which teams/agents have highest compliance)

---

## Acceptance Criteria

### Testing Checklists (4 checklists)

- [ ] `testing/base-testing-standards.yaml` - Common testing base (for inheritance)
  - Contains: test isolation, naming conventions, fixture management
  - Used by: All other testing checklists via extends
- [ ] `testing/unit-test-standards.yaml` - Unit test requirements
  - Extends: base-testing-standards
  - Contains: coverage >80%, fast execution <5s, mocking external dependencies
- [ ] `testing/integration-test-standards.yaml` - Integration test requirements
  - Extends: base-testing-standards
  - Contains: database setup/teardown, API contract testing, environment isolation
- [ ] `testing/e2e-test-standards.yaml` - End-to-end test requirements
  - Extends: base-testing-standards
  - Contains: user flow testing, browser automation, test data management

### Code Quality Checklists (5 checklists)

- [ ] `code-quality/solid-principles.yaml` - SOLID principles checklist
  - Contains: Single responsibility, Open/closed, Liskov substitution, Interface segregation, Dependency inversion
- [ ] `code-quality/clean-code.yaml` - Clean code practices
  - Contains: DRY principle, meaningful names, small functions, error handling
- [ ] `code-quality/python-standards.yaml` - Python-specific standards
  - Contains: PEP 8 compliance, docstrings, list comprehensions, context managers
- [ ] `code-quality/type-safety.yaml` - Type hints and mypy standards
  - Contains: Type hints on all functions, no Any types, mypy strict mode
- [ ] `code-quality/refactoring.yaml` - Refactoring checklist
  - Contains: God class detection, code duplication, cyclomatic complexity

### Security Checklists (4 checklists)

- [ ] `security/owasp-top-10.yaml` - OWASP Top 10 vulnerabilities
  - Contains: SQL injection, XSS, authentication, authorization, secrets management
- [ ] `security/secure-coding.yaml` - Secure coding practices
  - Contains: Input validation, output encoding, session management, error handling
- [ ] `security/secrets-management.yaml` - Secrets and credentials handling
  - Contains: No secrets in code, environment variables, secret rotation
- [ ] `security/api-security.yaml` - API security checklist
  - Contains: Rate limiting, authentication tokens, CORS, input validation

### Deployment Checklists (4 checklists)

- [ ] `deployment/production-readiness.yaml` - Production deployment checklist
  - Contains: Health checks, monitoring, database migrations, security scan
- [ ] `deployment/rollout-checklist.yaml` - Feature rollout checklist
  - Contains: Feature flags, rollback plan, monitoring alerts, documentation
- [ ] `deployment/database-migration.yaml` - Database migration safety
  - Contains: Reversible migrations, tested in staging, backup procedures
- [ ] `deployment/configuration-management.yaml` - Configuration checklist
  - Contains: Environment-specific configs, secrets management, version control

### Operations Checklists (4 checklists)

- [ ] `operations/incident-response.yaml` - Incident response checklist
  - Contains: Issue detection, communication, mitigation, postmortem
- [ ] `operations/change-management.yaml` - Change management process
  - Contains: Change approval, testing, rollback plan, communication
- [ ] `operations/monitoring-setup.yaml` - Monitoring and alerting setup
  - Contains: Application metrics, logging, traces, alerting thresholds
- [ ] `operations/disaster-recovery.yaml` - Disaster recovery checklist
  - Contains: Backup procedures, recovery testing, RTO/RPO, documentation

### General/Workflow Checklists (4 checklists)

- [ ] `general/code-review.yaml` - Code review checklist
  - Contains: Logic correctness, test coverage, code quality, security
- [ ] `general/pr-review.yaml` - Pull request review checklist
  - Contains: PR description, tests added, documentation updated, atomic commits
- [ ] `general/documentation.yaml` - Documentation standards
  - Contains: README, API docs, architecture diagrams, runbooks
- [ ] `general/story-implementation.yaml` - Story implementation checklist
  - Contains: Acceptance criteria met, tests passing, documentation updated

### Quality Requirements

- [ ] All 21 checklists validate against schema (Story 14.1)
- [ ] Each checklist has 5-15 items (focused, not overwhelming)
- [ ] All severity levels used appropriately:
  - critical: 2-3 items per checklist (must-fix)
  - high: 3-5 items per checklist (should-fix)
  - medium: 3-5 items per checklist (fix soon)
  - low: 1-3 items per checklist (nice-to-have)
- [ ] Help text provided for all high/critical items
- [ ] References provided for security and compliance items
- [ ] Inheritance used where appropriate (testing checklists extend base-testing-standards)
- [ ] Metadata fields populated:
  - domain: software-engineering, operations, general
  - applicable_to: story-implementation, code-review, deployment, etc.
  - author: Murat (testing), Winston (security), Bob (workflow)
  - tags: descriptive tags for search
- [ ] Integration test loads all 21 checklists successfully

**Files to Create:**
- 21 YAML files in `gao_dev/config/checklists/` (organized by category)
- `tests/core/checklists/test_core_library.py` (integration test)
- `docs/checklists/README.md` (checklist catalog)

**Dependencies:**
- Story 14.1 (Schema) - REQUIRED for validation
- Story 14.2 (ChecklistLoader) - REQUIRED for loading

---

## Technical Notes

### Checklist Design Patterns

**Pattern 1: Inheritance for Common Rules**

```yaml
# testing/base-testing-standards.yaml (parent)
checklist:
  name: "Base Testing Standards"
  category: "testing"
  version: "1.0.0"
  description: "Common testing standards inherited by all testing checklists"

  items:
    - id: "test-isolation"
      text: "Tests are isolated and do not depend on execution order"
      severity: "critical"
      help_text: "Each test should set up its own fixtures and clean up after itself."

    - id: "test-naming"
      text: "Test names clearly describe what is being tested"
      severity: "low"
      help_text: "Use pattern: test_<function>_<scenario>_<expected_result>"

# testing/unit-test-standards.yaml (child)
checklist:
  name: "Unit Test Standards"
  category: "testing"
  version: "1.0.0"
  description: "Standards for unit tests"

  extends: "testing/base-testing-standards"  # Inherits test-isolation and test-naming

  items:
    - id: "test-coverage"
      text: "Test coverage is >80% for all new code"
      severity: "high"
      help_text: "Use pytest --cov to measure coverage."
```

**Pattern 2: Severity Levels Guide**

- **critical**: Deployment blockers (security vulnerabilities, data loss risks)
  - Example: "No SQL injection vulnerabilities", "Database migrations are reversible"
- **high**: Should fix before deployment (test coverage, monitoring setup)
  - Example: "Test coverage >80%", "Health check endpoints implemented"
- **medium**: Fix in near term (code quality, refactoring)
  - Example: "Functions are <50 lines", "No code duplication"
- **low**: Nice to have, can defer (naming conventions, documentation style)
  - Example: "Test names follow convention", "Comments are clear"

**Pattern 3: Help Text Best Practices**

```yaml
# Good help text: Actionable, specific, includes tool/command
- id: "test-coverage"
  text: "Test coverage is >80% for all new code"
  severity: "high"
  help_text: "Use pytest --cov to measure coverage. Focus on edge cases and error paths."
  references:
    - "https://docs.pytest.org/en/stable/how-to/coverage.html"

# Bad help text: Vague, no actionable guidance
- id: "test-coverage"
  text: "Test coverage is adequate"
  severity: "medium"
  help_text: "Make sure you have enough tests."
```

### Converting qa-comprehensive.md to YAML

The existing `gao_dev/checklists/qa-comprehensive.md` should be decomposed into focused YAML checklists:

1. **Extract sections** - Each major section becomes a checklist
2. **Categorize items** - Assign to testing, code-quality, security, etc.
3. **Assign severity** - Based on impact (critical for security, high for tests, medium for quality)
4. **Add help text** - Convert prose into actionable help_text
5. **Remove duplication** - Use inheritance to avoid repeating common rules

**Example Conversion:**

```markdown
# qa-comprehensive.md (original)

## Testing Requirements
- All code must have tests
- Test coverage >80%
- Tests must pass

## Code Quality
- Follow SOLID principles
- No code duplication
- Functions <50 lines
```

Becomes:

```yaml
# testing/unit-test-standards.yaml
items:
  - id: "tests-required"
    text: "All new code has corresponding unit tests"
    severity: "critical"
  - id: "test-coverage"
    text: "Test coverage is >80%"
    severity: "high"
  - id: "tests-passing"
    text: "All tests pass in CI pipeline"
    severity: "critical"

# code-quality/clean-code.yaml
items:
  - id: "solid-principles"
    text: "Code follows SOLID principles"
    severity: "high"
  - id: "no-duplication"
    text: "No code duplication (DRY principle)"
    severity: "high"
  - id: "small-functions"
    text: "Functions are <50 lines"
    severity: "medium"
```

### Directory Structure

```
gao_dev/config/checklists/
├── testing/
│   ├── base-testing-standards.yaml
│   ├── unit-test-standards.yaml
│   ├── integration-test-standards.yaml
│   └── e2e-test-standards.yaml
├── code-quality/
│   ├── solid-principles.yaml
│   ├── clean-code.yaml
│   ├── python-standards.yaml
│   ├── type-safety.yaml
│   └── refactoring.yaml
├── security/
│   ├── owasp-top-10.yaml
│   ├── secure-coding.yaml
│   ├── secrets-management.yaml
│   └── api-security.yaml
├── deployment/
│   ├── production-readiness.yaml
│   ├── rollout-checklist.yaml
│   ├── database-migration.yaml
│   └── configuration-management.yaml
├── operations/
│   ├── incident-response.yaml
│   ├── change-management.yaml
│   ├── monitoring-setup.yaml
│   └── disaster-recovery.yaml
└── general/
    ├── code-review.yaml
    ├── pr-review.yaml
    ├── documentation.yaml
    └── story-implementation.yaml
```

**Files to Create:**
- 21 checklist YAML files (as above)
- `tests/core/checklists/test_core_library.py`
- `docs/checklists/README.md` (catalog of all checklists)
## Testing Requirements

### Unit Tests - Individual Checklist Validation

**Test Class: TestCoreChecklistLibrary**

1. **Schema Validation Tests**
   - [ ] All 21 checklists validate against schema
   - [ ] No schema validation errors
   - [ ] All required fields present in every checklist
   - [ ] All enum values are valid
   - [ ] All version strings match semver pattern
   - [ ] All item IDs match kebab-case pattern

2. **Inheritance Tests**
   - [ ] base-testing-standards is valid standalone
   - [ ] unit-test-standards correctly references base-testing-standards
   - [ ] integration-test-standards correctly references base-testing-standards
   - [ ] e2e-test-standards correctly references base-testing-standards
   - [ ] Extends field format is correct ("category/checklist-name")

3. **Content Quality Tests**
   - [ ] Each checklist has 5-15 items
   - [ ] All critical items have help_text
   - [ ] All high items have help_text
   - [ ] Security checklists have references
   - [ ] No duplicate item IDs within a checklist

4. **Metadata Tests**
   - [ ] All checklists have domain field
   - [ ] All checklists have applicable_to field
   - [ ] All checklists have author field
   - [ ] All checklists have tags field
   - [ ] Applicable_to values are meaningful

### Integration Tests

1. **Bulk Loading Test**
   - [ ] ChecklistLoader can load all 21 checklists
   - [ ] No loading errors or exceptions
   - [ ] Checklists loaded in <1 second total
   - [ ] All checklists accessible after loading

2. **Category Organization Test**
   - [ ] All 5 categories have checklists
   - [ ] testing/ has 4 checklists
   - [ ] code-quality/ has 5 checklists
   - [ ] security/ has 4 checklists
   - [ ] deployment/ has 4 checklists
   - [ ] operations/ has 4 checklists
   - [ ] general/ has 4 checklists (21 total)

3. **Cross-Reference Test**
   - [ ] All extends references resolve correctly
   - [ ] No circular dependencies
   - [ ] Referenced checklists exist

### Useability Tests

1. **Agent Integration Test**
   - [ ] Amelia can load story-implementation checklist
   - [ ] Checklist items are actionable for agent
   - [ ] Help text provides sufficient guidance

2. **Human Readability Test**
   - [ ] Checklist names are clear and descriptive
   - [ ] Item text is concise and understandable
   - [ ] Help text is actionable
   - [ ] Severity levels are appropriate

### Performance Tests

1. **Load Time Test**
   - [ ] Single checklist loads in <10ms
   - [ ] All 21 checklists load in <1 second
   - [ ] Memory usage <50MB for all loaded checklists

2. **Validation Time Test**
   - [ ] Single checklist validates in <10ms
   - [ ] All 21 checklists validate in <500ms

### Test Coverage Target
- [ ] Line coverage >80%
- [ ] All checklists tested for schema compliance
- [ ] Integration test covers all loading scenarios

---

## Documentation Requirements

### Checklist Catalog

**Location:** `docs/checklists/README.md`

Must include:
- [ ] Overview of checklist library purpose
- [ ] Complete list of all 21 checklists with descriptions
- [ ] Category-based organization
- [ ] Usage examples for each checklist
- [ ] Severity level explanation
- [ ] Inheritance relationships diagram
- [ ] Integration with workflows (when to use which checklists)
- [ ] Plugin extension guide

**Example Catalog Entry:**

```markdown
## Testing Checklists

### unit-test-standards.yaml
**Category:** testing
**Extends:** base-testing-standards
**Items:** 8
**Use When:** Implementing or reviewing unit tests

#### Key Items:
- Test coverage >80% (high)
- Tests run in <5 seconds (medium)
- No external dependencies (high)

#### Usage:
```bash
gao-dev checklist run testing/unit-test-standards --story 12.1
```
```

### Individual Checklist Documentation

Each checklist should have inline YAML comments explaining:
- [ ] Purpose of the checklist
- [ ] When to use it (applicable_to)
- [ ] How to interpret severity levels
- [ ] Common pitfalls to avoid

### Integration Guide

**Location:** `docs/checklists/integration-guide.md`

Must include:
- [ ] How to use checklists in story implementation workflow
- [ ] How to use checklists in code review workflow
- [ ] How to use checklists in deployment workflow
- [ ] How to combine multiple checklists
- [ ] How to create custom checklists (link to authoring guide)
- [ ] CLI commands for checklist operations

### Migration Guide

**Location:** `docs/checklists/migration-from-qa-comprehensive.md`

Must include:
- [ ] Mapping from qa-comprehensive.md sections to YAML checklists
- [ ] What changed and why
- [ ] How to update existing workflows
- [ ] Backwards compatibility notes
- [ ] Timeline for deprecating qa-comprehensive.md

---

## Implementation Details

### Development Approach

1. **Phase 1: Extract from qa-comprehensive.md (2 hours)**
   - Read existing qa-comprehensive.md
   - Identify major sections (testing, quality, security, etc.)
   - Map sections to checklist categories
   - Extract individual requirements

2. **Phase 2: Create Base Checklists (3 hours)**
   - Create base-testing-standards.yaml (parent for all testing)
   - Create testing checklists (unit, integration, e2e)
   - Create code-quality checklists (SOLID, clean-code, python, type-safety)
   - Validate against schema as you go

3. **Phase 3: Create Security Checklists (2 hours)**
   - Create owasp-top-10.yaml (most critical)
   - Create secure-coding.yaml
   - Create secrets-management.yaml
   - Create api-security.yaml
   - Add references to OWASP documentation

4. **Phase 4: Create Deployment & Operations Checklists (2 hours)**
   - Create production-readiness.yaml
   - Create rollout-checklist.yaml
   - Create database-migration.yaml
   - Create operations checklists
   - Focus on operational best practices

5. **Phase 5: Create General/Workflow Checklists (1 hour)**
   - Create code-review.yaml
   - Create pr-review.yaml
   - Create documentation.yaml
   - Create story-implementation.yaml
   - Link to other checklists (story-implementation uses testing + quality + security)

6. **Phase 6: Polish and Test (2 hours)**
   - Validate all checklists against schema
   - Add help_text to all high/critical items
   - Add references where appropriate
   - Write integration test
   - Write catalog documentation

**Total Estimated Time:** 12 hours (5 story points)

### Checklist Content Guidelines

**DO:**
- Use clear, actionable language ("Implement X", "Verify Y", "Ensure Z")
- Provide specific thresholds (">80% coverage", "<5 seconds", "<50 lines")
- Include tool/command in help_text ("Use pytest --cov")
- Add references for security/compliance items
- Use severity levels consistently
- Keep checklists focused (5-15 items)

**DON'T:**
- Use vague language ("Code is good", "Tests are adequate")
- Omit help_text for critical/high items
- Duplicate items across checklists (use inheritance)
- Create overly long checklists (>15 items)
- Mix unrelated concerns in one checklist

### Quality Assurance Process

1. **Self-Review**
   - Validate each checklist against schema as created
   - Review item text for clarity
   - Verify help_text is actionable
   - Check severity levels are appropriate

2. **Peer Review**
   - Have another developer review checklists
   - Verify domain expert input (e.g., Winston reviews security checklists)
   - Test checklists in actual workflow

3. **Automated Testing**
   - Run schema validation on all checklists
   - Run integration test to load all checklists
   - Verify no breaking changes to existing workflows

### Integration with Workflows

**Story Implementation Workflow:**
```yaml
# Workflow uses these checklists:
checklists:
  - testing/unit-test-standards
  - code-quality/clean-code
  - code-quality/python-standards
  - code-quality/type-safety
  - security/secure-coding
  - general/story-implementation
```

**Code Review Workflow:**
```yaml
# Workflow uses these checklists:
checklists:
  - general/code-review
  - testing/unit-test-standards  # Verify tests exist
  - security/secure-coding  # Check for vulnerabilities
```

**Deployment Workflow:**
```yaml
# Workflow uses these checklists:
checklists:
  - deployment/production-readiness
  - deployment/configuration-management
  - operations/monitoring-setup
```

### Risk Mitigation

**Risk: Checklists too prescriptive**
- Mitigation: Use severity levels (critical = must do, low = optional)
- Mitigation: Metadata field allows context-specific interpretation

**Risk: Checklist maintenance burden**
- Mitigation: Use inheritance to reduce duplication
- Mitigation: YAML format makes updates easy
- Mitigation: Automated validation prevents errors

**Risk: Resistance to using checklists**
- Mitigation: Make checklists useful, not bureaucratic
- Mitigation: Integrate into existing workflows (transparent)
- Mitigation: Show metrics on quality improvement

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] 21 checklists created in correct directory structure
- [ ] All checklists validate against schema (Story 14.1)
- [ ] Each checklist has 5-15 items
- [ ] All high/critical items have help_text
- [ ] Security checklists have references
- [ ] Inheritance used appropriately (testing checklists)
- [ ] Integration test loads all checklists successfully
- [ ] Integration test passes
- [ ] All tests passing (>80% coverage)
- [ ] Documentation complete:
  - [ ] Checklist catalog (README.md)
  - [ ] Integration guide
  - [ ] Migration guide from qa-comprehensive.md
- [ ] qa-comprehensive.md deprecated (or marked for removal)
- [ ] No regression in existing workflows
- [ ] Code reviewed and approved
- [ ] Performance benchmarks met (<1s to load all)
- [ ] Committed with atomic commit message:
  ```
  feat(epic-14): implement Story 14.3 - Core Checklist Library

  - Create 21 core checklists covering testing, code quality, security, deployment, operations
  - Convert qa-comprehensive.md to structured YAML checklists
  - Implement inheritance pattern (base-testing-standards extended by unit/integration/e2e)
  - Add comprehensive help_text for high/critical items
  - Add references for security checklists (OWASP, etc.)
  - Create checklist catalog documentation
  - Add integration test loading all 21 checklists
  - Organize checklists by category (testing, code-quality, security, deployment, operations, general)
  - Validate all checklists against schema

  Categories created:
  - Testing (4): base, unit, integration, e2e
  - Code Quality (5): SOLID, clean-code, python, type-safety, refactoring
  - Security (4): OWASP top 10, secure coding, secrets, API security
  - Deployment (4): production readiness, rollout, DB migration, configuration
  - Operations (4): incident response, change management, monitoring, disaster recovery
  - General (4): code review, PR review, documentation, story implementation

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
