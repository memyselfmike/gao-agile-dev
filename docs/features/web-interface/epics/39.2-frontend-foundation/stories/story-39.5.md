# Story 39.5: Basic Layout with shadcn/ui

**Story Number**: 39.5
**Epic**: 39.2 - Frontend Foundation
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 3 points)
**Dependencies**: Story 39.4 (React + Vite setup)

## User Story
As a **user**, I want **professional, clean layout with tab navigation** so that **I can easily access different features and enjoy a familiar interface**.

## Acceptance Criteria
- [ ] AC1: Top bar with project name, session status, agent switcher, settings
- [ ] AC2: Sidebar with tab icons (Chat, Activity, Files, Kanban, Git, Ceremonies)
- [ ] AC3: Main content area (full-width, full-height)
- [ ] AC4: Tab navigation with keyboard shortcuts (Cmd+1-6)
- [ ] AC5: Active tab highlighted
- [ ] AC6: Responsive layout (min width 1024px)
- [ ] AC7: Session status indicator: "Active", "Read-Only", "Disconnected"
- [ ] AC8: Read-only banner when CLI holds lock
- [ ] AC9: Smooth tab transitions (<100ms)
- [ ] AC10: shadcn/ui components integrated (Button, Tabs, Card, Sheet, Toast)
- [ ] AC11: Error boundaries for component crashes
- [ ] AC12: Loading states for initial data fetch

## Technical Context
**Components**: shadcn/ui (Radix UI + Tailwind)
**Layout**: CSS Grid for top bar + sidebar + main
**Accessibility**: Semantic HTML, keyboard nav, ARIA labels
