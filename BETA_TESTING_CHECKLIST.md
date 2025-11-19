# GAO-Dev Web Interface Beta Testing Guide

**Beta Version:** 0.2.1-beta.1
**Release Date:** 2025-11-19
**Latest Update:** 2025-11-19 - Fixed `gao-dev init` TypeError on Python 3.14
**Testing Duration:** 30-45 minutes
**For:** Beta testers evaluating the GAO-Dev Web Interface

---

## What is GAO-Dev?

GAO-Dev is an autonomous AI development orchestration system that helps you build complete applications from simple prompts. It uses 8 specialized Claude agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary) to handle the entire software development lifecycle.

**This beta release** introduces the **Web Interface** - a full-featured IDE-like experience for interacting with GAO-Dev agents through your browser.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed (python --version)
- **pip** package manager (pip --version)
- **Git** installed (git --version)
- **Node.js 18+** installed (node --version) - for frontend
- **Anthropic API key** (for Claude access)
  - Get one at: https://console.anthropic.com/
  - Set environment variable:
    - macOS/Linux: export ANTHROPIC_API_KEY="your-key-here"
    - Windows CMD: set ANTHROPIC_API_KEY=your-key-here
    - Windows PowerShell: \:ANTHROPIC_API_KEY="your-key-here"

---

## Upgrading to Latest Version

If you already have GAO-Dev installed and need to get the latest fixes:

### Upgrade to Latest Release (Recommended)

```bash
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

### Upgrade to Latest from Main Branch

```bash
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

### Verify Your Version

```bash
gao-dev --version
```

### Check Available Releases

Visit: https://github.com/memyselfmike/gao-agile-dev/releases

---

## Quick Start (10 minutes)

### Step 1: Create a Clean Project Directory

Create and enter a new project directory:
- mkdir my-gao-project
- cd my-gao-project
- git init
- git config user.name "Your Name"
- git config user.email "your@email.com"

### Step 2: Install GAO-Dev

pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

Verify: gao-dev --version

### Step 3: Initialize Your Project

gao-dev init --greenfield

### Step 4: Start the Web Interface

gao-dev web

Or: python -m uvicorn gao_dev.web.server:app --host 127.0.0.1 --port 3000

### Step 5: Open in Browser

Navigate to: http://localhost:3000

---

## Features to Test

1. **Chat with Brian** - Main chat panel
2. **Layout Presets** - Default, Code-Focused, Chat-Focused
3. **DM Conversations** - Direct message agents
4. **File Browser** - Browse and edit files
5. **Activity Feed** - Real-time events
6. **Git Timeline** - Commit history and diffs
7. **Kanban Board** - Stories/tasks
8. **Settings Panel** - Provider configuration
9. **Theme Toggle** - Light/dark themes
10. **WebSocket Connection** - Real-time status

---

## Success Checklist

- [ ] Installation completed
- [ ] Web server starts
- [ ] Browser loads interface
- [ ] Chat with Brian works
- [ ] Layout presets work
- [ ] Panel resizing works
- [ ] DM conversations work
- [ ] File browser works
- [ ] Activity feed works
- [ ] Git timeline works
- [ ] Kanban board works
- [ ] Settings work
- [ ] Theme toggle works
- [ ] WebSocket stable

---

## Known Limitations

1. Only Brian has full chat - other agents show "No messages yet"
2. Ceremony channels are placeholders
3. File editing may be read-only
4. Some workflows not fully implemented
5. First load may be slower

---

## Troubleshooting

- Port in use: netstat -ano | findstr :3000
- Blank page: Check browser console (F12)
- WebSocket failed: Check server is running

---

## Submit Feedback

GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues

**Happy Testing\!**
