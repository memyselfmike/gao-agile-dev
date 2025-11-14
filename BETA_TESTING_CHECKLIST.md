# GAO-Dev Beta Testing Guide

**Beta Version:** 0.1.0-beta.1
**Release Date:** 2025-01-14
**Testing Duration:** 30-45 minutes
**For:** End users testing the GAO-Dev product

---

## What is GAO-Dev?

GAO-Dev is an autonomous AI development orchestration system that helps you build complete applications from simple prompts. It uses 8 specialized Claude agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary) to handle the entire software development lifecycle.

**This beta test** verifies that the core installation, setup, and basic features work correctly on your system.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed (`python --version`)
- **pip** package manager (`pip --version`)
- **Git** installed (`git --version`)
- **Anthropic API key** (for Claude access)
  - Get one at: https://console.anthropic.com/
  - Set environment variable: `export ANTHROPIC_API_KEY="your-key-here"` (macOS/Linux)
  - Or: `set ANTHROPIC_API_KEY=your-key-here` (Windows CMD)
  - Or: `$env:ANTHROPIC_API_KEY="your-key-here"` (Windows PowerShell)

---

## Installation (5 minutes)

### Option 1: Install from GitHub Release (Recommended)

1. **Download the release:**
   ```bash
   # Download the .whl file from GitHub Releases
   # https://github.com/anthropics/gao-agile-dev/releases/tag/v0.1.0-beta.1

   pip install gao_dev-0.1.0b1-py3-none-any.whl
   ```

### Option 2: Install from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/anthropics/gao-agile-dev.git
   cd gao-agile-dev
   git checkout v0.1.0-beta.1
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

### Verify Installation

```bash
gao-dev --version
# Expected: gao-dev, version 0.1.0-beta.1

gao-dev --help
# Should display help text without errors
```

**If you see errors:**
- Try `python -m gao_dev --version`
- Check that Python scripts directory is in PATH
- Reinstall: `pip uninstall gao-dev && pip install -e .`

---

## Core Feature Tests

### Test 1: Health Check (2 minutes)

Verify system health and configuration.

```bash
gao-dev health
```

**Expected Output:**
- System status: HEALTHY or warnings
- Python version check
- Git availability check
- API key status (configured/missing)
- No crashes or errors

**Report if:**
- Command crashes
- Shows errors for properly configured items
- Reports incorrect Python/Git status

---

### Test 2: List Available Resources (3 minutes)

Check that workflows and agents are loaded.

```bash
# List all 8 agents
gao-dev list-agents

# Expected: Shows 8 agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary)

# List all workflows
gao-dev list-workflows

# Expected: Shows 50+ workflows organized by phase
```

**Report if:**
- Fewer than 8 agents shown
- Fewer than 50 workflows shown
- Any command crashes
- Output is garbled or unreadable

---

### Test 3: Project Initialization (5 minutes)

Test creating a new greenfield project.

```bash
# Create a test directory
mkdir -p /tmp/gao-test-project
cd /tmp/gao-test-project

# Initialize git repository
git init
git config user.name "Test User"
git config user.email "test@example.com"

# Initialize GAO-Dev project
gao-dev init --greenfield

# Check what was created
ls -la
ls -la .gao-dev/
```

**Expected Results:**
- `.gao-dev/` directory created
- `.gao-dev/documents.db` database file exists
- `.gao-dev/provider_preferences.yaml` exists (if you selected a provider)
- No errors during initialization

**Report if:**
- Initialization fails or crashes
- Missing `.gao-dev/` directory
- Database file not created
- Permission errors

---

### Test 4: Interactive Chat with Brian (5-10 minutes)

Test the main interactive interface.

```bash
gao-dev start
```

**Expected Behavior:**
1. Provider selection prompt appears (if not configured)
   - Shows options: Claude Code, OpenCode, Ollama
   - Allows selection via arrow keys
   - Saves preference

2. Welcome message from Brian
   - Project detection (should detect test project)
   - Prompt for input

3. Try some commands:
   ```
   > help
   > list workflows
   > what can you do?
   > exit
   ```

**Report if:**
- Chat doesn't start or crashes immediately
- Provider selection doesn't work
- Brian doesn't respond to commands
- Can't exit cleanly (use Ctrl+C if needed)
- Project not detected correctly

---

### Test 5: Simple Command Execution (5 minutes)

Test autonomous command execution (OPTIONAL - requires API key).

```bash
# Still in /tmp/gao-test-project

# Try creating a PRD (will use your API key)
gao-dev create-prd --name "Simple Todo App"

# This should:
# 1. Call Claude API to generate PRD
# 2. Create docs/PRD.md
# 3. Register document in database
```

**Expected Results:**
- Command runs without crashing
- Some output/progress displayed
- May take 30-60 seconds
- `docs/PRD.md` file created (if successful)

**Report if:**
- Command crashes
- Hangs indefinitely (>2 minutes)
- Creates files in wrong locations
- Database errors
- API errors (note: rate limiting is expected if testing multiple times)

---

### Test 6: Workflow Information (2 minutes)

Test getting information about workflows.

```bash
# Get details about a specific workflow
gao-dev list-workflows --phase 2

# Expected: Shows Phase 2 workflows (Planning)
```

**Report if:**
- Filtering doesn't work
- Shows workflows from wrong phase
- Command crashes

---

## What to Report Back

### Success Checklist

Please mark what worked:

- [ ] Installation completed successfully
- [ ] `gao-dev --version` shows correct version
- [ ] `gao-dev health` runs without errors
- [ ] `gao-dev list-agents` shows all 8 agents
- [ ] `gao-dev list-workflows` shows 50+ workflows
- [ ] `gao-dev init --greenfield` creates project structure
- [ ] `gao-dev start` launches interactive chat
- [ ] Provider selection works (if applicable)
- [ ] Brian responds to commands
- [ ] Commands execute without crashes

### Bug Report Template

If you encounter issues, please report:

```
**Environment:**
- OS: [Windows/macOS/Linux] + version
- Python version: [output of `python --version`]
- Installation method: [GitHub release / source]
- API key configured: [Yes/No]

**Issue:**
- Command attempted: [exact command]
- Expected behavior: [what should happen]
- Actual behavior: [what actually happened]
- Error message: [full error output if any]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [etc.]

**Additional Context:**
[Any other relevant information]
```

### Feature Feedback

We'd also love to hear:

- **What worked well?**
- **What was confusing?**
- **What features would you like to see?**
- **How was the performance?** (speed, responsiveness)
- **Was the documentation helpful?**

---

## Known Limitations (Don't Report These)

**Expected behaviors in this beta:**

1. **Provider Selection:**
   - First run will prompt for provider selection
   - Preference is saved and won't prompt again
   - Use `AGENT_PROVIDER` environment variable to skip prompt

2. **Interactive Chat:**
   - Some advanced features may not work yet
   - Focus on basic commands and navigation

3. **API Rate Limits:**
   - Claude API has rate limits
   - You may see 429 errors if testing repeatedly
   - This is expected behavior

4. **Performance:**
   - First run may be slower (loading workflows)
   - Subsequent runs should be faster (caching)

5. **Workflow Execution:**
   - Some workflows may be incomplete
   - Focus testing on basic commands
   - Not all 50+ workflows are fully implemented yet

---

## Getting Help

**Questions during testing?**

1. Check the help: `gao-dev --help`
2. Read the docs: `docs/README.md`
3. Open an issue: https://github.com/anthropics/gao-agile-dev/issues

**Emergency:**

If GAO-Dev becomes unresponsive:
- Press `Ctrl+C` to interrupt
- Check for hung processes: `ps aux | grep gao-dev`
- Kill if needed: `pkill -f gao-dev`

---

## After Testing

### Cleanup (Optional)

```bash
# Remove test project
rm -rf /tmp/gao-test-project

# Uninstall GAO-Dev (if desired)
pip uninstall gao-dev
```

### Submit Feedback

Please send your completed checklist and bug reports to:
- **Email:** [maintainer-email]
- **GitHub Issues:** https://github.com/anthropics/gao-agile-dev/issues
- **Discord:** [link if available]

---

## Thank You!

Your feedback is invaluable in making GAO-Dev better. We appreciate you taking the time to test this beta release!

**What's Next:**

Based on your feedback, we'll:
1. Fix critical bugs
2. Improve documentation
3. Enhance user experience
4. Prepare for the next beta release

---

**Questions?** Open an issue or contact the maintainers.

**Happy Testing!** 🚀
