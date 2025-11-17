# Story 39.20: Workflow Execution Timeline

**Epic**: 39.6 - Workflow Visualization
**Story Points**: 4
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING

---

## Description

As a **product manager**, I want to **see a timeline view of all executed workflows** so that **I can understand the sequence and duration of autonomous development activities**.

## Acceptance Criteria

1. **AC1**: GET /api/workflows/timeline endpoint returns workflow execution records with id, workflow_id, workflow_name, status, started_at, completed_at, duration
2. **AC2**: Timeline displays horizontal bars representing workflow duration on a time axis
3. **AC3**: Workflow bars are color-coded by status (pending=gray, running=blue, completed=green, failed=red, cancelled=orange)
4. **AC4**: Click workflow bar to open detail panel (Story 39.21)
5. **AC5**: Timeline auto-scrolls to current time when workflows are running
6. **AC6**: Filter controls allow filtering by workflow type, date range, and status
7. **AC7**: Filter by workflow type shows dropdown with all workflow names (PRD, Architecture, Story Implementation, etc.)
8. **AC8**: Filter by date range provides calendar date picker (start date, end date)
9. **AC9**: Filter by status provides multi-select checkboxes (pending, running, completed, failed, cancelled)
10. **AC10**: Real-time updates via WebSocket when workflow status changes (workflow.started, workflow.completed, workflow.failed events)
11. **AC11**: Timeline supports virtual scrolling for 1000+ workflow records without performance degradation
12. **AC12**: Accessibility: ARIA labels, keyboard navigation (Tab to focus workflows, Enter to open details), screen reader support

## Technical Notes

### Backend Implementation

**File**: `gao_dev/web/server.py`

**Endpoint**: `GET /api/workflows/timeline`

**Query Parameters**:
- `workflow_type` (optional): Filter by workflow name
- `start_date` (optional): ISO 8601 date string (e.g., "2025-01-01T00:00:00Z")
- `end_date` (optional): ISO 8601 date string
- `status` (optional): Comma-separated list (e.g., "running,completed")

**Response Structure**:
```json
{
  "workflows": [
    {
      "id": 1,
      "workflow_id": "wf-123",
      "workflow_name": "PRD Creation",
      "status": "completed",
      "started_at": "2025-01-16T10:00:00Z",
      "completed_at": "2025-01-16T10:05:23Z",
      "duration": 323,  // seconds
      "agent": "John",
      "epic": 39,
      "story_num": 1
    }
  ],
  "total": 1,
  "filters": {
    "workflow_types": ["PRD Creation", "Architecture", "Story Implementation"],
    "date_range": {"min": "2025-01-01", "max": "2025-01-17"},
    "statuses": ["pending", "running", "completed", "failed", "cancelled"]
  }
}
```

**Data Source**:
- Query `WorkflowExecution` records from `.gao-dev/documents.db`
- Use `GitIntegratedStateManager.query_workflows()`
- Calculate duration: `completed_at - started_at` (if completed)
- Extract agent from workflow execution metadata

**Status Mapping**:
- `started` → `pending` (not yet running)
- `running` → `running` (in progress)
- `completed` → `completed` (success)
- `failed` → `failed` (error)
- `cancelled` → `cancelled` (user-terminated)

### Frontend Implementation

**Components Created**:

1. **WorkflowTimeline.tsx** (180 lines)
   - Timeline visualization using horizontal bars
   - X-axis: Time (hours/days, auto-scaled)
   - Y-axis: Workflow name + workflow_id
   - Scrollable container with virtual scrolling (react-window or @tanstack/react-virtual)
   - Color-coded bars by status
   - Hover tooltips showing workflow details
   - Click handler to open detail panel

2. **TimelineFilters.tsx** (90 lines)
   - Workflow type dropdown (Select component from shadcn/ui)
   - Date range picker (Calendar component from shadcn/ui)
   - Status multi-select (Checkbox group)
   - "Clear Filters" button
   - Filter state managed in workflowStore

3. **WorkflowBar.tsx** (60 lines)
   - Single workflow bar component
   - Width proportional to duration
   - Status-based background color
   - Hover effect: elevation shadow + border highlight
   - Accessible: role="button", tabIndex, aria-label

**State Management**:
```typescript
interface WorkflowTimelineState {
  workflows: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  filters: {
    workflowType: string | null;
    startDate: Date | null;
    endDate: Date | null;
    statuses: string[];
  };
  fetchTimeline: () => Promise<void>;
  applyFilters: (filters: Filters) => void;
  clearFilters: () => void;
  selectWorkflow: (workflowId: string) => void;
  selectedWorkflowId: string | null;
}
```

**Timeline Visualization Library**:
- Option 1: Custom D3.js implementation (full control)
- Option 2: vis-timeline (battle-tested, feature-rich)
- Option 3: react-calendar-timeline (React-native)
- **Recommended**: vis-timeline or custom D3.js for Gantt-style visualization

**Color Palette**:
- Pending: `bg-gray-400` (#9CA3AF)
- Running: `bg-blue-500` (#3B82F6)
- Completed: `bg-green-500` (#10B981)
- Failed: `bg-red-500` (#EF4444)
- Cancelled: `bg-orange-500` (#F59E0B)

### WebSocket Integration

**Events**:
- `workflow.started`: New workflow execution started
- `workflow.completed`: Workflow finished successfully
- `workflow.failed`: Workflow failed with error
- `workflow.cancelled`: Workflow cancelled by user
- `workflow.status_changed`: Generic status change event

**Event Payload**:
```typescript
{
  type: 'workflow.started',
  data: {
    workflow_id: 'wf-123',
    workflow_name: 'PRD Creation',
    agent: 'John',
    started_at: '2025-01-16T10:00:00Z'
  }
}
```

**Frontend Handling**:
- Listen to workflow events in `workflowStore`
- Update timeline state in real-time
- Auto-scroll to new workflows if user is at bottom
- Show toast notification for completed/failed workflows

### Performance Optimization

**Virtual Scrolling**:
- Render only visible workflow bars (viewport + buffer)
- Use `react-window` or `@tanstack/react-virtual`
- Item height: 60px (workflow bar + spacing)
- Viewport height: 600px (10 visible items)
- Buffer: 5 items above/below viewport

**Caching**:
- Cache timeline data in Zustand store
- Invalidate cache on workflow events
- Refresh interval: 30 seconds (for pending workflows)

**Load Time Targets**:
- API response: <200ms for 100 workflows
- Initial render: <500ms
- Filter application: <100ms
- Real-time update: <50ms

### Accessibility

**ARIA Attributes**:
- Timeline container: `role="region"`, `aria-label="Workflow Timeline"`
- Workflow bar: `role="button"`, `aria-label="[workflow_name] - [status] - [duration]"`
- Filter controls: `aria-label` on each input

**Keyboard Navigation**:
- Tab: Focus workflow bars sequentially
- Enter/Space: Open workflow detail panel
- Arrow keys: Navigate between workflow bars
- Escape: Close detail panel

**Screen Reader Support**:
- Announce workflow count: "Showing 23 workflows"
- Announce filter changes: "Filtered by status: completed"
- Announce status changes: "Workflow [name] completed in 5 minutes"

### Dependencies

**NPM Packages**:
```json
{
  "vis-timeline": "^7.7.3",  // Timeline visualization (Option 2)
  "date-fns": "^2.30.0",     // Date formatting
  "@tanstack/react-virtual": "^3.0.0"  // Virtual scrolling (if not using vis-timeline)
}
```

**Backend Dependencies**:
- Epic 39.1: Backend Foundation (FastAPI)
- Epic 27: GitIntegratedStateManager (WorkflowExecution queries)
- WorkflowExecutor: Workflow event emission

**Frontend Dependencies**:
- Epic 39.2: Frontend Foundation (React, Zustand)
- Epic 39.1: WebSocket Event Bus
- shadcn/ui: Select, Calendar, Checkbox components

### Testing

**Unit Tests**: `tests/e2e/test_workflow_timeline.py` (12 tests)
1. GET /api/workflows/timeline endpoint registration
2. Timeline returns empty array when no workflows
3. Timeline returns workflows with all required fields
4. Timeline filters by workflow_type
5. Timeline filters by date_range
6. Timeline filters by status
7. Timeline calculates duration correctly
8. Timeline handles incomplete workflows (running, no completed_at)
9. Frontend store structure validation
10. Filter state management
11. Real-time WebSocket updates
12. All 12 acceptance criteria validated

**Test Coverage**: >95% of new code

**E2E Tests**: Manual validation via browser
- Load timeline with 100+ workflows
- Apply each filter type
- Verify real-time updates when workflow completes
- Test keyboard navigation
- Test screen reader announcements
- Verify performance with 1000+ workflows (virtual scrolling)

### Performance

- Timeline load time: <300ms (100 workflows)
- Filter application: <50ms
- Real-time update: <20ms
- Virtual scrolling: 60fps for 10,000+ workflows
- Memory usage: <10MB for 1000 workflows

## Dependencies

- Story 39.1-39.4: Core infrastructure (backend, frontend, WebSocket)
- Epic 27: WorkflowExecution model and GitIntegratedStateManager
- WorkflowExecutor: Workflow event emission

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] GET /api/workflows/timeline endpoint implemented with filtering
- [ ] WorkflowTimeline component renders horizontal bars on time axis
- [ ] TimelineFilters component with all filter types (workflow type, date range, status)
- [ ] Color-coded workflow bars by status
- [ ] Real-time updates via WebSocket events
- [ ] Virtual scrolling for 1000+ workflows
- [ ] Keyboard navigation functional
- [ ] Screen reader support verified
- [ ] ARIA labels on all interactive elements
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
