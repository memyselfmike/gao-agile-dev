# GAO-Dev Installation Guide

**Complete installation guide for beta testers and developers**

---

## Table of Contents

1. [Installation Modes](#installation-modes)
2. [Beta Tester Installation](#beta-tester-installation-recommended)
3. [Developer Installation](#developer-installation)
4. [Switching Between Modes](#switching-between-modes)
5. [Troubleshooting](#troubleshooting)
6. [Verification](#verification)

---

## Installation Modes

GAO-Dev supports **two distinct installation modes**. Choose the mode that matches your use case:

| Mode | Use Case | Installation Method | Updates | Changes Effect |
|------|----------|---------------------|---------|----------------|
| **Beta Testing** | Using GAO-Dev to build projects | `pip install git+https://...` | Manual upgrade | Not applicable |
| **Development** | Contributing to GAO-Dev itself | `pip install -e .` | Automatic | Immediate |

### When to Use Each Mode

**Beta Testing Mode** - Choose this if you:
- Want to use GAO-Dev to build applications
- Are testing the latest release
- Don't plan to modify GAO-Dev source code
- Want stable, versioned releases

**Development Mode** - Choose this if you:
- Are contributing features or bug fixes to GAO-Dev
- Need to test changes to GAO-Dev source code
- Want source code changes to take effect immediately
- Are working on GAO-Dev itself (not just using it)

**⚠️ CRITICAL: Never Mix Both Modes**

Running both modes on the same system causes conflicts that prevent changes from taking effect. If you need both modes, use separate virtual environments (see [Switching Between Modes](#switching-between-modes)).

---

## Beta Tester Installation (Recommended)

### Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should show 3.11 or higher
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Anthropic API Key**
   - Get one at: https://console.anthropic.com/
   - Set as environment variable (optional - can enter during setup):
     ```bash
     # macOS/Linux
     export ANTHROPIC_API_KEY="your-key-here"

     # Windows CMD
     set ANTHROPIC_API_KEY=your-key-here

     # Windows PowerShell
     $env:ANTHROPIC_API_KEY="your-key-here"
     ```

### Installation Steps

**Step 1: Install from GitHub**

```bash
# Install latest beta release
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Or install specific version:**
```bash
# Install specific tag
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

**Step 2: Verify Installation**

```bash
gao-dev --version
gao-dev health
```

**Step 3: Start Using GAO-Dev**

```bash
# Create your project directory
mkdir my-project
cd my-project

# Start GAO-Dev (launches onboarding wizard + web interface)
gao-dev start
```

### Upgrading to Latest Version

```bash
# Upgrade to latest release
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Verify new version
gao-dev --version
```

---

## Developer Installation

### Prerequisites

Same as beta testing, plus:
- Familiarity with Python development
- Understanding of virtual environments
- Git workflow knowledge

### Installation Steps

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
# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

**Step 4: Verify Installation**

```bash
# Verify editable mode is active
python verify_install.py

# Should show:
# [PASS] Import Location
# [PASS] Site-Packages
# [PASS] Pip Installation
# [PASS] Bytecode Cache
```

**Step 5: Test Development Workflow**

```bash
# Make a change to any source file
# Changes take effect immediately - no reinstall needed!

# Run tests
pytest

# Run specific test
pytest tests/cli/test_commands.py::test_health
```

### Development Workflow

With editable mode, your workflow is:

```bash
# 1. Edit source files
vim gao_dev/cli/chat_repl.py

# 2. Test immediately (no reinstall needed!)
gao-dev start

# 3. Run tests
pytest

# 4. Commit changes
git add .
git commit -m "feat(cli): improve chat interface"
```

---

## Switching Between Modes

If you need **both** beta testing and development modes, use separate virtual environments.

### Quick Setup

For a **comprehensive dual-environment setup** with helper scripts and testing workflows:

**See**: [docs/LOCAL_BETA_TESTING_GUIDE.md](docs/LOCAL_BETA_TESTING_GUIDE.md)

This comprehensive guide includes:
- Automated setup scripts
- Complete testing workflow
- Pre-release validation checklists
- Environment switching helpers
- Best practices for real project testing

**Quick Start** (Windows):
```cmd
cd C:\Testing\scripts
setup-beta-environment.bat
```

### Manual Setup (Basic)

If you prefer a manual setup:

```bash
# Beta testing environment
python -m venv venv-beta
venv-beta/Scripts/activate  # Windows
source venv-beta/bin/activate  # macOS/Linux
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
deactivate

# Development environment
cd gao-agile-dev
python -m venv venv-dev
venv-dev/Scripts/activate  # Windows
source venv-dev/bin/activate  # macOS/Linux
pip install -e ".[dev]"
deactivate
```

### Usage

```bash
# For beta testing
source venv-beta/bin/activate  # or venv-beta\Scripts\activate on Windows
gao-dev start

# For development
cd gao-agile-dev
source venv-dev/bin/activate  # or venv-dev\Scripts\activate on Windows
gao-dev start
```

**Tip**: Use the helper scripts from [LOCAL_BETA_TESTING_GUIDE.md](docs/LOCAL_BETA_TESTING_GUIDE.md) for easier environment management.

---

## Troubleshooting

### Problem: Changes Not Taking Effect

**Symptom**: You edit source files but changes don't appear when running `gao-dev` commands.

**Cause**: Stale installation from mixing installation modes or corrupted editable install.

**Solution**:

**Option 1: Automated Fix (Recommended)**
```bash
cd C:\Projects\gao-agile-dev  # or your project path
reinstall_dev.bat  # Windows
./reinstall_dev.sh  # macOS/Linux
```

**Option 2: Manual Fix**
```bash
# Step 1: Uninstall completely
pip uninstall -y gao-dev

# Step 2: Clean global site-packages (Windows)
rmdir /s /q "C:\Python314\Lib\site-packages\gao_dev"
rmdir /s /q "C:\Python314\Lib\site-packages\gao_dev-*.dist-info"

# Step 2: Clean global site-packages (macOS/Linux)
rm -rf /usr/local/lib/python3.11/site-packages/gao_dev*

# Step 3: Clean user site-packages (Windows)
rmdir /s /q "%APPDATA%\Python\Python314\site-packages\gao_dev"

# Step 3: Clean user site-packages (macOS/Linux)
rm -rf ~/.local/lib/python3.11/site-packages/gao_dev*

# Step 4: Clean build artifacts
cd gao-agile-dev
rm -rf gao_dev.egg-info build dist
find . -type d -name "__pycache__" -exec rm -rf {} +

# Step 5: Reinstall in editable mode
pip install -e ".[dev]"

# Step 6: Verify
python verify_install.py
```

### Problem: Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'gao_dev'`

**Solution**:
```bash
# Verify installation
pip show gao-dev

# If not installed, reinstall
pip install -e .  # For development
# OR
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main  # For beta testing
```

### Problem: Wrong Project Root in Logs

**Symptom**: Logs show `project_root=C:\Python314\Lib\site-packages` instead of your actual project path.

**Cause**: Stale installation in global site-packages.

**Solution**: Run the troubleshooting steps above for "Changes Not Taking Effect".

### Problem: Permission Denied Errors

**Symptom**: Cannot delete site-packages directories.

**Cause**: Files are locked by running processes.

**Solution**:
```bash
# Step 1: Close all terminal windows running gao-dev
# Step 2: Kill any running processes
# Windows:
taskkill /F /IM python.exe

# macOS/Linux:
pkill -9 python

# Step 3: Run cleanup again
reinstall_dev.bat  # or ./reinstall_dev.sh
```

---

## Verification

### Verify Beta Testing Installation

```bash
# Check version
gao-dev --version

# Check health
gao-dev health

# Check installation type
pip show gao-dev
# Should show: Location: <site-packages path>
# Should NOT show: Editable project location
```

### Verify Development Installation

```bash
# Run verification script
python verify_install.py

# Expected output:
# [PASS] Import Location
# [PASS] Site-Packages (no stale copies)
# [PASS] Pip Installation (editable mode)
# [PASS] Bytecode Cache

# Check import location
python -c "import gao_dev; print(gao_dev.__file__)"
# Should show: /path/to/gao-agile-dev/gao_dev/__init__.py

# Check pip details
pip show gao-dev
# Should show: Editable project location: /path/to/gao-agile-dev
```

### Verify No Conflicts

```bash
# Check for stale copies
# Windows:
dir "C:\Python314\Lib\site-packages\gao_dev" 2>nul && echo "STALE COPY FOUND!" || echo "OK"

# macOS/Linux:
ls /usr/local/lib/python3.*/site-packages/gao_dev 2>/dev/null && echo "STALE COPY FOUND!" || echo "OK"
```

---

## Quick Reference

### Installation Commands

```bash
# Beta Testing
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Development
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"

# Upgrade Beta Testing
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Clean Development Install
pip uninstall -y gao-dev
rm -rf gao_dev.egg-info build dist
pip install -e ".[dev]"
```

### Verification Commands

```bash
# Version
gao-dev --version

# Health Check
gao-dev health

# Installation Type
pip show gao-dev

# Development Mode Verification
python verify_install.py

# Check Import Location
python -c "import gao_dev; print(gao_dev.__file__)"
```

### Troubleshooting Commands

```bash
# Windows - Clean Reinstall
reinstall_dev.bat

# macOS/Linux - Clean Reinstall
./reinstall_dev.sh

# Verify Clean State
python verify_install.py
```

---

## Getting Help

- **Documentation**: See `CLAUDE.md` for development patterns
- **Contributing**: See `CONTRIBUTING.md` for contribution guidelines
- **Beta Testing**: See `BETA_TESTING_CHECKLIST.md` for testing guide
- **Troubleshooting**: See `DEV_TROUBLESHOOTING.md` for detailed troubleshooting
- **Issues**: https://github.com/memyselfmike/gao-agile-dev/issues

---

**Important Notes:**

1. **Never use `pip install .`** (without `-e`) during development - it creates the stale copy problem
2. **Always verify** after installation using `python verify_install.py` (development) or `gao-dev --version` (beta testing)
3. **Use separate virtual environments** if you need both modes
4. **Run `reinstall_dev.bat`** if you encounter any installation issues during development

---

**Last Updated**: 2025-11-20
**Version**: 1.0
