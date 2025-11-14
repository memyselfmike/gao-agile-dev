# GAO-Dev Beta Testing Checklist

**Version:** Test Fixes Release (Commits a73088f + 3b2090d)
**Date:** 2025-01-14
**Estimated Time:** 15-20 minutes

## Pre-Testing Setup

### 1. Pull Latest Changes
```bash
cd gao-agile-dev
git pull origin main
git log --oneline -3
# Should see:
# 3b2090d docs: Add release notes for test suite improvements
# a73088f fix(tests): Fix 68+ test failures for orchestrator refactoring
```

### 2. Install/Update Dependencies
```bash
pip install -e .
```

### 3. Verify Installation
```bash
gao-dev --version
# Should return version without errors
```

---

## Core Functionality Tests

### ✅ Test 1: Orchestrator Initialization (1 min)
**What:** Verify the orchestrator can initialize properly

**Test:**
```bash
python -m pytest tests/integration/test_workflow_driven_core.py::test_orchestrator_initialization -v
```

**Expected Result:** ✅ PASSED
**If Failed:** Report error message

---

### ✅ Test 2: Workflow Registry Access (1 min)
**What:** Verify workflow registry loads correctly

**Test:**
```bash
python -m pytest tests/integration/test_workflow_driven_core.py::test_workflow_registry_loaded -v
```

**Expected Result:** ✅ PASSED
**If Failed:** Report error message

---

### ✅ Test 3: ChatREPL Exit Commands (1 min)
**What:** Verify ChatREPL command detection works

**Test:**
```bash
python -m pytest tests/cli/test_chat_repl.py::test_is_exit_command -v
```

**Expected Result:** ✅ PASSED
**If Failed:** Report error message

---

### ✅ Test 4: Feature Creation Command (2 min)
**What:** Verify feature creation works end-to-end

**Test:**
```bash
# Create a test directory
mkdir -p /tmp/test-gao-project
cd /tmp/test-gao-project
git init
gao-dev init --greenfield

# Try creating a feature (should fail gracefully if not in project)
gao-dev create-feature test-feature --scale-level 2
```

**Expected Result:** Command runs without crashes
**If Failed:** Report error message and behavior

---

### ✅ Test 5: Full Test Suite for Fixed Files (5 min)
**What:** Run all the fixed test files to verify they pass

**Test:**
```bash
cd gao-agile-dev
python -m pytest tests/integration/test_workflow_driven_core.py -v
```

**Expected Results:**
- ✅ 11/11 tests should pass
- Runtime: ~30-60 seconds

**If Failed:** Note which specific tests failed

---

## Quick Smoke Tests

### ✅ Test 6: CLI Help Command (30 sec)
```bash
gao-dev --help
```
**Expected:** Help text displays without errors

---

### ✅ Test 7: List Workflows (30 sec)
```bash
gao-dev list-workflows
```
**Expected:** Displays list of available workflows without errors

---

### ✅ Test 8: List Agents (30 sec)
```bash
gao-dev list-agents
```
**Expected:** Shows all 8 agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary)

---

### ✅ Test 9: Health Check (30 sec)
```bash
gao-dev health
```
**Expected:** Reports system health status

---

## Known Issues to Verify (Optional)

### ⚠️ Known Issue 1: Test Suite Performance
**What:** Full test suite takes longer than expected

**Test:**
```bash
# Start timer
time python -m pytest tests/cli/test_chat_repl.py -q

# Note the duration
```

**Expected:** May take 1-2 minutes (slower than ideal)
**Action:** Just note the timing, don't report as bug

---

### ⚠️ Known Issue 2: Coverage Below Target
**What:** Test coverage is ~13% (target is 80%)

**Test:**
```bash
python -m pytest --cov=gao_dev tests/integration/test_workflow_driven_core.py --cov-report=term-missing | grep "TOTAL"
```

**Expected:** Low coverage percentage shown
**Action:** Note the percentage, don't report as bug

---

## Regression Tests (Optional - 5 min)

### Test 10: ChatREPL Provider Selection
```bash
python -m pytest tests/cli/test_chat_repl_provider_selection.py -v
```
**Expected:** Tests pass or skip gracefully

---

### Test 11: Git-Integrated Commands
```bash
python -m pytest tests/cli/test_git_integrated_commands.py::TestCLIGitIntegration::test_create_prd_uses_git_state_manager -v
```
**Expected:** ✅ PASSED

---

## What to Report Back

### ✅ Success Checklist
- [ ] All core tests (1-5) passed
- [ ] CLI commands work without crashes
- [ ] No unexpected errors or warnings
- [ ] Installation was smooth

### 🐛 If You Find Issues
Please report:
1. **Test name** that failed
2. **Full error message**
3. **Your environment:**
   - OS: (Windows/Mac/Linux)
   - Python version: `python --version`
   - Commit: `git log --oneline -1`
4. **Steps to reproduce**

### 📊 Performance Notes
Please note:
- How long did Test 5 take? (Expected: ~30-60 seconds)
- Did any commands feel unusually slow?
- Any memory/CPU issues?

---

## Quick Summary Report Template

Copy and fill this out:

```
GAO-Dev Beta Test Results
Date: [DATE]
Tester: [YOUR NAME]
Commit: [git log --oneline -1]

✅ PASSING:
- Test 1 (Orchestrator Init): PASS / FAIL
- Test 2 (Workflow Registry): PASS / FAIL
- Test 3 (ChatREPL): PASS / FAIL
- Test 4 (Feature Creation): PASS / FAIL
- Test 5 (Full Suite): X/11 tests passed

⚠️ ISSUES FOUND:
- [List any failures or unexpected behavior]

💡 NOTES:
- Test 5 duration: [X] seconds
- Overall impression: [Your feedback]
```

---

## Expected Results Summary

**What should work:**
- ✅ Core orchestrator tests (11/11 passing)
- ✅ CLI commands run without crashes
- ✅ Feature creation/listing
- ✅ Git-integrated workflows
- ✅ Help and status commands

**Known limitations:**
- ⚠️ Test suite slower than expected (~15-30% slower)
- ⚠️ Test coverage at 13% (below 80% target)
- ⚠️ Some integration tests may be slow

**Blockers (report immediately):**
- ❌ Core tests failing
- ❌ CLI commands crashing
- ❌ Installation errors
- ❌ Import errors

---

## Contact

**Questions?** Check `RELEASE_NOTES_TEST_FIXES.md` for detailed information.

**Done testing?** Send results to project maintainer.

**Thanks for beta testing!** 🎉
