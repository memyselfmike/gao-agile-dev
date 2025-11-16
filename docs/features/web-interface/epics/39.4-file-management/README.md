# Epic 39.4: File Management

**Epic Number**: 39.4
**Epic Name**: File Management
**Feature**: Web Interface
**Scale Level**: 4 (Greenfield Significant Feature)
**Status**: Planned
**Priority**: MUST HAVE (P0)
**Effort Estimate**: 14 story points
**Dependencies**: Epic 39.1 (Backend), Epic 39.2 (Frontend), Epic 27 (GitIntegratedStateManager)

---

## Epic Overview

Deliver the Files Tab with integrated file tree navigation and Monaco editor for viewing and editing project files. This epic enforces GAO-Dev's conventions: all file edits require commit messages and validation, ensuring humans follow the same quality standards as autonomous agents.

### Business Value

- **Code Exploration**: Navigate project structure and view files in familiar VS Code-style editor
- **Real-Time Monitoring**: See files created/modified by agents in real-time
- **Convention Enforcement**: All edits require commit messages (humans = AI agents quality standards)
- **Git Integration**: Every save is an atomic file+DB+git commit
- **Validation**: Document lifecycle rules enforced universally

### User Stories Summary

This epic includes file management features:

1. **Story 39.11**: File Tree Navigation Component
2. **Story 39.12**: Monaco Editor Integration (Read-Only)
3. **Story 39.13**: Real-Time File Updates from Agents
4. **Story 39.14**: Monaco Edit Mode with Commit Enforcement

### Success Criteria

- [ ] File tree loads 500+ files in <300ms
- [ ] Virtual scrolling handles large file trees without lag
- [ ] Monaco editor loads 10,000-line files in <500ms
- [ ] Syntax highlighting works for 20+ languages
- [ ] Real-time file updates appear within 100ms
- [ ] File tree highlights recently changed files (last 5 minutes)
- [ ] Read-only mode when CLI holds lock
- [ ] Edit mode prompts for commit message
- [ ] Commit message validation prevents empty messages
- [ ] Atomic save: file write + DB update + git commit
- [ ] Document lifecycle validation enforced
- [ ] Diff view shows changes vs last commit
- [ ] Editor pooling prevents memory leaks (max 10 open files)

### Technical Approach

**File Tree Component**:
- Custom component using shadcn/ui (Collapsible, ScrollArea)
- Only show tracked directories (docs/, src/, gao_dev/, tests/)
- Respect .gitignore files
- Virtual scrolling for large projects
- FileSystemWatcher for real-time updates
- Highlight recently changed files

**Monaco Editor Integration**:
- @monaco-editor/react wrapper (basic Monaco, NOT monaco-vscode-api)
- Editor instance pooling (reuse editors, max 10 open)
- Lazy loading (only load when Files Tab active)
- Proper disposal of Monaco models on tab close
- Read-only mode respects session lock
- Edit mode requires commit message

**Commit Enforcement**:
- "Save" button prompts for commit message
- Template: `<type>(<scope>): <description>`
- Validation: not empty, follows format
- Backend: GitIntegratedStateManager.update_document()
- Atomic operation: file write + DB update + git commit
- Activity stream shows commit (same as agent commits)

**Integration Points**:
- Epic 27: GitIntegratedStateManager for ALL file operations
- FileSystemWatcher for real-time file change detection
- WebSocket events: file.created, file.modified, file.deleted

### Definition of Done

- [ ] All stories in epic completed and tested
- [ ] Integration tests pass (file tree, editor, commits)
- [ ] Performance tests meet targets (<300ms tree, <500ms editor)
- [ ] E2E tests cover file viewing and editing flows
- [ ] Accessibility tests pass (keyboard nav)
- [ ] Memory leak tests pass (editor pooling)
- [ ] Large file/project tests pass (10,000 lines, 500+ files)
- [ ] Convention enforcement validated (all edits create git commits)
- [ ] Documentation complete (user guide, commit message guide)
- [ ] Code review approved
- [ ] Beta testing complete with positive feedback

---

**Epic Owner**: Winston (Technical Architect)
**Implementation**: Amelia (Software Developer)
**Testing**: Murat (Test Architect)
