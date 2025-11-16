# Story 39.12: Monaco Editor Integration (Read-Only)

**Story Number**: 39.12
**Epic**: 39.4 - File Management
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 4 points)
**Dependencies**: Story 39.11 (File Tree)

## User Story
As a **user**, I want **to view files in a VS Code-style editor** so that **I can read code with syntax highlighting and familiar UX**.

## Acceptance Criteria
- [ ] AC1: Monaco editor loads when file selected from tree
- [ ] AC2: Syntax highlighting for 20+ languages (JS, TS, Python, Markdown, etc.)
- [ ] AC3: Line numbers, minimap, code folding
- [ ] AC4: Read-only mode (no editing in this story)
- [ ] AC5: Monaco editor loads 10,000-line files in <500ms
- [ ] AC6: Multiple file tabs (max 10 open)
- [ ] AC7: Tab close buttons with unsaved indicator (future)
- [ ] AC8: Keyboard shortcuts: Cmd+W close tab
- [ ] AC9: Resizable split panel (file tree | editor)
- [ ] AC10: Editor instance pooling (max 10 instances)
- [ ] AC11: Auto-close LRU when limit exceeded
- [ ] AC12: Proper Monaco model disposal on tab close (prevent memory leaks)

## Technical Context
**Library**: @monaco-editor/react (basic Monaco, NOT monaco-vscode-api)
**Backend**: GET /api/files/content?path=... returns file content
**Memory**: Editor pooling prevents leaks, max 10 open files
