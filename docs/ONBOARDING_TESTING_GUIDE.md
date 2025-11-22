# Onboarding System - Testing Guide

**Phase**: Phase 2 - End-to-End Testing
**Prerequisites**: Phase 1 fixes applied (commit c20b3c6)

---

## Quick Start - Development Testing

### 1. Start the Web Server

```bash
cd C:\Projects\gao-agile-dev
gao-dev start
```

Or:
```bash
python -m gao_dev.cli.main start
```

**Expected**:
- Server starts on http://localhost:5173
- Browser opens automatically
- Onboarding wizard appears

### 2. Test Onboarding Flow

**Step 1: Project Configuration**
- Check: Project name is pre-filled with "gao-agile-dev" (or current directory name)
- Check: Project path shows current directory
- Action: Enter description (optional)
- Action: Click "Continue"

**Step 2: Git Setup**
- Check: Git name/email pre-filled if configured globally
- Action: Enter git name and email if not pre-filled
- Action: Click "Continue"

**Step 3: Provider Selection** (CRITICAL - This was the sticking point)
- Check: Should show 2 provider cards:
  1. Claude Code (sparkles icon)
  2. OpenCode SDK (globe icon)
- Check: Each card shows:
  - Provider name and description
  - Icon
  - "API key required" message
  - API key environment variable name
  - Whether key is currently set
- Action: Select a provider
- Action: Click "Continue"

**Step 4: Credentials**
- Check: Shows selected provider's API key requirements
- Check: Can enter API key or use environment variable
- Action: Enter API key OR set environment variable
- Action: Validate (optional)
- Action: Click "Continue"

**Step 5: Completion**
- Check: Shows summary of configuration
- Check: All steps marked complete
- Action: Click "Start Building"
- Expected: Wizard closes, main interface appears

### 3. Check Browser Console

Open DevTools (F12) → Console tab

**Expected**:
- No JavaScript errors
- No 404 errors for API endpoints
- No schema validation errors
- Provider data loads successfully

**Watch for**:
- `available_providers` is an array of objects
- Each provider has all 8 fields
- No "undefined" errors

### 4. Check Server Logs

Look at the terminal where `gao-dev start` is running.

**Expected logs**:
```
onboarding_status_retrieved
  needs_onboarding=True
  current_step=project
  provider_count=2

provider_config_saved
  provider=claude-code
  model=...

onboarding_complete
  project=...
  path=...
```

**Watch for**:
- No errors or exceptions
- Each step saves successfully
- Provider data loads without warnings

---

## Test Scenarios

### A. Happy Path - First-Time User

1. Clean state (no .gao-dev directory)
2. Start server
3. Complete all wizard steps
4. Verify project initialized correctly

### B. Resume Functionality

1. Complete steps 1-2
2. Refresh browser (F5)
3. Wizard should resume at step 3
4. Complete remaining steps

### C. Error Handling

**Test Invalid Inputs:**

1. **Project Step**:
   - Empty project name → Should show error
   - Invalid characters → Should show error
   - Invalid path → Should show error

2. **Git Step**:
   - Invalid email format → Should show error
   - Empty name → Should show error

3. **Provider Step**:
   - No provider selected → Should show error
   - Click Continue without selection

4. **Credentials Step**:
   - Empty API key → Should show error
   - Invalid key format → Should show error
   - Validation fails → Should show clear message

**Expected**:
- Clear, actionable error messages
- Form doesn't submit if invalid
- User can fix errors and continue

### D. Navigation Testing

1. Complete step 1
2. Click "Back" → Should go to previous step
3. Click "Continue" → Should go to next step
4. Click "Back" multiple times → Should navigate correctly
5. Progress indicator should update

### E. Provider Selection Specific Tests

**Test 1: Provider List Loads**
```
Expected providers: 2 (claude-code, opencode-sdk)
Each provider should have:
  - id: string
  - name: string
  - description: string
  - icon: string ('sparkles' or 'globe')
  - requires_api_key: boolean (true)
  - api_key_env_var: string
  - has_api_key: boolean (false if key not set)
  - models: array (not used in onboarding)
```

**Test 2: Provider Selection**
```
1. Click on Claude Code card
2. Card should highlight/become selected
3. Click on OpenCode SDK card
4. Previous selection should deselect
5. Current card should highlight
6. Can proceed to credentials step
```

**Test 3: API Key Detection**
```
Scenario A: No API key set
  - has_api_key = false
  - Should show "API key required" message
  - Should prompt for key in credentials step

Scenario B: API key set
  - Set ANTHROPIC_API_KEY environment variable
  - Restart server
  - has_api_key = true
  - Should show "API key detected" or similar
  - Can skip key entry (use environment variable)
```

---

## Verification Checklist

### Development Environment

- [ ] Server starts without errors
- [ ] Browser opens automatically
- [ ] Onboarding wizard appears
- [ ] **Provider selection step shows 2 providers**
- [ ] **Each provider has icon, name, description**
- [ ] **Provider selection works (can click and select)**
- [ ] All wizard steps complete successfully
- [ ] No console errors
- [ ] No server errors in logs
- [ ] State persists across browser refresh
- [ ] Can navigate back and forward
- [ ] Error messages are clear
- [ ] Completion summary is correct
- [ ] Main interface launches after completion

### Beta Environment (After Dev Testing Passes)

- [ ] Install latest from main branch
- [ ] Beta environment isolated from dev
- [ ] Onboarding wizard works same as dev
- [ ] Provider selection works
- [ ] No regressions in existing features
- [ ] Settings panel still works
- [ ] Provider switching still works

---

## Known Issues (Pre-Existing)

These issues existed before our fixes and are NOT related to provider selection:

1. **Git Configuration Methods** (mypy warnings)
   - `GitManager.set_config()` and `add_files()` method signature issues
   - Not blocking - git functionality works

2. **Bootstrap Mode**
   - `bootstrap_mode` field in response but not used by frontend
   - No functional impact

---

## Troubleshooting

### Problem: Provider list is empty

**Check**:
1. Browser console for errors
2. Server logs for provider loading errors
3. Network tab - did `/api/onboarding/status` request succeed?

**Expected response**:
```json
{
  "needs_onboarding": true,
  "available_providers": [
    {
      "id": "claude-code",
      "name": "Claude Code",
      ...
    }
  ]
}
```

**Fix**:
- Ensure ProviderFactory is working
- Check that `get_available_providers()` is called
- Verify no import errors in provider_utils.py

### Problem: Console error about undefined provider

**Symptoms**:
- "Cannot read property 'id' of undefined"
- Provider cards don't render

**Check**:
- Response schema from `/api/onboarding/status`
- `available_providers` field exists and is an array
- Each provider object has all 8 required fields

**Fix**:
- Verify backend changes were applied
- Check that server was restarted after code changes
- Clear browser cache and reload

### Problem: API key detection not working

**Symptoms**:
- `has_api_key` always shows false even when key is set

**Check**:
- Environment variable is actually set in server process
- Variable name matches (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.)
- Server was restarted after setting environment variable

**Fix**:
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-key-here"
gao-dev start

# Windows (CMD)
set ANTHROPIC_API_KEY=your-key-here
gao-dev start

# Unix/Linux/Mac
export ANTHROPIC_API_KEY="your-key-here"
gao-dev start
```

### Problem: Wizard doesn't appear

**Symptoms**:
- Main interface loads instead of wizard
- No onboarding flow

**Check**:
- `.gao-dev/onboarding_state.yaml` might indicate onboarding is complete
- Check `needs_onboarding` in status response

**Fix**:
```bash
# Delete onboarding state to restart
rm .gao-dev/onboarding_state.yaml

# Restart server
gao-dev start
```

---

## Success Criteria

**Onboarding is considered working when**:

1. ✅ Wizard loads without errors
2. ✅ Provider selection step shows providers
3. ✅ Can select a provider
4. ✅ Can complete all steps
5. ✅ State persists across refresh
6. ✅ Error messages are clear
7. ✅ No console errors
8. ✅ No server errors
9. ✅ Works in both dev and beta environments
10. ✅ No regressions in existing functionality

---

## Next Steps After Testing

### If Tests Pass ✅

1. Mark Phase 2 complete
2. Create Playwright UI tests for regression prevention
3. Update onboarding documentation
4. Deploy to beta testers for UI/UX refinement
5. Collect feedback

### If Tests Fail ❌

1. Document specific failure
2. Capture screenshots and logs
3. Add to bug tracking document
4. Prioritize and fix
5. Re-test

---

## Contact

**Bug Reports**: Document in `ONBOARDING_BUG_TRACKING.md`

**Questions**: Check:
- This guide first
- Bug tracking document
- Fixes summary document

---

**Last Updated**: 2025-11-22
**Phase**: Phase 2 - End-to-End Testing
**Status**: Ready for testing

