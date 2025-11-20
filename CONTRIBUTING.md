# Contributing to GAO-Dev

Thank you for your interest in contributing to GAO-Dev! This document provides guidelines and best practices for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Conventional Commits](#conventional-commits)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment (recommended)

### ⚠️ Critical: Installation Modes

GAO-Dev has **two installation modes** - **NEVER MIX THEM**:

1. **Beta Testing Mode**: `pip install git+https://...` (for using GAO-Dev)
2. **Development Mode**: `pip install -e .` (for contributing to GAO-Dev)

**Mixing modes causes stale installation issues where your code changes don't take effect.**

**If you previously installed for beta testing and now want to develop:**

```bash
# Step 1: Clean up completely
pip uninstall -y gao-dev
# Remove any stale directories (see INSTALLATION.md for details)

# Step 2: Clone and install in editable mode
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"

# Step 3: Verify (critical!)
python verify_install.py
```

**For detailed troubleshooting:** See [INSTALLATION.md](INSTALLATION.md) and [DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md)

### Setup Development Environment

**Step 1: Clone Repository**
```bash
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
```

**Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows CMD:
venv\Scripts\activate

# Windows PowerShell:
venv\Scripts\Activate.ps1

# macOS/Linux/Git Bash:
source venv/bin/activate
```

**Step 3: Install in Editable Mode**
```bash
# Install with development dependencies
pip install -e ".[dev]"
```

**Step 4: Verify Installation** (**CRITICAL STEP**)
```bash
# Run verification script
python verify_install.py

# Should show all [PASS]
# If any [FAIL], run: reinstall_dev.bat (Windows) or ./reinstall_dev.sh (macOS/Linux)
```

**Step 5: Test Development Workflow**
```bash
# Make a test change
echo "# Test comment" >> gao_dev/cli/chat_repl.py

# Test immediately (no reinstall needed!)
gao-dev --help

# Changes take effect immediately in editable mode
```

### Common Setup Issues

**Problem: Changes don't take effect**
- **Cause**: Stale installation from mixing modes
- **Solution**: Run `reinstall_dev.bat` (Windows) or `./reinstall_dev.sh` (macOS/Linux)

**Problem: Import errors**
- **Cause**: Not in editable mode
- **Solution**: `pip install -e ".[dev]"` and verify with `python verify_install.py`

**Problem: Permission errors**
- **Cause**: Files locked by running processes
- **Solution**: Close all terminals running gao-dev, then run cleanup script

---

## Conventional Commits

GAO-Dev uses [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages. This enables automatic changelog generation and clear communication of changes.

### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | Appears in Changelog |
|------|-------------|---------------------|
| `feat` | New feature | ✅ Yes (Features) |
| `fix` | Bug fix | ✅ Yes (Bug Fixes) |
| `docs` | Documentation changes | ✅ Yes (Documentation) |
| `perf` | Performance improvement | ✅ Yes (Performance) |
| `refactor` | Code refactoring (no behavior change) | ✅ Yes (Refactoring) |
| `style` | Code style changes (formatting, etc.) | ❌ No |
| `test` | Adding or updating tests | ❌ No |
| `chore` | Build process, dependency updates | ❌ No |
| `ci` | CI/CD configuration changes | ❌ No |
| `build` | Build system changes | ❌ No |
| `revert` | Revert previous commit | ✅ Yes (Reverts) |

### Scope

The scope indicates the area of the codebase affected:

**Examples:**
- `epic-36` - Epic 36 related changes
- `brian` - Brian agent changes
- `sandbox` - Sandbox system changes
- `cli` - CLI command changes
- `orchestrator` - Orchestrator changes
- `tests` - Test-related changes

### Examples

#### Simple Feature Addition
```
feat(cli): add new command for feature validation

Implement `gao-dev validate-structure` command that checks
feature-based document structure compliance.
```

#### Bug Fix with Issue Reference
```
fix(brian): correct workflow selection for greenfield projects

Brian was incorrectly routing greenfield projects to Level 2 instead
of Level 4. Updated scale level detection logic.

Fixes #123
```

#### Breaking Change
```
feat(api)!: change provider interface to async

BREAKING CHANGE: All provider implementations must now use async/await.
Migration guide included in docs/migration.md.
```

#### Documentation Update
```
docs(readme): update installation instructions for Python 3.11+

Add requirements for Python 3.11 and clarify venv setup steps.
```

#### Performance Improvement
```
perf(cache): optimize context loading with LRU cache

Implement LRU cache for fast context loading, reducing load times
from 50ms to <5ms for cached entries.
```

#### Refactoring
```
refactor(services): extract GitManager to dedicated service

Split GitManager from orchestrator into standalone service for better
separation of concerns and testability.
```

### Breaking Changes

Breaking changes MUST be indicated in one of two ways:

**Method 1: Exclamation Mark**
```
feat(api)!: change provider interface signature
```

**Method 2: Footer**
```
feat(api): change provider interface signature

BREAKING CHANGE: Provider.execute() now requires async context.
Update all implementations to use async/await pattern.
```

### Co-Authorship

GAO-Dev is an AI-powered system. Commits generated by AI agents include co-authorship attribution:

```
feat(epic-36): implement changelog generation

Automatic changelog generation from conventional commits using git-cliff.

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/epic-XX-description
```

### 2. Make Changes
- Follow code quality standards (see below)
- Write tests for new functionality
- Update documentation

### 3. Commit with Conventional Format
```bash
git add .
git commit -m "feat(scope): add new feature"
```

### 4. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gao_dev --cov-report=html

# Run specific test
pytest tests/cli/test_commands.py::test_health
```

### 5. Push and Create Pull Request
```bash
git push origin feature/epic-XX-description

# Create PR using GitHub CLI
gh pr create --title "feat(scope): add new feature" --body "Description"
```

---

## Code Quality Standards

### Required Standards
- ✅ DRY Principle (Don't Repeat Yourself)
- ✅ SOLID Principles
- ✅ Type hints throughout (no `Any` types)
- ✅ Comprehensive error handling
- ✅ Structured logging with `structlog`
- ✅ 80%+ test coverage
- ✅ ASCII only (no emojis - Windows compatibility)
- ✅ Black formatting (line length 100)

### Code Formatting
```bash
# Format code with Black
black gao_dev tests --line-length 100

# Check with Ruff
ruff gao_dev tests

# Type checking with MyPy
mypy gao_dev --strict
```

### Type Hints
```python
# Good
def process_workflow(workflow_name: str, context: Dict[str, Any]) -> WorkflowResult:
    """Process a workflow with the given context."""
    ...

# Bad - missing type hints
def process_workflow(workflow_name, context):
    ...
```

### Error Handling
```python
# Good - specific exceptions with context
try:
    result = execute_command(cmd)
except CommandExecutionError as e:
    logger.error("Command execution failed", cmd=cmd, error=str(e))
    raise WorkflowExecutionError(f"Failed to execute {cmd}") from e

# Bad - bare except
try:
    result = execute_command(cmd)
except:
    pass
```

### Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Good - structured logging
logger.info("Workflow started", workflow=workflow_name, context_id=ctx.id)
logger.error("Validation failed", errors=validation_errors, count=len(validation_errors))

# Bad - string formatting
logger.info(f"Workflow {workflow_name} started with context {ctx.id}")
```

---

## Testing

### Test Organization
```
tests/
├── cli/                 # CLI command tests
├── core/                # Core service tests
├── agents/              # Agent tests
├── workflows/           # Workflow tests
└── integration/         # Integration tests
```

### Writing Tests

**Unit Tests**
```python
def test_workflow_selection():
    """Test Brian selects correct workflow for greenfield project."""
    brian = BrianAgent()
    result = brian.analyze_request("Build a todo app")

    assert result.scale_level == 4
    assert "greenfield" in result.project_type
    assert len(result.workflows) > 0
```

**Integration Tests**
```python
@pytest.mark.integration
def test_full_workflow_execution(tmp_path):
    """Test complete workflow execution end-to-end."""
    orchestrator = GAODevOrchestrator()
    result = orchestrator.execute_workflow(
        workflow_name="create_prd",
        context={"project_root": tmp_path}
    )

    assert result.success
    assert (tmp_path / "docs" / "PRD.md").exists()
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/cli/test_commands.py

# Specific test
pytest tests/cli/test_commands.py::test_health

# With coverage
pytest --cov=gao_dev --cov-report=html

# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration
```

---

## Documentation

### Code Documentation

**Module Docstrings**
```python
"""
Service for managing git operations with atomic transactions.

This module provides GitManager class that handles all git operations
including commits, branches, tags, and status checks. All operations
are atomic and include automatic rollback on failure.
"""
```

**Function/Method Docstrings**
```python
def create_feature_branch(self, branch_name: str) -> bool:
    """
    Create and checkout a new feature branch.

    Args:
        branch_name: Name of the branch to create (e.g., 'feature/epic-36-changelog')

    Returns:
        True if branch created successfully, False otherwise

    Raises:
        GitError: If branch already exists or git operation fails

    Example:
        >>> git_manager = GitManager(repo_path)
        >>> git_manager.create_feature_branch('feature/epic-36-changelog')
        True
    """
```

### Project Documentation

Update relevant documentation when making changes:
- `README.md` - User-facing features
- `CLAUDE.md` - Claude AI agent instructions
- `docs/` - Feature-specific documentation
- `CHANGELOG.md` - Auto-generated, don't edit manually

---

## Changelog Generation

Changelogs are automatically generated from commit messages:

```bash
# Generate full changelog
git-cliff --config .cliff.toml --output CHANGELOG.md

# Generate for specific version
git-cliff --config .cliff.toml --tag v0.2.0 --output CHANGELOG.md

# Generate unreleased changes
git-cliff --config .cliff.toml --unreleased --output CHANGELOG.md
```

**Note:** Never edit `CHANGELOG.md` manually. All changes are derived from commit messages.

---

## Questions or Issues?

- **Bug Reports**: [Open an issue](https://github.com/memyselfmike/gao-agile-dev/issues/new?template=bug_report.md)
- **Feature Requests**: [Open an issue](https://github.com/memyselfmike/gao-agile-dev/issues/new?template=feature_request.md)
- **Discussions**: [GitHub Discussions](https://github.com/memyselfmike/gao-agile-dev/discussions)

---

## License

By contributing to GAO-Dev, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to GAO-Dev!** 🚀
