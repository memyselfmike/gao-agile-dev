# GAO-Dev Beta Tester Guide

**Welcome to GAO-Dev Beta Testing!**

This guide will help you install, use, and update GAO-Dev safely during the beta testing phase.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [First Time Setup](#first-time-setup)
5. [Daily Usage](#daily-usage)
6. [Updating GAO-Dev](#updating-gao-dev)
7. [Troubleshooting](#troubleshooting)
8. [Getting Help](#getting-help)

---

## Quick Start

**3 Steps to Get Started**:

```bash
# 1. Install GAO-Dev
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# 2. Navigate to your project
cd /path/to/your/project

# 3. Start GAO-Dev
gao-dev start
```

That's it! GAO-Dev will initialize your project and start the interactive chat.

---

## Requirements

Before installing, ensure you have:

- ✅ **Python 3.11 or higher**
  ```bash
  python --version
  # Should show: Python 3.11.x or higher
  ```

- ✅ **Git installed**
  ```bash
  git --version
  # Should show: git version 2.x.x or higher
  ```

- ✅ **Internet connection** (for installation and updates)

- ✅ **Virtual environment** (recommended)
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  ```

---

## Installation

### Step 1: Install GAO-Dev

```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**What this does**:
- Downloads GAO-Dev from GitHub
- Installs it to your Python environment (site-packages)
- Creates the `gao-dev` command in your PATH

**Installation time**: 1-2 minutes

### Step 2: Verify Installation

```bash
gao-dev --version
```

**Expected output**:
```
GAO-Dev 1.0.0-beta.1
```

If you see this, installation succeeded! ✅

---

## First Time Setup

### Option A: New Project (Greenfield)

GAO-Dev can create a new project from scratch:

```bash
# 1. Create project directory
mkdir my-new-app
cd my-new-app

# 2. Initialize git (if not already a repo)
git init

# 3. Start GAO-Dev
gao-dev start
```

GAO-Dev will:
- Create `.gao-dev/` directory for project tracking
- Initialize project structure based on your needs
- Start interactive chat with Brian (our AI coordinator)

### Option B: Existing Project (Brownfield)

GAO-Dev can work with existing projects:

```bash
# 1. Navigate to your project
cd /path/to/existing/project

# 2. Start GAO-Dev
gao-dev start
```

GAO-Dev will:
- Create `.gao-dev/` directory in your project
- Analyze existing code structure
- Offer to create missing documentation (PRD, architecture, etc.)

---

## Daily Usage

### Starting GAO-Dev

```bash
# From your project directory
cd /path/to/your/project
gao-dev start
```

**Interactive Chat**: You'll enter a chat interface with Brian.

```
╭─────────────────────────────────────────────────────────────╮
│  GAO-Dev - AI Software Engineering Team                     │
│  Project: my-todo-app                                       │
│  Status: Ready                                              │
╰─────────────────────────────────────────────────────────────╯

Brian: Hi! I'm Brian, your workflow coordinator. What would you like to build today?

You: I want to add user authentication to my app
```

### Common Commands

During chat, you can use:

```
help              Show available commands
status            Check project status
list epics        Show all epics
list stories      Show all stories in an epic
exit              Exit chat
```

### Running Specific Workflows

```bash
# Create a PRD
gao-dev create-prd --name "User Authentication"

# Create architecture document
gao-dev create-architecture --name "Auth System"

# Implement a story
gao-dev implement-story --epic 1 --story 1

# Run retrospective
gao-dev retrospective --epic 1
```

---

## Updating GAO-Dev

### When to Update

You should update when:
- We announce a new beta release (Discord/email)
- You encounter a bug that was fixed
- You want to try new features

### How to Update

```bash
# One command to update
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Update time**: 1-2 minutes

### What Happens During Update

1. ✅ Your project files are **NOT touched**
2. ✅ Your `.gao-dev/` data is **preserved**
3. ✅ **Automatic backup** created before any database changes
4. ✅ Database migrations run automatically (if needed)
5. ✅ Health check validates installation

### After Update

```bash
# Verify new version
gao-dev --version

# Run health check (optional)
gao-dev health-check

# Continue working
cd /path/to/your/project
gao-dev start
```

Your project state is **completely preserved**!

---

## Important: Where to Run GAO-Dev

### ✅ CORRECT: Run from Your Project

```bash
# Good!
cd /path/to/your/project
gao-dev start
```

### ❌ WRONG: Don't Run from GAO-Dev Source

If you cloned GAO-Dev's source code for some reason, **DO NOT** run `gao-dev` from that directory:

```bash
# BAD! Don't do this!
cd /path/to/gao-agile-dev  # GAO-Dev source repo
gao-dev start              # ⚠️ ERROR!
```

**You'll see this error**:
```
[E001] Running from GAO-Dev Source Directory

GAO-Dev must be installed via pip and run from your project directory.

Suggested Fix:
  cd /path/to/your/project
  gao-dev start

Alternative Fix:
  gao-dev start --project /path/to/your/project

Documentation: https://docs.gao-dev.com/errors/E001
Support: https://github.com/memyselfmike/gao-agile-dev/issues/new
```

**Why?** GAO-Dev needs to operate on YOUR project, not its own source code.

---

## Understanding Your Project Structure

After initializing, your project will have:

```
your-project/
├── .gao-dev/              ← GAO-Dev tracking (IMPORTANT!)
│   ├── documents.db       ← Project state database
│   ├── version.txt        ← GAO-Dev version used
│   ├── context.json       ← Execution context
│   └── provider_preferences.yaml  ← AI provider settings
│
├── docs/                  ← Documentation GAO-Dev creates
│   ├── features/          ← Feature documentation
│   │   └── mvp/           ← MVP feature
│   │       ├── PRD.md
│   │       ├── ARCHITECTURE.md
│   │       └── epics/
│   │           └── 1-foundation/
│   │               ├── README.md
│   │               └── stories/
│   │                   └── story-1.1.md
│   └── README.md
│
├── src/                   ← Your source code
├── tests/                 ← Your tests
├── .git/                  ← Your git repo
└── ...
```

**Important**: The `.gao-dev/` directory contains all GAO-Dev's tracking data. Don't delete it!

---

## What Gets Updated vs What Stays

### GAO-Dev Code (Updated)

```
# Installed in Python site-packages
~/.local/lib/python3.11/site-packages/gao_dev/
├── cli/                   ← GAO-Dev commands (UPDATED)
├── orchestrator/          ← AI agents (UPDATED)
├── workflows/             ← Workflows (UPDATED)
└── config/                ← Configuration (UPDATED)
```

### Your Project (Never Touched)

```
~/your-project/
├── .gao-dev/              ← PRESERVED (with migrations if needed)
├── docs/                  ← PRESERVED
├── src/                   ← PRESERVED
├── tests/                 ← PRESERVED
└── .git/                  ← PRESERVED
```

**Key Point**: Updates only affect GAO-Dev's code, never your project files!

---

## Troubleshooting

### Installation Issues

#### Problem: "Command 'git' not found"

**Solution**: Install Git
```bash
# Windows: Download from https://git-scm.com/
# macOS: brew install git
# Linux: sudo apt install git  # Ubuntu/Debian
#        sudo yum install git  # RHEL/CentOS
```

#### Problem: "Python version too old"

**Solution**: Install Python 3.11+
```bash
python --version  # Check current version

# Install Python 3.11 or higher from https://python.org/
```

#### Problem: "pip command not found"

**Solution**: Ensure pip is installed
```bash
python -m ensurepip --upgrade
```

---

### Usage Issues

#### Problem: "Running from source repository" error

**Cause**: You're in GAO-Dev's source directory, not your project.

**Solution**:
```bash
cd /path/to/your/actual/project
gao-dev start
```

#### Problem: "No .gao-dev directory found"

**Cause**: Project not initialized yet.

**Solution**:
```bash
# Initialize project
gao-dev init

# Or just start (will initialize automatically)
gao-dev start
```

#### Problem: "Database is locked"

**Cause**: Multiple GAO-Dev instances running.

**Solution**:
```bash
# Check for running processes
ps aux | grep gao-dev

# Kill if needed
kill <pid>

# Restart
gao-dev start
```

---

### Update Issues

#### Problem: Update failed with error

**Solution**: Your project was automatically backed up.

```bash
# Check backup location
ls -la .gao-dev-backups/

# Contact support with error details
gao-dev health-check --verbose > health-report.txt
# Send health-report.txt to support
```

#### Problem: "Version incompatible" error

**Cause**: Project created with much older/newer GAO-Dev version.

**Solution**:
```bash
# Try updating GAO-Dev
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

# If still failing, contact support
```

---

## Getting Help

### Before Asking for Help

1. Check this guide (you're reading it!)
2. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
3. Check [FAQ.md](./FAQ.md)
4. Search GitHub Issues

### Support Channels

#### Discord (Fastest for Beta)

- Invite: [Discord link]
- Response time: <1 hour (during beta)
- Best for: Quick questions, general discussion

#### GitHub Issues (For Bugs)

- URL: https://github.com/memyselfmike/gao-agile-dev/issues
- Response time: <24 hours
- Best for: Bug reports, feature requests

#### Email (For Private Issues)

- Email: [support email]
- Response time: <48 hours
- Best for: Sensitive issues, detailed problems

### When Reporting Issues

**Include**:
1. GAO-Dev version: `gao-dev --version`
2. Python version: `python --version`
3. Operating system: Windows/macOS/Linux + version
4. Command you ran
5. Full error message
6. Health check output: `gao-dev health-check --verbose`

**Template**:
```
**Environment**:
- GAO-Dev: 1.0.0-beta.1
- Python: 3.11.5
- OS: macOS 14.1

**Command**:
gao-dev start

**Error**:
[paste full error message]

**Health Check**:
[paste output of: gao-dev health-check --verbose]
```

---

## Best Practices

### 1. Use Virtual Environments

```bash
# Create venv
python -m venv .venv

# Activate (do this every time)
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Install GAO-Dev
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Why?** Isolates GAO-Dev from your system Python and other projects.

### 2. Commit .gao-dev to Git

```bash
# Add to git
git add .gao-dev/
git commit -m "Add GAO-Dev project tracking"
```

**Why?** Team members can see project state and history.

### 3. Update Regularly

```bash
# Weekly updates recommended
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Why?** Get latest features and bug fixes.

### 4. Read Changelogs

Before updating, check:
- https://github.com/memyselfmike/gao-agile-dev/blob/main/CHANGELOG.md

**Why?** Know what changed and if any action is needed.

### 5. Backup Before Major Changes

```bash
# Manual backup
cp -r .gao-dev .gao-dev.backup

# Or use GAO-Dev's backup
gao-dev backup
```

**Why?** Extra safety for important projects.

---

## Common Workflows

### Create a New Feature

```bash
cd my-project
gao-dev start

# In chat:
You: I want to add user profile editing
Brian: Great! Let me help you plan that...
# Brian will guide you through PRD → Architecture → Stories → Implementation
```

### Implement a Specific Story

```bash
gao-dev implement-story --epic 1 --story 3

# Or in chat:
You: Implement story 1.3
```

### Check Project Status

```bash
gao-dev status

# Or in chat:
You: status
```

### Run Team Ceremonies

```bash
# Sprint planning
gao-dev ceremony planning --epic 1

# Sprint retrospective
gao-dev ceremony retrospective --epic 1

# Or in chat:
You: Let's do a retrospective for epic 1
```

---

## Advanced Usage

### Using Specific Branches

During beta, we may ask you to test specific branches:

```bash
# Install from specific branch
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@feature/new-workflow

# Or specific commit
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@abc1234
```

### Multiple Projects

GAO-Dev supports working with multiple projects:

```bash
# Project 1
cd ~/project1
gao-dev start

# (exit)

# Project 2
cd ~/project2
gao-dev start
```

Each project has its own `.gao-dev/` tracking directory.

### Using Different AI Providers

GAO-Dev supports multiple AI providers:

```bash
# First run will prompt for provider selection
gao-dev start

# Or set environment variable
export AGENT_PROVIDER=opencode
gao-dev start

# Or configure in .gao-dev/provider_preferences.yaml
```

---

## FAQ

### General Questions

**Q: Is GAO-Dev free?**
A: Yes! GAO-Dev is open source. You pay only for AI API usage (Anthropic Claude or OpenCode).

**Q: Can I use GAO-Dev offline?**
A: No. GAO-Dev requires internet to communicate with AI providers.

**Q: Will GAO-Dev overwrite my code?**
A: No. GAO-Dev creates new files and documents but never modifies existing code without your approval.

**Q: Can I use GAO-Dev with my team?**
A: Yes! Commit `.gao-dev/` to your git repo and your team can collaborate.

### Technical Questions

**Q: What programming languages does GAO-Dev support?**
A: Python, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby, PHP, and more. Greenfield initialization supports 9 languages.

**Q: Does GAO-Dev work with monorepos?**
A: Yes! Run `gao-dev init` in each sub-project directory.

**Q: Can I customize workflows?**
A: Not yet in beta, but coming soon! You'll be able to create custom workflows via YAML.

**Q: Does GAO-Dev collect telemetry?**
A: Not currently. We may add opt-in telemetry in the future (with your permission).

### Beta-Specific Questions

**Q: How stable is the beta?**
A: We're actively developing. Expect weekly updates and occasional breaking changes (with migrations).

**Q: Will my project break during beta?**
A: No. We have automatic backups, migrations, and rollback mechanisms to protect your project.

**Q: Can I use GAO-Dev for production projects?**
A: Use caution. Beta is suitable for side projects and experimentation. Wait for 1.0.0 for production use.

**Q: How do I give feedback?**
A: Discord for quick feedback, GitHub Issues for bugs/features, or fill out our weekly survey.

See [FAQ.md](./FAQ.md) for complete list.

---

## Tips for Success

1. **Start Small**: Try GAO-Dev on a test project first
2. **Read Brian's Suggestions**: Brian provides helpful context and recommendations
3. **Iterate Quickly**: Don't aim for perfection on first try
4. **Ask Questions**: We're here to help during beta!
5. **Give Feedback**: Your input shapes GAO-Dev's future

---

## What's Next?

Now that you're set up:

1. ✅ Try creating a simple feature
2. ✅ Explore different commands
3. ✅ Join our Discord community
4. ✅ Share your feedback
5. ✅ Help us improve GAO-Dev!

**Happy building! 🚀**

---

## Document Updates

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-13 | Initial guide |

---

## Quick Reference Card

```
INSTALLATION
  pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

VERIFICATION
  gao-dev --version

USAGE
  cd /path/to/your/project
  gao-dev start

UPDATE
  pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

HELP
  Discord: [link]
  GitHub: https://github.com/memyselfmike/gao-agile-dev/issues
  Docs: [link]
```

Print this for quick reference! 📋
