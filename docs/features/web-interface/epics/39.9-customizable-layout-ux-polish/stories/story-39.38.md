# Story 39.38: Resizable Panel Layout

**Epic**: 39.9 - Customizable Layout & UX Polish
**Story Points**: 4 (Medium)
**Priority**: P2 (Could Have - V1.2)
**Status**: Ready for Testing
**Assignee**: Amelia (Developer)
**Implementation Date**: 2025-11-18

---

## User Story

> As a user, I want to resize panels (sidebar, main content, rightbar) so that I can customize my workspace layout to my preferences.

---

## Description

Implement resizable panel system allowing users to drag panel dividers to adjust panel widths. Supports dual sidebar + main content layout with smooth resize interactions.

**Implementation**: Uses react-resizable-panels library for battle-tested, performant panel management.

---

## Acceptance Criteria

- [x] Draggable dividers between panels (left sidebar | main | right sidebar) ✅
- [x] Smooth resize animation with 200ms transition ✅
- [x] Min/max width constraints: ✅
  - Sidebars: min 200px, max 400px
  - Main content: min 400px, no max
- [x] Cursor changes to `col-resize` on hover over divider ✅
- [x] Visual feedback during drag (divider highlighted) ✅
- [ ] Double-click divider to reset to default width ⚠️ *Deferred to Story 39.39*
- [ ] Panels snap to default width when close (within 20px threshold) ⚠️ *Enhancement for Story 39.39*
- [x] Resize preserves scroll position in all panels ✅
- [x] Touch-friendly drag targets (min 16px touch area) ✅
- [x] Keyboard accessible: Focus divider + Arrow keys to resize ✅
- [x] Stable test IDs: `data-testid="divider-left"`, `data-testid="divider-right"` ✅
- [x] Responsive: Disable resize on mobile (<768px), show single column ✅

**Status**: 10/12 acceptance criteria complete. 2 criteria deferred to Story 39.39 (low priority enhancements).

---

## Technical Implementation

**Library**: `react-resizable-panels` or custom implementation with `useRef` + mouse events

**Component**: `<ResizableLayout>` wrapping `<LeftSidebar>`, `<MainContent>`, `<RightSidebar>`

**State**: Local component state for panel sizes (widths in pixels or percentages)

**Events**:
- `onDragStart`: Highlight divider, set cursor
- `onDrag`: Update panel widths in real-time
- `onDragEnd`: Finalize sizes, emit resize event

**Performance**: Use `requestAnimationFrame` for smooth 60fps resizing

---

## API Integration

None required (client-side only)

---

## Dependencies

- Epic 39.8: Unified Chat/Channels/DM Interface (layout structure)

---

## QA Testing

### Manual Testing
1. Drag left divider → verify left sidebar resizes
2. Drag right divider → verify right sidebar resizes
3. Drag beyond min/max → verify constraints enforced
4. Double-click divider → verify reset to default
5. Resize window → verify responsive behavior
6. Test on touch device → verify touch drag works

### Automated Testing
- Unit tests: Panel width calculations, constraint enforcement
- E2E tests: Drag simulation, double-click reset

---

## Out of Scope

- Vertical panel resizing (top/bottom split)
- Collapsible panels (defer to Story 39.40)
- Layout presets (handled in Story 39.39)

---

## Implementation Notes

**Files Created**:
- `gao_dev/web/frontend/src/components/layout/ResizableLayout.tsx` (171 lines)
- `gao_dev/web/frontend/src/components/layout/ResizableLayout.test.tsx` (295 lines)
- `docs/features/web-interface/epics/39.9-customizable-layout-ux-polish/TESTING_GUIDE_39.38.md`
- `docs/features/web-interface/epics/39.9-customizable-layout-ux-polish/ACCEPTANCE_VALIDATION_39.38.md`

**Files Modified**:
- `gao_dev/web/frontend/src/components/layout/MainContent.tsx` (integrated ResizableLayout)

**Library Used**: react-resizable-panels v3.0.6 (already installed)

**Key Features**:
- WCAG AA compliant (ARIA labels, keyboard navigation)
- Touch-friendly (16px+ touch targets)
- Performant (CSS transforms, 60fps expected)
- Auto-save to localStorage (key: `gao-dev-layout`)
- Responsive (mobile <768px: single column)

**Known Limitations**:
1. Double-click reset (AC-6): Requires custom implementation, deferred to Story 39.39
2. Snap to default (AC-7): Requires custom logic, deferred to Story 39.39

**Next Steps**: Complete manual testing per TESTING_GUIDE_39.38.md

---

## Notes

- Dividers are accessible via keyboard for WCAG AA compliance ✅
- CSS `user-select: none` handled by library during drag ✅
- Used `react-resizable-panels` library for battle-tested implementation ✅
