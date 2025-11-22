# Development Patterns & Best Practices

**TL;DR**: Complete development workflow for GAO-Dev contributors - from starting a session to committing changes. Follow these patterns to maintain code quality and project standards.

**Quick Links**:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow overview
- [ADDING_WORKFLOWS.md](ADDING_WORKFLOWS.md) - Add new workflows
- [ADDING_WEB_FEATURES.md](ADDING_WEB_FEATURES.md) - Extend web interface
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing patterns

---

## 1. Starting a Session

**ALWAYS START HERE**:
1. **Verify installation**: `python verify_install.py` (should show all [PASS])
2. Read `docs/bmm-workflow-status.md` - Current epic, story, what's next
3. Read relevant PRD/Architecture (`docs/features/<feature-name>/`)
4. Check latest commits: `git log --oneline -10`
5. Read current story file for acceptance criteria

**Why this matters**: Starting with context prevents rework and ensures you're working on the right things.

---

## 2. Working on Stories

### The Standard Pattern

```bash
# 1. Create feature branch
git checkout -b feature/epic-N-name

# 2. Plan with TodoWrite
# Create todo list with ONE task in_progress at a time

# 3. Write tests first (TDD)
# Create tests in tests/ directory

# 4. Implement functionality
# Write code to pass tests

# 5. Run tests and validate
pytest --cov=gao_dev tests/

# 6. Atomic commit (ONE per story)
git commit -m "feat(scope): Story N.M - Description"

# 7. Update story status
# Mark story as completed in docs/sprint-status.yaml
```

### Commit Message Format

```
<type>(<scope>): <description>

<optional body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build, config, or tooling changes

**Examples**:
```
feat(web): Story 39.5 - Add file tree component with real-time updates
fix(onboarding): Story 40.3 - Fix undefined property access in wizard
docs(api): Add TL;DR sections to API reference
```

---

## 3. Progress Tracking

### TodoWrite Pattern

```python
# Always use TodoWrite to track progress
TodoWrite([
    {"content": "Task 1", "status": "in_progress", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "pending", "activeForm": "Doing task 2"},
    {"content": "Task 3", "status": "pending", "activeForm": "Doing task 3"},
])
```

### Rules

- **Exactly ONE task `in_progress` at a time** (not zero, not two)
- Mark completed **IMMEDIATELY** after finishing (don't batch)
- Clear todo list when all tasks done
- NEVER batch multiple completions

### Why This Matters

TodoWrite gives users real-time visibility into your progress and helps you stay focused on one task at a time.

---

## 4. Code Quality Standards

### Required Standards

✅ **DRY Principle** - No code duplication, extract common patterns
✅ **SOLID Principles** - Single responsibility, open/closed, etc.
✅ **Type Hints** - Full type coverage, no `Any` types
✅ **Error Handling** - Comprehensive try/except with logging
✅ **Logging** - Use structlog for observability
✅ **Test Coverage** - 80%+ coverage required
✅ **ASCII Only** - No emojis (Windows compatibility)
✅ **Black Formatting** - Line length 100

### Testing Requirements

```python
# Unit tests for all new code
def test_new_feature():
    result = new_feature(input_data)
    assert result == expected_output

# Integration tests for workflows
def test_workflow_execution(orchestrator):
    result = orchestrator.execute_workflow("prd")
    assert result.success

# Type checking with MyPy
# Must pass: mypy gao_dev/ --strict
```

### Current Status

- **400+ tests passing**
- **80%+ code coverage**
- **MyPy strict mode**

---

## 5. Bug Fixing and Testing

### CRITICAL: Use Bug-Tester Agent

**When working on bug fixes, ALWAYS use the bug-tester agent**

### Bug Fix Workflow

1. **Invoke bug-tester agent** - Use Task tool with `subagent_type='bug-tester'`
2. **Systematic verification** - Test in BOTH dev and beta environments
3. **Playwright UI testing** - Verify UI changes systematically
4. **Log monitoring** - Check server logs before and after fixes
5. **Regression tests** - Create tests that prevent bug recurrence
6. **Documentation** - Create comprehensive verification reports

### Quick Commands

```bash
/verify-bug-fix   # Complete verification workflow (dev + beta)
/test-ui          # Systematic Playwright UI testing
```

### When to Use Bug-Tester Agent

- ✅ Fixing any bug (UI, backend, API, WebSocket, etc.)
- ✅ Verifying bug fixes before committing
- ✅ Testing changes in both environments
- ✅ Creating regression tests
- ✅ Performing visual regression testing
- ✅ Monitoring server logs for issues

### Required for ALL Bug Fixes

- ✅ Test in development environment (`C:\Projects\gao-agile-dev`)
- ✅ Test in beta environment (`C:\Testing`)
- ✅ Playwright verification with screenshots
- ✅ Server log analysis
- ✅ Console error checking
- ✅ Regression test creation
- ✅ Verification report
- ✅ No regressions in related features

### Example

```python
# When user reports a bug or you're fixing one
# ALWAYS invoke the bug-tester agent
Task(
    subagent_type="bug-tester",
    description="Verify bug fix #123",
    prompt="""
    Bug: Onboarding wizard crashes on step 2
    Fix: Updated gao_dev/web/api/onboarding.py

    Please:
    1. Verify fix in dev environment
    2. Test with Playwright
    3. Install in beta environment (C:/Testing)
    4. Verify in beta environment
    5. Create regression test
    6. Generate verification report
    """
)
```

### Resources

- `.claude/agents/bug-tester.md` - Complete bug testing workflow
- `.claude/skills/ui-testing/SKILL.md` - Playwright patterns
- `.claude/skills/bug-verification/SKILL.md` - Verification workflow
- `docs/LOCAL_BETA_TESTING_GUIDE.md` - Beta environment setup

---

## 6. Tool Usage Patterns

### Read Before Write/Edit

```python
# ALWAYS read first
Read(file_path="gao_dev/core/workflow_executor.py")

# Then edit or write
Edit(
    file_path="gao_dev/core/workflow_executor.py",
    old_string="old code",
    new_string="new code"
)
```

**Why**: Understanding existing code prevents breaking changes and maintains consistency.

### Parallel Tool Calls

```python
# If multiple independent reads needed, call in parallel
Read(file_path="gao_dev/agents/brian.py")
Read(file_path="gao_dev/agents/john.py")
Read(file_path="gao_dev/agents/winston.py")
```

**Benefit**: User sees all calls at once (more efficient, better UX).

### Provide Full Visibility

- ✅ Tell user what you're about to do
- ✅ Explain results as you get them
- ✅ Show progress for long operations
- ✅ Allow user to interrupt or redirect

---

## 7. Common Pitfalls to Avoid

### ❌ DON'T

- **Batch multiple story commits** - One commit per story
- **Leave uncommitted work** - Commit after each story
- **Create files without reading existing code** - Always read first
- **Use `Any` type hints** - Full type coverage required
- **Skip tests** - 80%+ coverage required
- **Forget to update TodoWrite** - Track progress continuously
- **Create unnecessary new files** - Prefer editing existing files

### ✅ DO

- **One commit per story** - Atomic, traceable changes
- **Read before write** - Understand context first
- **Type everything** - No `Any` types
- **Test everything** - Unit + integration tests
- **Update progress frequently** - TodoWrite after each task
- **Edit existing files when possible** - Don't create duplicates

---

## Common Development Tasks

### Adding a New Workflow

See [ADDING_WORKFLOWS.md](ADDING_WORKFLOWS.md)

```yaml
# gao_dev/workflows/phase/name/workflow.yaml
name: my-new-workflow
description: Brief description
phase: 2
author: AgentName (Agent Role)
autonomous: true
variables:
  project_name:
    description: Project name
    type: string
    required: true
```

### Adding a Web Feature

See [ADDING_WEB_FEATURES.md](ADDING_WEB_FEATURES.md)

```python
# Backend: gao_dev/web/api/your_feature.py
@router.post("/items", response_model=ItemResponse)
async def create_item(request: CreateItemRequest):
    # Implementation
    pass

# Frontend: gao_dev/web/frontend/src/components/YourFeature.tsx
export function YourFeature() {
    // Implementation
}
```

### Adding a New Agent

See [ADDING_AGENTS.md](ADDING_AGENTS.md)

```yaml
# gao_dev/config/agents/your_agent.yaml
agent:
  name: "YourAgent"
  role: "Your Agent Role"
  type: "your-agent-type"
responsibilities:
  - Primary responsibility 1
```

### Running Tests

See [TESTING_GUIDE.md](TESTING_GUIDE.md)

```bash
# All tests
pytest --cov=gao_dev tests/

# Specific test file
pytest tests/web/api/test_chat.py

# Type checking
mypy gao_dev/ --strict
```

---

## Installation Verification

### Check Installation Mode

```bash
python verify_install.py  # Should show all [PASS]
```

### Fix Stale Installation

If you see [FAIL] or code changes don't take effect:

```bash
# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh
```

**Symptoms of Stale Installation**:
- Code changes don't take effect
- Web server uses wrong `project_root`
- Logs show `C:\Python314\Lib\site-packages` instead of project directory

---

## Quick Reference

| Task | Command | Documentation |
|------|---------|---------------|
| **Verify installation** | `python verify_install.py` | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **Check current status** | Read `docs/bmm-workflow-status.md` | [bmm-workflow-status.md](../bmm-workflow-status.md) |
| **Add workflow** | Create YAML + template.md | [ADDING_WORKFLOWS.md](ADDING_WORKFLOWS.md) |
| **Add web feature** | API router + React component | [ADDING_WEB_FEATURES.md](ADDING_WEB_FEATURES.md) |
| **Run tests** | `pytest --cov=gao_dev` | [TESTING_GUIDE.md](TESTING_GUIDE.md) |
| **Type check** | `mypy gao_dev/ --strict` | - |
| **Format code** | `black gao_dev/ --line-length 100` | - |
| **Fix bug** | Use bug-tester agent | `.claude/agents/bug-tester.md` |

---

## Success Checklist

**Before committing, verify**:

- ✅ Installation verified (`python verify_install.py`)
- ✅ Tests passing (`pytest --cov=gao_dev`)
- ✅ Type checking passing (`mypy gao_dev/ --strict`)
- ✅ Code formatted (`black gao_dev/`)
- ✅ 80%+ test coverage
- ✅ TodoWrite updated and cleared
- ✅ Story status updated
- ✅ Atomic commit with proper format
- ✅ No regressions in related features

---

**See Also**:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow overview
- [ADDING_WORKFLOWS.md](ADDING_WORKFLOWS.md) - Add new workflows
- [ADDING_WEB_FEATURES.md](ADDING_WEB_FEATURES.md) - Extend web interface
- [ADDING_AGENTS.md](ADDING_AGENTS.md) - Add specialized agents
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing patterns
- [Code Examples](../examples/) - Real-world examples
