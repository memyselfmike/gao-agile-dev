# Story 2.4: Dependency Installation

**Epic**: Epic 2 - Boilerplate Integration
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev sandbox
**I want** project dependencies automatically installed after boilerplate cloning
**So that** sandbox projects are immediately ready to run

---

## Acceptance Criteria

### AC1: Python Dependencies
- ✅ Detects `requirements.txt` or `pyproject.toml`
- ✅ Installs dependencies with pip/uv
- ✅ Creates virtual environment if configured
- ✅ Handles version conflicts gracefully

### AC2: Node.js Dependencies
- ✅ Detects `package.json`
- ✅ Installs with npm, yarn, or pnpm (auto-detect)
- ✅ Uses lockfile if present (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`)
- ✅ Handles peer dependency warnings

### AC3: Other Package Managers
- ✅ Detects `Gemfile` (Ruby)
- ✅ Detects `Cargo.toml` (Rust)
- ✅ Detects `go.mod` (Go)
- ✅ Graceful skip if package manager not installed

### AC4: Progress & Error Handling
- ✅ Shows installation progress
- ✅ Captures and logs output
- ✅ Reports installation failures clearly
- ✅ Handles timeout for slow installations
- ✅ Cleans up on failure

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/dependency_installer.py`

```python
"""Dependency installation for boilerplate projects."""

import subprocess
from pathlib import Path
from typing import Optional, List
from enum import Enum

class PackageManager(Enum):
    """Supported package managers."""
    PIP = "pip"
    UV = "uv"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    BUNDLER = "bundler"
    CARGO = "cargo"
    GO = "go"

class DependencyInstaller:
    """
    Handles dependency installation for various project types.
    """

    def install_dependencies(
        self,
        project_path: Path,
        timeout: int = 600,
    ) -> bool:
        """
        Auto-detect and install project dependencies.

        Args:
            project_path: Root directory of project
            timeout: Installation timeout in seconds

        Returns:
            True if successful, False otherwise

        Raises:
            DependencyInstallError: If installation fails
        """
        pass

    def detect_package_managers(self, project_path: Path) -> List[PackageManager]:
        """Detect which package managers are needed."""
        pass

    def install_python_deps(self, project_path: Path) -> bool:
        """Install Python dependencies."""
        pass

    def install_node_deps(self, project_path: Path) -> bool:
        """Install Node.js dependencies."""
        pass

    def detect_node_package_manager(self, project_path: Path) -> PackageManager:
        """Detect npm/yarn/pnpm from lockfile."""
        pass

    def is_package_manager_available(self, pm: PackageManager) -> bool:
        """Check if package manager is installed."""
        pass
```

### Detection Logic

**Python**:
```python
if (project_path / "requirements.txt").exists():
    use pip install -r requirements.txt
elif (project_path / "pyproject.toml").exists():
    use uv or pip install
```

**Node.js**:
```python
if (project_path / "pnpm-lock.yaml").exists():
    use pnpm install
elif (project_path / "yarn.lock").exists():
    use yarn install
elif (project_path / "package-lock.json").exists():
    use npm install
elif (project_path / "package.json").exists():
    use npm install
```

**Other**:
- Ruby: `bundle install` if `Gemfile` exists
- Rust: `cargo build` if `Cargo.toml` exists
- Go: `go mod download` if `go.mod` exists

### Installation Order

1. System-level dependencies first (if any)
2. Language-level dependencies
3. Development dependencies (optional)

### Error Scenarios

1. **Package Manager Not Found**: Log warning, skip installation
2. **Network Failure**: Retry with exponential backoff (3 attempts)
3. **Version Conflict**: Log error with resolution suggestions
4. **Timeout**: Kill process, report timeout error
5. **Disk Space**: Check available space before install

---

## Testing Requirements

### Unit Tests

```python
def test_detect_python_requirements():
    """Test detection of requirements.txt."""
    pass

def test_detect_node_package_json():
    """Test detection of package.json."""
    pass

def test_detect_pnpm_from_lockfile():
    """Test pnpm detection from lockfile."""
    pass

def test_package_manager_not_available():
    """Test graceful skip when PM not installed."""
    pass

def test_installation_timeout():
    """Test timeout handling."""
    pass

def test_network_retry_logic():
    """Test retry on network failure."""
    pass
```

### Integration Tests

- Test with real Next.js starter (pnpm)
- Test with Python project (pip)
- Test with project having multiple package managers
- Test with missing package manager

---

## Definition of Done

- [ ] DependencyInstaller class implemented
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Supports Python, Node.js at minimum
- [ ] Error handling comprehensive
- [ ] Progress reporting working
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Type hints complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 2.3 (variable substitution complete)
- **Blocks**: Story 2.5 (validation needs installed deps)

---

## Notes

- Consider caching dependencies for faster subsequent installs
- May need to handle lockfile updates in future
- Should document required package managers in README

---

*Created as part of Epic 2: Boilerplate Integration*
