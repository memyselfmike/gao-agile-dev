---
name: ui-testing
description: Systematic UI testing using Playwright for GAO-Dev web interface. Provides patterns for testing layouts, interactions, and visual regressions. Use when testing web interface changes or verifying UI bug fixes.
allowed-tools: Read, Grep, Glob, Bash, mcp__playwright__*
---

# UI Testing Skill - Playwright-Based Testing

This skill provides systematic patterns for testing the GAO-Dev web interface using Playwright.

## When to Use

Use this skill when:
- Testing UI bug fixes
- Verifying layout changes
- Testing responsive behavior
- Capturing screenshots for documentation
- Performing visual regression testing
- Testing user interactions and workflows

## Core Testing Patterns

### 1. Basic Navigation and Screenshot

**Pattern**: Navigate to a page and capture its state

```python
# Start browser and navigate
mcp__playwright__browser_navigate(url="http://localhost:5173")

# Wait for content to load
mcp__playwright__browser_wait_for(text="GAO-Dev")

# Take screenshot
mcp__playwright__browser_take_screenshot(
    filename="page-initial-state.png",
    type="png"
)
```

**When to use**: Initial state capture, documentation, baseline comparisons

### 2. Element Interaction

**Pattern**: Find and interact with UI elements

```python
# Get page snapshot to identify elements
snapshot = mcp__playwright__browser_snapshot()

# Click a button
mcp__playwright__browser_click(
    element="Submit button",
    ref="button[data-testid='submit']"
)

# Fill a form field
mcp__playwright__browser_type(
    element="Email input",
    ref="input[name='email']",
    text="test@example.com",
    submit=False
)

# Select dropdown option
mcp__playwright__browser_select_option(
    element="Provider dropdown",
    ref="select[data-testid='provider-select']",
    values=["anthropic"]
)
```

**When to use**: Testing user interactions, form submissions, UI workflows

### 3. Layout Testing

**Pattern**: Test responsive layouts and resizing behavior

```python
# Test default layout
mcp__playwright__browser_take_screenshot(filename="layout-default.png")

# Resize to mobile
mcp__playwright__browser_resize(width=375, height=812)
mcp__playwright__browser_wait_for(time=1)  # Allow layout to settle
mcp__playwright__browser_take_screenshot(filename="layout-mobile.png")

# Resize to tablet
mcp__playwright__browser_resize(width=768, height=1024)
mcp__playwright__browser_wait_for(time=1)
mcp__playwright__browser_take_screenshot(filename="layout-tablet.png")

# Resize to desktop
mcp__playwright__browser_resize(width=1920, height=1080)
mcp__playwright__browser_wait_for(time=1)
mcp__playwright__browser_take_screenshot(filename="layout-desktop.png")
```

**When to use**: Testing responsive design, verifying layout presets, checking resize behavior

### 4. Console Error Detection

**Pattern**: Check for JavaScript errors in browser console

```python
# Perform actions that might cause errors
mcp__playwright__browser_click(element="Button", ref="button#test")

# Check console for errors
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)

# If errors found, they'll be in the response
# Use this to verify no errors occurred
```

**When to use**: After any UI interaction, after page navigation, after state changes

### 5. Network Request Verification

**Pattern**: Verify API calls and responses

```python
# Perform action that triggers API call
mcp__playwright__browser_click(element="Save button", ref="button[type='submit']")

# Wait for response
mcp__playwright__browser_wait_for(text="Saved successfully")

# Get network requests
requests = mcp__playwright__browser_network_requests()

# Check for specific request/response
# Requests are returned in the response for analysis
```

**When to use**: Testing form submissions, API integrations, data loading

### 6. Multi-Step Workflow Testing

**Pattern**: Test complex user journeys

```python
# Step 1: Navigate to page
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Welcome")
mcp__playwright__browser_take_screenshot(filename="workflow-step1-landing.png")

# Step 2: Fill form
mcp__playwright__browser_fill_form(fields=[
    {"name": "Project Name", "type": "textbox", "ref": "input[name='projectName']", "value": "Test Project"},
    {"name": "Description", "type": "textbox", "ref": "textarea[name='description']", "value": "Test Description"}
])
mcp__playwright__browser_take_screenshot(filename="workflow-step2-form-filled.png")

# Step 3: Submit
mcp__playwright__browser_click(element="Submit", ref="button[type='submit']")
mcp__playwright__browser_wait_for(text="Project created")
mcp__playwright__browser_take_screenshot(filename="workflow-step3-success.png")

# Step 4: Verify result
snapshot = mcp__playwright__browser_snapshot()
# Analyze snapshot for expected content
```

**When to use**: Testing end-to-end user workflows, onboarding flows, multi-step forms

### 7. Visual Regression Testing

**Pattern**: Compare visual states before and after changes

```python
# Capture baseline (before changes)
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Dashboard")
mcp__playwright__browser_take_screenshot(filename="baseline-dashboard.png")

# Make changes (e.g., via UI or code)
# ... apply changes ...

# Restart browser to clear cache
mcp__playwright__browser_close()
mcp__playwright__browser_navigate(url="http://localhost:5173")

# Capture after changes
mcp__playwright__browser_wait_for(text="Dashboard")
mcp__playwright__browser_take_screenshot(filename="after-dashboard.png")

# Compare screenshots manually or with image diff tools
```

**When to use**: Verifying CSS changes, testing theme changes, ensuring no visual regressions

## GAO-Dev Specific Test Scenarios

### Testing Onboarding Wizard

```python
# Navigate to onboarding
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Welcome to GAO-Dev")

# Step 1: Project Details
mcp__playwright__browser_take_screenshot(filename="onboarding-step1.png")
mcp__playwright__browser_fill_form(fields=[
    {"name": "Project Name", "type": "textbox", "ref": "input[name='projectName']", "value": "My App"},
    {"name": "Description", "type": "textbox", "ref": "textarea[name='description']", "value": "Test app"}
])
mcp__playwright__browser_click(element="Next", ref="button:has-text('Next')")

# Step 2: Provider Selection
mcp__playwright__browser_wait_for(text="Select Provider")
mcp__playwright__browser_take_screenshot(filename="onboarding-step2.png")
mcp__playwright__browser_select_option(
    element="Provider dropdown",
    ref="select[name='provider']",
    values=["anthropic"]
)
mcp__playwright__browser_click(element="Next", ref="button:has-text('Next')")

# Step 3: Complete
mcp__playwright__browser_wait_for(text="Setup Complete")
mcp__playwright__browser_take_screenshot(filename="onboarding-complete.png")

# Verify no console errors
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)
```

### Testing Layout Presets

```python
# Navigate to main interface
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Dashboard")

# Test Default preset
mcp__playwright__browser_take_screenshot(filename="layout-preset-default.png")

# Test Code-Focused preset
mcp__playwright__browser_click(element="Code-Focused button", ref="button:has-text('Code-Focused')")
mcp__playwright__browser_wait_for(time=1)  # Allow transition
mcp__playwright__browser_take_screenshot(filename="layout-preset-code-focused.png")

# Test Chat-Focused preset
mcp__playwright__browser_click(element="Chat-Focused button", ref="button:has-text('Chat-Focused')")
mcp__playwright__browser_wait_for(time=1)
mcp__playwright__browser_take_screenshot(filename="layout-preset-chat-focused.png")

# Verify resize behavior
mcp__playwright__browser_resize(width=1280, height=720)
mcp__playwright__browser_take_screenshot(filename="layout-preset-resized.png")
```

### Testing Chat Interface

```python
# Navigate to chat
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Chat")

# Send a message
mcp__playwright__browser_type(
    element="Message input",
    ref="textarea[placeholder*='message']",
    text="Hello Brian",
    submit=True
)

# Wait for response
mcp__playwright__browser_wait_for(text="Hello", time=5)
mcp__playwright__browser_take_screenshot(filename="chat-with-response.png")

# Verify no errors
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)
```

### Testing File Browser

```python
# Navigate to files
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Files")

# Expand folder
mcp__playwright__browser_click(element="Folder icon", ref="button[aria-label*='folder']")
mcp__playwright__browser_wait_for(time=0.5)
mcp__playwright__browser_take_screenshot(filename="files-expanded.png")

# Click file
mcp__playwright__browser_click(element="File name", ref="div:has-text('README.md')")
mcp__playwright__browser_wait_for(time=0.5)
mcp__playwright__browser_take_screenshot(filename="file-opened.png")
```

## Screenshot Organization

### Naming Conventions

Use descriptive, hierarchical names:

```
# Feature-based
<feature>-<component>-<state>.png
Examples:
- onboarding-step1-initial.png
- onboarding-step2-filled.png
- chat-empty-state.png
- chat-with-messages.png

# Bug-based
bug-<issue>-<environment>-<state>.png
Examples:
- bug-422-dev-before.png
- bug-422-dev-after.png
- bug-422-beta-verified.png

# Layout-based
layout-<preset>-<size>.png
Examples:
- layout-default-desktop.png
- layout-code-focused-mobile.png
- layout-chat-focused-tablet.png
```

### Storage Locations

```
.playwright-mcp/           # Playwright MCP screenshots (auto-created)
C:/Testing/screenshots/    # Beta testing screenshots
docs/screenshots/          # Documentation screenshots
```

## Error Handling

### Common Playwright Errors

**Element not found:**
```python
# Solution: Wait for element before interacting
mcp__playwright__browser_wait_for(text="Expected text")
mcp__playwright__browser_click(element="Button", ref="button#id")
```

**Timeout waiting for element:**
```python
# Solution: Increase wait time or check if element exists
mcp__playwright__browser_wait_for(text="Slow loading text", time=10)
```

**Browser not started:**
```python
# Solution: Navigate first to start browser
mcp__playwright__browser_navigate(url="http://localhost:5173")
```

**Screenshot fails:**
```python
# Solution: Ensure page is loaded
mcp__playwright__browser_wait_for(time=1)  # Allow render
mcp__playwright__browser_take_screenshot(filename="page.png")
```

## Best Practices

### 1. Always Wait for Page Load

```python
# Good
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_wait_for(text="Page loaded indicator")
mcp__playwright__browser_take_screenshot(filename="page.png")

# Bad - might capture blank page
mcp__playwright__browser_navigate(url="http://localhost:5173")
mcp__playwright__browser_take_screenshot(filename="page.png")  # Too soon!
```

### 2. Use Descriptive Element Names

```python
# Good
mcp__playwright__browser_click(
    element="Submit registration form button",
    ref="button[type='submit']"
)

# Bad
mcp__playwright__browser_click(
    element="Button",
    ref="button"
)
```

### 3. Take Screenshots at Key Points

```python
# Capture state before action
mcp__playwright__browser_take_screenshot(filename="before-action.png")

# Perform action
mcp__playwright__browser_click(element="Delete button", ref="button.delete")

# Capture state after action
mcp__playwright__browser_wait_for(text="Deleted successfully")
mcp__playwright__browser_take_screenshot(filename="after-action.png")
```

### 4. Always Check Console Errors

```python
# After any significant action
mcp__playwright__browser_click(element="Submit", ref="button[type='submit']")
console_msgs = mcp__playwright__browser_console_messages(onlyErrors=True)
# Examine console_msgs for any errors
```

### 5. Clean Up

```python
# Always close browser when test is complete
mcp__playwright__browser_close()
```

## Testing Checklist

### Pre-Test
- [ ] Server is running (http://localhost:3000)
- [ ] Frontend is running (http://localhost:5173)
- [ ] Test scenario is clearly defined
- [ ] Expected outcome is documented

### During Test
- [ ] Navigate to correct page
- [ ] Wait for page load
- [ ] Take before screenshot
- [ ] Perform actions
- [ ] Wait for response/state change
- [ ] Take after screenshot
- [ ] Check console for errors
- [ ] Verify network requests if applicable

### Post-Test
- [ ] Review screenshots
- [ ] Check for console errors
- [ ] Verify expected behavior
- [ ] Document results
- [ ] Close browser

## Success Criteria

UI testing is successful when:
- All user interactions work as expected
- No console errors are present
- Screenshots clearly show intended behavior
- Layout is correct across screen sizes
- Visual regressions are detected
- Tests are reproducible

## Anti-Patterns to Avoid

- **No waiting**: Taking screenshots before page loads
- **Vague selectors**: Using generic refs like "button" or "div"
- **Ignoring errors**: Not checking console messages
- **No cleanup**: Leaving browser sessions open
- **Poor naming**: Using generic screenshot names like "test1.png"
- **No baseline**: Not capturing before state for comparison

---

**Remember**: Playwright tests should be systematic, reproducible, and provide clear evidence of UI behavior. Screenshots are your primary tool for documenting and verifying UI correctness.
