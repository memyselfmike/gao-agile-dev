# Test UI with Playwright

Run systematic UI tests using Playwright for GAO-Dev web interface.

## Instructions

This command helps you test UI changes, verify layouts, and capture screenshots using Playwright.

**What to test:**
- Specific component or page
- Layout presets
- Responsive behavior
- User workflows
- Visual regression

The UI testing will:
1. Start Playwright browser
2. Navigate to specified page
3. Perform test actions
4. Capture screenshots
5. Check for console errors
6. Verify network requests
7. Test responsive layouts (if requested)

## Example Usage

### Test a Specific Component

```
/test-ui

Component: Onboarding Wizard
Tests:
- Navigate through all steps
- Verify form validation
- Check completion state
- Capture screenshots of each step
```

### Test Layout Presets

```
/test-ui

Feature: Layout presets
Tests:
- Test Default preset
- Test Code-Focused preset
- Test Chat-Focused preset
- Verify resize behavior
- Capture screenshots of each
```

### Test Responsive Design

```
/test-ui

Page: Dashboard
Tests:
- Test mobile (375x812)
- Test tablet (768x1024)
- Test desktop (1920x1080)
- Verify all elements visible
- Check no overflow issues
```

### Visual Regression Test

```
/test-ui

Purpose: Visual regression test for chat interface
Tests:
- Capture baseline screenshot
- Make changes (or test existing)
- Capture after screenshot
- Compare for regressions
```

## Test Patterns Available

### 1. Navigation and Screenshot
- Navigate to page
- Wait for load
- Capture state

### 2. Element Interaction
- Click buttons
- Fill forms
- Select dropdowns
- Type text

### 3. Layout Testing
- Resize browser
- Test multiple sizes
- Verify responsive behavior

### 4. Error Detection
- Check console errors
- Verify network requests
- Monitor WebSocket

### 5. Multi-Step Workflow
- Complete user journey
- Capture each step
- Verify end-to-end flow

### 6. Visual Regression
- Before/after comparison
- Detect unwanted changes
- Verify expected changes

## What You'll Get

**Output includes:**
- Screenshots at each test step
- Console error report (if any)
- Network request analysis (if requested)
- Test result summary
- Recommendations for issues found

**Screenshot naming:**
- Descriptive, hierarchical names
- Stored in `.playwright-mcp/`
- Easy to review and compare

## Prerequisites

Before running:
- [ ] Web server running (http://localhost:3000)
- [ ] Frontend running (http://localhost:5173)
- [ ] Know what component/page to test
- [ ] Have test scenario in mind

**Start servers:**
```bash
# Start both backend and frontend
start_web.bat

# OR start separately
# Backend: restart_server.bat
# Frontend: cd gao_dev/web/frontend && npm run dev
```

## Common Test Scenarios

### Test Onboarding
```
Navigate through wizard
Fill in all fields
Verify completion
Check no errors
```

### Test Chat
```
Send message
Wait for response
Verify display
Check no console errors
```

### Test File Browser
```
Expand folders
Open file
Verify Monaco editor loads
Check syntax highlighting
```

### Test Layout Resize
```
Start with default size
Resize to various dimensions
Verify no layout breaks
Check element visibility
```

## Tips

**Good test:**
- Clear objective
- Specific actions
- Expected outcomes
- Evidence captured (screenshots)

**Effective screenshots:**
- Descriptive file names
- Before/after states
- Key interaction points
- Error states (if applicable)

**Best practices:**
- Wait for page load before actions
- Check console after interactions
- Test edge cases
- Document what you're testing

## Related Commands

- `/verify-bug-fix` - Complete bug verification workflow
- `/sandbox-status` - Check if test environment is ready

## Notes

- Screenshots saved to `.playwright-mcp/`
- Browser auto-closes after tests
- Console errors highlighted in results
- Can run same tests in beta environment (C:/Testing)
