# E2E Test Plan: Playwright MCP for Claude Code

**Feature**: Browser-Based Web Interface for GAO-Dev
**Epic Number**: 39
**Test Architect**: Murat
**Version**: 1.0
**Last Updated**: 2025-01-16
**Status**: Ready for Implementation

---

## Executive Summary

This document provides a detailed end-to-end (E2E) test plan specifically designed for **Claude Code to test GAO-Dev via Playwright MCP** (Model Context Protocol). The plan covers 14 E2E scenarios across all 3 phases, with complete Given/When/Then specifications, semantic HTML requirements, and data-testid naming conventions.

### Purpose

Enable Claude Code to act as an **automated beta tester** for the GAO-Dev web interface, finding real UX issues, validating functionality, and providing continuous quality feedback.

### Key Principles

1. **AI-Testable by Design**: Every interactive element has semantic HTML, stable selectors, and ARIA labels
2. **Clear State Indicators**: `data-state` attributes make state visible to AI (loading, error, success)
3. **Semantic Selectors**: Use `data-testid` attributes for stable, human-readable selectors
4. **Screenshot Comparison**: Visual regression testing for layout changes
5. **Comprehensive Scenarios**: Cover all critical user journeys across 3 phases

---

## Table of Contents

1. [Playwright MCP Setup](#playwright-mcp-setup)
2. [Semantic HTML Requirements](#semantic-html-requirements)
3. [data-testid Naming Conventions](#data-testid-naming-conventions)
4. [Phase 1: MVP E2E Scenarios](#phase-1-mvp-e2e-scenarios)
5. [Phase 2: V1.1 E2E Scenarios](#phase-2-v11-e2e-scenarios)
6. [Phase 3: V1.2 E2E Scenarios](#phase-3-v12-e2e-scenarios)
7. [Screenshot Comparison Strategy](#screenshot-comparison-strategy)
8. [Test Execution Guide](#test-execution-guide)
9. [Troubleshooting](#troubleshooting)

---

## Playwright MCP Setup

### Prerequisites

**For Claude Code**:
- Playwright MCP installed and configured
- Access to localhost (GAO-Dev server running)
- Chromium browser installed

**For GAO-Dev**:
- Web server running: `gao-dev start --web --test-mode`
- Test mode enables:
  - Reduced animation duration (faster tests)
  - Deterministic IDs (no UUIDs)
  - Mock AI responses (no real Anthropic API calls)
  - Test data fixtures pre-loaded

### Installation

```bash
# Install Playwright
npm install -D @playwright/test

# Install browsers
npx playwright install chromium

# Verify installation
npx playwright test --list
```

### Configuration

**File**: `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Run sequentially for predictable state
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for state consistency
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['list'], // Console output
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1440, height: 900 }, // Default resolution
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'gao-dev start --web --test-mode',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

### Test Utilities

**File**: `tests/e2e/utils/helpers.ts`

```typescript
import { Page, expect } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /** Wait for element with timeout */
  async waitForTestId(testId: string, timeout = 5000) {
    await this.page.waitForSelector(`[data-testid="${testId}"]`, { timeout });
  }

  /** Click element by test ID */
  async clickTestId(testId: string) {
    await this.page.click(`[data-testid="${testId}"]`);
  }

  /** Fill input by test ID */
  async fillTestId(testId: string, value: string) {
    await this.page.fill(`[data-testid="${testId}"]`, value);
  }

  /** Get text content by test ID */
  async getTextByTestId(testId: string): Promise<string> {
    const element = await this.page.locator(`[data-testid="${testId}"]`);
    return await element.textContent() || '';
  }

  /** Wait for state indicator */
  async waitForState(testId: string, state: string, timeout = 5000) {
    await this.page.waitForSelector(
      `[data-testid="${testId}"][data-state="${state}"]`,
      { timeout }
    );
  }

  /** Take screenshot with name */
  async screenshot(name: string) {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}.png`,
      fullPage: true,
    });
  }

  /** Compare screenshot (visual regression) */
  async compareScreenshot(name: string) {
    await expect(this.page).toHaveScreenshot(`${name}.png`, {
      maxDiffPixels: 100, // Allow small differences
    });
  }
}
```

---

## Semantic HTML Requirements

### Guiding Principles

**All interactive elements MUST use semantic HTML**:

**Good Examples**:
```html
<button data-testid="chat-send-button">Send</button>
<nav data-testid="sidebar">...</nav>
<main data-testid="main-content">...</main>
<input type="text" data-testid="chat-input" aria-label="Type your message" />
<a href="/docs" data-testid="docs-link">Documentation</a>
```

**Bad Examples** (DO NOT USE):
```html
<div onClick={handleClick}>Send</div> <!-- Not semantic -->
<div className="nav">...</div> <!-- Should be <nav> -->
<div className="button">Click me</div> <!-- Should be <button> -->
```

### Required Semantic Elements

| Component | Semantic Tag | Required Attributes |
|-----------|--------------|---------------------|
| **Buttons** | `<button>` | `data-testid`, `aria-label` (if icon-only) |
| **Navigation** | `<nav>` | `data-testid`, `aria-label` |
| **Main Content** | `<main>` | `data-testid` |
| **Links** | `<a>` | `data-testid`, `href` |
| **Inputs** | `<input>` | `data-testid`, `aria-label` or `<label>` |
| **Textareas** | `<textarea>` | `data-testid`, `aria-label` or `<label>` |
| **Sections** | `<section>` | `data-testid`, `aria-labelledby` |
| **Headers** | `<header>` | `data-testid` |
| **Footers** | `<footer>` | `data-testid` |
| **Articles** | `<article>` | `data-testid` |

### State Indicators

**All interactive elements MUST indicate their state**:

**Pattern**: `data-state="{state}"`

**Valid States**:
- `idle` - Default state
- `loading` - Operation in progress
- `success` - Operation succeeded
- `error` - Operation failed
- `disabled` - Element disabled
- `active` - Element active (e.g., selected tab)

**Example**:
```html
<button
  data-testid="chat-send-button"
  data-state={isLoading ? 'loading' : 'idle'}
  disabled={isLoading}
  aria-label="Send message to Brian"
>
  {isLoading ? 'Sending...' : 'Send'}
</button>
```

### ARIA Labels

**All icon-only buttons MUST have aria-label**:

```html
<button
  data-testid="theme-toggle"
  aria-label="Toggle dark/light theme"
>
  <ThemeIcon />
</button>
```

**All form inputs MUST have labels**:

```html
<!-- Option 1: <label> element -->
<label htmlFor="commit-message">Commit Message</label>
<textarea
  id="commit-message"
  data-testid="commit-message-input"
/>

<!-- Option 2: aria-label -->
<textarea
  data-testid="chat-input"
  aria-label="Type your message to Brian"
  placeholder="Ask Brian anything..."
/>
```

---

## data-testid Naming Conventions

### Pattern

**General**: `{component}-{element}-{modifier}`

**Examples**:
- `chat-input` (component: chat, element: input)
- `chat-send-button` (component: chat, element: send button)
- `chat-message-user` (component: chat, element: message, modifier: user)
- `activity-event-card` (component: activity, element: event card)
- `file-tree-item` (component: file tree, element: item)

### Component-Specific Conventions

**Chat Tab**:
- `chat-input` - Chat input textarea
- `chat-send-button` - Send button
- `chat-message-user` - User message
- `chat-message-brian` - Brian's message
- `chat-message-john` - John's message (etc. for other agents)
- `agent-switcher` - Agent selection dropdown
- `agent-option-brian` - Agent option (Brian)
- `reasoning-toggle` - Toggle to show/hide reasoning

**Activity Stream**:
- `activity-stream` - Main activity stream container
- `activity-event` - Event card
- `activity-event-agent` - Agent name in event
- `activity-event-timestamp` - Event timestamp
- `activity-filter-time` - Time window filter
- `activity-filter-type` - Event type filter
- `activity-filter-agent` - Agent filter
- `activity-search-input` - Search input

**Files Tab**:
- `file-tree` - File tree container
- `file-tree-item` - File/folder item (use `data-path` for specific file)
- `file-tree-item[data-path="docs/PRD.md"]` - Specific file selector
- `monaco-editor` - Monaco editor instance
- `file-breadcrumb` - File path breadcrumb
- `file-save-button` - Save button
- `commit-message-input` - Commit message textarea

**Kanban Board**:
- `kanban-board` - Main Kanban container
- `kanban-column-backlog` - Backlog column
- `kanban-column-ready` - Ready column
- `kanban-column-in_progress` - In Progress column
- `kanban-column-in_review` - In Review column
- `kanban-column-done` - Done column
- `epic-card-{num}` - Epic card (e.g., `epic-card-1`)
- `story-card-{epic}.{story}` - Story card (e.g., `story-card-1.1`)
- `transition-confirm-dialog` - Confirmation dialog
- `confirm-transition` - Confirm button

**Layout**:
- `sidebar` - Sidebar navigation
- `main-layout` - Main layout container
- `main-content` - Main content area
- `top-bar` - Top navigation bar
- `tab-chat` - Chat tab
- `tab-activity` - Activity tab
- `tab-files` - Files tab
- `tab-kanban` - Kanban tab
- `tab-git` - Git tab
- `tab-ceremonies` - Ceremonies tab
- `tab-metrics` - Metrics tab
- `theme-toggle` - Theme toggle button
- `settings-button` - Settings button

**Modals/Dialogs**:
- `{feature}-dialog` - Dialog container (e.g., `transition-confirm-dialog`)
- `dialog-title` - Dialog title
- `dialog-content` - Dialog content
- `dialog-confirm` - Confirm button
- `dialog-cancel` - Cancel button

**Toasts**:
- `toast-success` - Success toast
- `toast-error` - Error toast
- `toast-info` - Info toast
- `toast-warning` - Warning toast

### Custom Data Attributes

**For complex selectors, add custom data attributes**:

```html
<!-- File tree item with path -->
<div
  data-testid="file-tree-item"
  data-path="docs/PRD.md"
  data-type="file"
>
  PRD.md
</div>

<!-- Activity event with agent -->
<div
  data-testid="activity-event"
  data-agent="brian"
  data-type="workflow.started"
>
  Brian started workflow: create-prd
</div>

<!-- Story card with epic and story numbers -->
<div
  data-testid="story-card-1.1"
  data-epic="1"
  data-story="1"
  data-status="in_progress"
>
  Story 1.1: Setup Project
</div>
```

---

## Phase 1: MVP E2E Scenarios

### Scenario 1: Server Startup and Accessibility

**ID**: MVP-1
**Priority**: P0
**Duration**: ~10 seconds
**Prerequisites**: None (fresh start)

**Objective**: Verify server starts successfully and main interface loads.

**Given/When/Then**:

```gherkin
Given: GAO-Dev server is running at localhost:3000
When: User navigates to localhost:3000
Then: Page loads successfully with title "GAO-Dev"
  And: Main layout is visible
  And: Sidebar navigation is visible
  And: Chat tab is active by default
  And: All essential UI elements are present
```

**Test Implementation**:

```typescript
import { test, expect } from '@playwright/test';

test('MVP-1: Server startup and accessibility', async ({ page }) => {
  // Navigate to localhost:3000
  await page.goto('http://localhost:3000');

  // Verify page title
  await expect(page).toHaveTitle(/GAO-Dev/);

  // Verify main layout visible
  await expect(page.locator('[data-testid="main-layout"]')).toBeVisible();

  // Verify sidebar navigation visible
  await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();

  // Verify default tab (Chat) is active
  const chatTab = page.locator('[data-testid="tab-chat"]');
  await expect(chatTab).toBeVisible();
  await expect(chatTab).toHaveAttribute('data-state', 'active');

  // Verify all navigation tabs present
  await expect(page.locator('[data-testid="tab-activity"]')).toBeVisible();
  await expect(page.locator('[data-testid="tab-files"]')).toBeVisible();

  // Verify top bar present
  await expect(page.locator('[data-testid="top-bar"]')).toBeVisible();

  // Verify theme toggle present
  await expect(page.locator('[data-testid="theme-toggle"]')).toBeVisible();

  // Verify main content area visible
  await expect(page.locator('[data-testid="main-content"]')).toBeVisible();

  // Take baseline screenshot
  await expect(page).toHaveScreenshot('mvp-1-startup.png');
});
```

**Success Criteria**:
- Page loads in <2 seconds
- All UI elements visible
- No console errors
- Screenshot matches baseline

---

### Scenario 2: Chat Flow

**ID**: MVP-2
**Priority**: P0
**Duration**: ~30 seconds
**Prerequisites**: Server running, MVP-1 passed

**Objective**: Send message to Brian and receive streaming response.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
  And: Chat tab is active
When: User types "Create a PRD for user authentication" in chat input
  And: User clicks send button
Then: User message appears in chat history
  And: Brian's response streams in (chunks appear)
  And: Response contains expected content (PRD, authentication, etc.)
  And: Send button is re-enabled after response completes
```

**Test Implementation**:

```typescript
test('MVP-2: Send message to Brian and receive response', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Verify chat tab is active
  await expect(page.locator('[data-testid="tab-chat"]')).toHaveAttribute('data-state', 'active');

  // Type message
  const input = page.locator('[data-testid="chat-input"]');
  await input.fill('Create a PRD for user authentication');

  // Verify send button is enabled
  const sendButton = page.locator('[data-testid="chat-send-button"]');
  await expect(sendButton).toBeEnabled();

  // Click send
  await sendButton.click();

  // Verify send button disabled during loading
  await expect(sendButton).toHaveAttribute('data-state', 'loading');
  await expect(sendButton).toBeDisabled();

  // Verify user message appears
  const userMessage = page.locator('[data-testid="chat-message-user"]').last();
  await expect(userMessage).toContainText('Create a PRD for user authentication');

  // Wait for Brian's response to start streaming
  await page.waitForSelector('[data-testid="chat-message-brian"]', { timeout: 5000 });

  // Wait for response to complete (button re-enabled)
  await expect(sendButton).toHaveAttribute('data-state', 'idle', { timeout: 10000 });
  await expect(sendButton).toBeEnabled();

  // Verify Brian's response contains expected content
  const brianMessage = page.locator('[data-testid="chat-message-brian"]').last();
  const responseText = await brianMessage.textContent();

  // Check for keywords (fuzzy match)
  const hasRelevantContent = /PRD|Product Requirements|authentication|John|workflow/i.test(responseText || '');
  expect(hasRelevantContent).toBeTruthy();

  // Verify reasoning toggle visible (optional)
  const reasoningToggle = brianMessage.locator('[data-testid="reasoning-toggle"]');
  if (await reasoningToggle.isVisible()) {
    // Click to expand reasoning
    await reasoningToggle.click();
    await expect(brianMessage.locator('[data-testid="reasoning-content"]')).toBeVisible();
  }

  // Take screenshot of chat
  await expect(page).toHaveScreenshot('mvp-2-chat-response.png');
});
```

**Success Criteria**:
- Message sent successfully
- Streaming response appears within 5 seconds
- Response contains relevant content
- UI updates correctly (loading states)

---

### Scenario 3: Activity Stream

**ID**: MVP-3
**Priority**: P0
**Duration**: ~20 seconds
**Prerequisites**: Server running, workflow triggered

**Objective**: Verify activity stream shows real-time events.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User navigates to Activity tab
  And: A workflow is triggered (via chat or CLI)
Then: Events appear in activity stream in real-time
  And: Events display agent name, timestamp, and action
  And: Events are ordered chronologically (newest first)
```

**Test Implementation**:

```typescript
test('MVP-3: Activity stream shows real-time events', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Activity tab
  await page.click('[data-testid="tab-activity"]');

  // Verify tab is active
  await expect(page.locator('[data-testid="tab-activity"]')).toHaveAttribute('data-state', 'active');

  // Verify activity stream visible
  await expect(page.locator('[data-testid="activity-stream"]')).toBeVisible();

  // Trigger event (send chat message to create activity)
  await page.click('[data-testid="tab-chat"]');
  await page.fill('[data-testid="chat-input"]', 'List workflows');
  await page.click('[data-testid="chat-send-button"]');

  // Return to activity tab
  await page.click('[data-testid="tab-activity"]');

  // Wait for event to appear (real-time)
  await page.waitForSelector('[data-testid="activity-event"]', { timeout: 3000 });

  // Verify event structure
  const firstEvent = page.locator('[data-testid="activity-event"]').first();
  await expect(firstEvent).toBeVisible();

  // Verify event shows agent
  const agentName = firstEvent.locator('[data-testid="activity-event-agent"]');
  await expect(agentName).toBeVisible();
  const agent = await agentName.textContent();
  expect(['brian', 'john', 'winston', 'sally', 'bob', 'amelia', 'murat', 'mary']).toContain(agent?.toLowerCase());

  // Verify event shows timestamp
  const timestamp = firstEvent.locator('[data-testid="activity-event-timestamp"]');
  await expect(timestamp).toBeVisible();

  // Verify event shows action
  const action = await firstEvent.textContent();
  expect(action).toBeTruthy();

  // Test progressive disclosure (click to expand)
  await firstEvent.click();

  // Verify expanded details visible
  await expect(firstEvent.locator('[data-testid="activity-event-details"]')).toBeVisible();

  // Take screenshot
  await expect(page).toHaveScreenshot('mvp-3-activity-stream.png');
});
```

**Success Criteria**:
- Events appear in real-time (<100ms latency)
- Event structure correct (agent, timestamp, action)
- Progressive disclosure works (expand/collapse)

---

### Scenario 4: File Tree and Monaco Editor

**ID**: MVP-4
**Priority**: P0
**Duration**: ~20 seconds
**Prerequisites**: Server running, project has files

**Objective**: Browse file tree and view file in Monaco editor.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User navigates to Files tab
  And: User clicks on a file in the file tree
Then: Monaco editor opens
  And: File content is displayed
  And: File path is shown in breadcrumb
  And: Editor is in read-only mode (if CLI holds lock)
```

**Test Implementation**:

```typescript
test('MVP-4: Browse file tree and view file in Monaco', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Files tab
  await page.click('[data-testid="tab-files"]');

  // Verify tab is active
  await expect(page.locator('[data-testid="tab-files"]')).toHaveAttribute('data-state', 'active');

  // Verify file tree visible
  await expect(page.locator('[data-testid="file-tree"]')).toBeVisible();

  // Wait for file tree to load
  await page.waitForSelector('[data-testid="file-tree-item"]', { timeout: 3000 });

  // Click on a specific file (e.g., PRD.md)
  const prdFile = page.locator('[data-testid="file-tree-item"][data-path="docs/PRD.md"]');
  if (await prdFile.isVisible()) {
    await prdFile.click();
  } else {
    // Fallback: Click first file
    await page.locator('[data-testid="file-tree-item"][data-type="file"]').first().click();
  }

  // Verify Monaco editor opens
  await page.waitForSelector('[data-testid="monaco-editor"]', { timeout: 5000 });
  await expect(page.locator('[data-testid="monaco-editor"]')).toBeVisible();

  // Verify Monaco editor container (using .monaco-editor class)
  await expect(page.locator('.monaco-editor')).toBeVisible();

  // Verify file breadcrumb shows path
  const breadcrumb = page.locator('[data-testid="file-breadcrumb"]');
  await expect(breadcrumb).toBeVisible();
  const breadcrumbText = await breadcrumb.textContent();
  expect(breadcrumbText).toBeTruthy();

  // Check if editor is read-only
  const editor = page.locator('[data-testid="monaco-editor"]');
  const isReadOnly = await editor.getAttribute('data-readonly');
  if (isReadOnly === 'true') {
    // Verify save button disabled
    const saveButton = page.locator('[data-testid="file-save-button"]');
    await expect(saveButton).toBeDisabled();
  }

  // Take screenshot
  await expect(page).toHaveScreenshot('mvp-4-monaco-editor.png');
});
```

**Success Criteria**:
- File tree renders 500+ files in <300ms
- Monaco editor loads in <500ms
- File content displayed correctly
- Read-only mode enforced when applicable

---

### Scenario 5: Read-Only Mode

**ID**: MVP-5
**Priority**: P0
**Duration**: ~15 seconds
**Prerequisites**: Server running, CLI holds lock

**Objective**: Verify read-only mode when CLI is active.

**Given/When/Then**:

```gherkin
Given: CLI is running and holds write lock
When: User opens web interface
Then: Read-only banner is visible
  And: Banner message is clear ("CLI is active")
  And: All write controls are disabled (send button, save button, etc.)
  And: Monaco editor is read-only
  And: Read operations still work (view files, chat history, etc.)
```

**Test Implementation**:

```typescript
test('MVP-5: Read-only mode when CLI active', async ({ page }) => {
  // Simulate CLI holding lock (create session.lock file)
  // This would be done by test setup

  await page.goto('http://localhost:3000');

  // Verify read-only banner visible
  const banner = page.locator('[data-testid="read-only-banner"]');
  await expect(banner).toBeVisible();

  // Verify banner message
  const bannerText = await banner.textContent();
  expect(bannerText).toMatch(/read-only|CLI is active|observability/i);

  // Verify chat send button disabled
  const chatSendButton = page.locator('[data-testid="chat-send-button"]');
  await expect(chatSendButton).toBeDisabled();

  // Verify chat input disabled
  const chatInput = page.locator('[data-testid="chat-input"]');
  await expect(chatInput).toBeDisabled();

  // Navigate to Files tab
  await page.click('[data-testid="tab-files"]');

  // Click on a file
  await page.waitForSelector('[data-testid="file-tree-item"]', { timeout: 3000 });
  await page.locator('[data-testid="file-tree-item"][data-type="file"]').first().click();

  // Verify Monaco editor is read-only
  await page.waitForSelector('[data-testid="monaco-editor"]', { timeout: 5000 });
  const editor = page.locator('[data-testid="monaco-editor"]');
  await expect(editor).toHaveAttribute('data-readonly', 'true');

  // Verify save button disabled
  const saveButton = page.locator('[data-testid="file-save-button"]');
  await expect(saveButton).toBeDisabled();

  // Verify read operations still work (can still view)
  await expect(page.locator('.monaco-editor')).toBeVisible();

  // Take screenshot
  await expect(page).toHaveScreenshot('mvp-5-read-only-mode.png');
});
```

**Success Criteria**:
- Read-only banner visible
- All write controls disabled
- Read operations work correctly
- Clear messaging to user

---

### Scenario 6: Theme Toggle

**ID**: MVP-6
**Priority**: P1
**Duration**: ~10 seconds
**Prerequisites**: Server running

**Objective**: Verify dark/light theme toggle works.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User clicks theme toggle button
Then: Theme switches (dark ↔ light)
  And: All components update colors
  And: Theme preference persisted to localStorage
```

**Test Implementation**:

```typescript
test('MVP-6: Dark/light theme toggle', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Get initial theme
  const html = page.locator('html');
  const initialTheme = await html.getAttribute('data-theme');

  // Take screenshot of initial theme
  await expect(page).toHaveScreenshot('mvp-6-theme-initial.png');

  // Click theme toggle
  await page.click('[data-testid="theme-toggle"]');

  // Wait for theme to change
  await page.waitForTimeout(200); // Allow transition

  // Verify theme switched
  const newTheme = await html.getAttribute('data-theme');
  expect(newTheme).not.toBe(initialTheme);
  expect(['light', 'dark']).toContain(newTheme);

  // Verify background color changed
  const mainLayout = page.locator('[data-testid="main-layout"]');
  const bgColor = await mainLayout.evaluate((el) => {
    return window.getComputedStyle(el).backgroundColor;
  });
  expect(bgColor).toBeTruthy();

  // Take screenshot of new theme
  await expect(page).toHaveScreenshot('mvp-6-theme-toggled.png');

  // Reload page
  await page.reload();

  // Verify theme persisted
  const persistedTheme = await html.getAttribute('data-theme');
  expect(persistedTheme).toBe(newTheme);

  // Toggle back
  await page.click('[data-testid="theme-toggle"]');

  // Verify back to original
  const finalTheme = await html.getAttribute('data-theme');
  expect(finalTheme).toBe(initialTheme);
});
```

**Success Criteria**:
- Theme switches smoothly (<100ms)
- All components update
- Theme persisted across page reloads
- Visual comparison confirms color changes

---

## Phase 2: V1.1 E2E Scenarios

### Scenario 7: Kanban Drag-Drop

**ID**: V1.1-1
**Priority**: P0
**Duration**: ~30 seconds
**Prerequisites**: Server running, V1.1 features deployed

**Objective**: Drag story card to change state.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
  And: Kanban tab is available
When: User navigates to Kanban tab
  And: User drags story card from Backlog to Ready
  And: User confirms transition in dialog
Then: Story moves to Ready column
  And: Git commit is created
  And: WebSocket broadcasts state change
  And: Git tab shows new commit
```

**Test Implementation**:

```typescript
test('V1.1-1: Drag story card to change state', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Kanban tab
  await page.click('[data-testid="tab-kanban"]');

  // Verify tab is active
  await expect(page.locator('[data-testid="tab-kanban"]')).toHaveAttribute('data-state', 'active');

  // Verify Kanban board visible
  await expect(page.locator('[data-testid="kanban-board"]')).toBeVisible();

  // Find story 1.1 in Backlog
  const story = page.locator('[data-testid="story-card-1.1"]');
  await expect(story).toBeVisible();

  // Verify initially in Backlog
  const backlogColumn = page.locator('[data-testid="kanban-column-backlog"]');
  await expect(backlogColumn.locator('[data-testid="story-card-1.1"]')).toBeVisible();

  // Drag story to Ready column
  const readyColumn = page.locator('[data-testid="kanban-column-ready"]');
  await story.dragTo(readyColumn);

  // Wait for confirmation dialog
  await page.waitForSelector('[data-testid="transition-confirm-dialog"]', { timeout: 2000 });
  await expect(page.locator('[data-testid="transition-confirm-dialog"]')).toBeVisible();

  // Verify dialog message
  const dialogContent = page.locator('[data-testid="dialog-content"]');
  await expect(dialogContent).toContainText(/Story 1.1|transition|ready/i);

  // Confirm transition
  await page.click('[data-testid="confirm-transition"]');

  // Wait for dialog to close
  await expect(page.locator('[data-testid="transition-confirm-dialog"]')).not.toBeVisible();

  // Verify story moved to Ready column
  await expect(readyColumn.locator('[data-testid="story-card-1.1"]')).toBeVisible({ timeout: 3000 });

  // Verify story no longer in Backlog
  await expect(backlogColumn.locator('[data-testid="story-card-1.1"]')).not.toBeVisible();

  // Navigate to Git tab to verify commit
  await page.click('[data-testid="tab-git"]');

  // Wait for git timeline to load
  await page.waitForSelector('[data-testid="commit-card"]', { timeout: 3000 });

  // Verify latest commit message contains story transition
  const latestCommit = page.locator('[data-testid="commit-message"]').first();
  const commitText = await latestCommit.textContent();
  expect(commitText).toMatch(/Story 1.1|ready|transition/i);

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.1-1-kanban-drag-drop.png');
});
```

**Success Criteria**:
- Drag-and-drop smooth and responsive
- Confirmation dialog prevents accidental moves
- State change atomic (DB + git commit)
- Real-time WebSocket update

---

### Scenario 8: Workflow Controls

**ID**: V1.1-2
**Priority**: P1
**Duration**: ~30 seconds
**Prerequisites**: Server running, workflow active

**Objective**: Pause and resume workflow.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
  And: A workflow is running
When: User navigates to Workflows tab
  And: User clicks pause button
Then: Workflow pauses
  And: Status shows "Paused"
When: User clicks resume button
Then: Workflow resumes
  And: Status shows "Running"
```

**Test Implementation**:

```typescript
test('V1.1-2: Pause and resume workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Trigger a workflow (via chat)
  await page.fill('[data-testid="chat-input"]', 'Create a PRD');
  await page.click('[data-testid="chat-send-button"]');

  // Wait for workflow to start
  await page.waitForTimeout(2000);

  // Navigate to Workflows tab
  await page.click('[data-testid="tab-workflows"]');

  // Wait for workflow list
  await page.waitForSelector('[data-testid="workflow-card"]', { timeout: 5000 });

  // Verify workflow is running
  const workflowStatus = page.locator('[data-testid="workflow-status"]').first();
  await expect(workflowStatus).toContainText(/running|active/i);

  // Click pause button
  await page.click('[data-testid="workflow-pause-btn"]');

  // Verify status changes to paused
  await expect(workflowStatus).toContainText(/paused/i, { timeout: 3000 });

  // Verify pause button disabled, resume button enabled
  await expect(page.locator('[data-testid="workflow-pause-btn"]')).toBeDisabled();
  await expect(page.locator('[data-testid="workflow-resume-btn"]')).toBeEnabled();

  // Click resume
  await page.click('[data-testid="workflow-resume-btn"]');

  // Verify status changes to running
  await expect(workflowStatus).toContainText(/running|active/i, { timeout: 3000 });

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.1-2-workflow-controls.png');
});
```

**Success Criteria**:
- Workflow pauses immediately
- UI updates correctly
- Resume restores workflow state

---

### Scenario 9: Git History and Diff

**ID**: V1.1-3
**Priority**: P1
**Duration**: ~20 seconds
**Prerequisites**: Server running, git repository has commits

**Objective**: View commit history and diff.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User navigates to Git tab
  And: User clicks on a commit
Then: Diff view opens
  And: Shows added/removed lines
  And: Can switch between files in commit
```

**Test Implementation**:

```typescript
test('V1.1-3: View commit history and diff', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Git tab
  await page.click('[data-testid="tab-git"]');

  // Wait for commit history to load
  await page.waitForSelector('[data-testid="commit-card"]', { timeout: 5000 });

  // Verify commit cards visible
  const commitCards = page.locator('[data-testid="commit-card"]');
  expect(await commitCards.count()).toBeGreaterThan(0);

  // Click on first commit
  await commitCards.first().click();

  // Wait for diff view to open
  await page.waitForSelector('[data-testid="diff-viewer"]', { timeout: 3000 });
  await expect(page.locator('[data-testid="diff-viewer"]')).toBeVisible();

  // Verify diff shows changes
  const diffContent = page.locator('[data-testid="diff-content"]');
  await expect(diffContent).toBeVisible();

  // Verify added lines visible (green)
  const addedLines = page.locator('.diff-line-added');
  if (await addedLines.count() > 0) {
    await expect(addedLines.first()).toBeVisible();
  }

  // Verify removed lines visible (red)
  const removedLines = page.locator('.diff-line-removed');
  if (await removedLines.count() > 0) {
    await expect(removedLines.first()).toBeVisible();
  }

  // Check if multiple files in commit
  const fileSelectorExists = await page.locator('[data-testid="diff-file-selector"]').isVisible();
  if (fileSelectorExists) {
    // Click file selector to switch files
    await page.click('[data-testid="diff-file-selector"]');
    await page.click('[data-testid="diff-file-option"]');

    // Verify diff updates
    await expect(diffContent).toBeVisible();
  }

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.1-3-git-diff.png');
});
```

**Success Criteria**:
- Commit history renders 10,000+ commits (virtual scrolling)
- Diff view loads quickly
- Syntax highlighting in diffs

---

### Scenario 10: Provider Configuration

**ID**: V1.1-4
**Priority**: P1
**Duration**: ~20 seconds
**Prerequisites**: Server running

**Objective**: Change AI provider in settings.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User opens settings panel
  And: User selects different provider
  And: User selects model
  And: User clicks save
Then: Settings saved to YAML file
  And: Success toast appears
  And: Provider change persisted
```

**Test Implementation**:

```typescript
test('V1.1-4: Change AI provider in settings', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Open settings
  await page.click('[data-testid="settings-button"]');

  // Wait for settings dialog
  await page.waitForSelector('[data-testid="settings-dialog"]', { timeout: 2000 });
  await expect(page.locator('[data-testid="settings-dialog"]')).toBeVisible();

  // Get current provider
  const providerSelect = page.locator('[data-testid="provider-select"]');
  const initialProvider = await providerSelect.inputValue();

  // Select different provider
  const newProvider = initialProvider === 'claude_code' ? 'opencode' : 'claude_code';
  await providerSelect.selectOption(newProvider);

  // Wait for model options to load
  await page.waitForTimeout(500);

  // Select a model
  const modelSelect = page.locator('[data-testid="model-select"]');
  await modelSelect.selectOption({ index: 0 }); // Select first available model

  // Click save
  await page.click('[data-testid="save-settings"]');

  // Verify success toast appears
  await page.waitForSelector('[data-testid="toast-success"]', { timeout: 3000 });
  await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();

  // Verify toast message
  const toastText = await page.locator('[data-testid="toast-success"]').textContent();
  expect(toastText).toMatch(/saved|updated|success/i);

  // Close settings dialog
  await page.click('[data-testid="dialog-cancel"]');

  // Reload page to verify persistence
  await page.reload();

  // Open settings again
  await page.click('[data-testid="settings-button"]');
  await page.waitForSelector('[data-testid="settings-dialog"]', { timeout: 2000 });

  // Verify provider persisted
  const persistedProvider = await page.locator('[data-testid="provider-select"]').inputValue();
  expect(persistedProvider).toBe(newProvider);

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.1-4-provider-config.png');
});
```

**Success Criteria**:
- Provider selection works
- Settings saved to YAML
- Persistence verified after reload

---

## Phase 3: V1.2 E2E Scenarios

### Scenario 11: Ceremony Channel

**ID**: V1.2-1
**Priority**: P1
**Duration**: ~30 seconds
**Prerequisites**: Server running, ceremony active

**Objective**: Join retrospective ceremony channel.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
  And: A retrospective ceremony is active
When: User navigates to Ceremony Channels tab
  And: User clicks on retrospective channel
Then: Message stream appears
  And: Messages show agent avatars
  And: User can see intra-agent discussion
```

**Test Implementation**:

```typescript
test('V1.2-1: Join retrospective ceremony channel', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Trigger retrospective ceremony (via chat)
  await page.fill('[data-testid="chat-input"]', 'Run a retrospective for Epic 1');
  await page.click('[data-testid="chat-send-button"]');

  // Wait for ceremony to start
  await page.waitForTimeout(3000);

  // Verify Ceremony Channels tab becomes visible
  await expect(page.locator('[data-testid="tab-ceremonies"]')).toBeVisible({ timeout: 5000 });

  // Navigate to Ceremony Channels tab
  await page.click('[data-testid="tab-ceremonies"]');

  // Verify channel list visible
  await page.waitForSelector('[data-testid="ceremony-channel"]', { timeout: 3000 });

  // Click on retrospective channel
  const retroChannel = page.locator('[data-testid="ceremony-channel"]').filter({ hasText: /retrospective/i });
  await retroChannel.click();

  // Verify message stream visible
  await page.waitForSelector('[data-testid="ceremony-message"]', { timeout: 5000 });
  await expect(page.locator('[data-testid="ceremony-message"]').first()).toBeVisible();

  // Verify messages show agent avatars
  const messageAvatar = page.locator('[data-testid="message-avatar"]').first();
  await expect(messageAvatar).toBeVisible();

  // Verify agent name in message
  const agentName = page.locator('[data-testid="message-agent-name"]').first();
  await expect(agentName).toBeVisible();

  // Verify message content
  const messageContent = page.locator('[data-testid="message-content"]').first();
  await expect(messageContent).toBeVisible();

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.2-1-ceremony-channel.png');
});
```

**Success Criteria**:
- Channel appears when ceremony starts
- Messages stream in real-time
- Agent identification clear

---

### Scenario 12: Layout Resize

**ID**: V1.2-2
**Priority**: P2
**Duration**: ~15 seconds
**Prerequisites**: Server running

**Objective**: Resize panel and persist layout.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
  And: Files tab is open
When: User drags panel divider to resize
Then: Panel width changes
  And: Layout persisted to localStorage
When: User reloads page
Then: Layout restored from localStorage
```

**Test Implementation**:

```typescript
test('V1.2-2: Resize panel and persist layout', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Files tab
  await page.click('[data-testid="tab-files"]');

  // Get initial file tree width
  const fileTree = page.locator('[data-testid="file-tree"]');
  const initialBox = await fileTree.boundingBox();
  const initialWidth = initialBox?.width || 0;

  // Find panel divider
  const divider = page.locator('[data-testid="panel-divider"]');
  const dividerBox = await divider.boundingBox();

  if (dividerBox) {
    // Drag divider to resize
    await page.mouse.move(dividerBox.x + dividerBox.width / 2, dividerBox.y + dividerBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(dividerBox.x + 200, dividerBox.y + dividerBox.height / 2); // Move 200px right
    await page.mouse.up();

    // Wait for resize to complete
    await page.waitForTimeout(500);

    // Get new width
    const newBox = await fileTree.boundingBox();
    const newWidth = newBox?.width || 0;

    // Verify width changed
    expect(Math.abs(newWidth - initialWidth - 200)).toBeLessThan(50); // Allow some variance
  }

  // Reload page
  await page.reload();

  // Navigate back to Files tab
  await page.click('[data-testid="tab-files"]');

  // Verify layout persisted
  const restoredBox = await fileTree.boundingBox();
  const restoredWidth = restoredBox?.width || 0;

  // Should be close to resized width
  expect(Math.abs(restoredWidth - (initialWidth + 200))).toBeLessThan(50);

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.2-2-layout-resize.png');
});
```

**Success Criteria**:
- Panel resizes smoothly
- Layout persisted to localStorage
- Restored after reload

---

### Scenario 13: Metrics Dashboard

**ID**: V1.2-3
**Priority**: P1
**Duration**: ~20 seconds
**Prerequisites**: Server running, metrics data available

**Objective**: View metrics dashboard with charts.

**Given/When/Then**:

```gherkin
Given: User is on the web interface
When: User navigates to Metrics tab
Then: Dashboard loads with charts
  And: Velocity chart is visible
  And: Agent activity chart is visible
  And: User can hover over data points for details
```

**Test Implementation**:

```typescript
test('V1.2-3: View metrics dashboard with charts', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Metrics tab
  await page.click('[data-testid="tab-metrics"]');

  // Wait for dashboard to load
  await page.waitForSelector('[data-testid="metrics-dashboard"]', { timeout: 5000 });
  await expect(page.locator('[data-testid="metrics-dashboard"]')).toBeVisible();

  // Verify velocity chart visible
  await expect(page.locator('[data-testid="velocity-chart"]')).toBeVisible();

  // Verify agent activity chart visible
  await expect(page.locator('[data-testid="agent-activity-chart"]')).toBeVisible();

  // Hover over data point to show tooltip
  const dataPoint = page.locator('[data-testid="chart-data-point"]').first();
  if (await dataPoint.isVisible()) {
    await dataPoint.hover();

    // Verify tooltip appears
    await page.waitForSelector('[data-testid="chart-tooltip"]', { timeout: 2000 });
    await expect(page.locator('[data-testid="chart-tooltip"]')).toBeVisible();

    // Verify tooltip has content
    const tooltipText = await page.locator('[data-testid="chart-tooltip"]').textContent();
    expect(tooltipText).toBeTruthy();
  }

  // Verify workflow success rate chart
  await expect(page.locator('[data-testid="workflow-success-chart"]')).toBeVisible();

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.2-3-metrics-dashboard.png');
});
```

**Success Criteria**:
- Charts render correctly
- Data visualization accurate
- Interactive tooltips work

---

### Scenario 14: Export Metrics

**ID**: V1.2-4
**Priority**: P2
**Duration**: ~15 seconds
**Prerequisites**: Server running, metrics data available

**Objective**: Export metrics to CSV.

**Given/When/Then**:

```gherkin
Given: User is on Metrics tab
When: User clicks export button
Then: CSV file downloads
  And: File contains expected data (Story, Points, Status columns)
```

**Test Implementation**:

```typescript
test('V1.2-4: Export metrics to CSV', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Navigate to Metrics tab
  await page.click('[data-testid="tab-metrics"]');

  // Wait for dashboard to load
  await page.waitForSelector('[data-testid="metrics-dashboard"]', { timeout: 5000 });

  // Start waiting for download
  const downloadPromise = page.waitForEvent('download');

  // Click export button
  await page.click('[data-testid="export-metrics-btn"]');

  // Wait for download to start
  const download = await downloadPromise;

  // Verify filename
  const filename = download.suggestedFilename();
  expect(filename).toMatch(/metrics.*\.csv/i);

  // Save download to temp path
  const path = await download.path();
  expect(path).toBeTruthy();

  // Read file contents (optional - verify structure)
  const fs = require('fs');
  if (path) {
    const content = fs.readFileSync(path, 'utf-8');

    // Verify CSV headers
    expect(content).toContain('Story');
    expect(content).toContain('Points');
    expect(content).toContain('Status');

    // Verify has data rows
    const lines = content.split('\n');
    expect(lines.length).toBeGreaterThan(1); // Header + at least one data row
  }

  // Take screenshot
  await expect(page).toHaveScreenshot('v1.2-4-export-metrics.png');
});
```

**Success Criteria**:
- File downloads successfully
- CSV format correct
- Data accurate

---

## Screenshot Comparison Strategy

### Visual Regression Testing

**Purpose**: Detect unintended UI changes by comparing screenshots.

**Approach**:
1. **Baseline Screenshots**: First test run creates baseline images
2. **Comparison**: Subsequent runs compare against baseline
3. **Threshold**: Allow small differences (max 100 pixels) for minor rendering variations
4. **Update**: Update baselines when intentional UI changes made

**Configuration**:

```typescript
// In test
await expect(page).toHaveScreenshot('scenario-name.png', {
  maxDiffPixels: 100, // Allow 100 pixels difference
  threshold: 0.2, // 20% pixel difference threshold
});
```

**Best Practices**:
- Use full-page screenshots for layout tests
- Use component screenshots for specific UI elements
- Always take screenshots at stable state (no animations)
- Use deterministic test data (no random UUIDs, timestamps)

**Example**:

```typescript
test('Visual regression: Chat layout', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Wait for stable state
  await page.waitForLoadState('networkidle');

  // Take full-page screenshot
  await expect(page).toHaveScreenshot('chat-layout.png', {
    fullPage: true,
    maxDiffPixels: 100,
  });
});
```

**Handling Failures**:

When screenshot comparison fails:

1. **Review Diff**: Playwright generates diff image showing changes
2. **Intentional Change**: Update baseline with `--update-snapshots` flag
   ```bash
   npx playwright test --update-snapshots
   ```
3. **Bug**: Fix the UI issue causing unexpected change

**Storage**:
- Baseline screenshots: `tests/e2e/screenshots/`
- Diff screenshots: `test-results/`

---

## Test Execution Guide

### Running Tests

**All E2E Tests**:
```bash
npx playwright test
```

**Specific Scenario**:
```bash
npx playwright test --grep "MVP-1"
```

**Phase-Specific**:
```bash
npx playwright test --grep "MVP-"   # Phase 1 only
npx playwright test --grep "V1.1-" # Phase 2 only
npx playwright test --grep "V1.2-" # Phase 3 only
```

**Headed Mode** (visible browser):
```bash
npx playwright test --headed
```

**Debug Mode**:
```bash
npx playwright test --debug
```

**Update Screenshots**:
```bash
npx playwright test --update-snapshots
```

### Test Reports

**Generate HTML Report**:
```bash
npx playwright show-report
```

**View Test Results**:
```bash
# After test run, opens HTML report in browser
npx playwright show-report
```

**Report Contents**:
- Test execution summary
- Pass/fail status
- Screenshots (failures only)
- Videos (failures only)
- Trace files (retries only)

### CI/CD Integration

**GitHub Actions** (see TEST_STRATEGY.md for full workflow):

```yaml
- name: Run Playwright tests
  run: npx playwright test

- name: Upload Playwright report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

---

## Troubleshooting

### Common Issues

**Issue 1: Server not starting**

**Symptoms**: Tests timeout waiting for server

**Solution**:
```bash
# Start server manually first
gao-dev start --web --test-mode

# Then run tests
npx playwright test
```

**Issue 2: Flaky tests (random failures)**

**Symptoms**: Test passes sometimes, fails other times

**Solution**:
- Add explicit waits: `await page.waitForSelector(..., { timeout: 5000 })`
- Wait for network idle: `await page.waitForLoadState('networkidle')`
- Use `data-state` attributes to wait for state changes
- Avoid hardcoded `setTimeout`, use conditional waits

**Issue 3: Screenshot comparison fails**

**Symptoms**: "Screenshot comparison failed" error

**Solution**:
1. Review diff image in `test-results/`
2. If intentional change, update baseline:
   ```bash
   npx playwright test --update-snapshots
   ```
3. If bug, fix UI issue

**Issue 4: Element not found**

**Symptoms**: "Element not found" error

**Solution**:
- Verify `data-testid` attribute exists in component
- Check for typos in selector
- Wait for element to appear:
  ```typescript
  await page.waitForSelector('[data-testid="..."]', { timeout: 5000 });
  ```

**Issue 5: WebSocket connection fails**

**Symptoms**: Tests timeout waiting for real-time events

**Solution**:
- Verify WebSocket server running
- Check browser console for WebSocket errors
- Verify session token passed correctly
- Check CORS configuration

### Debugging Tips

**1. Use Playwright Inspector**:
```bash
npx playwright test --debug
```

**2. Take Screenshots During Test**:
```typescript
await page.screenshot({ path: 'debug.png' });
```

**3. Print Page Content**:
```typescript
const html = await page.content();
console.log(html);
```

**4. Check Console Logs**:
```typescript
page.on('console', msg => console.log('BROWSER:', msg.text()));
```

**5. Slow Down Execution**:
```typescript
await page.waitForTimeout(1000); // Pause for 1 second
```

---

## Conclusion

This E2E test plan provides Claude Code with comprehensive instructions to test GAO-Dev's web interface via Playwright MCP. The plan covers:

- **14 E2E Scenarios** across 3 phases (MVP, V1.1, V1.2)
- **Semantic HTML Requirements** ensuring AI-testable design
- **data-testid Naming Conventions** for stable, readable selectors
- **Screenshot Comparison** for visual regression testing
- **Test Execution Guide** for running tests and viewing reports
- **Troubleshooting** for common issues

**Expected Outcomes**:
- Claude Code can run all 14 scenarios automatically
- Visual regression catches unintended UI changes
- Clear pass/fail criteria for each scenario
- Actionable error messages when tests fail
- Continuous quality feedback throughout development

**Next Steps**:
1. Review and approve E2E test plan
2. Implement semantic HTML with data-testid attributes
3. Create Playwright test files for all 14 scenarios
4. Set up CI/CD pipeline to run tests on every PR
5. Use Claude Code to execute tests and find UX issues

---

**Document Status**: Complete - Ready for Implementation
**Author**: Murat (Test Architect)
**Reviewers**: Winston (Architect), Sally (UX Designer), Amelia (Developer)
**Version**: 1.0
**Last Updated**: 2025-01-16
