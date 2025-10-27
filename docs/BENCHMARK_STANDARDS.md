# Benchmark Standards - GAO-Dev

**Version**: 1.0.0
**Last Updated**: 2025-10-27
**Purpose**: Define standards for creating and maintaining reproducible benchmarks

---

## Table of Contents

1. [Why Standardized Prompts?](#why-standardized-prompts)
2. [The Golden Rules](#the-golden-rules)
3. [Benchmark Levels](#benchmark-levels)
4. [Creating a Benchmark](#creating-a-benchmark)
5. [Initial Prompt Guidelines](#initial-prompt-guidelines)
6. [Versioning Benchmarks](#versioning-benchmarks)
7. [Success Criteria](#success-criteria)
8. [Tracking Metrics](#tracking-metrics)

---

## Why Standardized Prompts?

### The Problem

Without standardized prompts, we cannot:
- Compare runs meaningfully (different inputs = different outputs)
- Track improvement over time
- Identify regressions
- Make data-driven decisions

### The Solution

**Standardized Initial Prompts** ensure:
- ✅ **Consistency**: Same starting point every time
- ✅ **Reproducibility**: Results can be verified
- ✅ **Comparability**: Run N vs. Run N+1 is apples-to-apples
- ✅ **Trending**: Track improvement across iterations
- ✅ **Baseline**: Clear reference point for all measurements

### Example: Why This Matters

**Without standardization**:
```
Run 001: "Build a todo app"
Run 002: "Build a todo app with authentication"
Run 003: "Build a simple todo list"
```
→ Cannot compare! Different features, different complexity.

**With standardization**:
```
Run 001: [todo-app-baseline.yaml] → 3 hours, 5 interventions
Run 002: [todo-app-baseline.yaml] → 2.5 hours, 3 interventions ✓ IMPROVEMENT!
Run 003: [todo-app-baseline.yaml] → 2 hours, 1 intervention ✓ MORE IMPROVEMENT!
```
→ Clear trend, measurable progress!

---

## The Golden Rules

### Rule 1: Never Modify Initial Prompts

**Once a benchmark starts tracking metrics, its `initial_prompt` is IMMUTABLE.**

❌ **WRONG**:
```yaml
# First run
initial_prompt: "Build a todo app"

# Later (after seeing issues)
initial_prompt: "Build a todo app with better error handling"
```

✓ **CORRECT**:
```yaml
# Create a new version
# Old: todo-app-baseline-v1.yaml
# New: todo-app-baseline-v2.yaml
```

### Rule 2: Version Control Everything

Every benchmark file must:
- Be in git version control
- Include version history section
- Document all changes
- Include prompt hash for verification

### Rule 3: One Benchmark = One Standardized Prompt

Each benchmark measures ONE specific task. Don't:
- Mix multiple features
- Change requirements between runs
- Add "just one more thing"

### Rule 4: Detailed Over Vague

Prompts should be:
- ✅ **Specific**: "Add pagination with 10 items per page"
- ❌ **Vague**: "Add pagination"

- ✅ **Measurable**: "80% test coverage"
- ❌ **Unmeasurable**: "Good test coverage"

### Rule 5: Document Expected Outcomes

Every benchmark must define:
- Target completion time
- Expected number of manual interventions
- Acceptable ranges for metrics
- Success criteria

---

## Benchmark Levels

### Level 1: Simple (30-60 min)

**Purpose**: Quick validation, smoke tests
**Complexity**: Low
**Example**: Simple REST API with 3 endpoints

**Use When**:
- Testing small changes
- Quick validation
- Initial capability testing

**Characteristics**:
- 3-5 features max
- No authentication
- In-memory data storage
- Basic testing
- < 1 hour to complete

### Level 2: Medium (1-2 hours)

**Purpose**: Core functionality testing
**Complexity**: Medium
**Example**: Todo app without authentication

**Use When**:
- Testing significant changes
- Validating core workflows
- Pre-baseline validation

**Characteristics**:
- 5-10 features
- Database integration
- Comprehensive testing
- Some complexity (filtering, sorting)
- 1-2 hours to complete

### Level 3: High (2-4 hours)

**Purpose**: Production-ready validation (THE GOLD STANDARD)
**Complexity**: High
**Example**: Full-stack todo app with auth, tests, deployment

**Use When**:
- Measuring full autonomy
- Validating production readiness
- Official benchmark runs
- Comparing to other systems

**Characteristics**:
- 10+ features
- Authentication/authorization
- Complete test suite (unit, integration, E2E)
- Security considerations
- Deployment configuration
- Comprehensive documentation
- 2-4 hours to complete

---

## Creating a Benchmark

### Step 1: Choose Complexity Level

Pick the appropriate level (1, 2, or 3) based on:
- What you're testing
- Available time
- Current system capabilities

### Step 2: Copy the Template

```bash
cp benchmarks/templates/benchmark-template.yaml \
   benchmarks/my-new-benchmark.yaml
```

### Step 3: Craft the Initial Prompt

This is the MOST IMPORTANT step!

**Guidelines**:
1. Be extremely specific
2. List exact features required
3. Define technical requirements clearly
4. Specify testing expectations
5. Include documentation requirements
6. Define success criteria in the prompt

**Template Structure**:
```
Build a [type] application with [features].

Frontend Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
...

Backend Requirements:
- [Specific requirement 1]
- [Specific requirement 2]
...

Technical Requirements:
- [Language/framework]
- [Testing requirements]
...

Success Criteria:
- [Measurable criterion 1]
- [Measurable criterion 2]
...
```

### Step 4: Define Success Criteria

For each criterion, specify:
- **Name**: What it measures
- **Type**: Category (functional, test, quality, etc.)
- **Required**: true/false
- **Threshold**: Numeric target (if applicable)
- **Validation**: How to verify

### Step 5: Set Expected Outcomes

Based on current capabilities, estimate:
- Manual interventions needed
- Time to complete
- Completion percentage
- Cost

Be realistic! These will improve over time.

### Step 6: Run Initial Validation

Before making it official:
1. Run the benchmark once manually
2. Validate timing estimates
3. Confirm success criteria are achievable
4. Adjust if needed (BEFORE tracking begins!)

### Step 7: Lock It Down

Once you start tracking:
1. Commit to git
2. Add to version control
3. Document as "baseline"
4. **NEVER modify the initial_prompt**

---

## Initial Prompt Guidelines

### Anatomy of a Good Prompt

```
Build a [WHAT] with [KEY FEATURES].

[SECTION 1: Frontend Requirements]
- Specific, measurable requirements
- UI/UX expectations
- Responsiveness needs
- Accessibility requirements

[SECTION 2: Backend Requirements]
- API endpoints (be specific!)
- Data models
- Business logic
- Authentication/authorization

[SECTION 3: Technical Requirements]
- Exact tech stack
- Testing expectations
- Code quality standards
- Error handling

[SECTION 4: Documentation]
- What docs are needed
- Level of detail required

[SECTION 5: Success Criteria]
- How to know it's done
- What "working" means
- Quality bars to meet
```

### Good Example

```yaml
initial_prompt: |
  Build a REST API for managing tasks.

  API Endpoints:
  - GET /tasks - Return all tasks (JSON array)
  - POST /tasks - Create task (require: title, description)
  - PUT /tasks/:id - Update task
  - DELETE /tasks/:id - Delete task

  Data Model:
  - Task: { id: uuid, title: string, description: string, completed: boolean, createdAt: timestamp }

  Technical Requirements:
  - Node.js with Express
  - TypeScript (strict mode)
  - Jest for testing
  - At least 80% test coverage
  - OpenAPI documentation

  Success Criteria:
  - All 4 endpoints functional
  - All tests passing
  - Zero TypeScript errors
  - API documented
```

### Bad Example

```yaml
initial_prompt: |
  Build a task management system.
  It should have an API.
  Make it good.
```

❌ Too vague!
❌ No specific features
❌ No technical requirements
❌ No success criteria

---

## Versioning Benchmarks

### When to Create a New Version

Create a new version (v2, v3, etc.) when:
- Prompt needs to change
- Requirements evolve
- Technology changes significantly
- Success criteria need adjustment

### Versioning Convention

```
Format: [benchmark-name]-v[major].[minor].yaml

Examples:
- todo-app-baseline-v1.0.yaml
- todo-app-baseline-v2.0.yaml
- simple-api-baseline-v1.0.yaml
- simple-api-baseline-v1.1.yaml
```

**Major version** (v1, v2, v3):
- Significant prompt changes
- Different features
- Breaking changes

**Minor version** (v1.1, v1.2):
- Clarifications
- Small adjustments
- Non-breaking changes

### Version History

Every version must document:
```yaml
version_history:
  - version: "2.0.0"
    date: "2025-11-01"
    changes: "Added authentication requirement"
    prompt_hash: "sha256:abc123..."
    reason: "Testing auth capabilities"
    breaking_changes: true
```

### Comparing Across Versions

**Valid comparison**:
- Run 1 vs. Run 2 (same version) ✓

**Invalid comparison**:
- Run 1 (v1.0) vs. Run 2 (v2.0) ✗

---

## Success Criteria

### Types of Criteria

| Type | Measures | Example |
|------|----------|---------|
| `functional` | Features work | "All CRUD operations functional" |
| `test_results` | Tests passing | "100% tests pass" |
| `coverage` | Code coverage | ">=80% coverage" |
| `type_check` | Type safety | "Zero TypeScript errors" |
| `lint` | Code quality | "Zero ESLint errors" |
| `security` | Security issues | "Zero high/critical vulnerabilities" |
| `documentation` | Docs complete | "README includes API docs" |
| `deployment` | Can deploy | "docker-compose up works" |
| `accessibility` | A11y compliance | "WCAG 2.1 AA compliant" |

### Defining Criteria

```yaml
success_criteria:
  - name: "All features functional"
    type: "functional"
    required: true
    validation: "Manual testing of all features"

  - name: "Test coverage >= 80%"
    type: "coverage"
    threshold: 80
    required: true
    validation: "Coverage report shows >=80%"

  - name: "Zero TypeScript errors"
    type: "type_check"
    threshold: 0
    required: true
    validation: "tsc --noEmit passes"
```

---

## Tracking Metrics

### Four Metric Categories

1. **Performance Metrics**
   - Total time (start → finish)
   - Time per phase
   - Token usage
   - API cost

2. **Autonomy Metrics**
   - Manual interventions required
   - One-shot success rate
   - Error recovery rate
   - Agent handoff success

3. **Quality Metrics**
   - Test coverage
   - Type errors
   - Lint errors
   - Security vulnerabilities
   - Code quality score

4. **Workflow Metrics**
   - Stories created/completed
   - Cycle time
   - Rework rate
   - Phase distribution

### Recording Results

After each run, document in `ITERATION_LOG.md`:
- Which benchmark was used
- Actual vs. expected metrics
- What worked / what didn't
- Improvements made
- Next steps

---

## Best Practices

### DO

- ✅ Keep prompts detailed and specific
- ✅ Version control all benchmarks
- ✅ Document expected outcomes
- ✅ Run initial validation before tracking
- ✅ Create new versions when needed
- ✅ Track metrics consistently
- ✅ Review and iterate

### DON'T

- ❌ Modify prompts after tracking begins
- ❌ Make vague requirements
- ❌ Skip success criteria
- ❌ Compare different versions
- ❌ Change benchmarks mid-tracking
- ❌ Forget to document changes

---

## Example Workflow

### Initial Setup
```bash
# 1. Choose benchmark level
Level 2 (Medium complexity)

# 2. Copy template
cp benchmarks/templates/benchmark-template.yaml \
   benchmarks/my-feature-v1.yaml

# 3. Fill in details
# - Craft detailed initial_prompt
# - Define success criteria
# - Set expected outcomes

# 4. Validate
gao-dev sandbox init test-run-001
# Run manually, time it, validate
gao-dev sandbox clean test-run-001 --force

# 5. Commit
git add benchmarks/my-feature-v1.yaml
git commit -m "feat: add my-feature benchmark v1.0"
```

### Running Benchmarks
```bash
# Run 001
gao-dev sandbox init my-feature-run-001
gao-dev sandbox run benchmarks/my-feature-v1.yaml
# Document results in ITERATION_LOG.md

# Make improvements to GAO-Dev...

# Run 002 (same benchmark!)
gao-dev sandbox init my-feature-run-002
gao-dev sandbox run benchmarks/my-feature-v1.yaml
# Compare metrics: Run 001 vs Run 002

# Repeat until autonomous!
```

---

## Conclusion

Standardized benchmarks are the foundation of measuring and improving GAO-Dev's autonomous capabilities. By following these standards, we ensure:

- **Consistent** measurement across all runs
- **Reproducible** results that can be verified
- **Comparable** metrics that show real improvement
- **Reliable** data for making decisions

**Remember**: The initial prompt is sacred. Once tracking begins, it never changes!

---

*This document defines the standards for all GAO-Dev benchmarks. Follow these guidelines to ensure meaningful, comparable results.*
