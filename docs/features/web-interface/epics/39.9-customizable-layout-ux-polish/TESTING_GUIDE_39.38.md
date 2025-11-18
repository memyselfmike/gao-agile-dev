# Testing Guide - Story 39.38: Resizable Panel Layout

**Epic**: 39.9 - Customizable Layout & UX Polish
**Story**: 39.38 - Resizable Panel Layout
**Status**: Implementation Complete - Testing Required

---

## Overview

This guide provides comprehensive testing procedures for the resizable panel layout feature. All acceptance criteria must be validated before marking the story complete.

---

## Acceptance Criteria Checklist

### AC-1: Draggable Dividers
- [ ] Draggable divider exists between left sidebar and main content
- [ ] Draggable divider exists between main content and right sidebar (when present)
- [ ] Dividers respond to mouse drag
- [ ] Dividers respond to touch drag (mobile)
- [ ] Test IDs present: `data-testid="divider-left"`, `data-testid="divider-right"`

**Test Steps**:
1. Open Communication tab
2. Locate divider between Primary+Secondary sidebars and main content
3. Click and drag divider left/right
4. Verify panels resize smoothly
5. Verify `data-testid="divider-left"` exists in DOM
6. If right sidebar exists, repeat for `data-testid="divider-right"`

---

### AC-2: Smooth Resize Animation
- [ ] Resize transition uses 200ms duration
- [ ] Animation is smooth with no janky frames
- [ ] Performance: maintains 60fps during drag

**Test Steps**:
1. Open React DevTools Profiler
2. Drag divider continuously for 5 seconds
3. Verify no frame drops (each frame <16.67ms)
4. Inspect divider element CSS
5. Verify `transition: all 200ms` or similar

---

### AC-3: Min/Max Width Constraints
- [ ] Left sidebar: min 200px, max 400px
- [ ] Right sidebar: min 200px, max 400px
- [ ] Main content: min 400px, no max

**Test Steps**:
1. Drag left divider to the far left
2. Verify left sidebar stops at ~200px (cannot go smaller)
3. Drag left divider to the far right
4. Verify left sidebar stops at ~400px (cannot go larger)
5. Verify main content always maintains at least 400px
6. Repeat for right sidebar if present
7. Use browser DevTools to measure pixel widths

---

### AC-4: Cursor Changes
- [ ] Cursor changes to `col-resize` on hover over divider
- [ ] Cursor persists during drag
- [ ] Cursor returns to default after drag

**Test Steps**:
1. Hover mouse over divider
2. Verify cursor changes to vertical resize cursor (↔)
3. Inspect element and verify CSS `cursor: col-resize`
4. Start dragging
5. Verify cursor remains `col-resize` during drag

---

### AC-5: Visual Feedback During Drag
- [ ] Divider highlighted on hover
- [ ] Divider highlighted during drag
- [ ] Visual indicator (grip icon) appears on hover/focus
- [ ] Highlight intensity increases during drag

**Test Steps**:
1. Hover over divider
2. Verify divider changes color/opacity
3. Verify grip icon (⋮⋮) appears
4. Click and hold divider
5. Verify highlight becomes more prominent
6. Release drag
7. Verify highlight returns to hover state

---

### AC-6: Double-Click to Reset
- [ ] Double-clicking divider resets panel to default width

**Test Steps**:
1. Resize left panel to non-default width (e.g., 300px)
2. Double-click the left divider
3. Verify panel returns to default width (20% of viewport)
4. Repeat for right divider if present

**Note**: This feature requires custom implementation as react-resizable-panels doesn't provide built-in double-click reset. Current implementation documents this as a known limitation.

---

### AC-7: Snap to Default
- [ ] Panel snaps to default width when within 20px threshold
- [ ] Snap happens on drag release, not during drag

**Test Steps**:
1. Drag panel to within 20px of default width
2. Release drag
3. Verify panel "snaps" to default width
4. Drag panel to >20px from default
5. Release drag
6. Verify panel does NOT snap (stays at custom width)

**Note**: This feature may require additional implementation if not provided by react-resizable-panels. Document as enhancement if not present.

---

### AC-8: Preserve Scroll Position
- [ ] Scrolling in panel maintains scroll position during resize
- [ ] All three panels maintain independent scroll positions

**Test Steps**:
1. Add long content to left sidebar (scroll to middle)
2. Scroll main content to middle
3. If right sidebar present, scroll to middle
4. Resize panels by dragging dividers
5. Verify all scroll positions remain unchanged
6. Panels should not jump or reset scroll

---

### AC-9: Touch-Friendly Drag Targets
- [ ] Divider touch target is at least 16px wide
- [ ] Touch drag works on tablet/mobile devices
- [ ] No double-tap zoom interference

**Test Steps** (Requires touch device or Chrome DevTools Device Emulation):
1. Open Chrome DevTools (F12)
2. Click "Toggle Device Toolbar" (Ctrl+Shift+M)
3. Select iPad or similar device
4. Tap and drag divider with touch simulation
5. Verify drag works smoothly
6. Inspect divider element
7. Verify touch target width ≥16px (may be invisible hit area)

---

### AC-10: Keyboard Accessible
- [ ] Divider can receive focus via Tab key
- [ ] Visible focus indicator when focused
- [ ] Arrow Left/Right keys resize panel
- [ ] Arrow keys respect min/max constraints
- [ ] Proper ARIA labels for screen readers

**Test Steps**:
1. Click in browser address bar
2. Press Tab repeatedly until divider receives focus
3. Verify visible focus ring/outline around divider
4. Press Arrow Right key
5. Verify left panel width increases
6. Press Arrow Left key
7. Verify left panel width decreases
8. Press Arrow keys at min/max bounds
9. Verify panel stops at constraints
10. Inspect divider element
11. Verify `aria-label="Resize left panel"` exists
12. Verify `tabindex="0"` exists

---

### AC-11: Stable Test IDs
- [ ] `data-testid="divider-left"` exists
- [ ] `data-testid="divider-right"` exists (when right sidebar present)
- [ ] Test IDs remain stable across renders

**Test Steps**:
1. Open React DevTools
2. Inspect divider elements
3. Verify `data-testid` attributes present
4. Resize panels
5. Re-inspect dividers
6. Verify test IDs unchanged

---

### AC-12: Responsive Behavior
- [ ] On mobile (<768px), resize is disabled
- [ ] On mobile, layout shows single column
- [ ] On desktop (≥768px), resize is enabled

**Test Steps**:
1. Open Chrome DevTools Device Toolbar
2. Select iPhone 12 Pro (375px width)
3. Verify dividers are hidden
4. Verify only main content visible
5. Change to desktop viewport (1920px)
6. Verify dividers appear
7. Verify all panels visible
8. Test breakpoint boundary (767px vs 768px)

---

## Performance Testing

### Frame Rate (60fps requirement)

**Tools**: React DevTools Profiler, Chrome Performance tab

**Steps**:
1. Open React DevTools Profiler
2. Click "Record"
3. Drag divider continuously for 10 seconds
4. Stop recording
5. Analyze flame graph
6. Verify no red/orange bars (indicates slow frames)
7. Calculate average frame time: should be <16.67ms (1000ms/60fps)

**Pass Criteria**: 95%+ of frames under 16.67ms

---

### Memory Leaks

**Tools**: Chrome DevTools Memory tab

**Steps**:
1. Open Memory tab
2. Take heap snapshot (baseline)
3. Resize panels 50 times
4. Force garbage collection (trash icon)
5. Take second heap snapshot
6. Compare snapshots
7. Verify no significant memory growth (<1MB difference)

**Pass Criteria**: Memory growth <1MB after GC

---

### Bundle Size Impact

**Steps**:
1. Run `npm run build`
2. Check output for bundle sizes
3. Verify `react-resizable-panels` chunk size
4. Total increase should be <50KB gzipped

**Pass Criteria**: Bundle size increase <50KB

---

## Manual Testing Checklist

### Basic Functionality
- [ ] Can resize left panel by dragging divider
- [ ] Can resize right panel by dragging divider (if present)
- [ ] Main content adjusts width automatically
- [ ] Panels cannot overlap
- [ ] Layout looks visually correct

### Edge Cases
- [ ] Resize on very small viewport (1024px)
- [ ] Resize on very large viewport (2560px)
- [ ] Rapid drag left/right
- [ ] Drag to min boundary
- [ ] Drag to max boundary
- [ ] Multiple rapid resizes
- [ ] Resize while scrolling
- [ ] Resize with long content (1000+ items)

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (macOS/iOS)
- [ ] Edge (latest)

### Accessibility
- [ ] Keyboard-only navigation (no mouse)
- [ ] Screen reader announces divider labels
- [ ] Focus visible at all times
- [ ] No keyboard traps

---

## Automated Test Setup (Future)

### Unit Tests (Vitest + React Testing Library)

**Installation**:
```bash
cd gao_dev/web/frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

**Configuration** (`vite.config.ts`):
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

**Run Tests**:
```bash
npm run test
```

---

### E2E Tests (Playwright)

**Installation**:
```bash
npm install --save-dev @playwright/test
npx playwright install
```

**Test File** (`e2e/resizable-layout.spec.ts`):
```typescript
import { test, expect } from '@playwright/test';

test('can resize left panel', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // Get initial width
  const divider = page.getByTestId('divider-left');
  const box = await divider.boundingBox();

  // Drag divider 100px to the right
  await divider.hover();
  await page.mouse.down();
  await page.mouse.move(box.x + 100, box.y);
  await page.mouse.up();

  // Verify panel resized
  // Add assertions here
});
```

**Run E2E Tests**:
```bash
npx playwright test
```

---

## Known Issues / Limitations

### Double-Click Reset (AC-6)
**Status**: Partially implemented
**Issue**: react-resizable-panels doesn't provide imperative reset API
**Workaround**: Would require accessing PanelGroup's imperativeHandle
**Impact**: Low (nice-to-have feature)
**Recommendation**: Document as enhancement for Story 39.39

### Snap to Default (AC-7)
**Status**: Not implemented
**Issue**: Requires custom logic to detect proximity to default width
**Impact**: Low (nice-to-have feature)
**Recommendation**: Implement in Story 39.39 with layout persistence

### Layout Persistence
**Status**: Implemented via react-resizable-panels
**Details**: Uses localStorage with key `gao-dev-layout`
**Story**: Layout preferences will be enhanced in Story 39.39

---

## Regression Testing

Ensure existing functionality still works:

### Communication Tab
- [ ] Primary sidebar visible (Home, DMs, Channels, Settings icons)
- [ ] Secondary sidebar shows correct content based on primary view
- [ ] DM conversation view works when agent selected
- [ ] Channel view works when channel selected
- [ ] Message sending still works
- [ ] Scrolling works in all panels

### Other Tabs
- [ ] Activity tab loads
- [ ] Files tab loads
- [ ] Kanban tab loads
- [ ] Git tab loads
- [ ] Tab switching works via Cmd+1-5

### WebSocket
- [ ] WebSocket connection establishes
- [ ] Real-time messages appear
- [ ] Activity events stream correctly

---

## Sign-Off Criteria

Story 39.38 is COMPLETE when:

✅ **Functionality**:
- All 12 acceptance criteria pass manual testing
- No console errors or warnings
- TypeScript compiles with no errors
- ESLint passes (or only pre-existing warnings)

✅ **Performance**:
- 60fps maintained during resize
- No memory leaks
- Bundle size increase acceptable (<50KB)

✅ **Accessibility**:
- WCAG AA compliant
- Keyboard navigation works
- Screen reader compatible
- Focus management correct

✅ **Regression**:
- All existing features still work
- No visual regressions
- No functional regressions

✅ **Documentation**:
- Code comments complete
- This testing guide accurate
- Known issues documented

---

## Next Steps (Story 39.39)

After Story 39.38 is complete:
- Story 39.39: Layout Persistence & Presets
- Story 39.40: Collapsible Panels
- Additional UX polish

---

**Last Updated**: 2025-11-18
**Tested By**: [Tester Name]
**Test Date**: [Date]
**Build Version**: [Git SHA]
