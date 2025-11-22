# Contributing to GAO-Dev

Thank you for contributing to GAO-Dev! This guide will help you get started with development.

## TL;DR

**Quick Start**:
1. Fork and clone the repository
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Verify installation: `python verify_install.py` (all [PASS])
4. Create feature branch: `git checkout -b feature/epic-N-name`
5. Make changes with tests
6. Run tests: `pytest --cov=gao_dev`
7. Commit: Follow conventional commit format
8. Submit PR with description

**Key Rules**:
- ✅ One commit per story/feature
- ✅ Tests required (80%+ coverage)
- ✅ Type hints required (no `Any`)
- ✅ Update documentation alongside code
- ✅ Follow TDD when possible

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Format](#commit-message-format)
- [Documentation](#documentation)
- [Common Tasks](#common-tasks)

---

## Getting Started

### Prerequisites

- **Python**: 3.11+ (3.10+ supported)
- **Node.js**: 20+ (for web UI development)
- **Git**: For version control
- **IDE**: VS Code recommended (with Python + Pylance extensions)

### Installation Modes

**CRITICAL**: GAO-Dev has two distinct installation modes - never mix them!

#### Development Mode (You are here)

```bash
# Clone repository
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
python verify_install.py  # MUST show all [PASS]
```

#### Beta Testing Mode (Users)

```bash
# Users install from GitHub
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**⚠️ If you previously installed for beta testing, clean up first**:

```bash
# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh
```

**Symptoms of stale installation**:
- Code changes don't take effect
- Logs show `C:\Python314\Lib\site-packages` instead of project directory
- Web server uses wrong project_root

**Fix**: Run `python verify_install.py` → If [FAIL], run `reinstall_dev.bat`

### First-Time Setup

```bash
# 1. Verify installation
python verify_install.py  # Should show all [PASS]

# 2. Run tests to ensure everything works
pytest

# 3. (Optional) Set up pre-commit hooks
pip install pre-commit
pre-commit install

# 4. (Optional) Install web UI dependencies
cd gao_dev/web/frontend
npm install
cd ../../..
```

---

## Development Workflow

### 1. Start Every Session

**ALWAYS START HERE**:

1. **Verify installation**: `python verify_install.py` (should show all [PASS])
2. **Read current status**: `docs/bmm-workflow-status.md`
3. **Check latest commits**: `git log --oneline -10`
4. **Read relevant docs**: PRD, Architecture, Current story file

### 2. Create Feature Branch

```bash
# Feature branch naming: feature/epic-N-name
git checkout -b feature/epic-39-web-ui

# Bug fix branch naming: fix/issue-description
git checkout -b fix/onboarding-crash

# Documentation: docs/topic-name
git checkout -b docs/quick-start-guide
```

### 3. Plan Your Work (TodoWrite)

Use TodoWrite tool to track progress:

```python
TodoWrite([
    {"content": "Task 1", "status": "in_progress", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "pending", "activeForm": "Doing task 2"},
])
```

**Rules**:
- Exactly ONE task `in_progress` at a time
- Mark completed IMMEDIATELY after finishing
- Clear todo list when done
- NEVER batch multiple completions

### 4. Follow TDD (Recommended)

**Test-Driven Development workflow**:

```bash
# 1. Write test first (defines expected behavior)
# tests/feature/test_new_feature.py

# 2. Run test (should fail)
pytest tests/feature/test_new_feature.py

# 3. Implement feature
# gao_dev/feature/new_feature.py

# 4. Run test (should pass)
pytest tests/feature/test_new_feature.py

# 5. Refactor with confidence
```

### 5. Make Changes

**Before writing code**:
- ✅ Read existing code first (use Read tool)
- ✅ Understand architecture and patterns
- ✅ Check for similar implementations
- ✅ Plan your approach

**While coding**:
- ✅ Follow code standards (see below)
- ✅ Add type hints (no `Any`)
- ✅ Write comprehensive error handling
- ✅ Use structlog for logging
- ✅ Keep functions focused (SRP)

### 6. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gao_dev --cov-report=term-missing

# Run specific test file
pytest tests/web/api/test_feature.py

# Run with verbose output
pytest -v
```

**Requirements**:
- All tests must pass
- Coverage must be ≥80%
- No type errors: `mypy gao_dev`

### 7. Commit Changes

**ONE commit per story/feature** (atomic commits):

```bash
# Stage changes
git add relevant/files.py

# Commit with conventional format
git commit -m "feat(scope): Story N.M - Description

More detailed explanation if needed.

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 8. Create Pull Request

```bash
# Push branch
git push -u origin feature/epic-N-name

# Create PR (use gh CLI or GitHub UI)
gh pr create --title "Epic N: Feature Name" --body "Description"
```

---

## Code Standards

### Required Standards

- ✅ **DRY Principle**: No code duplication
- ✅ **SOLID Principles**: Clean architecture
- ✅ **Type hints**: Throughout (no `Any`)
- ✅ **Error handling**: Comprehensive
- ✅ **Logging**: Use structlog for observability
- ✅ **Test coverage**: 80%+ required
- ✅ **ASCII only**: No emojis (Windows compatibility)
- ✅ **Black formatting**: Line length 100

### Python Style

```python
# Type hints required
def process_data(input: str, max_length: int = 100) -> dict[str, Any]:
    """Process input data with validation.

    Args:
        input: Input string to process
        max_length: Maximum allowed length

    Returns:
        Processed data dictionary

    Raises:
        ValueError: If input exceeds max_length
    """
    if len(input) > max_length:
        raise ValueError(f"Input too long: {len(input)} > {max_length}")

    return {"data": input.strip(), "length": len(input)}


# Use structlog for logging
import structlog

logger = structlog.get_logger(__name__)

def some_function():
    logger.info("processing_started", item_count=10)
    # ... process ...
    logger.info("processing_completed", duration_ms=42)
```

### TypeScript/React Style

```typescript
// Type everything
interface FeatureProps {
  id: string;
  name: string;
  onUpdate?: (id: string) => void;
}

export function Feature({ id, name, onUpdate }: FeatureProps) {
  // Component implementation
}

// Use proper hooks
const [state, setState] = useState<FeatureState>({ loading: false });

// Use Zustand for global state
const { items, addItem } = useFeatureStore();
```

### Formatting

```bash
# Python: Black (line length 100)
black --line-length 100 gao_dev/

# Python: isort (import sorting)
isort gao_dev/

# TypeScript: Prettier (via npm)
cd gao_dev/web/frontend
npm run format
```

### Type Checking

```bash
# Python: MyPy (strict mode)
mypy gao_dev/

# TypeScript: Built into Vite
cd gao_dev/web/frontend
npm run type-check
```

---

## Testing Requirements

### Minimum Requirements

- ✅ **Unit tests** for all new code
- ✅ **Integration tests** for workflows
- ✅ **80%+ code coverage** overall
- ✅ **100% coverage** for critical paths
- ✅ **Regression tests** for all bug fixes

### Test Organization

```
tests/
├── unit/               # Fast, isolated tests
│   ├── core/
│   ├── services/
│   └── web/
├── integration/        # Multi-component tests
│   ├── workflows/
│   └── agents/
└── e2e/               # End-to-end scenarios
```

### Writing Tests

```python
# tests/feature/test_new_feature.py
import pytest
from gao_dev.feature.new_feature import NewFeature


class TestNewFeature:
    """Test suite for NewFeature."""

    def test_basic_functionality(self):
        """Test basic feature functionality."""
        feature = NewFeature()
        result = feature.process("test")

        assert result.success
        assert result.data == "test"

    def test_error_handling(self):
        """Test error handling."""
        feature = NewFeature()

        with pytest.raises(ValueError, match="Invalid input"):
            feature.process("")

    @pytest.mark.parametrize("input,expected", [
        ("valid", True),
        ("", False),
        (None, False),
    ])
    def test_validation(self, input, expected):
        """Test validation with various inputs."""
        feature = NewFeature()
        result = feature.validate(input)

        assert result == expected
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=gao_dev --cov-report=html

# Specific markers
pytest -m integration  # Integration tests only
pytest -m "not slow"   # Skip slow tests

# Fail fast
pytest -x  # Stop on first failure

# Verbose output
pytest -v
```

---

## Pull Request Process

### Before Creating PR

- [ ] All tests pass locally
- [ ] Coverage ≥80%
- [ ] MyPy passes (no type errors)
- [ ] Black formatting applied
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Story status updated in sprint-status.yaml

### PR Requirements

1. **Title**: Use conventional commit format
   ```
   feat(scope): Add feature X
   fix(scope): Fix bug Y
   docs(scope): Update documentation
   ```

2. **Description**: Include
   - What changed and why
   - Link to issue/story (if applicable)
   - Testing performed
   - Screenshots (for UI changes)

3. **Size**: Keep PRs focused
   - One story/feature per PR
   - Max ~500 lines changed
   - Break large changes into multiple PRs

4. **Review**: Address all comments
   - Request review from relevant experts
   - Respond to feedback
   - Update based on review

### Example PR Description

```markdown
## Summary
Implement feature X to enable Y.

## Changes
- Added `feature_x.py` with implementation
- Added tests in `test_feature_x.py`
- Updated documentation in `docs/QUICK_START.md`

## Testing
- [x] Unit tests (15 new tests)
- [x] Integration tests (2 scenarios)
- [x] Manual testing in dev environment
- [x] Coverage: 85%

## Screenshots
(For UI changes)

## Related Issues
Closes #123
Related to Epic 39

🤖 Generated with GAO-Dev
```

---

## Commit Message Format

### Conventional Commits

**Format**:
```
<type>(<scope>): <description>

[optional body]

[optional footer]

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(web): Add settings panel` |
| `fix` | Bug fix | `fix(api): Fix validation error` |
| `docs` | Documentation | `docs(guide): Add testing guide` |
| `refactor` | Code refactoring | `refactor(core): Simplify workflow executor` |
| `test` | Add/update tests | `test(api): Add endpoint tests` |
| `chore` | Maintenance | `chore(deps): Update dependencies` |
| `perf` | Performance | `perf(db): Add index for queries` |
| `style` | Formatting | `style(core): Apply black formatting` |

### Examples

```bash
# Feature
git commit -m "feat(web): Add kanban board drag-and-drop

Implement drag-and-drop for kanban cards using react-dnd.
Supports state transitions with atomic commits.

Story 39.5: Kanban Board Implementation

🤖 Generated with GAO-Dev"

# Bug fix
git commit -m "fix(onboarding): Fix schema validation error

The onboarding wizard was crashing due to localStorage schema mismatch.
Added validation with fallback to default values.

Fixes #142

🤖 Generated with GAO-Dev"

# Documentation
git commit -m "docs(developers): Add workflow creation guide

Complete guide for adding new workflows to GAO-Dev.
Includes schema reference, examples, and testing patterns.

🤖 Generated with GAO-Dev"
```

---

## Documentation

### Documentation Requirements

**When to update documentation**:
- ✅ New features (add to QUICK_START.md or relevant guide)
- ✅ API changes (update API_REFERENCE.md)
- ✅ Architecture changes (update ARCHITECTURE.md)
- ✅ New workflows (document in workflow guide)
- ✅ Breaking changes (update MIGRATION_GUIDE.md)

### Documentation Standards

Follow Diana's quality standards:

- ✅ **TL;DR** for docs >500 lines (<100 tokens)
- ✅ **Quick starts** <2,000 tokens
- ✅ **Code examples** copy-paste ready
- ✅ **Complete workflows** (not fragments)
- ✅ **Cross-references** with purpose
- ✅ **Inverted pyramid** structure (key facts first)

### Where to Add Documentation

| Change Type | Documentation Location |
|-------------|------------------------|
| New workflow | `docs/developers/ADDING_WORKFLOWS.md` example section |
| New API endpoint | `docs/API_REFERENCE.md` |
| New component | `docs/developers/ADDING_WEB_FEATURES.md` |
| New agent | `docs/developers/ADDING_AGENTS.md` |
| Testing pattern | `docs/developers/TESTING_GUIDE.md` |
| Architecture change | `docs/ARCHITECTURE_OVERVIEW.md` |

---

## Common Tasks

### Adding a Feature

```bash
# 1. Read current documentation
cat docs/bmm-workflow-status.md
cat docs/features/your-feature/PRD.md

# 2. Create feature branch
git checkout -b feature/epic-N-feature-name

# 3. Write tests first (TDD)
# tests/feature/test_new_feature.py

# 4. Implement feature
# gao_dev/feature/new_feature.py

# 5. Update documentation
# docs/QUICK_START.md (add example)

# 6. Run tests
pytest --cov=gao_dev

# 7. Commit
git add .
git commit -m "feat(feature): Add new feature

Story N.M: Feature Name

🤖 Generated with GAO-Dev"

# 8. Create PR
gh pr create --title "Epic N: Feature Name"
```

### Fixing a Bug

```bash
# 1. Create bug fix branch
git checkout -b fix/bug-description

# 2. Write regression test
# tests/test_bug_fix.py

# 3. Fix bug
# gao_dev/module/file.py

# 4. Verify test passes
pytest tests/test_bug_fix.py

# 5. Commit
git commit -m "fix(scope): Fix bug description

Add regression test to prevent recurrence.

Fixes #123

🤖 Generated with GAO-Dev"

# 6. Create PR
gh pr create --title "Fix: Bug description"
```

### Running Development Server

```bash
# Backend only (CLI)
gao-dev health

# Web UI (development mode)
cd gao_dev/web/frontend
npm run dev

# Full stack (production mode)
gao-dev start
```

---

## Getting Help

### Resources

- **Documentation**: Start with `docs/QUICK_START.md`
- **Developer Guides**: `docs/developers/` directory
- **Architecture**: `docs/ARCHITECTURE_OVERVIEW.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Project Guide**: `CLAUDE.md`

### Questions?

- **Issues**: [GitHub Issues](https://github.com/memyselfmike/gao-agile-dev/issues)
- **Discussions**: [GitHub Discussions](https://github.com/memyselfmike/gao-agile-dev/discussions)
- **Documentation**: Check existing docs first

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers
- Follow the project's technical standards
- Document your work

---

## License

By contributing to GAO-Dev, you agree that your contributions will be licensed under the project's license.

---

**Thank you for contributing to GAO-Dev!** 🚀

**Estimated tokens**: ~2,100
