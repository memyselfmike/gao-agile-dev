# Story 39.11: File Tree Navigation Component

**Story Number**: 39.11
**Epic**: 39.4 - File Management
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 3 points)
**Dependencies**: Story 39.5 (Layout)

## User Story
As a **user**, I want **to navigate project files in a tree structure** so that **I can explore the codebase and find files quickly**.

## Acceptance Criteria
- [ ] AC1: Hierarchical folder structure (collapsible)
- [ ] AC2: File icons by type (JS, Python, Markdown, etc.)
- [ ] AC3: Only show tracked directories (docs/, src/, gao_dev/, tests/)
- [ ] AC4: Respect .gitignore files (hidden files not shown)
- [ ] AC5: Click file to open in Monaco editor
- [ ] AC6: Highlight recently changed files (last 5 minutes)
- [ ] AC7: Search within file tree (fuzzy search)
- [ ] AC8: Filter by file type dropdown
- [ ] AC9: Context menu: "View in Git tab", "Copy path"
- [ ] AC10: Virtual scrolling handles 500+ files without lag
- [ ] AC11: Keyboard navigation (Arrow keys, Enter to open)
- [ ] AC12: Folder expand/collapse state persists in localStorage

## Technical Context
**Component**: Custom component using shadcn/ui (Collapsible, ScrollArea)
**Virtual Scrolling**: @tanstack/react-virtual
**Backend**: GET /api/files/tree returns file structure
