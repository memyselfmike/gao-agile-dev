# Story 7.6: Create Example Benchmark with Artifacts

**Epic**: Epic 7 - Autonomous Artifact Creation & Git Integration
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer), Bob (Scrum Master)
**Created**: 2025-10-28

---

## User Story

**As a** developer testing the benchmark system
**I want** an example benchmark that demonstrates full artifact creation
**So that** I can validate Epic 7 functionality and provide a reference implementation

---

## Context

After implementing Stories 7.1-7.5, we have all the pieces for artifact creation. This story creates a working example that demonstrates:
- GAODevOrchestrator usage
- Artifact creation
- Git commits
- Metrics collection
- Verification

---

## Acceptance Criteria

### AC1: New Benchmark Config Created
- [ ] File: `sandbox/benchmarks/simple-with-artifacts.yaml`
- [ ] Based on greenfield-simple.yaml
- [ ] Includes artifact expectations
- [ ] Simplified for quick validation (<5 min run)

### AC2: Benchmark Runs Successfully
- [ ] Completes all phases
- [ ] Creates expected artifacts
- [ ] Git commits created
- [ ] Metrics collected
- [ ] No errors or warnings

### AC3: Artifacts Verified
- [ ] PRD created at docs/PRD.md
- [ ] Architecture at docs/ARCHITECTURE.md
- [ ] Stories in docs/stories/
- [ ] Implementation files in src/
- [ ] Tests in tests/
- [ ] Git log shows all commits

### AC4: Documentation Provided
- [ ] README explains what benchmark does
- [ ] Expected output documented
- [ ] How to run instructions
- [ ] How to verify results

---

## Technical Details

### Benchmark Config

```yaml
name: "Simple Project with Artifacts"
description: "Minimal greenfield project demonstrating artifact creation"
type: greenfield
version: "1.0.0"

project:
  name: "hello-world"
  description: "Simple hello world application"
  type: "python-cli"

initial_prompt: |
  Create a simple Python CLI application that:
  - Prints "Hello, World!"
  - Has proper project structure
  - Includes tests
  - Has documentation

phases:
  - name: "create-prd"
    command: "create-prd"
    timeout: 120
    expected_artifacts:
      - "docs/PRD.md"

  - name: "create-architecture"
    command: "create-architecture"
    timeout: 120
    expected_artifacts:
      - "docs/ARCHITECTURE.md"

  - name: "create-story"
    command: "create-story"
    args:
      epic: 1
    timeout: 120
    expected_artifacts:
      - "docs/stories/epic-1/*.md"

  - name: "implement-story"
    command: "implement-story"
    args:
      epic: 1
      story: 1
    timeout: 300
    expected_artifacts:
      - "src/hello.py"
      - "tests/test_hello.py"
      - "README.md"
      - "requirements.txt"

success_criteria:
  artifacts_created: true
  tests_passing: true
  git_commits_created: true
  no_errors: true
```

### Expected Project Structure

```
sandbox/projects/hello-world-001/
├── .git/
├── .gitignore
├── README.md
├── requirements.txt
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── stories/
│       └── epic-1/
│           └── story-1.1.md
├── src/
│   ├── __init__.py
│   └── hello.py
└── tests/
    ├── __init__.py
    └── test_hello.py
```

### Expected Git History

```
$ git log --oneline
abc1234 feat(story-1.1): Implement hello world functionality
def5678 feat(stories): Create user stories for Epic 1
ghi9012 feat(architecture): Create system architecture design
jkl3456 feat(prd): Create Product Requirements Document
mno7890 chore: Initialize project structure
```

---

## Files to Create

**New**:
- `sandbox/benchmarks/simple-with-artifacts.yaml` - Benchmark config
- `docs/examples/simple-artifacts-benchmark.md` - Documentation

**Modify**:
- `README.md` - Add example to docs

---

## Dependencies

**Requires**:
- Stories 7.1-7.5 complete
- All Epic 7 functionality working

**Blocks**:
- None (validation story)

---

## Implementation Steps

1. **Create Benchmark Config**
   - Copy greenfield-simple.yaml
   - Add expected_artifacts
   - Simplify for quick run
   - Add clear documentation

2. **Run Benchmark**
   - Execute: `gao-dev run-benchmark simple-with-artifacts`
   - Monitor output
   - Fix any issues
   - Document quirks

3. **Verify Results**
   - Check all artifacts created
   - Verify git commits
   - Run tests in generated project
   - Check metrics

4. **Document Example**
   - Write guide explaining benchmark
   - Document expected results
   - Add troubleshooting tips
   - Include sample output

5. **Add to Test Suite**
   - Integration test using this benchmark
   - Automated verification
   - CI-friendly (if possible)

---

## Testing Approach

### Manual Testing
1. Run benchmark: `gao-dev run-benchmark simple-with-artifacts`
2. Check exit code (should be 0)
3. Verify artifacts created
4. Check git log
5. Run tests in generated project

### Automated Testing
```python
def test_simple_artifacts_benchmark():
    """Integration test for simple artifacts benchmark."""
    runner = BenchmarkRunner()
    result = runner.run("simple-with-artifacts.yaml")

    assert result.success
    assert result.artifacts_created == 6
    assert result.commits_count == 4
    assert result.tests_passing
```

---

## Definition of Done

- [ ] Benchmark config created
- [ ] Runs successfully end-to-end
- [ ] All expected artifacts created
- [ ] Git history shows all commits
- [ ] Generated project is functional
- [ ] Tests pass in generated project
- [ ] Documentation complete
- [ ] Example added to main README
- [ ] Integration test added
- [ ] Code reviewed
- [ ] Committed with atomic commit

---

## Notes

**Purpose**: This example serves multiple purposes:
1. **Validation**: Proves Epic 7 works end-to-end
2. **Documentation**: Shows developers how to use the system
3. **Testing**: Provides automated integration test
4. **Demo**: Can show stakeholders what GAO-Dev does

**Keep It Simple**: This should be the simplest possible example that demonstrates all Epic 7 features. Don't add complexity.

---

**Created by**: Bob (Scrum Master)
**Estimated Completion**: 1-2 hours
