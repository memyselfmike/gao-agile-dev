# GAO-Dev Benchmarks

This directory contains benchmarks for testing GAO-Dev's autonomous development capabilities.

---

## Current Benchmark

### `workflow-driven-todo.yaml` - The Production Benchmark

**Purpose**: Validates GAO-Dev's core value proposition - autonomous development from a simple prompt.

**What It Tests**:
- Brian's intelligent workflow selection
- Multi-workflow sequence execution
- Autonomous artifact creation (PRD, architecture, code, tests)
- Atomic git commits
- Quality validation

**Format**: Workflow-Driven (Epic 7.2)
- Provides only `initial_prompt` and `success_criteria`
- GAO-Dev autonomously decides HOW to build
- Tests ACTUAL autonomous capability

**Run It**:
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the benchmark
gao-dev sandbox run sandbox/benchmarks/workflow-driven-todo.yaml

# Or with Python
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml
```

**Expected Output**:
- Complete todo application autonomously created
- docs/PRD.md, docs/ARCHITECTURE.md
- backend/ with Python/FastAPI code
- frontend/ with React/TypeScript code
- tests/ with comprehensive test suite
- Multiple atomic git commits
- All success criteria met

**Duration**: ~2-3 hours (depends on complexity and API speed)

---

## Architecture Evolution

GAO-Dev has evolved through three benchmark formats:

### 1. Phase-Based (Epic 1-5) - OBSOLETE
```yaml
phases:
  - phase_name: "Planning"
    agent: "John"
```
**Problem**: Waterfall approach, all planning upfront

### 2. Story-Based (Epic 6) - OBSOLETE
```yaml
epics:
  - stories:
    - name: "Story 1"
      agent: "Amelia"
```
**Problem**: Manual story breakdown required

### 3. Workflow-Driven (Epic 7.2) - CURRENT ✅
```yaml
initial_prompt: "Build a todo application..."
```
**Solution**: Autonomous workflow selection and execution

---

## Archived Benchmarks

The `_archive/` directory contains obsolete benchmarks from earlier epics:

**Phase-Based Benchmarks** (Epic 1-5):
- `full-featured.yaml` - Complex phase-based config
- `greenfield-simple.yaml` - Simple phase-based
- `minimal.yaml` - Minimal phase-based
- `simple-with-artifacts.yaml` - Phase-based with artifacts
- `todo-app.yaml` - Original todo app (phase-based)

**Story-Based Benchmarks** (Epic 6):
- `simple-story-test.yaml` - Story-based test
- `todo-app-incremental.yaml` - Incremental story-based
- `STORY-BASED-FORMAT.md` - Documentation for story format

**Why Archived**: These represent obsolete patterns. The workflow-driven approach (Epic 7.2) supersedes all previous approaches because it:
- Tests autonomous capability (not copying)
- Requires minimal configuration
- Lets GAO-Dev decide the workflow
- Validates the core value proposition

See `docs/ARCHITECTURAL-SHIFT.md` for details on why we moved away from manual workflow definition.

---

## Creating New Benchmarks

To create a new workflow-driven benchmark:

### 1. Start with the Template
```yaml
benchmark:
  name: "my-benchmark"
  description: "What this tests"

  # THE PROMPT - What to build
  initial_prompt: |
    Describe what you want GAO-Dev to build.
    Be specific about features, tech stack, and requirements.

  # Optional: Scale level hint (0-4)
  scale_level: 2

  # Success criteria
  success_criteria:
    artifacts_exist:
      - "docs/PRD.md"
      - "src/**/*.py"
    tests_pass: true
    min_test_coverage: 80
```

### 2. Focus on WHAT, Not HOW

**Good Prompt** (WHAT to build):
```
Build a blog platform with:
- User authentication
- Post creation/editing
- Comments
- Tag system
- Python/FastAPI backend
```

**Bad Prompt** (HOW to build):
```
First create a PRD, then architecture, then implement Story 1...
```

Let GAO-Dev decide the HOW!

### 3. Define Success Criteria

```yaml
success_criteria:
  artifacts_exist: [...]  # Required files/directories
  tests_pass: true        # Tests must pass
  builds_successfully: true  # Must build
  min_test_coverage: 80   # Coverage requirement
  quality_checks:         # Linting, type checking, etc
    - type: "linting"
      tool: "ruff"
      must_pass: true
```

### 4. Run and Validate

```bash
gao-dev sandbox run sandbox/benchmarks/my-benchmark.yaml
```

---

## Benchmark Results

After running, results are stored in:
```
sandbox/projects/my-benchmark-<timestamp>/
├── docs/           # Documentation created by John, Winston, Sally
├── src/            # Code created by Amelia
├── tests/          # Tests created by Amelia, validated by Murat
├── .git/           # Git history with atomic commits
└── metrics.db      # Performance metrics
```

View reports:
```bash
gao-dev sandbox report run my-benchmark-<timestamp>
```

---

## Key Principles

1. **Autonomous First**: GAO-Dev decides workflows, not humans
2. **Validate, Don't Prescribe**: Define success criteria, not implementation steps
3. **Test Reality**: Can GAO-Dev BUILD it, not copy it
4. **Keep It Simple**: Just provide the prompt and success criteria

---

## Questions?

- **How do I run a benchmark?**: See "Run It" section above
- **Do I need an API key?**: Yes, set `ANTHROPIC_API_KEY`
- **How long does it take?**: 1-3 hours depending on complexity
- **Can I create my own benchmark?**: Yes, follow "Creating New Benchmarks" section
- **Why only one benchmark file?**: Focus on validating core capability first

**See Also**:
- `docs/ARCHITECTURAL-SHIFT.md` - Why we moved to workflow-driven
- `docs/WORKFLOW-DRIVEN-TEST-RESULTS.md` - Architecture validation results
- `test_workflow_driven.py` - Test script demonstrating the flow

---

**Last Updated**: 2025-10-29
**Current Benchmark**: workflow-driven-todo.yaml
**Status**: Ready to run (requires ANTHROPIC_API_KEY)
