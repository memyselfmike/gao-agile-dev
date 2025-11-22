# GAO-Dev Development Troubleshooting Guide

## Problem: Changes Not Taking Effect

### Root Cause
When you see changes not taking effect after editing source code, it's usually because:

1. **Stale site-packages**: Old copies of `gao_dev` in global or user site-packages
2. **Not truly editable**: `pip install -e .` didn't complete properly
3. **Multiple Python environments**: Importing from wrong location

### Symptoms
- Code changes don't appear when running `gao-dev` commands
- Web server uses wrong project_root
- Logs show paths like `C:\Python314\Lib\site-packages` instead of `C:\Projects\gao-agile-dev`

## Quick Fix (Automated)

Run the cleanup script:
```cmd
cd C:\Projects\gao-agile-dev
reinstall_dev.bat
```

## Manual Fix (Step by Step)

### 1. Uninstall Completely
```cmd
pip uninstall -y gao-dev
```

### 2. Clean Global Site-Packages
```cmd
# Remove from global site-packages
rmdir /s /q "C:\Python314\Lib\site-packages\gao_dev"
rmdir /s /q "C:\Python314\Lib\site-packages\gao_dev-*.dist-info"
```

### 3. Clean User Site-Packages
```cmd
# Remove from user site-packages
rmdir /s /q "%APPDATA%\Python\Python314\site-packages\gao_dev"
rmdir /s /q "%APPDATA%\Python\Python314\site-packages\gao_dev-*.dist-info"
```

### 4. Clean Build Artifacts
```cmd
cd C:\Projects\gao-agile-dev

# Remove Python cache
for /d /r . %%G in ("__pycache__") do @if exist "%%G" rmdir /s /q "%%G"

# Remove build artifacts
rmdir /s /q gao_dev.egg-info
rmdir /s /q build
rmdir /s /q dist
```

### 5. Reinstall in Editable Mode
```cmd
pip install -e .
```

### 6. Verify Installation
```cmd
# Check where Python imports from
python -c "import gao_dev; print('Import location:', gao_dev.__file__)"

# Should show: C:\Projects\gao-agile-dev\gao_dev\__init__.py

# Check pip installation
pip show gao-dev

# Should show:
# Location: C:\Users\<user>\AppData\Roaming\Python\Python314\site-packages
# Editable project location: C:\Projects\gao-agile-dev
```

## Verification Steps

After reinstalling, verify everything works:

### 1. Check Import Location
```cmd
python verify_install.py
```

### 2. Test Change Detection
1. Edit a file (e.g., add a print statement to `gao_dev/cli/chat_repl.py`)
2. Run `gao-dev start`
3. Verify you see your change

### 3. Check Web Server Project Root
```cmd
gao-dev start
# Look for log line: process_executor_initialized project_root=C:\Projects\gao-agile-dev
# Should NOT be: C:\Python314\Lib\site-packages
```

## Prevention: Development Workflow

To avoid this issue in the future:

### 1. Always Use Editable Mode for Development
```cmd
pip install -e .  # NOT pip install .
```

### 2. Clean Before Release Installs
If you need to test a release install:
```cmd
# Uninstall dev version first
pip uninstall -y gao-dev

# Clean everything
reinstall_dev.bat

# Then do release install
pip install .
```

### 3. Separate Virtual Environments
Consider using separate virtual environments:
```cmd
# Development environment
python -m venv venv-dev
venv-dev\Scripts\activate
pip install -e .

# Testing environment
python -m venv venv-test
venv-test\Scripts\activate
pip install .
```

## Common Issues

### Issue: "pip install -e ." Doesn't Create .egg-link

**Symptom**: No `.egg-link` file in site-packages after `pip install -e .`

**Solution**: This is normal for modern `pip` with `pyproject.toml`. It uses `.dist-info` instead.

### Issue: Python Still Imports from site-packages

**Symptom**: `gao_dev.__file__` shows `site-packages/gao_dev/__init__.py`

**Solution**:
1. Run `reinstall_dev.bat` to clean everything
2. Check for stale `.pth` files in site-packages
3. Verify PYTHONPATH environment variable doesn't include site-packages

### Issue: Changes Work Sometimes, Not Others

**Symptom**: Some changes take effect, others don't

**Solution**: This indicates bytecode cache issues. Clear `__pycache__`:
```cmd
for /d /r . %%G in ("__pycache__") do @if exist "%%G" rmdir /s /q "%%G"
```

## Why This Happens

### The Editable Install Process

When you run `pip install -e .`:
1. Pip creates a link/reference in site-packages pointing to your source directory
2. Python imports should come from your source directory
3. Changes to source files take effect immediately

### What Goes Wrong

1. **Previous non-editable install**: If you ran `pip install .` before, it copied files to site-packages
2. **Incomplete uninstall**: `pip uninstall` sometimes leaves directories behind
3. **Multiple Python installations**: Installing in wrong Python's site-packages

## Testing Your Fix

Use this checklist to verify everything works:

- [ ] `python -c "import gao_dev; print(gao_dev.__file__)"` shows project directory
- [ ] `pip show gao-dev` shows "Editable project location"
- [ ] Edit a source file and see changes immediately
- [ ] `gao-dev start` shows correct project_root in logs
- [ ] No `gao_dev` directory in global site-packages
- [ ] No `gao_dev` directory in user site-packages

## Release Process (Going Forward)

To prevent this issue when preparing releases:

1. **Development**:
   - Always use `pip install -e .`
   - Test changes immediately

2. **Pre-Release Testing**:
   - Create fresh virtual environment
   - Install with `pip install .` (non-editable)
   - Test release behavior

3. **Cleanup**:
   - After testing, run `reinstall_dev.bat`
   - Return to editable mode

## Beta Testing Environment

If you need to test GAO-Dev as a beta tester would (separate from development):

**See**: [LOCAL_BETA_TESTING_GUIDE.md](LOCAL_BETA_TESTING_GUIDE.md)

This guide covers:
- Setting up a completely isolated beta testing environment
- Testing on real projects outside the dev repo
- Switching between dev and beta environments
- Pre-release validation workflows
- Helper scripts for easy environment management

**Quick Setup**:
```cmd
cd C:\Testing\scripts
setup-beta-environment.bat
```

This creates a separate environment at `C:\Testing\` that won't conflict with your dev installation.

## Additional Resources

- **Beta Testing Guide**: [LOCAL_BETA_TESTING_GUIDE.md](LOCAL_BETA_TESTING_GUIDE.md) - Comprehensive dual-environment setup
- Python Packaging Guide: https://packaging.python.org/
- Pip Editable Installs: https://pip.pypa.io/en/stable/topics/local-project-installs/
- CLAUDE.md: See "Development Patterns & Best Practices"
