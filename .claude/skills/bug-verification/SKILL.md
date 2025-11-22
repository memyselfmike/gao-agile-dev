---
name: bug-verification
description: Complete workflow for verifying bug fixes across development and beta test environments. Provides systematic testing procedures, verification checklists, and reporting templates. Use when verifying bug fixes are complete and ready for release.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, mcp__playwright__*, mcp__ide__getDiagnostics
---

# Bug Verification Workflow Skill

This skill provides a complete, systematic workflow for verifying bug fixes in both development (CWD) and beta test (C:/Testing) environments.

## When to Use

Use this skill when:
- Verifying a bug fix is complete
- Testing changes across environments
- Creating verification reports
- Ensuring no regressions
- Preparing for release

## Complete Verification Workflow

### Phase 1: Development Environment Verification (CWD)

**Location**: `C:\Projects\gao-agile-dev`
**Environment**: Editable install (pip install -e .)

#### Step 1: Verify Bug Exists (Pre-Fix)

```bash
# Checkout branch with bug (if needed)
git checkout main

# Start web interface
start_web.bat

# Use Playwright to reproduce bug
# Document steps and take screenshots
```

**Checklist:**
- [ ] Bug is reproducible
- [ ] Reproduction steps documented
- [ ] Screenshots captured showing bug
- [ ] Server logs captured showing error
- [ ] Console errors documented

#### Step 2: Apply Fix

```bash
# Make code changes
# Run unit tests to verify fix
pytest tests/unit/ -v

# Run type checking
mypy gao_dev/

# Check for any diagnostics
# Use mcp__ide__getDiagnostics if available
```

**Checklist:**
- [ ] Code changes made
- [ ] Unit tests pass
- [ ] Type hints correct
- [ ] No new diagnostics
- [ ] Code follows style guide

#### Step 3: Manual Verification (Dev)

```bash
# Restart server to apply changes
restart_server.bat

# Test the fix with Playwright
# Take screenshots showing it works
# Monitor server logs
```

**Playwright Test:**
```python
# Navigate to affected page
mcp__playwright__browser_navigate(url="http://localhost:5173")

# Reproduce the scenario that caused the bug
# Verify the bug is fixed

# Take screenshot
mcp__playwright__browser_take_screenshot(filename="bug-X-dev-fixed.png")

# Check console for errors
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)

# Verify no errors
# Close browser
mcp__playwright__browser_close()
```

**Checklist:**
- [ ] Server starts without errors
- [ ] Bug scenario no longer triggers issue
- [ ] UI displays correctly
- [ ] No console errors
- [ ] Server logs clean
- [ ] Screenshots captured

#### Step 4: Regression Testing (Dev)

```bash
# Run full test suite
pytest tests/ -v --cov=gao_dev

# Run integration tests
pytest tests/integration/ -v

# Test related features
# Use Playwright to test workflows that might be affected
```

**Checklist:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Coverage maintained/improved
- [ ] Related features work
- [ ] No new bugs introduced

#### Step 5: Create Regression Test

**Create test file:**
```python
# tests/regression/test_bug_ISSUE_NUMBER.py

def test_bug_ISSUE_NUMBER_regression():
    """
    Regression test for bug #ISSUE_NUMBER

    Bug: [Brief description]

    Reproduction:
    1. [Step 1]
    2. [Step 2]
    3. [Expected behavior]

    Fixed in: [Commit hash]
    """
    # Test setup

    # Test execution

    # Assertions
    assert expected_behavior, "Bug #ISSUE_NUMBER regression detected"
```

**Checklist:**
- [ ] Regression test created
- [ ] Test reproduces original bug scenario
- [ ] Test fails on old code
- [ ] Test passes on new code
- [ ] Test documented

#### Step 6: Commit Changes

```bash
# Add changes
git add .

# Commit with clear message
git commit -m "$(cat <<'EOF'
fix(component): Fix bug #ISSUE - Brief description

Detailed description of the bug and fix.

Changes:
- [Change 1]
- [Change 2]

Tests:
- Added test_bug_ISSUE_regression()

Verified in:
- Dev environment: ✅
- Beta environment: Pending

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to GitHub
git push origin main
```

**Checklist:**
- [ ] Clear commit message
- [ ] All changes committed
- [ ] Tests included
- [ ] Pushed to main

### Phase 2: Beta Environment Verification (C:/Testing)

**Location**: `C:\Testing`
**Environment**: Standard pip install from GitHub

#### Step 7: Install Beta Version

```bash
# Open NEW command prompt (not dev environment)
# Navigate to Testing directory
cd C:\Testing

# Activate beta venv
call scripts\activate-beta.bat

# Verify environment
call scripts\verify-environment.bat

# Should show:
# Environment: BETA TESTING
# Location: C:\Testing\venv-beta

# Upgrade to latest from GitHub
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Verify installation
gao-dev --version
pip show gao-dev
# Should show: Location: C:\Testing\venv-beta\Lib\site-packages
# Should NOT show: Editable project location
```

**Checklist:**
- [ ] Beta environment activated
- [ ] Not in dev environment
- [ ] Latest version installed
- [ ] Installation location correct (venv-beta\Lib\site-packages)
- [ ] Not editable install

#### Step 8: Test in Beta Environment

```bash
# Navigate to test project
cd C:\Testing\test-projects\test-app

# Start GAO-Dev
gao-dev start

# OR start web interface specifically
# (if project already initialized)
```

**Playwright Test (Beta):**
```python
# Same tests as dev, but in beta environment
# Navigate to page
mcp__playwright__browser_navigate(url="http://localhost:5173")

# Reproduce scenario
# Verify fix works

# Take screenshot
mcp__playwright__browser_take_screenshot(filename="bug-X-beta-verified.png")

# Check console
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)

# Close browser
mcp__playwright__browser_close()
```

**Checklist:**
- [ ] Server starts without errors
- [ ] Fix verified in beta environment
- [ ] Same tests pass as in dev
- [ ] No environment-specific issues
- [ ] Screenshots match dev behavior

#### Step 9: Test Onboarding (If Applicable)

```bash
# Create fresh test project
cd C:\Testing\test-projects
mkdir fresh-test-$(date +%Y%m%d)
cd fresh-test-*

# Start fresh onboarding
gao-dev start

# Test onboarding wizard
# Verify no issues with new projects
```

**Playwright Test (Onboarding):**
```python
# Navigate to onboarding
mcp__playwright__browser_navigate(url="http://localhost:5173")

# Complete onboarding steps
# Verify no errors

# Take screenshots of each step
mcp__playwright__browser_take_screenshot(filename="onboarding-beta-step1.png")
# ... etc

# Verify completion
mcp__playwright__browser_wait_for(text="Setup Complete")
mcp__playwright__browser_take_screenshot(filename="onboarding-beta-complete.png")
```

**Checklist:**
- [ ] Onboarding wizard loads
- [ ] All steps complete successfully
- [ ] No console errors
- [ ] Project initializes correctly
- [ ] Can proceed to main interface

#### Step 10: Test Common Workflows

**Test these key workflows in beta:**

1. **Chat with Brian**
   ```python
   # Send message
   mcp__playwright__browser_type(
       element="Message input",
       ref="textarea[placeholder*='message']",
       text="Hello Brian",
       submit=True
   )
   # Verify response
   mcp__playwright__browser_wait_for(text="Hello")
   ```

2. **File Browser**
   ```python
   # Navigate to files
   # Expand folders
   # Open files
   # Verify Monaco editor loads
   ```

3. **Layout Presets**
   ```python
   # Test each preset
   # Verify resize behavior
   # Check no layout bugs
   ```

4. **Git Timeline**
   ```python
   # View commits
   # Open diffs
   # Verify visualization
   ```

**Checklist:**
- [ ] Chat works
- [ ] File browser works
- [ ] Editor loads files
- [ ] Layout presets work
- [ ] Git timeline works
- [ ] No regressions in core features

### Phase 3: Verification Report

#### Step 11: Create Verification Report

**Report Template:**

```markdown
# Bug Fix Verification Report

**Bug ID**: #ISSUE_NUMBER
**Title**: [Bug title]
**Fixed in**: [Commit hash]
**Tested by**: Bug Tester Agent
**Date**: [YYYY-MM-DD]

## Bug Description

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior (Before Fix):**
[What was happening]

**Impact:**
- Severity: [Critical/High/Medium/Low]
- Affected Users: [Who experiences this]
- Affected Features: [What features are impacted]

## Fix Description

**Changes Made:**
- [Change 1]
- [Change 2]

**Files Modified:**
- `path/to/file1.py`
- `path/to/file2.tsx`

**Root Cause:**
[What caused the bug]

**Solution:**
[How the fix addresses the root cause]

## Verification Results

### Development Environment (CWD)

**Location**: `C:\Projects\gao-agile-dev`
**Install Type**: Editable (pip install -e .)

**Test Results:**
- ✅ Unit Tests: All passing (X/Y tests)
- ✅ Integration Tests: All passing
- ✅ Type Checking: No errors
- ✅ Playwright UI Test: Fix verified
- ✅ Server Logs: Clean (no errors)
- ✅ Console Errors: None
- ✅ Regression Test: Added and passing

**Regression Test:**
- File: `tests/regression/test_bug_ISSUE.py`
- Test: `test_bug_ISSUE_regression()`
- Status: ✅ Passing

**Screenshots:**
- Before fix: `bug-ISSUE-dev-before.png`
- After fix: `bug-ISSUE-dev-after.png`

**Server Logs:**
```
[No errors or warnings related to the bug]
```

**Console Output:**
```
[No errors in browser console]
```

### Beta Environment (C:/Testing)

**Location**: `C:\Testing\test-projects\test-app`
**Install Type**: Standard pip install from GitHub
**Version**: [Version installed]

**Test Results:**
- ✅ Installation: Successful
- ✅ Server Start: No errors
- ✅ Playwright UI Test: Fix verified
- ✅ Server Logs: Clean
- ✅ Console Errors: None
- ✅ Onboarding: Not affected (OR: Tested and working)
- ✅ Core Workflows: All working

**Workflows Tested:**
- Chat with Brian: ✅
- File Browser: ✅
- Layout Presets: ✅
- Git Timeline: ✅
- [Other relevant features]: ✅

**Screenshots:**
- Beta verified: `bug-ISSUE-beta-verified.png`
- Onboarding (if applicable): `bug-ISSUE-beta-onboarding.png`

**Installation Output:**
```
Successfully installed gao-dev-X.Y.Z
Location: C:\Testing\venv-beta\Lib\site-packages\gao_dev
```

**Server Logs:**
```
[No errors or warnings]
```

## Regression Testing

**New Tests Added:**
- `tests/regression/test_bug_ISSUE.py::test_bug_ISSUE_regression`
- [Additional tests if applicable]

**Test Coverage:**
- Module: `gao_dev.path.to.module`
- Coverage Before: X%
- Coverage After: Y%
- Change: +Z%

**Related Tests Updated:**
- [List any existing tests that were updated]

## Related Features Tested

**Potentially Affected Features:**
1. [Feature 1]: ✅ No regression
2. [Feature 2]: ✅ No regression
3. [Feature 3]: ✅ No regression

**Test Scenarios:**
- [Scenario 1]: ✅ Passing
- [Scenario 2]: ✅ Passing

## Performance Impact

**Metrics (if applicable):**
- Load time: [Before → After]
- Memory usage: [Before → After]
- API response time: [Before → After]

**Observations:**
[Any performance improvements or considerations]

## Known Limitations

**Remaining Issues:**
[None OR list any known limitations]

**Future Enhancements:**
[Suggestions for future improvements]

## Sign-Off

**Verification Checklist:**
- [x] Bug reproduced in dev environment
- [x] Fix implemented and tested locally
- [x] Unit tests passing
- [x] Integration tests passing
- [x] Regression test created
- [x] Code committed and pushed
- [x] Beta environment installed latest version
- [x] Fix verified in beta environment
- [x] Onboarding tested (if applicable)
- [x] Core workflows tested
- [x] No regressions detected
- [x] Verification report completed
- [x] Screenshots captured
- [x] Ready for release

**Confidence Level**: High ✅

**Release Recommendation**: Ready for beta release

**Additional Notes:**
[Any additional context, observations, or recommendations]

---

**Verified by**: Bug Tester Agent
**Date**: [YYYY-MM-DD HH:MM]
**Environments**: Development (CWD) + Beta (C:/Testing)
```

**Checklist:**
- [ ] Report created
- [ ] All sections completed
- [ ] Screenshots referenced
- [ ] Test results documented
- [ ] Sign-off checklist complete

### Phase 4: Documentation and Communication

#### Step 12: Update Issue/Bug Tracker

```markdown
# Comment on GitHub Issue

## ✅ Bug Verified Fixed

**Status**: Fixed and verified in both environments
**Fixed in**: [Commit hash]
**Verification Report**: [Link to report or attach]

**Summary:**
- ✅ Dev environment: All tests passing
- ✅ Beta environment: Fix verified
- ✅ Regression test added
- ✅ No regressions detected

**Ready for release**: Yes

See full verification report for details.
```

**Checklist:**
- [ ] GitHub issue updated
- [ ] Status changed to "Verified"
- [ ] Verification report attached
- [ ] Ready for release indicated

#### Step 13: Clean Up

```bash
# Development environment
# Close any test browsers
# Stop servers if not needed

# Beta environment
# Deactivate venv
deactivate

# Return to dev environment if continuing work
cd C:\Projects\gao-agile-dev
```

**Checklist:**
- [ ] Browsers closed
- [ ] Servers stopped (if not needed)
- [ ] Environments cleaned up
- [ ] Ready for next task

## Quick Reference Checklist

### Full Verification Checklist

**Development (CWD):**
- [ ] Bug reproduced with screenshots
- [ ] Fix applied
- [ ] Unit tests pass
- [ ] Type checking clean
- [ ] Playwright verification successful
- [ ] Server logs clean
- [ ] Console errors: none
- [ ] Regression test created and passing
- [ ] Code committed and pushed

**Beta (C:/Testing):**
- [ ] Beta venv activated
- [ ] Latest version installed
- [ ] Installation verified (not editable)
- [ ] Server starts successfully
- [ ] Playwright verification successful
- [ ] Server logs clean
- [ ] Console errors: none
- [ ] Onboarding tested (if applicable)
- [ ] Core workflows tested
- [ ] No regressions detected

**Documentation:**
- [ ] Verification report created
- [ ] Screenshots captured and referenced
- [ ] GitHub issue updated
- [ ] Ready for release

## Common Issues and Solutions

### Issue: Beta install shows editable mode

**Problem:** `pip show gao-dev` shows "Editable project location"

**Solution:**
```bash
# Ensure you're in beta venv
call C:\Testing\scripts\verify-environment.bat

# Should show BETA TESTING
# If not, activate beta venv
call C:\Testing\scripts\activate-beta.bat

# Uninstall editable
pip uninstall gao-dev

# Install from GitHub
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

### Issue: Changes not visible in beta

**Problem:** Fix works in dev but not in beta

**Possible causes:**
1. Code not pushed to GitHub
2. Beta install didn't upgrade
3. Cache issues

**Solution:**
```bash
# Verify code is pushed
git log origin/main --oneline -1

# Force reinstall in beta
pip install --upgrade --force-reinstall --no-cache-dir git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Clear browser cache
# Restart server
```

### Issue: Playwright can't find element

**Problem:** Element selector not working

**Solution:**
```python
# Get fresh snapshot
snapshot = mcp__playwright__browser_snapshot()

# Use correct ref from snapshot
# Ensure page is loaded
mcp__playwright__browser_wait_for(text="Expected text")

# Then interact
mcp__playwright__browser_click(element="...", ref="...")
```

### Issue: Server logs show errors after fix

**Problem:** New errors appear in logs

**Solution:**
- Review error messages
- Check if errors are related to fix
- Test in isolation
- May need to revise fix
- Update tests

## Success Criteria

Bug verification is successful when:
- Bug is fixed in both dev and beta environments
- All tests pass (unit, integration, regression)
- No console errors in browser
- Server logs are clean
- No regressions in related features
- Onboarding works (if applicable)
- Verification report is complete
- Code is committed and pushed
- Issue tracker is updated

## Anti-Patterns to Avoid

- **Testing only in dev**: Beta environment may reveal environment-specific issues
- **Skipping regression tests**: Bug will likely reappear
- **Not checking logs**: Hidden errors may exist
- **Incomplete verification**: Test related features too
- **No documentation**: Future developers need context
- **Mixing environments**: Keep dev and beta completely separate

---

**Remember**: Complete verification means testing in BOTH environments with systematic Playwright tests, clean logs, passing test suite, and comprehensive documentation. Never skip the beta environment verification—it's where environment-specific issues appear.
