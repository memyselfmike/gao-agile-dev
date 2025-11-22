# Workspace Hygiene Guide

**Version**: 1.0
**Last Updated**: 2025-11-22
**Status**: Production

## Overview

This guide ensures a clean, professional GAO-Dev workspace by preventing test artifacts, corrupt directories, and temporary files from polluting the repository.

---

## Quick Reference

| Task | Command |
|------|---------|
| **Clean workspace (Windows)** | `scripts\cleanup_workspace.bat` |
| **Clean workspace (Unix/Linux/macOS)** | `./scripts/cleanup_workspace.sh` |
| **Run tests with auto-cleanup** | `pytest` (cleanup runs automatically) |
| **Check workspace status** | `git status` |
| **Manual cleanup** | Follow [Manual Cleanup](#manual-cleanup) section |

---

## Automatic Cleanup

### Test Suite Cleanup

The test suite automatically cleans up artifacts after all tests complete.

**Configured in**: `tests/conftest.py`

**What gets cleaned up**:
- Corrupt/malformed directories (Windows path issues)
- Test database files in root
- Playwright screenshots
- Coverage reports
- Server logs
- Pip artifacts
- Frontend build cache
- Test transcripts

**How it works**:
```python
@pytest.fixture(scope="session", autouse=True)
def cleanup_workspace():
    """Runs automatically after all tests complete."""
    yield  # Tests run here
    # Cleanup happens here
```

**Usage**: Just run `pytest` - cleanup happens automatically!

---

## Release Cleanup

Run cleanup scripts before creating a release or committing changes.

### Windows

```bash
scripts\cleanup_workspace.bat
```

### Unix/Linux/macOS

```bash
./scripts/cleanup_workspace.sh
```

### What Gets Cleaned Up

1. **Corrupt directories** (Windows path issues):
   - `C:Projectsgao-agile-devtestsunitcore`
   - `C:Testingscripts`
   - `C:Usersmikejgao-final-test`
   - `Projectsgao-agile-devgao_devwebfrontend`
   - `Testingvenv-beta`
   - `-p`

2. **Test artifacts**:
   - `gao_dev.db`
   - `server_output.log`
   - `nul`
   - `test_output.log`
   - `test_output.txt`
   - `=*.*.*` (pip artifacts)

3. **Playwright artifacts**:
   - `.playwright-mcp/`
   - `*.png` (except in `docs/screenshots/`)

4. **Frontend build cache**:
   - `gao_dev/web/frontend/.vite/`

5. **Coverage reports**:
   - `.coverage`
   - `htmlcov/`

6. **Test transcripts**:
   - `.gao-dev/test_transcripts/`
   - `tests/e2e/debug_reports/`

---

## Gitignore Protection

The `.gitignore` file is configured to prevent these artifacts from being committed.

**Key entries**:
```gitignore
# Playwright MCP artifacts
.playwright-mcp/
*.png

# Frontend build cache
.vite/
**/node_modules/.vite/

# Corrupt/malformed directories
C:Projectsgao-agile-devtestsunitcore/
C:Testingscripts/
/C:*/
/=*/

# Test artifacts
/gao_dev.db
/server_output.log
/nul
```

**Full list**: See `.gitignore` in project root

---

## Pre-Release Checklist

Before creating a release, follow this checklist:

- [ ] Run cleanup script:
  - Windows: `scripts\cleanup_workspace.bat`
  - Unix/Linux/macOS: `./scripts/cleanup_workspace.sh`
- [ ] Check workspace status: `git status`
- [ ] Verify no untracked artifacts: Review output carefully
- [ ] Run full test suite: `pytest`
- [ ] Verify installation: `python verify_install.py` (should show all [PASS])
- [ ] Build package: `python -m build`
- [ ] Test installation in clean environment
- [ ] Create git tag with proper version

---

## Manual Cleanup

If automatic cleanup fails or you need to clean up manually:

### Remove All Artifacts

**Windows PowerShell**:
```powershell
# Navigate to project root
cd C:\Projects\gao-agile-dev

# Remove corrupt directories
Get-ChildItem -Directory | Where-Object { $_.Name -match "^[A-Z]:" -or $_.Name -eq "-p" } | Remove-Item -Recurse -Force

# Remove test artifacts
Remove-Item -Force gao_dev.db, server_output.log, nul, test_output.log, .coverage -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .playwright-mcp, htmlcov, .vite -ErrorAction SilentlyContinue

# Remove pip artifacts
Get-ChildItem -File -Filter "=*.*.*" | Remove-Item -Force
```

**Unix/Linux/macOS**:
```bash
# Navigate to project root
cd ~/Projects/gao-agile-dev

# Remove corrupt directories
rm -rf C:* Projectsgao* Testingvenv-beta -p 2>/dev/null || true

# Remove test artifacts
rm -f gao_dev.db server_output.log nul test_output.log .coverage 2>/dev/null || true
rm -rf .playwright-mcp htmlcov .vite 2>/dev/null || true

# Remove pip artifacts
rm -f =*.*.* 2>/dev/null || true
```

### Remove Specific Category

**Test Databases**:
```bash
# Windows
del /f /q gao_dev.db *test*.db

# Unix/Linux/macOS
rm -f gao_dev.db *test*.db
```

**Playwright Artifacts**:
```bash
# Windows
rmdir /s /q .playwright-mcp

# Unix/Linux/macOS
rm -rf .playwright-mcp
```

**Coverage Reports**:
```bash
# Windows
del /f /q .coverage
rmdir /s /q htmlcov

# Unix/Linux/macOS
rm -f .coverage
rm -rf htmlcov
```

---

## Preventing Corruption

### Root Cause: Windows Path Handling

Corrupt directories with missing slashes (e.g., `C:Projectsgao-agile-dev`) are caused by incorrect path construction on Windows.

**Common Issues**:

1. **String concatenation instead of Path operations**:
   ```python
   # BAD
   path = "C:Projects" + "gao-agile-dev"  # Missing slash!

   # GOOD
   path = Path("C:/Projects") / "gao-agile-dev"
   ```

2. **Using forward slashes in Windows paths**:
   ```python
   # BAD (on Windows)
   path = "C:/Projects/gao-agile-dev".replace("/", "")  # Removes slashes!

   # GOOD
   path = Path("C:/Projects/gao-agile-dev")  # Handles OS differences
   ```

**Best Practices**:

✅ **DO**:
- Use `pathlib.Path` for all path operations
- Use `/` operator to join paths: `Path("a") / "b"`
- Use `Path.home()` for user directory
- Use `Path.cwd()` for current directory
- Test path construction on both Windows and Unix

❌ **DON'T**:
- Concatenate strings for paths
- Use OS-specific separators (`\` or `/`)
- Assume path format (use `Path` instead)
- Use `os.path.join` (prefer `pathlib.Path`)

### Testing Path Construction

When writing tests that create paths:

```python
import tempfile
from pathlib import Path

# GOOD - Use temp directories
def test_something():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        test_file = project_root / "test.txt"
        test_file.write_text("content")
        # Cleanup happens automatically

# BAD - Use project root
def test_something_bad():
    project_root = Path(".")  # Writes to actual project!
    test_file = project_root / "test.txt"
    test_file.write_text("content")
    # Pollutes workspace!
```

---

## Troubleshooting

### Issue: Cleanup script fails

**Error**: "Access denied" or "Permission denied"

**Solution**:
1. Close all terminals/editors accessing the project
2. Run as administrator (Windows) or with sudo (Unix)
3. Check file/directory permissions
4. Manually delete stubborn files

### Issue: Corrupt directories won't delete

**Error**: "The filename, directory name, or volume label syntax is incorrect"

**Solution**:
```bash
# Windows (run as administrator)
rmdir /s /q "\\?\C:\Projects\gao-agile-dev\C:Projectsgao-agile-devtestsunitcore"

# Or use PowerShell
Remove-Item -LiteralPath "C:Projectsgao-agile-devtestsunitcore" -Recurse -Force
```

### Issue: Git shows deleted files

**Error**: Git shows files as deleted but they still exist

**Solution**:
```bash
# Refresh git index
git add -A

# Or reset specific files
git checkout -- <filename>
```

### Issue: .coverage or htmlcov keeps reappearing

**Cause**: Running pytest creates these files

**Solution**:
1. Add to `.gitignore` (already done)
2. Run cleanup script after tests
3. Or run with `--no-cov` flag: `pytest --no-cov`

---

## CI/CD Integration

### Pre-commit Hook

Add cleanup to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Pre-commit hook to ensure workspace is clean

echo "Running workspace cleanup..."
if [ -f "scripts/cleanup_workspace.sh" ]; then
    ./scripts/cleanup_workspace.sh
elif [ -f "scripts/cleanup_workspace.bat" ]; then
    scripts/cleanup_workspace.bat
fi

# Check for untracked artifacts
git status --short | grep "^??" | while read status file; do
    case "$file" in
        *.db|*.log|*.png|=*)
            echo "ERROR: Untracked artifact detected: $file"
            echo "Run cleanup script before committing"
            exit 1
            ;;
    esac
done
```

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
- name: Clean workspace
  run: |
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
      scripts/cleanup_workspace.bat
    else
      ./scripts/cleanup_workspace.sh
    fi

- name: Verify clean workspace
  run: |
    if [[ -n $(git status --porcelain) ]]; then
      echo "ERROR: Workspace is not clean"
      git status
      exit 1
    fi
```

---

## Maintenance

### Monthly Tasks

- [ ] Review `.gitignore` for new patterns
- [ ] Check for new corrupt directories: `ls -la | grep "^[A-Z]:"`
- [ ] Update cleanup scripts with new artifact patterns
- [ ] Run full cleanup and commit changes

### After Major Changes

- [ ] Run cleanup script
- [ ] Test cleanup script on both Windows and Unix
- [ ] Update documentation if new artifacts are introduced
- [ ] Add new patterns to `.gitignore`

---

## Reference

### Related Documentation

- **INSTALLATION.md** - Installation and environment setup
- **CONTRIBUTING.md** - Development guidelines
- **DEV_TROUBLESHOOTING.md** - Detailed troubleshooting

### Scripts

- **scripts/cleanup_workspace.bat** - Windows cleanup script
- **scripts/cleanup_workspace.sh** - Unix/Linux/macOS cleanup script

### Configuration Files

- **.gitignore** - Git ignore patterns
- **tests/conftest.py** - Test cleanup fixtures
- **pytest.ini** - Pytest configuration

---

## Questions?

- **Issues**: https://github.com/memyselfmike/gao-agile-dev/issues
- **Discussions**: https://github.com/memyselfmike/gao-agile-dev/discussions

---

**Last Updated**: 2025-11-22
**Version**: 1.0
