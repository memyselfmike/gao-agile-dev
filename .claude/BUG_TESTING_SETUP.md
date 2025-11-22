# Bug Testing & Verification System

**Created**: 2025-11-22
**Version**: 1.0

## Overview

This document describes the comprehensive bug testing and verification system created for GAO-Dev. The system ensures all bug fixes are systematically tested across both development and beta test environments before release.

---

## Components Created

### 1. Bug-Tester Agent

**File**: `.claude/agents/bug-tester.md`

**Purpose**: Specialized QA Engineer agent for systematic bug testing and verification

**Capabilities**:
- Systematic bug reproduction with documentation
- Dual-environment testing (dev CWD + beta C:/Testing)
- Playwright-based UI testing
- Server log monitoring and analysis
- Regression test creation
- Comprehensive verification reporting

**When Invoked**:
- Automatically when fixing bugs
- When verifying bug fixes
- When testing changes in both environments
- When creating regression tests
- When performing visual regression testing

**Tools Available**: Read, Write, Edit, Grep, Glob, Bash, mcp__playwright__*, mcp__ide__getDiagnostics

---

### 2. UI Testing Skill

**File**: `.claude/skills/ui-testing/SKILL.md`

**Purpose**: Systematic UI testing patterns using Playwright

**Features**:
- 7 core testing patterns (navigation, interaction, layout, errors, network, workflows, regression)
- Screenshot organization and naming conventions
- GAO-Dev-specific test scenarios (onboarding, layout presets, chat, file browser)
- Console error detection
- Network request verification
- Visual regression testing

**Common Patterns**:
```python
# Navigation and Screenshot
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Dashboard")
mcp__playwright__browser_take_screenshot(filename="dashboard.png")

# Element Interaction
mcp__playwright__browser_click(element="Submit", ref="button[type='submit']")

# Layout Testing
mcp__playwright__browser_resize(width=1920, height=1080)

# Error Detection
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)
```

**Tools Available**: Read, Grep, Glob, Bash, mcp__playwright__*

---

### 3. Bug Verification Workflow Skill

**File**: `.claude/skills/bug-verification/SKILL.md`

**Purpose**: Complete end-to-end bug fix verification workflow

**Workflow Phases**:

**Phase 1: Development Environment (CWD)**
1. Verify bug exists (pre-fix)
2. Apply fix
3. Manual verification with Playwright
4. Regression testing
5. Create regression test
6. Commit changes

**Phase 2: Beta Environment (C:/Testing)**
7. Install beta version from GitHub
8. Test in beta environment
9. Test onboarding (if applicable)
10. Test common workflows

**Phase 3: Verification Report**
11. Create comprehensive report
12. Document all test results
13. Capture screenshots
14. Update issue tracker

**Verification Checklist**:
- ✅ Dev environment: All tests passing
- ✅ Beta environment: Fix verified
- ✅ Playwright verification successful
- ✅ Server logs clean
- ✅ Console errors: none
- ✅ Regression test created
- ✅ No regressions detected
- ✅ Documentation complete

**Tools Available**: Read, Write, Edit, Grep, Glob, Bash, mcp__playwright__*, mcp__ide__getDiagnostics

---

### 4. Slash Commands

#### `/verify-bug-fix`

**File**: `.claude/commands/verify-bug-fix.md`

**Purpose**: Invoke complete bug verification workflow

**Usage**:
```
/verify-bug-fix

Bug: #123 - Onboarding wizard crashes on step 2
Fixed in: da8505c
Files: gao_dev/web/api/onboarding.py, gao_dev/web/frontend/src/components/OnboardingWizard.tsx
```

**What It Does**:
1. Tests in development environment (CWD)
2. Tests in beta environment (C:/Testing)
3. Runs Playwright UI tests
4. Monitors server logs
5. Checks for regressions
6. Creates verification report
7. Provides screenshots
8. Gives release recommendation

**Output**: Comprehensive verification report with screenshots and test results

---

#### `/test-ui`

**File**: `.claude/commands/test-ui.md`

**Purpose**: Run systematic Playwright UI tests

**Usage**:
```
/test-ui

Component: Onboarding Wizard
Tests:
- Navigate through all steps
- Verify form validation
- Check completion state
- Capture screenshots of each step
```

**What It Does**:
1. Starts Playwright browser
2. Navigates to specified page
3. Performs test actions
4. Captures screenshots
5. Checks for console errors
6. Verifies network requests
7. Tests responsive layouts (if requested)

**Output**: Screenshots, console error report, network analysis, test summary

---

### 5. Updated Documentation

#### CLAUDE.md

**Section Added**: "Bug Fixing and Testing" (Section 5)

**Key Points**:
- CRITICAL: Always use bug-tester agent for bug fixes
- Systematic verification in BOTH environments required
- Playwright UI testing mandatory
- Log monitoring required
- Regression tests required
- Comprehensive documentation required

**Quick Commands**:
- `/verify-bug-fix` - Complete verification workflow
- `/test-ui` - Systematic Playwright UI testing

---

#### .claude/AGENTS_AND_SKILLS_README.md

**Updates**:
- Added Bug Tester agent (section 7)
- Added UI Testing skill (section 5)
- Added Bug Verification skill (section 6)
- Updated agent selection guide
- Updated agent coordination workflow
- Updated version history to v1.1

---

## System Architecture

### Dual-Environment Testing

**Development Environment (CWD)**:
- Location: `C:\Projects\gao-agile-dev`
- Install Type: Editable (`pip install -e .`)
- Purpose: Rapid development and testing
- Changes: Immediate effect (hot reload)

**Beta Test Environment**:
- Location: `C:\Testing`
- Install Type: Standard (`pip install git+https://...`)
- Purpose: Production-like testing
- Changes: Only after reinstall from GitHub

### Testing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Bug Reported                           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            PHASE 1: Development Environment                 │
│  1. Reproduce bug with Playwright (screenshots + logs)      │
│  2. Apply fix in code                                       │
│  3. Run unit tests                                          │
│  4. Verify with Playwright                                  │
│  5. Check server logs                                       │
│  6. Create regression test                                  │
│  7. Commit and push to GitHub                               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│             PHASE 2: Beta Environment                       │
│  1. Activate beta venv (C:\Testing)                         │
│  2. Install latest from GitHub                              │
│  3. Verify installation (not editable)                      │
│  4. Test with Playwright                                    │
│  5. Test onboarding (if applicable)                         │
│  6. Test core workflows                                     │
│  7. Check for regressions                                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            PHASE 3: Verification Report                     │
│  1. Create comprehensive report                             │
│  2. Document test results                                   │
│  3. Attach screenshots                                      │
│  4. Update GitHub issue                                     │
│  5. Provide release recommendation                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Example 1: Fix UI Bug

```python
# User reports: "Chat interface doesn't show messages"

# Claude automatically invokes bug-tester agent
Task(
    subagent_type="bug-tester",
    description="Verify chat message display bug fix",
    prompt="""
    Bug: Chat interface doesn't show messages after sending
    Fixed in: abc123d
    Files: gao_dev/web/frontend/src/components/Chat.tsx

    Please:
    1. Reproduce the bug in dev environment with Playwright
    2. Verify the fix works
    3. Test in beta environment
    4. Create regression test
    5. Generate verification report with screenshots
    """
)

# Agent will:
# 1. Navigate to chat in dev, send message, verify it displays
# 2. Take screenshots before/after
# 3. Check server logs and console
# 4. Install in C:/Testing and repeat tests
# 5. Create test_chat_message_display_regression()
# 6. Generate comprehensive report
```

### Example 2: Test Layout Changes

```
# User: "I fixed the layout resize issue, can you verify it?"

/test-ui

Feature: Layout resize behavior
Tests:
- Test Default preset at multiple sizes
- Test Code-Focused preset resize
- Test Chat-Focused preset resize
- Verify no overflow or broken layouts
- Capture screenshots at each size
```

### Example 3: Complete Bug Verification

```
# User: "Please verify bug #456 is fixed"

/verify-bug-fix

Bug: #456 - Onboarding wizard validation errors not displayed
Fixed in: def789g
Files:
- gao_dev/web/api/onboarding.py
- gao_dev/web/frontend/src/components/OnboardingWizard.tsx
```

---

## Best Practices

### For Bug Fixes

1. **Always use the bug-tester agent** - Don't test manually
2. **Test in BOTH environments** - Dev AND beta
3. **Use Playwright for UI** - Systematic, reproducible
4. **Monitor logs** - Before and after fixes
5. **Create regression tests** - Prevent recurrence
6. **Document thoroughly** - Verification reports

### For UI Testing

1. **Wait for page load** - Before taking screenshots
2. **Use descriptive names** - For elements and screenshots
3. **Check console errors** - After every interaction
4. **Test responsive** - Multiple screen sizes
5. **Capture before/after** - For visual comparison

### For Verification

1. **Follow the workflow** - All 3 phases
2. **Complete checklist** - Don't skip steps
3. **Evidence-based** - Screenshots and logs
4. **Update issues** - Keep GitHub in sync
5. **Sign-off required** - All criteria met

---

## Integration with Development Workflow

### When Claude Works on Bugs

**Automatic Invocation**:
- Claude detects "bug", "fix", "broken", "error" in user message
- Automatically invokes bug-tester agent
- Follows systematic verification workflow

**Manual Invocation**:
- User runs `/verify-bug-fix`
- User explicitly requests "use bug-tester agent"
- User asks to "verify the fix works"

**Required Steps** (enforced by CLAUDE.md):
- ✅ Test in development environment
- ✅ Test in beta environment
- ✅ Playwright verification
- ✅ Server log analysis
- ✅ Console error checking
- ✅ Regression test creation
- ✅ Verification report
- ✅ No regressions detected

---

## Directory Structure

```
.claude/
├── agents/
│   ├── bug-tester.md              # NEW: Bug testing agent
│   ├── test-architect.md
│   ├── developer.md
│   └── ...
│
├── skills/
│   ├── ui-testing/
│   │   └── SKILL.md               # NEW: Playwright UI testing patterns
│   ├── bug-verification/
│   │   └── SKILL.md               # NEW: Complete verification workflow
│   ├── code-review/
│   ├── story-writing/
│   └── ...
│
├── commands/
│   ├── verify-bug-fix.md          # NEW: /verify-bug-fix command
│   ├── test-ui.md                 # NEW: /test-ui command
│   ├── release-status.md
│   └── ...
│
├── AGENTS_AND_SKILLS_README.md    # UPDATED: Added bug-tester, ui-testing, bug-verification
└── BUG_TESTING_SETUP.md           # NEW: This file

CLAUDE.md                           # UPDATED: Added Section 5 - Bug Fixing and Testing
```

---

## Prerequisites

### For Development Testing

- Editable install: `pip install -e .`
- Verify: `python verify_install.py` (all [PASS])
- Servers running: `start_web.bat`

### For Beta Testing

- Beta environment setup: See `docs/LOCAL_BETA_TESTING_GUIDE.md`
- Beta venv created: `C:\Testing\venv-beta`
- Scripts available: `C:\Testing\scripts/`

### For Playwright Testing

- Playwright MCP installed and configured
- Browser installed: `mcp__playwright__browser_install` (if needed)
- Servers running: Backend (port 3000), Frontend (port 5173)

---

## Troubleshooting

### Bug-Tester Agent Not Invoked

**Problem**: Claude doesn't use the agent for bug fixes

**Solutions**:
1. Explicitly request: "Use bug-tester agent to verify this fix"
2. Use slash command: `/verify-bug-fix`
3. Mention "bug" or "fix" in your message
4. Check CLAUDE.md is loaded (should auto-load from project root)

### Playwright Tests Fail

**Problem**: Can't find elements or timeout errors

**Solutions**:
1. Ensure servers are running: `start_web.bat`
2. Check page loaded: `mcp__playwright__browser_wait_for(text="...")`
3. Get fresh snapshot: `mcp__playwright__browser_snapshot()`
4. Use correct refs from snapshot
5. Increase timeout if needed

### Beta Environment Issues

**Problem**: Fix works in dev but not in beta

**Solutions**:
1. Verify code is pushed to GitHub
2. Force reinstall: `pip install --upgrade --force-reinstall --no-cache-dir git+https://...`
3. Clear browser cache
4. Restart server
5. Check installation location (should be venv-beta\Lib\site-packages)

### Environment Confusion

**Problem**: Not sure which environment you're in

**Solution**:
```bash
call C:\Testing\scripts\verify-environment.bat

# Should show:
# Environment: BETA TESTING
# Location: C:\Testing\venv-beta

# OR for dev:
# Environment: DEVELOPMENT
# Location: C:\Projects\gao-agile-dev
```

---

## Success Metrics

### System is Working When:

- ✅ Bug-tester agent is automatically invoked for bug fixes
- ✅ All bug fixes tested in both dev and beta environments
- ✅ Playwright screenshots captured for every UI change
- ✅ Server logs analyzed for all fixes
- ✅ Regression tests created for all bugs
- ✅ Verification reports generated and attached to issues
- ✅ No bugs slip through to release without full verification

### Quality Indicators:

- Zero bugs released without dual-environment testing
- 100% of UI bugs verified with Playwright
- All bugs have regression tests
- All verification reports include screenshots
- Beta testers report fewer bugs (system catches them first)

---

## Future Enhancements

### Potential Improvements:

1. **Automated Screenshot Comparison**
   - Pixel-by-pixel diff for visual regression
   - Highlight changed areas
   - Threshold-based pass/fail

2. **Performance Metrics**
   - Load time before/after fix
   - Memory usage comparison
   - API response time tracking

3. **Test Recording**
   - Record Playwright test sessions
   - Replay for debugging
   - Share with team

4. **CI Integration**
   - Run bug verification in GitHub Actions
   - Auto-comment on PRs with results
   - Block merge if verification fails

5. **Bug Analytics**
   - Track bug frequency by component
   - Identify regression-prone areas
   - Suggest preventive measures

---

## References

### Documentation

- `.claude/agents/bug-tester.md` - Bug tester agent specification
- `.claude/skills/ui-testing/SKILL.md` - UI testing patterns
- `.claude/skills/bug-verification/SKILL.md` - Verification workflow
- `CLAUDE.md` - Main project guide (Section 5: Bug Fixing and Testing)
- `.claude/AGENTS_AND_SKILLS_README.md` - All agents and skills
- `docs/LOCAL_BETA_TESTING_GUIDE.md` - Beta environment setup

### Commands

- `/verify-bug-fix` - Complete verification workflow
- `/test-ui` - Systematic UI testing
- `/release-status` - Check release status
- `/pre-release-check` - Pre-release validation

### Related Tools

- Playwright MCP: UI testing and screenshots
- mcp__ide__getDiagnostics: Code diagnostics
- TodoWrite: Progress tracking

---

## Contact & Support

**Questions**: Ask Claude with context from this document
**Issues**: Document in GitHub issues with verification report
**Improvements**: Suggest enhancements to the workflow

---

**Version**: 1.0
**Created**: 2025-11-22
**Last Updated**: 2025-11-22
**Status**: ✅ Production Ready

---

**Remember**: This system ensures all bug fixes are thoroughly tested across both development and beta environments before release. Always use the bug-tester agent for bug fixes—it's not optional, it's required for quality!
