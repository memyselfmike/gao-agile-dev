# Story 39.6: Dark/Light Theme Support

**Story Number**: 39.6
**Epic**: 39.2 - Frontend Foundation
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: S (Small - 2 points)
**Dependencies**: Story 39.5 (Layout with shadcn/ui)

## User Story
As a **user**, I want **dark and light themes** so that **I can work comfortably in different lighting conditions and respect my system preferences**.

## Acceptance Criteria
- [ ] AC1: Detect system preference via `prefers-color-scheme` media query
- [ ] AC2: Apply dark/light theme automatically on first load
- [ ] AC3: Theme toggle in settings (user can override system preference)
- [ ] AC4: Theme stored in localStorage
- [ ] AC5: Smooth theme transition (<100ms, no flash)
- [ ] AC6: All components styled for both themes
- [ ] AC7: WCAG 2.1 AA contrast ratios met (4.5:1 for text)
- [ ] AC8: Color palette defined in Tailwind config
- [ ] AC9: CSS variables for theme colors
- [ ] AC10: Theme state synced across tabs (localStorage event)

## Technical Context
**Implementation**: CSS variables + Tailwind dark: variant
**Storage**: localStorage theme key
**Components**: ThemeProvider context, ThemeToggle component
