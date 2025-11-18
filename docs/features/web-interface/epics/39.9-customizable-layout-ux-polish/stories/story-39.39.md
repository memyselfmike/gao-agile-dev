# Story 39.39: Layout Persistence & Presets

**Epic**: 39.9 - Customizable Layout & UX Polish
**Story Points**: 3 (Small-Medium)
**Priority**: P2 (Could Have - V1.2)
**Status**: Complete
**Assignee**: Amelia (Developer)

---

## User Story

> As a user, I want my panel layout to persist across sessions and quickly switch between layout presets so that I don't have to reconfigure my workspace every time.

---

## Description

Implement localStorage-based persistence for panel sizes and provide 3 pre-defined layout presets (Default, Code-Focused, Chat-Focused) for quick workspace configuration.

---

## Acceptance Criteria

- [x] Panel sizes automatically saved to localStorage on resize (via react-resizable-panels autoSaveId)
- [x] Panel sizes restored on page load (via react-resizable-panels autoSaveId)
- [x] Layout presets dropdown in Settings menu:
  - **Default**: Balanced (20% | 60% | 20%)
  - **Code-Focused**: Wide main content (15% | 85% | 0% - right panel hidden)
  - **Chat-Focused**: Wide chat panel (15% | 45% | 40%)
- [x] Apply preset button triggers smooth transition animation (300ms ease-in-out)
- [x] Current preset highlighted in dropdown (RadioGroup indicator)
- [x] Reset to Default button in Settings
- [x] Settings panel accessed via layout icon in top-right corner (next to gear icon)
- [x] Toast notification on preset applied: "Layout preset applied: Code-Focused"
- [x] Stable test IDs: `data-testid="layout-preset-default"`, etc.
- [x] Keyboard navigation in preset dropdown (RadioGroup built-in support)

---

## Technical Implementation

**Storage**: `localStorage.setItem('gao-layout', JSON.stringify({ leftWidth, rightWidth }))`

**State**: Zustand store for layout state

```typescript
interface LayoutState {
  leftWidth: number;
  rightWidth: number;
  preset: 'default' | 'code-focused' | 'chat-focused' | 'custom';
  setLayout: (left: number, right: number) => void;
  applyPreset: (preset: string) => void;
}
```

**Presets**: Defined as constants in `layout.constants.ts`

```typescript
export const LAYOUT_PRESETS = {
  default: { leftWidth: 250, rightWidth: 300 },
  'code-focused': { leftWidth: 200, rightWidth: 0 },
  'chat-focused': { leftWidth: 200, rightWidth: 400 },
};
```

**Debouncing**: Use `lodash.debounce` or custom hook to debounce localStorage writes

---

## API Integration

None required (client-side only)

---

## Dependencies

- Story 39.38: Resizable Panel Layout (layout system)

---

## QA Testing

### Manual Testing
1. Resize panels → Refresh page → Verify sizes restored
2. Select "Code-Focused" preset → Verify right panel hidden, main content expanded
3. Select "Chat-Focused" preset → Verify right panel wide (400px)
4. Manually resize → Verify preset changes to "Custom"
5. Click Reset to Default → Verify default layout applied

### Automated Testing
- Unit tests: LocalStorage read/write, preset calculations
- E2E tests: Apply preset, verify panel widths, refresh page, verify persistence

---

## Out of Scope

- Multiple saved custom layouts (defer to V1.3)
- Server-side layout sync across devices (defer to V1.3)
- Layout animation library (use CSS transitions)

---

## Notes

- Handle localStorage errors gracefully (fall back to defaults)
- Clear localStorage if corrupted (invalid JSON)
- Ensure preset transitions are smooth (use CSS `transition` property)
- Consider adding keyboard shortcut for quick preset switching (e.g., `Cmd+1`, `Cmd+2`, `Cmd+3`)
