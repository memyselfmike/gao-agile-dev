# LayoutSettings Component - Test Plan

**Story 39.39**: Layout Persistence & Presets

## Manual Testing Checklist

### Visual Tests

- [ ] Layout icon button appears in TopBar (top-right, before settings icon)
- [ ] Button has proper hover state
- [ ] Button is accessible via keyboard (Tab navigation)

### Dropdown Menu Tests

- [ ] Click layout button opens dropdown menu
- [ ] Dropdown shows 3 presets: Default, Code-Focused, Chat-Focused
- [ ] Current preset is highlighted with radio indicator
- [ ] Preset descriptions are visible
- [ ] Reset to Default button appears at bottom

### Preset Application Tests

- [ ] **Default Preset**: Click applies balanced layout (20% | 60% | 20%)
- [ ] **Code-Focused Preset**: Click applies wide main content (15% | 85% | 0%)
- [ ] **Chat-Focused Preset**: Click applies wide chat panel (15% | 45% | 40%)
- [ ] Toast notification appears on preset application
- [ ] Toast shows correct preset name
- [ ] Toast shows preset description

### Smooth Transitions

- [ ] Layout changes animate smoothly (300ms ease-in-out)
- [ ] No jarring jumps or flickers
- [ ] Content remains visible during transition
- [ ] Scroll position preserved

### Preset Detection

- [ ] Manually resize panels → Preset changes to "Custom"
- [ ] Custom preset appears in dropdown (disabled, not selectable)
- [ ] Resizing to match preset (within 2%) auto-detects preset

### Keyboard Navigation

- [ ] Tab to layout button, press Enter → Opens dropdown
- [ ] Arrow keys navigate between presets
- [ ] Enter key selects highlighted preset
- [ ] Escape closes dropdown

### Reset to Default

- [ ] Click "Reset to Default" button
- [ ] Layout resets to Default preset (20% | 60% | 20%)
- [ ] Toast notification appears
- [ ] Current preset updated to "Default"

### Persistence Tests

- [ ] Apply preset → Refresh page → Layout restored
- [ ] Manually resize → Refresh page → Custom layout restored
- [ ] localStorage key `gao-dev-layout:layout` exists
- [ ] Clear localStorage → Page loads with default layout

### Edge Cases

- [ ] Rapid preset switching works correctly
- [ ] Switching presets during manual resize works
- [ ] No memory leaks on repeated preset changes
- [ ] Works on mobile viewport (if applicable)

## Automated Tests (Future)

When Vitest is set up, implement:

1. **Unit Tests**:
   - Preset metadata correct
   - Preset detection logic
   - Store state updates

2. **Integration Tests**:
   - Click preset → Layout changes
   - Toast notification triggered
   - Store state synced

3. **E2E Tests** (Playwright):
   - Full user flow: Open dropdown → Select preset → Verify layout
   - Persistence across page refreshes
   - Keyboard navigation

## Test Data IDs

```tsx
// Layout Settings Button
data-testid="layout-settings-trigger"

// Preset Options
data-testid="layout-preset-default"
data-testid="layout-preset-code-focused"
data-testid="layout-preset-chat-focused"
data-testid="layout-preset-custom" // Only when custom

// Reset Button
data-testid="layout-reset-default"
```

## Expected Toast Messages

```
Success: "Layout preset applied: Default"
Description: "Balanced layout (20% | 60% | 20%)"

Success: "Layout preset applied: Code-Focused"
Description: "Wide main content (15% | 85% | hidden)"

Success: "Layout preset applied: Chat-Focused"
Description: "Wide chat panel (15% | 45% | 40%)"
```

## Accessibility Requirements

- [ ] Layout button has `aria-label="Layout settings"`
- [ ] Dropdown menu is keyboard navigable
- [ ] Radio group properly announced by screen readers
- [ ] Focus visible on all interactive elements
- [ ] Color contrast meets WCAG AA standards

## Performance Requirements

- [ ] Preset application completes in <100ms
- [ ] Transition animation runs at 60fps
- [ ] No layout thrashing during resize
- [ ] localStorage writes debounced (via react-resizable-panels)

## Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Known Limitations

1. **Custom preset not selectable**: Custom appears only when manually resized
2. **Preset detection tolerance**: 2% tolerance may miss edge cases
3. **Mobile**: Layout settings may be hidden on mobile (<768px)

## Success Criteria

All 10 acceptance criteria from Story 39.39 must pass:
- [x] Panel sizes auto-saved to localStorage (via react-resizable-panels)
- [x] Panel sizes restored on page load
- [x] Layout presets dropdown in Settings menu
- [x] Apply preset triggers smooth transition (300ms)
- [x] Current preset highlighted
- [x] Reset to Default button
- [x] Settings accessed via gear icon
- [x] Toast notification on preset applied
- [x] Stable test IDs
- [x] Keyboard navigation
