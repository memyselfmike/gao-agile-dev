# GAO-Dev Documentation Index

**Complete guide to all GAO-Dev documentation**

---

## 🚀 Getting Started

### New Users

1. **[QUICK_START.md](QUICK_START.md)** ⭐ START HERE
   - Beta tester or developer?
   - Quick installation commands
   - Troubleshooting quick reference

2. **[INSTALLATION.md](INSTALLATION.md)** - Complete Installation Guide
   - Beta testing vs development modes
   - Step-by-step instructions
   - Switching between modes
   - Verification procedures

3. **[README.md](README.md)** - Project Overview
   - Features and capabilities
   - Prerequisites
   - Quick installation
   - Getting started

### Beta Testers

4. **[BETA_TESTING_CHECKLIST.md](BETA_TESTING_CHECKLIST.md)** - Beta Testing Guide
   - What to test
   - Success checklist
   - Known limitations
   - How to report issues

---

## 👨‍💻 Contributing

### Developers

5. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution Guidelines
   - Development environment setup
   - Conventional commits
   - Code quality standards
   - Testing requirements
   - Documentation guidelines

6. **[CLAUDE.md](CLAUDE.md)** - Claude AI Agent Instructions
   - Project structure and status
   - Development patterns
   - Code quality standards
   - Workflow-driven architecture
   - Troubleshooting reference

---

## 🔧 Troubleshooting & Tools

### Problem Resolution

7. **[DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md)** - Development Troubleshooting
   - Root cause: Stale installations
   - Changes not taking effect
   - Manual fix steps
   - Prevention strategies
   - Release process

### Verification Tools

8. **verify_install.py** - Installation Verification Script
   - Checks import location
   - Detects stale site-packages
   - Verifies pip installation
   - Reports all issues

9. **reinstall_dev.bat** / **reinstall_dev.sh** - Cleanup Scripts
   - Automated cleanup
   - Complete reinstall
   - Fixes stale installations
   - Platform-specific (Windows/Unix)

---

## 📋 Reference Documentation

### Architecture & Design

10. **[docs/features/](docs/features/)** - Feature Documentation
    - PRDs (Product Requirements Documents)
    - Architecture documents
    - Implementation guides
    - Epic and story documentation

11. **[docs/bmm-workflow-status.md](docs/bmm-workflow-status.md)** - Current Status
    - Current epic and story
    - What's next
    - Progress tracking

### Configuration

12. **[gao_dev/config/](gao_dev/config/)** - YAML Configurations
    - Agent configurations
    - Prompt templates
    - Workflow definitions
    - Default settings

---

## 🎯 Quick Reference by Task

### "I want to use GAO-Dev to build something"

→ [BETA_TESTING_CHECKLIST.md](BETA_TESTING_CHECKLIST.md)

**Quick Install:**
```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
gao-dev start
```

### "I want to contribute to GAO-Dev"

→ [CONTRIBUTING.md](CONTRIBUTING.md)

**Quick Install:**
```bash
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"
python verify_install.py
```

### "My changes aren't taking effect"

→ [DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md)

**Quick Fix:**
```bash
python verify_install.py
reinstall_dev.bat  # Windows
./reinstall_dev.sh  # macOS/Linux
```

### "I need to switch from beta testing to development"

→ [INSTALLATION.md](INSTALLATION.md#switching-between-modes)

**Quick Switch:**
```bash
pip uninstall -y gao-dev
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"
python verify_install.py
```

### "I want to understand the codebase"

→ [CLAUDE.md](CLAUDE.md)

**Key Sections:**
- Project Structure
- Development Patterns
- Code Quality Standards
- Workflow-Driven Architecture

---

## ⚠️ Critical Information

### Installation Modes (IMPORTANT!)

GAO-Dev has **two installation modes**:

1. **Beta Testing**: `pip install git+https://...`
2. **Development**: `pip install -e .`

**NEVER MIX BOTH MODES** - This causes stale installations where code changes don't take effect.

**If you've mixed them:**
```bash
# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh
```

### Common Issues

| Problem | Document | Quick Fix |
|---------|----------|-----------|
| Changes not taking effect | DEV_TROUBLESHOOTING.md | `reinstall_dev.bat` |
| Don't know which mode | INSTALLATION.md | See comparison table |
| Want to contribute | CONTRIBUTING.md | Follow setup steps |
| Testing beta release | BETA_TESTING_CHECKLIST.md | `pip install git+https://...` |
| Wrong project_root in logs | DEV_TROUBLESHOOTING.md | `reinstall_dev.bat` |

---

## 📁 Document Organization

```
gao-agile-dev/
├── QUICK_START.md              # ⭐ START HERE
├── INSTALLATION.md             # Complete installation guide
├── README.md                   # Project overview
├── CONTRIBUTING.md             # Contribution guidelines
├── CLAUDE.md                   # Claude AI instructions
├── BETA_TESTING_CHECKLIST.md  # Beta testing guide
├── DEV_TROUBLESHOOTING.md     # Troubleshooting guide
├── DOCUMENTATION_INDEX.md     # This file
│
├── verify_install.py           # Verification script
├── reinstall_dev.bat           # Windows cleanup script
├── reinstall_dev.sh            # Unix cleanup script
│
└── docs/                       # Feature documentation
    ├── features/               # PRDs and architecture
    ├── bmm-workflow-status.md  # Current status
    └── sprint-status.yaml      # Story tracking
```

---

## 🔄 Documentation Updates

**Last Updated**: 2025-11-20

**Recent Changes**:
- Added comprehensive installation modes documentation
- Created troubleshooting guide for stale installations
- Added verification and cleanup scripts
- Updated all docs with installation warnings
- Created quick start guide

**Version**: 2.0

---

## 🆘 Getting Help

- **General Questions**: [GitHub Discussions](https://github.com/memyselfmike/gao-agile-dev/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/memyselfmike/gao-agile-dev/issues)
- **Installation Help**: See [INSTALLATION.md](INSTALLATION.md)
- **Development Help**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Beta Testing Help**: See [BETA_TESTING_CHECKLIST.md](BETA_TESTING_CHECKLIST.md)

---

**Quick Links:**
- [GitHub Repository](https://github.com/memyselfmike/gao-agile-dev)
- [Latest Release](https://github.com/memyselfmike/gao-agile-dev/releases/latest)
- [Issue Tracker](https://github.com/memyselfmike/gao-agile-dev/issues)
- [Discussions](https://github.com/memyselfmike/gao-agile-dev/discussions)
