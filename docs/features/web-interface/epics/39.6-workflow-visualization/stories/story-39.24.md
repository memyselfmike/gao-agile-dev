# Story 39.24: Workflow Replay and History

**Epic**: 39.6 - Workflow Visualization
**Story Points**: 3
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING

---

## Description

As a **developer**, I want to **replay past workflow executions and compare runs** so that **I can reproduce issues and measure improvements over time**.

## Acceptance Criteria

1. **AC1**: GET /api/workflows/history endpoint returns paginated list of past workflow executions with filters (workflow type, date range, status)
2. **AC2**: History view displays workflows in reverse chronological order (most recent first) with pagination controls (20 per page)
3. **AC3**: Each history entry shows workflow name, status, start time, duration, agent, epic/story numbers
4. **AC4**: "Replay" button on each workflow entry triggers POST /api/workflows/replay with workflow_id, re-running workflow with same variables
5. **AC5**: Replay confirmation modal shows workflow name, original variables, and "Confirm Replay" button
6. **AC6**: Replay creates new workflow execution with status "pending", appears in timeline and history
7. **AC7**: "Compare" button allows selecting two workflow runs for side-by-side comparison
8. **AC8**: Comparison view shows differences in variables, steps, artifacts, duration, and errors
9. **AC9**: "Export" button downloads workflow execution as JSON file with all metadata, steps, variables, artifacts
10. **AC10**: Search box filters history by workflow name or workflow_id (case-insensitive)
11. **AC11**: Bookmark button allows saving important workflow runs with custom labels
12. **AC12**: Accessibility: ARIA labels, keyboard navigation (Tab to focus workflows, Enter to replay/compare), screen reader support

## Technical Notes

### Backend Implementation

**File**: `gao_dev/web/server.py`

**Endpoints**:

1. **GET /api/workflows/history**
   - Returns paginated workflow execution history
   - Query params: `page`, `limit`, `workflow_type`, `start_date`, `end_date`, `status`, `search`

2. **POST /api/workflows/replay**
   - Re-runs workflow with same variables
   - Request body: `{"workflow_id": "wf-123"}`
   - Returns new workflow_id for replay execution

3. **GET /api/workflows/compare**
   - Compares two workflow runs
   - Query params: `workflow_id_1`, `workflow_id_2`
   - Returns diff structure

4. **GET /api/workflows/{workflow_id}/export**
   - Exports workflow as JSON
   - Returns JSON file download

5. **POST /api/workflows/bookmark**
   - Bookmarks workflow with custom label
   - Request body: `{"workflow_id": "wf-123", "label": "Successful PRD run"}`

**GET /api/workflows/history Response**:
```json
{
  "workflows": [
    {
      "id": 156,
      "workflow_id": "wf-156",
      "workflow_name": "Story Implementation",
      "status": "completed",
      "started_at": "2025-01-17T09:23:15Z",
      "completed_at": "2025-01-17T10:15:42Z",
      "duration": 3147,
      "agent": "Amelia",
      "epic": 39,
      "story_num": 20,
      "bookmarked": false,
      "bookmark_label": null
    }
  ],
  "total": 156,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

**POST /api/workflows/replay Request**:
```json
{
  "workflow_id": "wf-123"
}
```

**POST /api/workflows/replay Response**:
```json
{
  "new_workflow_id": "wf-157",
  "status": "pending",
  "message": "Workflow replay scheduled",
  "original_workflow": {
    "workflow_id": "wf-123",
    "workflow_name": "PRD Creation",
    "variables": {
      "project_name": "GAO-Dev",
      "feature": "web-interface"
    }
  }
}
```

**GET /api/workflows/compare Response**:
```json
{
  "workflow_1": {
    "workflow_id": "wf-123",
    "workflow_name": "Story Implementation",
    "duration": 3147,
    "status": "completed",
    "variables": { ... },
    "steps": [ ... ],
    "artifacts": [ ... ]
  },
  "workflow_2": {
    "workflow_id": "wf-157",
    "workflow_name": "Story Implementation",
    "duration": 2890,
    "status": "completed",
    "variables": { ... },
    "steps": [ ... ],
    "artifacts": [ ... ]
  },
  "diff": {
    "duration_delta": -257,  // seconds faster
    "variables_diff": {
      "changed": ["epic"],  // Variable values changed
      "added": [],
      "removed": []
    },
    "steps_diff": {
      "changed": ["Implement components"],  // Step duration changed
      "added": ["Run linter"],
      "removed": []
    },
    "artifacts_diff": {
      "changed": [],
      "added": ["src/components/NewComponent.tsx"],
      "removed": []
    }
  }
}
```

**Replay Implementation**:
```python
@app.post("/api/workflows/replay")
async def replay_workflow(request: ReplayRequest):
    # Load original workflow execution
    original = state_manager.get_workflow_execution(request.workflow_id)

    # Extract variables from original execution
    variables = extract_variables_from_result(original.result)

    # Schedule new workflow execution
    new_workflow_id = orchestrator.execute_workflow(
        workflow_name=original.workflow_name,
        variables=variables,
        is_replay=True,
        original_workflow_id=request.workflow_id
    )

    return {
        "new_workflow_id": new_workflow_id,
        "status": "pending",
        "message": "Workflow replay scheduled"
    }
```

**Comparison Algorithm**:
```python
def compare_workflows(wf1, wf2):
    # Compare durations
    duration_delta = wf2.duration - wf1.duration

    # Compare variables (deep diff)
    variables_diff = deep_diff(wf1.variables, wf2.variables)

    # Compare steps (name, duration)
    steps_diff = diff_lists(wf1.steps, wf2.steps, key='name')

    # Compare artifacts (file paths)
    artifacts_diff = diff_lists(wf1.artifacts, wf2.artifacts, key='path')

    return {
        "duration_delta": duration_delta,
        "variables_diff": variables_diff,
        "steps_diff": steps_diff,
        "artifacts_diff": artifacts_diff
    }
```

### Frontend Implementation

**Components Created**:

1. **WorkflowHistory.tsx** (180 lines)
   - Paginated table of workflow executions
   - Columns: Name, Status, Start Time, Duration, Agent, Epic/Story, Actions
   - Actions: Replay, Compare, Export, Bookmark buttons
   - Search box for filtering
   - Loading skeleton for pagination

2. **ReplayModal.tsx** (90 lines)
   - Confirmation modal for workflow replay
   - Displays: workflow name, original variables (read-only table)
   - "Confirm Replay" and "Cancel" buttons
   - Warning: "This will create a new workflow execution"
   - Success toast on replay confirmation

3. **ComparisonView.tsx** (200 lines)
   - Side-by-side comparison of two workflows
   - Split pane layout (left: workflow 1, right: workflow 2)
   - Sections: Metadata, Variables, Steps, Artifacts, Errors
   - Diff highlighting: green (added), red (removed), yellow (changed)
   - Duration delta badge: green if faster, red if slower
   - Close button to return to history

4. **WorkflowSelector.tsx** (70 lines)
   - Multi-select checkbox for selecting workflows to compare
   - Max 2 selections enforced
   - "Compare" button enabled when 2 workflows selected
   - Clear selection button

5. **BookmarkModal.tsx** (60 lines)
   - Modal for adding bookmark label
   - Text input for custom label (max 50 chars)
   - "Save Bookmark" and "Cancel" buttons
   - Success toast on save

**State Management**:
```typescript
interface WorkflowHistoryState {
  workflows: WorkflowExecution[];
  total: number;
  page: number;
  limit: number;
  loading: boolean;
  error: string | null;
  searchQuery: string;
  filters: HistoryFilters;
  selectedWorkflows: string[];  // For comparison
  fetchHistory: (page: number) => Promise<void>;
  replayWorkflow: (workflowId: string) => Promise<void>;
  compareWorkflows: (wfId1: string, wfId2: string) => Promise<ComparisonData>;
  exportWorkflow: (workflowId: string) => void;
  bookmarkWorkflow: (workflowId: string, label: string) => Promise<void>;
  setSearchQuery: (query: string) => void;
  selectWorkflow: (workflowId: string) => void;
  clearSelection: () => void;
}
```

**Pagination**:
```typescript
function Pagination({ page, pages, onPageChange }) {
  return (
    <div>
      <Button disabled={page === 1} onClick={() => onPageChange(page - 1)}>
        Previous
      </Button>
      <span>Page {page} of {pages}</span>
      <Button disabled={page === pages} onClick={() => onPageChange(page + 1)}>
        Next
      </Button>
    </div>
  );
}
```

**Diff Highlighting**:
```typescript
function DiffRow({ label, value1, value2 }) {
  const isDifferent = value1 !== value2;

  return (
    <tr>
      <td>{label}</td>
      <td className={isDifferent ? 'bg-yellow-100' : ''}>{value1}</td>
      <td className={isDifferent ? 'bg-yellow-100' : ''}>{value2}</td>
    </tr>
  );
}
```

**JSON Export**:
```typescript
async function exportWorkflow(workflowId: string) {
  const response = await fetch(`/api/workflows/${workflowId}/export`);
  const data = await response.json();

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `workflow-${workflowId}-${new Date().toISOString()}.json`;
  a.click();
}
```

### Accessibility

**ARIA Attributes**:
- History table: `role="table"`, proper `<thead>`, `<tbody>`, `<th>`, `<td>`
- Replay button: `aria-label="Replay workflow [name]"`
- Compare button: `aria-label="Compare selected workflows"`
- Export button: `aria-label="Export workflow as JSON"`
- Bookmark button: `aria-label="Bookmark workflow [name]"`

**Keyboard Navigation**:
- Tab: Navigate through table rows and action buttons
- Enter: Activate button (Replay, Compare, Export, Bookmark)
- Arrow keys: Navigate table rows
- Escape: Close modal

**Screen Reader Support**:
- Announce workflow count: "Showing 20 workflows, page 1 of 8"
- Announce replay: "Workflow replay scheduled"
- Announce comparison: "Comparing [workflow 1] and [workflow 2]"
- Announce bookmark: "Workflow bookmarked as [label]"

### Dependencies

**NPM Packages**:
```json
{
  "date-fns": "^2.30.0"  // Date formatting
}
```

**Backend Dependencies**:
- Story 39.20: Workflow timeline data structure
- Story 39.21: Workflow detail data structure
- Epic 27: WorkflowExecution model
- WorkflowExecutor: Replay execution

**Frontend Dependencies**:
- Story 39.20: Timeline integration
- Story 39.21: Detail panel integration
- Epic 39.2: Frontend Foundation
- shadcn/ui: Table, Button, Modal, Badge, Input components

### Testing

**Unit Tests**: `tests/e2e/test_workflow_history.py` (12 tests)
1. GET /api/workflows/history endpoint with pagination
2. POST /api/workflows/replay creates new workflow execution
3. GET /api/workflows/compare returns diff structure
4. GET /api/workflows/{id}/export returns JSON data
5. POST /api/workflows/bookmark saves bookmark
6. Search filtering works
7. Frontend pagination functional
8. Replay modal shows correct variables
9. Comparison view highlights diffs
10. JSON export downloads correctly
11. Bookmark modal saves label
12. All 12 acceptance criteria validated

**Test Coverage**: >95% of new code

**E2E Tests**: Manual validation
- Load history, verify pagination
- Search for workflow, verify filtering
- Click Replay, verify confirmation modal
- Confirm replay, verify new workflow appears in timeline
- Select 2 workflows, click Compare, verify diff view
- Export workflow, verify JSON file downloaded
- Bookmark workflow, verify label saved
- Test keyboard navigation
- Test screen reader announcements

### Performance

- History fetch time: <200ms (20 workflows per page)
- Replay execution: <100ms (scheduling)
- Comparison fetch time: <300ms
- Export time: <100ms
- Bookmark save time: <50ms

## Dependencies

- Story 39.20: Workflow Execution Timeline (data source)
- Story 39.21: Workflow Detail Panel (data structure)
- Epic 27: WorkflowExecution model
- WorkflowExecutor: Replay execution capability

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] GET /api/workflows/history endpoint with pagination
- [ ] POST /api/workflows/replay endpoint functional
- [ ] GET /api/workflows/compare endpoint with diff algorithm
- [ ] GET /api/workflows/{id}/export endpoint
- [ ] POST /api/workflows/bookmark endpoint
- [ ] WorkflowHistory component with pagination
- [ ] ReplayModal component with variable display
- [ ] ComparisonView component with diff highlighting
- [ ] BookmarkModal component
- [ ] JSON export functional
- [ ] Search filtering functional
- [ ] Keyboard navigation verified
- [ ] ARIA labels on all interactive elements
- [ ] Screen reader support verified
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
