# Story 39.14: Monaco Edit Mode with Commit Enforcement

**Story Number**: 39.14
**Epic**: 39.4 - File Management
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort**: M (Medium - 4 points)
**Dependencies**: Story 39.12 (Monaco Read-Only), Story 39.3 (Session Lock), Epic 27 (GitIntegratedStateManager)

## User Story
As a **user**, I want **to edit files with mandatory commit messages** so that **I follow the same quality standards as autonomous agents and maintain git history**.

## Acceptance Criteria
- [ ] AC1: Monaco switches to edit mode when web has write lock
- [ ] AC2: Read-only mode when CLI holds lock (editing disabled)
- [ ] AC3: "Save" button prompts for commit message dialog
- [ ] AC4: Commit message template: `<type>(<scope>): <description>`
- [ ] AC5: Commit message validation: not empty, follows format
- [ ] AC6: Validation errors shown with actionable suggestions
- [ ] AC7: Atomic save: file write + DB update + git commit (GitIntegratedStateManager)
- [ ] AC8: Document lifecycle validation enforced (prevent invalid edits)
- [ ] AC9: Diff view shows changes vs last commit
- [ ] AC10: Unsaved changes indicator on tab
- [ ] AC11: Confirm dialog before closing tab with unsaved changes
- [ ] AC12: Activity stream shows commit (same as agent commits)
- [ ] AC13: Error handling: rollback on failed commit
- [ ] AC14: Success toast: "File saved and committed"

## Technical Context
**Backend**: POST /api/files/save with {path, content, commit_message}
**Integration**: GitIntegratedStateManager.update_document() for atomic operation
**Validation**: Document lifecycle rules enforced
**Convention**: Humans follow same standards as AI agents
