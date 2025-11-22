# Local Beta Testing Environment Guide

**For GAO-Dev Developers Testing the Beta Tester Experience**

**Last Updated**: 2025-11-20
**Version**: 1.0

---

## Overview

This guide helps you (as a GAO-Dev developer) set up a **completely separate testing environment** to safely test GAO-Dev as a beta tester would, without conflicts with your development installation.

### Why You Need This

- **Simulate real beta tester experience** - Test exactly what users will see
- **Avoid conflicts** - Keep dev environment pristine
- **Test on real projects** - Use actual codebases, not just sandbox
- **Fine-tune onboarding** - Validate the full user journey
- **Pre-release validation** - Catch issues before public release

---

## Architecture: Dual Environment Setup

```
Your Machine
├── C:\Projects\gao-agile-dev\          # Development Environment
│   ├── venv\                            # Dev virtual environment
│   ├── gao_dev\                         # Source code (editable)
│   └── sandbox\                         # Dev sandbox
│
└── C:\Testing\                          # Beta Testing Environment
    ├── venv-beta\                       # Beta virtual environment
    ├── test-projects\                   # Real test projects
    │   ├── my-todo-app\                 # Greenfield test
    │   ├── existing-python-app\         # Brownfield test
    │   └── node-microservice\           # Different stack test
    └── scripts\                         # Helper scripts
```

### Key Principles

1. **Complete isolation** - Separate directories, virtual environments, no shared dependencies
2. **Beta installation only** - Use `pip install git+https://...` (NOT editable mode)
3. **Real projects** - Test on actual codebases to catch real-world issues
4. **Easy switching** - Scripts to activate the right environment

---

## Quick Start Setup (10 minutes)

### Step 1: Create Testing Directory Structure

```cmd
:: Create testing root
mkdir C:\Testing
cd C:\Testing

:: Create subdirectories
mkdir test-projects
mkdir scripts

:: Create virtual environment for beta testing
python -m venv venv-beta
```

### Step 2: Activate Beta Environment

```cmd
:: Activate beta virtual environment
C:\Testing\venv-beta\Scripts\activate

:: Verify Python is from venv-beta
where python
:: Should show: C:\Testing\venv-beta\Scripts\python.exe
```

### Step 3: Install GAO-Dev as Beta Tester

**IMPORTANT**: Ensure you're in the beta virtual environment!

```cmd
:: Install from GitHub (latest main branch)
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

:: Verify installation
gao-dev --version
gao-dev health

:: Verify NOT editable mode
pip show gao-dev
:: Should show: Location: C:\Testing\venv-beta\Lib\site-packages
:: Should NOT show: Editable project location
```

### Step 4: Create Test Project

```cmd
:: Navigate to test projects directory
cd C:\Testing\test-projects

:: Create a new test project
mkdir my-todo-app
cd my-todo-app

:: Test the onboarding flow
gao-dev start
```

That's it! You now have a completely isolated beta testing environment.

---

## Testing Workflow

### Full Beta Tester Simulation

This simulates what a real beta tester experiences:

#### 1. Start Fresh Session

```cmd
:: Deactivate any active environment
deactivate

:: Activate beta environment
C:\Testing\venv-beta\Scripts\activate

:: Navigate to test project
cd C:\Testing\test-projects\my-todo-app
```

#### 2. Test Greenfield Project (New Project)

```cmd
:: Start GAO-Dev (launches onboarding)
gao-dev start

:: Follow the wizard:
:: - Project name: My Todo App
:: - Project type: Greenfield (new project)
:: - Git setup: Use your test credentials
:: - Provider: Select Claude Code / OpenAI / Ollama
:: - API key: Enter test API key (or use env var)

:: Test the web interface
:: - Navigate to http://localhost:8080
:: - Chat with Brian
:: - Test layout presets
:: - Try file browser
:: - Check activity feed
```

#### 3. Test Brownfield Project (Existing Code)

```cmd
:: Clone an existing project
cd C:\Testing\test-projects
git clone https://github.com/example/python-app.git existing-python-app
cd existing-python-app

:: Start GAO-Dev
gao-dev start

:: Select brownfield mode in wizard
:: Test how GAO-Dev handles existing code
```

#### 4. Test Upgrade Path

```cmd
:: Simulate upgrading to new version
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

:: Verify upgrade
gao-dev --version

:: Test that existing projects still work
cd C:\Testing\test-projects\my-todo-app
gao-dev start
```

### Testing Specific Features

#### Test Onboarding Wizard

```cmd
:: Create clean test project
cd C:\Testing\test-projects
mkdir test-onboarding
cd test-onboarding

:: Remove any existing .gao-dev (start completely fresh)
rmdir /s /q .gao-dev 2>nul

:: Test onboarding
gao-dev start

:: Checklist:
:: [ ] Environment detection works
:: [ ] Project setup wizard appears
:: [ ] Git configuration works
:: [ ] Provider selection works
:: [ ] Credential entry works
:: [ ] API key validation works
:: [ ] Web interface launches automatically
```

#### Test Provider Selection

```cmd
:: Test each provider type
gao-dev start

:: In wizard, test:
:: [ ] Claude Code provider
:: [ ] OpenAI provider
:: [ ] Ollama local provider (if installed)
:: [ ] Provider switching
:: [ ] Preference persistence
```

#### Test Web Interface

```cmd
:: Start web server
gao-dev start

:: Test in browser (http://localhost:8080):
:: [ ] Chat with Brian
:: [ ] Layout presets (Default, Code-Focused, Chat-Focused)
:: [ ] Panel resizing
:: [ ] DM conversations with agents
:: [ ] File browser
:: [ ] Activity feed
:: [ ] Git timeline
:: [ ] Kanban board
:: [ ] Settings panel
:: [ ] Theme toggle
:: [ ] WebSocket stability
```

---

## Helper Scripts

Create these scripts in `C:\Testing\scripts\` for easy environment management:

### activate-beta.bat

```bat
@echo off
REM Activate beta testing environment

echo Activating Beta Testing Environment...
call C:\Testing\venv-beta\Scripts\activate

echo.
echo Beta Environment Active
echo Location: C:\Testing\venv-beta
echo.
echo Test projects: C:\Testing\test-projects
echo.
echo Verify with: gao-dev --version
```

### activate-dev.bat

```bat
@echo off
REM Activate development environment

echo Activating Development Environment...
cd C:\Projects\gao-agile-dev
call venv\Scripts\activate

echo.
echo Dev Environment Active
echo Location: C:\Projects\gao-agile-dev\venv
echo.
echo Verify with: python verify_install.py
```

### upgrade-beta.bat

```bat
@echo off
REM Upgrade beta installation to latest

echo Activating beta environment...
call C:\Testing\venv-beta\Scripts\activate

echo.
echo Upgrading GAO-Dev to latest main...
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

echo.
echo Verifying installation...
gao-dev --version
gao-dev health

echo.
echo Upgrade complete!
```

### clean-beta.bat

```bat
@echo off
REM Clean beta environment and reinstall

echo WARNING: This will delete the beta virtual environment!
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" exit /b

echo.
echo Deactivating environment...
call deactivate 2>nul

echo Removing old environment...
rmdir /s /q C:\Testing\venv-beta

echo Creating new environment...
python -m venv C:\Testing\venv-beta

echo Activating new environment...
call C:\Testing\venv-beta\Scripts\activate

echo Installing GAO-Dev...
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

echo.
echo Clean installation complete!
gao-dev --version
```

### create-test-project.bat

```bat
@echo off
REM Create a new test project

if "%1"=="" (
    echo Usage: create-test-project.bat ^<project-name^>
    exit /b 1
)

set PROJECT_NAME=%1

echo Creating test project: %PROJECT_NAME%
cd C:\Testing\test-projects
mkdir %PROJECT_NAME%
cd %PROJECT_NAME%

echo.
echo Test project created at: C:\Testing\test-projects\%PROJECT_NAME%
echo.
echo To start testing:
echo   1. cd C:\Testing\test-projects\%PROJECT_NAME%
echo   2. gao-dev start
```

---

## Environment Verification

### Verify Beta Environment

When you activate the beta environment, verify it's configured correctly:

```cmd
:: Activate beta
call C:\Testing\scripts\activate-beta.bat

:: Check Python location
where python
:: Expected: C:\Testing\venv-beta\Scripts\python.exe

:: Check GAO-Dev installation
pip show gao-dev
:: Expected:
::   Location: C:\Testing\venv-beta\Lib\site-packages
::   (NO "Editable project location" line)

:: Check version
gao-dev --version

:: Check health
gao-dev health
```

### Verify Dev Environment

When you switch back to dev environment:

```cmd
:: Activate dev
call C:\Testing\scripts\activate-dev.bat

:: Check Python location
where python
:: Expected: C:\Projects\gao-agile-dev\venv\Scripts\python.exe

:: Check GAO-Dev installation
python verify_install.py
:: Expected: All [PASS]

:: Check import location
python -c "import gao_dev; print(gao_dev.__file__)"
:: Expected: C:\Projects\gao-agile-dev\gao_dev\__init__.py

:: Check pip details
pip show gao-dev
:: Expected: Editable project location: C:\Projects\gao-agile-dev
```

---

## Testing Scenarios

### Scenario 1: First-Time User Experience

**Goal**: Simulate a completely new user installing GAO-Dev

```cmd
:: 1. Clean slate - create new test project
cd C:\Testing\test-projects
mkdir first-time-user
cd first-time-user

:: 2. Ensure no .gao-dev exists
dir .gao-dev 2>nul
:: Should not exist

:: 3. Start GAO-Dev
gao-dev start

:: 4. Test checklist:
:: [ ] Onboarding wizard appears immediately
:: [ ] All wizard steps work smoothly
:: [ ] Error messages are clear and actionable
:: [ ] Web interface launches after completion
:: [ ] User can start chatting with Brian
```

### Scenario 2: Brownfield Python Project

**Goal**: Test GAO-Dev on existing Python codebase

```cmd
:: 1. Clone a real Python project
cd C:\Testing\test-projects
git clone https://github.com/pallets/flask.git flask-test
cd flask-test

:: 2. Start GAO-Dev
gao-dev start

:: 3. Select brownfield mode

:: 4. Test:
:: [ ] GAO-Dev detects Python project correctly
:: [ ] Existing Git config respected
:: [ ] File browser shows existing files
:: [ ] Can chat about existing codebase
:: [ ] Suggestions are contextually aware
```

### Scenario 3: Multi-Language Project

**Goal**: Test GAO-Dev with non-Python projects

```cmd
:: 1. Clone a Node.js project
cd C:\Testing\test-projects
git clone https://github.com/vercel/next.js.git nextjs-test
cd nextjs-test

:: 2. Start GAO-Dev
gao-dev start

:: 3. Test:
:: [ ] GAO-Dev handles non-Python project
:: [ ] Language detection works
:: [ ] File browser works
:: [ ] Suggestions are appropriate for Node.js
```

### Scenario 4: Upgrade Experience

**Goal**: Test upgrading from previous version

```cmd
:: 1. Install specific older version
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.0-beta.1

:: 2. Create project with old version
cd C:\Testing\test-projects
mkdir upgrade-test
cd upgrade-test
gao-dev start
:: Complete setup, use it briefly

:: 3. Upgrade to latest
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

:: 4. Test:
:: [ ] Existing project still works
:: [ ] New features are available
:: [ ] No data loss
:: [ ] .gao-dev structure preserved
```

### Scenario 5: Error Handling

**Goal**: Test error scenarios users might encounter

```cmd
:: Test 1: Invalid API key
:: - Start GAO-Dev
:: - Enter invalid API key
:: - Verify error message is clear and actionable

:: Test 2: Port already in use
:: - Start GAO-Dev on port 8080
:: - Try to start another instance
:: - Verify error handling

:: Test 3: No Git configuration
:: - Create project in environment without Git config
:: - Test wizard handles this gracefully

:: Test 4: Network issues
:: - Disable network
:: - Try to validate API key
:: - Verify offline handling
```

---

## Troubleshooting Beta Testing Environment

### Issue: Beta Install Conflicts with Dev

**Symptom**: Changes in dev environment appear in beta environment

**Cause**: Both environments are using the same Python or shared site-packages

**Solution**:

```cmd
:: 1. Verify environments are separate
call C:\Testing\venv-beta\Scripts\activate
where python
pip show gao-dev
:: Should NOT show editable location

:: 2. If conflict detected, clean beta environment
call C:\Testing\scripts\clean-beta.bat

:: 3. Verify dev environment is isolated
cd C:\Projects\gao-agile-dev
call venv\Scripts\activate
python verify_install.py
```

### Issue: Test Project Broken After Testing

**Symptom**: Test project no longer works after testing

**Cause**: Testing may have left project in inconsistent state

**Solution**:

```cmd
:: Option 1: Reset test project
cd C:\Testing\test-projects\my-todo-app
rmdir /s /q .gao-dev
rmdir /s /q docs
rmdir /s /q src
:: Start fresh

:: Option 2: Keep project, reset GAO-Dev state
cd C:\Testing\test-projects\my-todo-app
rmdir /s /q .gao-dev
gao-dev start
```

### Issue: Can't Switch Between Environments

**Symptom**: `deactivate` doesn't work or wrong environment active

**Cause**: Virtual environment activation conflicts

**Solution**:

```cmd
:: 1. Close ALL terminal windows

:: 2. Open new terminal

:: 3. Activate desired environment explicitly
call C:\Testing\venv-beta\Scripts\activate
:: OR
call C:\Projects\gao-agile-dev\venv\Scripts\activate

:: 4. Verify
where python
gao-dev --version
```

### Issue: Stale Installation in Beta

**Symptom**: Old version of GAO-Dev in beta environment despite upgrade

**Cause**: Pip cache or incomplete upgrade

**Solution**:

```cmd
:: Clean and reinstall
call C:\Testing\scripts\clean-beta.bat
```

---

## Best Practices

### 1. Keep Environments Separate

- ✅ **DO**: Always activate the correct environment before working
- ✅ **DO**: Use helper scripts for activation
- ❌ **DON'T**: Mix `pip install -e .` in beta environment
- ❌ **DON'T**: Use beta environment for development

### 2. Test on Real Projects

- ✅ **DO**: Clone real open-source projects for testing
- ✅ **DO**: Test on diverse project types (Python, Node, Go, etc.)
- ✅ **DO**: Test brownfield scenarios extensively
- ❌ **DON'T**: Only test on toy/demo projects

### 3. Simulate Real User Workflows

- ✅ **DO**: Start fresh (no pre-configured .gao-dev)
- ✅ **DO**: Follow onboarding wizard completely
- ✅ **DO**: Test error scenarios users might encounter
- ❌ **DON'T**: Skip onboarding steps
- ❌ **DON'T**: Only test happy path

### 4. Document Issues Immediately

- ✅ **DO**: Take screenshots of issues
- ✅ **DO**: Note exact reproduction steps
- ✅ **DO**: Check logs for error messages
- ✅ **DO**: File GitHub issues with full context

### 5. Clean Up After Testing

- ✅ **DO**: Remove test projects when done
- ✅ **DO**: Reset beta environment periodically
- ✅ **DO**: Keep test projects directory organized
- ❌ **DON'T**: Let test projects accumulate indefinitely

---

## Pre-Release Checklist

Before releasing to beta testers, validate using this environment:

### Installation & Setup
- [ ] Fresh install works from main branch
- [ ] Fresh install works from tagged release
- [ ] Upgrade from previous version works
- [ ] `gao-dev --version` shows correct version
- [ ] `gao-dev health` passes all checks

### Onboarding Experience
- [ ] Onboarding wizard launches automatically
- [ ] All wizard steps work smoothly
- [ ] Error messages are clear and actionable
- [ ] Git setup works (first-time user)
- [ ] Provider selection works (all options)
- [ ] Credential entry works (all methods)
- [ ] API key validation works
- [ ] Can skip/resume onboarding

### Web Interface
- [ ] Web server starts automatically after onboarding
- [ ] Browser opens automatically (desktop)
- [ ] Interface loads without errors
- [ ] Chat with Brian works
- [ ] All layout presets work
- [ ] Panel resizing works smoothly
- [ ] File browser works
- [ ] Activity feed updates
- [ ] Settings panel works
- [ ] Theme toggle works
- [ ] WebSocket remains stable

### Project Types
- [ ] Greenfield Python project works
- [ ] Brownfield Python project works
- [ ] Non-Python project works
- [ ] Large project (1000+ files) works
- [ ] Monorepo structure works

### Error Handling
- [ ] Invalid API key shows clear error
- [ ] Port conflict handled gracefully
- [ ] Network issues handled gracefully
- [ ] Missing Git config handled
- [ ] Disk space issues handled

### Documentation
- [ ] README is accurate
- [ ] INSTALLATION.md is accurate
- [ ] BETA_TESTING_CHECKLIST.md is accurate
- [ ] Error codes documented
- [ ] Troubleshooting guide is complete

---

## Maintenance

### Weekly Tasks

```cmd
:: Update beta installation to latest main
call C:\Testing\scripts\upgrade-beta.bat

:: Clean up old test projects
cd C:\Testing\test-projects
dir
:: Manually review and delete old projects
```

### Before Each Release

```cmd
:: 1. Clean beta environment completely
call C:\Testing\scripts\clean-beta.bat

:: 2. Install specific release tag
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@v0.3.0-beta.1

:: 3. Run full pre-release checklist

:: 4. Document any issues found

:: 5. Fix issues in dev environment

:: 6. Retest in beta environment
```

---

## Quick Reference

### Environment Activation

```cmd
:: Activate beta
call C:\Testing\venv-beta\Scripts\activate

:: Activate dev
cd C:\Projects\gao-agile-dev
call venv\Scripts\activate

:: Deactivate any
deactivate
```

### Common Commands

```cmd
:: Verify current environment
where python
pip show gao-dev
gao-dev --version

:: Upgrade beta installation
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

:: Create test project
cd C:\Testing\test-projects
mkdir test-project-name
cd test-project-name
gao-dev start

:: Clean test project
rmdir /s /q .gao-dev
```

### Verification Commands

```cmd
:: Verify beta environment
pip show gao-dev | findstr "Location"
:: Should show: venv-beta\Lib\site-packages
pip show gao-dev | findstr "Editable"
:: Should show nothing (not editable)

:: Verify dev environment
python verify_install.py
:: Should show all [PASS]
```

---

## Conclusion

This dual-environment setup allows you to:

- ✅ Test exactly what beta testers will experience
- ✅ Keep your development environment pristine
- ✅ Validate releases before publishing
- ✅ Fine-tune onboarding and user experience
- ✅ Catch issues before they reach users

**Remember**: Always activate the correct environment and verify before testing!

---

**Related Documentation**:
- [INSTALLATION.md](../INSTALLATION.md) - Installation modes
- [DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md) - Development issues
- [BETA_TESTING_CHECKLIST.md](../BETA_TESTING_CHECKLIST.md) - Beta testing guide
- [CLAUDE.md](../CLAUDE.md) - Development patterns

**Questions or Issues?**
- GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues

---

**Last Updated**: 2025-11-20
**Version**: 1.0
