# Epic 39.2: Frontend Foundation

**Epic Number**: 39.2
**Epic Name**: Frontend Foundation
**Feature**: Web Interface
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: 7 story points
**Dependencies**: Epic 39.1 (Backend Foundation)

---

## Epic Overview

Build the React frontend scaffolding with professional layout, theming, and state management. This epic establishes the UI framework that all feature tabs will integrate into.

### Business Value

- **Professional User Experience**: Clean, accessible interface reduces barrier to entry
- **Responsive Design**: Adapts to different screen sizes (min 1024px)
- **Dark/Light Mode**: Respects user preferences and reduces eye strain
- **Accessibility**: WCAG 2.1 AA compliance ensures inclusive design
- **AI-Testable**: Semantic HTML and stable selectors enable Playwright MCP testing

### User Stories Summary

This epic includes frontend infrastructure:

1. **Story 39.4**: React + Vite + Zustand Setup
2. **Story 39.5**: Basic Layout with shadcn/ui
3. **Story 39.6**: Dark/Light Theme Support

### Success Criteria

- [ ] Vite dev server starts in <2 seconds with HMR
- [ ] Production build completes in <30 seconds
- [ ] Initial page load <2 seconds (Lighthouse TTI)
- [ ] Layout renders correctly at 1024px minimum width
- [ ] Dark/light theme toggle works smoothly (<100ms transition)
- [ ] System preference detection works (prefers-color-scheme)
- [ ] All UI components keyboard accessible
- [ ] WCAG 2.1 AA contrast ratios met (4.5:1 for text)
- [ ] Lighthouse accessibility score >95/100

### Technical Approach

**Technology Stack**:
- React 18 (concurrent rendering, automatic batching)
- Vite 5 (fast dev server, optimized builds)
- Zustand (state management, <1KB)
- shadcn/ui (Radix UI + Tailwind CSS)
- TypeScript (strict mode, no Any types)

**State Management Strategy**:
- Zustand for global state (chat, activity, kanban)
- React Context for local state (theme, modals)
- No Redux (Zustand is simpler and faster)

**Accessibility Strategy**:
- Semantic HTML (button, nav, main)
- ARIA labels for screen readers
- Keyboard navigation (Tab, Enter, Escape)
- Focus visible indicators
- Color contrast compliance

### Definition of Done

- [ ] All stories in epic completed and tested
- [ ] E2E tests pass (layout, theme, navigation)
- [ ] Performance tests meet targets (<2s load, >95 Lighthouse)
- [ ] Accessibility tests pass (axe-core, keyboard nav)
- [ ] Cross-browser testing complete (Chrome, Firefox, Safari, Edge)
- [ ] Documentation complete (component guide, theming guide)
- [ ] Code review approved
- [ ] No console errors or warnings

---

**Epic Owner**: Sally (UX Designer)
**Implementation**: Amelia (Software Developer)
**Testing**: Murat (Test Architect)
