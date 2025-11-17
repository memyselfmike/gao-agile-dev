# Story 39.21: Workflow Detail Panel

**Epic**: 39.6 - Workflow Visualization
**Story Points**: 3
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING

---

## Description

As a **developer**, I want to **see detailed information about a selected workflow** so that **I can debug issues and understand workflow execution steps**.

## Acceptance Criteria

1. **AC1**: GET /api/workflows/{workflow_id}/details endpoint returns workflow metadata, steps, variables, artifacts, and errors
2. **AC2**: Detail panel opens as slide-out drawer from right side when workflow is clicked
3. **AC3**: Panel header displays workflow name, status badge, and close button (X icon)
4. **AC4**: Metadata section shows workflow_id, agent, epic/story numbers, start time, end time, duration
5. **AC5**: Steps section lists all workflow steps with name, status (completed/pending/failed), duration, and timestamps
6. **AC6**: Click step to expand and show step details (agent calls, tool invocations, outputs)
7. **AC7**: Variables section displays workflow input variables as key-value table
8. **AC8**: Artifacts section lists created files with links to Files tab (file path, type, size)
9. **AC9**: Errors section displays error messages, stack traces, and error timestamps (if workflow failed)
10. **AC10**: Panel supports scrolling for long content (steps, stack traces)
11. **AC11**: Close button (X) and Escape key both close the panel
12. **AC12**: Accessibility: Focus trap in panel, ARIA labels, keyboard navigation (Tab through sections)

## Technical Notes

### Backend Implementation

**File**: `gao_dev/web/server.py`

**Endpoint**: `GET /api/workflows/{workflow_id}/details`

**Path Parameters**:
- `workflow_id`: Workflow execution ID (e.g., "wf-123")

**Response Structure**:
```json
{
  "workflow": {
    "id": 1,
    "workflow_id": "wf-123",
    "workflow_name": "Story Implementation",
    "status": "completed",
    "started_at": "2025-01-16T10:00:00Z",
    "completed_at": "2025-01-16T10:45:23Z",
    "duration": 2723,  // seconds
    "agent": "Amelia",
    "epic": 39,
    "story_num": 15
  },
  "steps": [
    {
      "name": "Read story file",
      "status": "completed",
      "started_at": "2025-01-16T10:00:00Z",
      "completed_at": "2025-01-16T10:00:05Z",
      "duration": 5,
      "tool_calls": [
        {"tool": "Read", "args": {"file_path": "docs/features/.../story-39.15.md"}}
      ],
      "outputs": ["Successfully read 180 lines"]
    },
    {
      "name": "Implement components",
      "status": "completed",
      "started_at": "2025-01-16T10:00:05Z",
      "completed_at": "2025-01-16T10:30:12Z",
      "duration": 1807,
      "tool_calls": [
        {"tool": "Write", "args": {"file_path": "src/components/KanbanBoard.tsx"}},
        {"tool": "Write", "args": {"file_path": "src/stores/kanbanStore.ts"}}
      ],
      "outputs": ["Created 3 components", "280 lines of code"]
    }
  ],
  "variables": {
    "epic": "39",
    "story_num": "15",
    "feature": "web-interface",
    "prd_location": "docs/features/web-interface/PRD.md"
  },
  "artifacts": [
    {
      "path": "src/components/KanbanBoard.tsx",
      "type": "typescript",
      "size": 3456,
      "created_at": "2025-01-16T10:15:00Z"
    },
    {
      "path": "src/stores/kanbanStore.ts",
      "type": "typescript",
      "size": 2890,
      "created_at": "2025-01-16T10:20:00Z"
    }
  ],
  "errors": null  // or array of error objects if workflow failed
}
```

**Error Response** (if workflow failed):
```json
{
  "workflow": { ... },
  "steps": [ ... ],
  "variables": { ... },
  "artifacts": [ ... ],
  "errors": [
    {
      "timestamp": "2025-01-16T10:30:15Z",
      "message": "TypeScript compilation failed",
      "stack_trace": "Error: Cannot find name 'Card'\n  at src/components/KanbanBoard.tsx:25:10",
      "step": "Implement components"
    }
  ]
}
```

**Data Source**:
- Query `WorkflowExecution` by `workflow_id`
- Parse `result` JSON to extract steps, artifacts, errors
- Load variables from workflow execution context
- Use DocumentStructureManager to get artifact metadata

### Frontend Implementation

**Components Created**:

1. **WorkflowDetailPanel.tsx** (220 lines)
   - Slide-out drawer from right (Sheet component from shadcn/ui)
   - Header: workflow name, status badge, close button
   - Tabbed sections: Overview, Steps, Variables, Artifacts, Errors (if failed)
   - Scrollable content area
   - Close on Escape key
   - Focus trap (first element focused on open)
   - Accessibility: role="dialog", aria-modal="true"

2. **WorkflowMetadata.tsx** (70 lines)
   - Displays workflow metadata in key-value grid
   - Fields: workflow_id, agent, epic/story, start time, end time, duration
   - Duration formatting: "5m 23s" or "1h 15m 32s"
   - Copy workflow_id button (copy to clipboard)

3. **WorkflowSteps.tsx** (140 lines)
   - Accordion list of workflow steps (Accordion from shadcn/ui)
   - Step header: name, status icon, duration
   - Expanded view: tool calls, outputs, error messages
   - Status icons: green checkmark (completed), blue spinner (running), red X (failed)
   - Code blocks for outputs (syntax-highlighted if JSON/code)

4. **WorkflowVariables.tsx** (50 lines)
   - Table of key-value pairs
   - Searchable/filterable
   - Copy variable value button

5. **WorkflowArtifacts.tsx** (80 lines)
   - List of created files
   - File icon by type (TS, Python, Markdown, etc.)
   - File size display
   - Link to Files tab: `onClick` opens Files tab and navigates to file
   - "Open in editor" button (future: embedded Monaco editor)

6. **WorkflowErrors.tsx** (90 lines)
   - Displayed only if workflow failed
   - Error message in Alert component (destructive variant)
   - Stack trace in collapsible code block (ScrollArea)
   - Copy error message button
   - Link to failed step in Steps tab

**State Management**:
```typescript
interface WorkflowDetailState {
  selectedWorkflowId: string | null;
  workflowDetails: WorkflowDetails | null;
  loading: boolean;
  error: string | null;
  fetchDetails: (workflowId: string) => Promise<void>;
  closePanel: () => void;
  openFilesTab: (filePath: string) => void;  // Navigate to Files tab
}
```

**UI Components** (shadcn/ui):
- Sheet: Slide-out drawer
- Tabs: Section navigation (Overview, Steps, Variables, Artifacts, Errors)
- Accordion: Collapsible workflow steps
- Table: Variables and metadata
- Alert: Error display
- ScrollArea: Long content (stack traces)
- Badge: Status indicators
- Button: Actions (copy, close, open file)

**Duration Formatting**:
```typescript
function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
  if (minutes > 0) return `${minutes}m ${secs}s`;
  return `${secs}s`;
}
```

**Copy to Clipboard**:
```typescript
async function copyToClipboard(text: string) {
  await navigator.clipboard.writeText(text);
  toast({ title: "Copied to clipboard", duration: 2000 });
}
```

### Accessibility

**Focus Management**:
- Panel opens: focus on close button (X)
- Focus trap: Tab cycles through panel elements only
- Escape key: close panel and return focus to workflow bar

**ARIA Attributes**:
- Panel: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="workflow-title"`
- Close button: `aria-label="Close workflow details"`
- Tabs: `role="tablist"`, `aria-selected`
- Accordion: `aria-expanded`, `aria-controls`

**Keyboard Navigation**:
- Tab: Navigate through panel sections
- Arrow keys: Navigate tabs
- Escape: Close panel
- Enter/Space: Expand/collapse accordion steps

**Screen Reader Support**:
- Announce panel open: "Workflow details opened for [workflow_name]"
- Announce section changes: "Showing [section_name]"
- Announce workflow status: "[workflow_name] is [status]"

### Dependencies

**NPM Packages**:
```json
{
  "react-syntax-highlighter": "^15.5.0",  // Syntax highlighting for code blocks
  "date-fns": "^2.30.0"  // Date formatting
}
```

**Backend Dependencies**:
- Story 39.20: GET /api/workflows/timeline (data structure)
- Epic 27: WorkflowExecution model
- DocumentStructureManager: Artifact metadata

**Frontend Dependencies**:
- Story 39.20: Timeline (integration point)
- Epic 39.4: Files tab (navigation target for artifacts)
- shadcn/ui: Sheet, Tabs, Accordion, Table, Alert, ScrollArea, Badge, Button

### Testing

**Unit Tests**: `tests/e2e/test_workflow_detail_panel.py` (12 tests)
1. GET /api/workflows/{workflow_id}/details endpoint registration
2. Endpoint returns 404 if workflow_id not found
3. Endpoint returns workflow details with all sections
4. Steps parsed correctly from workflow result
5. Variables extracted from execution context
6. Artifacts listed with metadata
7. Errors displayed if workflow failed
8. Panel opens on workflow click
9. Panel closes on close button click
10. Panel closes on Escape key
11. Focus trap functional
12. All 12 acceptance criteria validated

**Test Coverage**: >95% of new code

**E2E Tests**: Manual validation
- Click workflow in timeline, verify panel opens
- Verify all sections display correct data
- Expand workflow steps, check tool calls and outputs
- Click artifact link, verify Files tab opens
- Test keyboard navigation (Tab, Escape, Arrow keys)
- Test screen reader announcements
- Test with failed workflow (verify error display)

### Performance

- Panel open time: <100ms
- Details fetch time: <150ms (API call)
- Render time: <200ms (all sections)
- Scroll performance: 60fps (virtual scrolling for large step lists)

## Dependencies

- Story 39.20: Workflow Execution Timeline (integration point)
- Epic 39.4: Files tab (artifact navigation)
- Epic 27: WorkflowExecution model and result parsing
- DocumentStructureManager: Artifact metadata

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] GET /api/workflows/{workflow_id}/details endpoint implemented
- [ ] WorkflowDetailPanel component with slide-out drawer
- [ ] All 6 sub-components implemented (Metadata, Steps, Variables, Artifacts, Errors)
- [ ] Focus trap functional
- [ ] Escape key closes panel
- [ ] Keyboard navigation verified
- [ ] ARIA labels on all interactive elements
- [ ] Screen reader support verified
- [ ] Artifact links navigate to Files tab
- [ ] 12 unit tests passing
- [ ] Manual E2E validation complete
- [ ] Code reviewed and approved
- [ ] Zero regressions
- [ ] Committed to feature branch

---

**Implementation Date**: TBD
**Developer**: Amelia (Software Developer)
**Tester**: Murat (Test Architect)
**Status**: PENDING
