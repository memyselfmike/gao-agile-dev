# ResizableLayout Component

**Story**: 39.38 - Resizable Panel Layout
**Status**: Production-Ready (10/12 AC complete)

---

## Quick Start

```tsx
import { ResizableLayout } from '@/components/layout/ResizableLayout';

function MyApp() {
  return (
    <ResizableLayout
      leftSidebar={<LeftPanel />}
      mainContent={<MainPanel />}
      rightSidebar={<RightPanel />} // optional
      defaultLayout={[20, 60, 20]} // optional: [left%, main%, right%]
    />
  );
}
```

---

## Features

- ✅ Draggable dividers between panels
- ✅ Min/max width constraints (200-400px sidebars, 400px+ main)
- ✅ Smooth 200ms resize animations
- ✅ Keyboard navigation (Tab + Arrow keys)
- ✅ Touch-friendly (16px+ touch targets)
- ✅ Responsive (mobile <768px: single column)
- ✅ Auto-save to localStorage
- ✅ WCAG AA accessible

---

## Props

```typescript
interface ResizableLayoutProps {
  /** Left sidebar content (e.g., navigation) */
  leftSidebar: ReactNode;

  /** Main content area (e.g., workspace) */
  mainContent: ReactNode;

  /** Right sidebar content (optional, e.g., properties panel) */
  rightSidebar?: ReactNode;

  /** Default width percentages [left, main, right]. Default: [20, 60, 20] */
  defaultLayout?: [number, number, number];

  /** Additional CSS class names */
  className?: string;
}
```

---

## Usage Examples

### Two-Panel Layout (Most Common)

```tsx
<ResizableLayout
  leftSidebar={<Sidebar />}
  mainContent={<Content />}
/>
```

### Three-Panel Layout

```tsx
<ResizableLayout
  leftSidebar={<Sidebar />}
  mainContent={<Content />}
  rightSidebar={<PropertiesPanel />}
/>
```

### Custom Default Sizes

```tsx
<ResizableLayout
  leftSidebar={<Sidebar />}
  mainContent={<Content />}
  defaultLayout={[15, 70, 15]} // narrower sidebars
/>
```

---

## Constraints

| Panel | Min Size | Max Size |
|-------|----------|----------|
| Left Sidebar | 13% (~200px @ 1536px) | 26% (~400px) |
| Main Content | 26% (~400px) | Unlimited |
| Right Sidebar | 13% (~200px) | 26% (~400px) |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Focus next divider |
| Shift+Tab | Focus previous divider |
| Arrow Left | Decrease left panel width |
| Arrow Right | Increase left panel width |
| Arrow Up/Down | (No effect) |

---

## Responsive Behavior

- **Desktop (≥768px)**: Three-panel resizable layout
- **Mobile (<768px)**: Single column, no resize

---

## Accessibility

- **ARIA Labels**: Each divider has descriptive label
- **Keyboard Navigation**: Full keyboard control
- **Screen Reader**: Announces panel resize actions
- **Focus Visible**: Clear focus indicators
- **Touch Targets**: 16px minimum (WCAG 2.5.5)

---

## Layout Persistence

Layouts auto-save to `localStorage` with key `gao-dev-layout`.

**Clear Saved Layout**:
```javascript
localStorage.removeItem('gao-dev-layout');
```

---

## Test IDs

For E2E testing:

```tsx
// Left divider
screen.getByTestId('divider-left')

// Right divider (if present)
screen.getByTestId('divider-right')
```

---

## Known Limitations

1. **Double-Click Reset**: Not implemented (library limitation)
   - Workaround: Manually drag to reset
   - Will be added in Story 39.39

2. **Snap to Default**: Not implemented (requires custom logic)
   - Panels don't auto-snap when close to default
   - Will be added in Story 39.39

---

## Performance

- **Frame Rate**: 60fps (CSS transforms, GPU-accelerated)
- **Bundle Size**: +20KB (react-resizable-panels)
- **Memory**: No leaks (React component lifecycle)

---

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14.1+
- ✅ Edge 90+
- ❌ IE11 (not supported)

---

## Troubleshooting

### Dividers Not Visible
**Issue**: Dividers not showing up
**Fix**: Ensure parent has `height` set (e.g., `h-screen`, `h-full`)

### Can't Resize Below Min Width
**Issue**: Panel stops resizing before reaching edge
**Fix**: This is intentional (min width constraint: 200px)

### Layout Not Persisting
**Issue**: Panel sizes reset on page reload
**Fix**: Check browser allows localStorage (not in private/incognito mode)

### Mobile Not Showing Single Column
**Issue**: Panels still resizable on mobile
**Fix**: Ensure viewport width is correctly detected (<768px)

---

## Related Components

- `DualSidebar`: Left sidebar (Primary + Secondary navigation)
- `MainContent`: Main content area with tabs
- `TopBar`: Top navigation bar

---

## Future Enhancements (Story 39.39)

- [ ] Double-click divider to reset to default
- [ ] Snap to default when within 20px
- [ ] Layout presets (Compact, Balanced, Spacious)
- [ ] User preferences UI
- [ ] Vertical panel resizing

---

## References

- **Library**: [react-resizable-panels](https://github.com/bvaughn/react-resizable-panels)
- **Story**: `docs/features/web-interface/epics/39.9-customizable-layout-ux-polish/stories/story-39.38.md`
- **Testing**: `docs/features/web-interface/epics/39.9-customizable-layout-ux-polish/TESTING_GUIDE_39.38.md`

---

**Last Updated**: 2025-11-18
**Version**: 1.0
