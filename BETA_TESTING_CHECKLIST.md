# GAO-Dev Beta Testing Guide

**Beta Version:** 0.3.0-beta.1
**Release Date:** 2025-11-19
**Latest Update:** 2025-11-20 - Installation Modes & Development Workflow
**Testing Duration:** 30-45 minutes
**For:** Beta testers evaluating GAO-Dev

---

## ⚠️ Important: Installation Modes

GAO-Dev has **two installation modes**:

- **Beta Testing Mode** (this guide): `pip install git+https://github.com/...`
- **Development Mode**: `pip install -e .` (for contributing to GAO-Dev)

**DO NOT MIX BOTH MODES!** Mixing modes causes conflicts where code changes don't take effect.

**If you're beta testing AND developing:**
- Use separate virtual environments (see [INSTALLATION.md](INSTALLATION.md#switching-between-modes))
- Use `reinstall_dev.bat` to clean up conflicts

**For complete installation guide:** See [INSTALLATION.md](INSTALLATION.md)

---

## What is GAO-Dev?

GAO-Dev is an autonomous AI development orchestration system that helps you build complete applications from simple prompts. It uses 8 specialized Claude agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary) to handle the entire software development lifecycle.

**This beta release** introduces **Streamlined Onboarding** - a unified `gao-dev start` command with automatic environment detection, guided wizards, and the full web interface.

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

## Quick Start (5 minutes)

### Step 1: Create a Clean Project Directory

```bash
mkdir my-gao-project
cd my-gao-project
```

### Step 2: Install GAO-Dev

```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

Verify: `gao-dev --version`

### Step 3: Start GAO-Dev

```bash
gao-dev start
```

That's it! The new unified command will:
- Auto-detect your environment (Desktop, Docker, SSH, WSL)
- Launch the appropriate onboarding wizard
- Guide you through setup (Git, provider, credentials)
- Start the web interface automatically

### Step 4: Follow the Onboarding Wizard

The wizard will guide you through:
1. **Project setup** - Name and type
2. **Git configuration** - Author name/email
3. **Provider selection** - Claude Code, OpenAI, or Ollama
4. **Credentials** - API key entry (secure storage)

### Step 5: Open in Browser

After onboarding completes, navigate to: http://localhost:8080

**Note:** For headless/CI environments, use `gao-dev start --headless`

---

## Features to Test

### New in This Release - Streamlined Onboarding
1. **Unified Start Command** - `gao-dev start` replaces init + web
2. **Environment Detection** - Auto-detects Desktop, Docker, SSH, WSL
3. **TUI Wizard** - Terminal-based onboarding for Docker/SSH
4. **Web Wizard** - Browser-based onboarding for Desktop
5. **Credential Manager** - Secure API key storage
6. **State Persistence** - Resume interrupted onboarding
7. **API Key Validation** - Real-time key verification

### Web Interface Features
8. **Chat with Brian** - Main chat panel
9. **Layout Presets** - Default, Code-Focused, Chat-Focused
10. **DM Conversations** - Direct message agents
11. **File Browser** - Browse and edit files
12. **Activity Feed** - Real-time events
13. **Git Timeline** - Commit history and diffs
14. **Kanban Board** - Stories/tasks
15. **Settings Panel** - Provider configuration
16. **Theme Toggle** - Light/dark themes

---

## Success Checklist

### Onboarding (New)
- [ ] `gao-dev start` launches without errors
- [ ] Environment correctly detected
- [ ] Onboarding wizard appears (TUI or Web)
- [ ] Project configuration works
- [ ] Git setup works
- [ ] Provider selection works
- [ ] Credential entry works
- [ ] API key validates (if online)

### Web Interface
- [ ] Web server starts after onboarding
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
6. Keychain not available in Docker/SSH (use environment variables)

---

## Deprecated Commands

The following commands are deprecated and will be removed in v3.0 (Q2 2026):

- `gao-dev init` - Use `gao-dev start` instead
- `gao-dev web start` - Use `gao-dev start` instead

These commands still work but will show a deprecation warning.
See: [Migration Guide](docs/migration/deprecated-commands.md)

---

## Troubleshooting

### Common Issues

- **Port in use**: `netstat -ano | findstr :8080` (Windows) or `lsof -i :8080` (macOS/Linux)
- **Blank page**: Check browser console (F12)
- **WebSocket failed**: Check server is running
- **API key invalid**: Check for extra spaces, get new key from provider

### Error Codes

If you see an error code (E001-E701), check:
[Common Errors Guide](docs/troubleshooting/common-errors.md)

---

## Submit Feedback

GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues

Include:
- Error message or code
- Operating system
- Python version (`python --version`)
- GAO-Dev version (`gao-dev --version`)

**Happy Testing!**
