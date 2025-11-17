# Story 39.23: Workflow Metrics Dashboard

**Epic**: 39.6 - Workflow Visualization
**Story Points**: 3
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING

---

## Description

As a **project manager**, I want to **see aggregate workflow metrics and analytics** so that **I can identify bottlenecks and measure team productivity**.

## Acceptance Criteria

1. **AC1**: GET /api/workflows/metrics endpoint returns aggregate statistics (success rate, average duration, agent utilization, failure analysis)
2. **AC2**: Metrics dashboard displays overall success rate as percentage with color coding (green >90%, yellow 70-90%, red <70%)
3. **AC3**: Average duration by workflow type shown as bar chart (X-axis: workflow type, Y-axis: average duration in minutes)
4. **AC4**: Agent utilization chart shows number of workflows executed by each agent (pie chart or bar chart)
5. **AC5**: Top 10 longest-running workflows displayed as table with workflow name, duration, status
6. **AC6**: Failure analysis section shows common failure points (which workflows fail most, which steps fail most)
7. **AC7**: Workflow count over time shown as line chart (X-axis: date, Y-axis: workflow count)
8. **AC8**: All charts support hover tooltips with detailed values
9. **AC9**: Metrics auto-refresh every 60 seconds (configurable interval)
10. **AC10**: Date range filter allows filtering metrics by time period (last 7 days, last 30 days, all time, custom range)
11. **AC11**: Export metrics as CSV button downloads metrics data
12. **AC12**: Accessibility: ARIA labels on charts, keyboard navigation, screen reader support with data tables

## Technical Notes

### Backend Implementation

**File**: `gao_dev/web/server.py`

**Endpoint**: `GET /api/workflows/metrics`

**Query Parameters**:
- `start_date` (optional): ISO 8601 date string (e.g., "2025-01-01T00:00:00Z")
- `end_date` (optional): ISO 8601 date string
- `epic` (optional): Filter by epic number

**Response Structure**:
```json
{
  "summary": {
    "total_workflows": 156,
    "completed": 142,
    "failed": 8,
    "cancelled": 3,
    "running": 2,
    "pending": 1,
    "success_rate": 91.03,  // (completed / (completed + failed + cancelled)) * 100
    "average_duration": 1247.5,  // seconds
    "total_duration": 195262  // seconds (cumulative)
  },
  "workflow_type_metrics": [
    {
      "workflow_type": "PRD Creation",
      "count": 12,
      "average_duration": 318.5,
      "success_rate": 100.0,
      "min_duration": 245,
      "max_duration": 412
    },
    {
      "workflow_type": "Story Implementation",
      "count": 85,
      "average_duration": 2145.3,
      "success_rate": 88.2,
      "min_duration": 890,
      "max_duration": 5420
    }
  ],
  "agent_utilization": [
    {
      "agent": "Amelia",
      "workflow_count": 92,
      "total_duration": 174523,  // seconds
      "percentage": 59.0  // of total workflows
    },
    {
      "agent": "John",
      "workflow_count": 15,
      "total_duration": 5245,
      "percentage": 9.6
    }
  ],
  "longest_workflows": [
    {
      "workflow_id": "wf-45",
      "workflow_name": "Story Implementation",
      "duration": 5420,  // seconds (90 minutes)
      "status": "completed",
      "agent": "Amelia",
      "started_at": "2025-01-15T14:23:10Z"
    }
  ],  // Top 10
  "failure_analysis": {
    "most_failed_workflows": [
      {
        "workflow_type": "Test Execution",
        "failure_count": 5,
        "total_count": 18,
        "failure_rate": 27.8
      }
    ],
    "most_failed_steps": [
      {
        "step_name": "Run TypeScript compiler",
        "failure_count": 12,
        "error_message": "Type errors found"
      }
    ],
    "common_errors": [
      {
        "error_message": "Module not found",
        "count": 8
      }
    ]
  },
  "workflows_over_time": [
    {
      "date": "2025-01-10",
      "completed": 8,
      "failed": 1,
      "cancelled": 0
    },
    {
      "date": "2025-01-11",
      "completed": 12,
      "failed": 0,
      "cancelled": 0
    }
  ]  // Daily aggregation
}
```

**Data Aggregation**:
- Query all `WorkflowExecution` records in date range
- Calculate success rate: `completed / (completed + failed + cancelled) * 100`
- Calculate average duration: `SUM(duration) / COUNT(*)`
- Group by workflow_type for type-specific metrics
- Group by agent for utilization metrics
- Group by date for time series
- Parse error messages from failed workflow results

**Performance**:
- Cache metrics for 60 seconds (avoid recalculating on every request)
- Use database indexes on `started_at`, `status`, `workflow_name`
- Paginate longest_workflows (top 10)

### Frontend Implementation

**Components Created**:

1. **MetricsDashboard.tsx** (180 lines)
   - Grid layout with metric cards and charts
   - Auto-refresh every 60 seconds
   - Date range filter dropdown
   - Export CSV button
   - Loading state with skeleton loaders

2. **SummaryMetrics.tsx** (80 lines)
   - Four metric cards: Total Workflows, Success Rate, Avg Duration, Total Duration
   - Success rate color coding (green/yellow/red)
   - Animated counter for numbers (count-up effect)
   - Icons for each metric

3. **WorkflowTypeChart.tsx** (90 lines)
   - Bar chart using recharts library
   - X-axis: Workflow type names
   - Y-axis: Average duration (minutes)
   - Tooltip: Shows exact duration and success rate
   - Responsive: scales to container width

4. **AgentUtilizationChart.tsx** (70 lines)
   - Pie chart or bar chart (user toggle)
   - Shows agent names and workflow counts
   - Color-coded segments
   - Tooltip: Shows count and percentage

5. **LongestWorkflowsTable.tsx** (100 lines)
   - Table component (shadcn/ui Table)
   - Columns: Workflow Name, Duration, Status, Agent, Started At
   - Duration formatted as "1h 30m 20s"
   - Status badge with color coding
   - Click row to open workflow detail panel

6. **FailureAnalysisSection.tsx** (120 lines)
   - Three subsections: Most Failed Workflows, Most Failed Steps, Common Errors
   - Bar charts for failure rates
   - Alert component for critical failure rate (>30%)
   - Copy error message button

7. **WorkflowsOverTimeChart.tsx** (80 lines)
   - Line chart using recharts
   - X-axis: Dates
   - Y-axis: Workflow count
   - Three lines: Completed (green), Failed (red), Cancelled (orange)
   - Tooltip: Shows counts for each status

**Chart Library**: recharts

**Why recharts?**
- React-native, declarative API
- Excellent TypeScript support
- Built-in responsive behavior
- Accessible (ARIA labels)
- Wide adoption, good docs

**State Management**:
```typescript
interface MetricsState {
  summary: MetricsSummary;
  workflowTypeMetrics: WorkflowTypeMetrics[];
  agentUtilization: AgentUtilization[];
  longestWorkflows: WorkflowRecord[];
  failureAnalysis: FailureAnalysis;
  workflowsOverTime: TimeSeriesData[];
  loading: boolean;
  error: string | null;
  dateRange: DateRange;
  autoRefresh: boolean;
  refreshInterval: number;  // seconds
  fetchMetrics: () => Promise<void>;
  setDateRange: (range: DateRange) => void;
  exportCSV: () => void;
}
```

**Color Palette**:
- Success rate green: `#10B981` (green-500)
- Success rate yellow: `#F59E0B` (yellow-500)
- Success rate red: `#EF4444` (red-500)
- Chart colors: Palette of 8 distinct colors for bars/segments

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

**Auto-Refresh**:
```typescript
useEffect(() => {
  if (!autoRefresh) return;

  const interval = setInterval(() => {
    fetchMetrics();
  }, refreshInterval * 1000);

  return () => clearInterval(interval);
}, [autoRefresh, refreshInterval]);
```

**CSV Export**:
```typescript
function exportCSV() {
  const csv = [
    ['Metric', 'Value'],
    ['Total Workflows', summary.total_workflows],
    ['Success Rate', `${summary.success_rate}%`],
    ['Average Duration', formatDuration(summary.average_duration)],
    // ... more rows
  ].map(row => row.join(',')).join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `workflow-metrics-${new Date().toISOString()}.csv`;
  a.click();
}
```

### Date Range Filter

**Presets**:
- Last 7 days
- Last 30 days
- Last 90 days
- All time
- Custom range (date picker)

**Implementation**:
```typescript
const dateRangePresets = [
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
  { label: 'All time', days: null },
  { label: 'Custom', days: 'custom' }
];

function applyDateRange(preset: DateRangePreset) {
  if (preset.days === null) {
    setDateRange({ start: null, end: null });
  } else if (preset.days === 'custom') {
    // Open date picker modal
  } else {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - preset.days);
    setDateRange({ start, end });
  }
  fetchMetrics();
}
```

### Accessibility

**ARIA Attributes**:
- Dashboard: `role="region"`, `aria-label="Workflow Metrics Dashboard"`
- Charts: `role="img"`, `aria-label="[chart description]"`
- Metric cards: `role="article"`, `aria-label="[metric name]: [value]"`
- Tables: `role="table"`, proper `<thead>`, `<tbody>`, `<th>`, `<td>`

**Keyboard Navigation**:
- Tab: Navigate through metric cards, charts, tables
- Enter: Activate date range filter, export button
- Arrow keys: Navigate table rows

**Screen Reader Support**:
- Provide data tables as fallback for charts
- Announce metric values: "Success rate is 91 percent"
- Announce chart tooltips on hover

**Data Table Fallback**:
- Hidden `<table>` elements for each chart
- Screen readers can access raw data
- Export CSV provides data export

### Dependencies

**NPM Packages**:
```json
{
  "recharts": "^2.10.0",       // Chart library
  "date-fns": "^2.30.0",       // Date formatting
  "papaparse": "^5.4.1"        // CSV parsing/export (optional)
}
```

**Backend Dependencies**:
- Story 39.20: Workflow timeline data
- Epic 27: WorkflowExecution model

**Frontend Dependencies**:
- Story 39.21: Workflow detail panel (integration)
- Epic 39.2: Frontend Foundation
- shadcn/ui: Card, Table, Badge, Button, Select components

### Testing

**Unit Tests**: `tests/e2e/test_workflow_metrics.py` (12 tests)
1. GET /api/workflows/metrics endpoint registration
2. Metrics calculation correctness (success rate, avg duration)
3. Workflow type aggregation
4. Agent utilization calculation
5. Longest workflows query (top 10)
6. Failure analysis data structure
7. Time series aggregation (daily)
8. Date range filtering
9. Frontend metrics rendering
10. CSV export functionality
11. Auto-refresh mechanism
12. All 12 acceptance criteria validated

**Test Coverage**: >95% of new code

**E2E Tests**: Manual validation
- Load dashboard with 100+ workflows
- Verify all charts render correctly
- Hover over charts, check tooltips
- Apply each date range filter
- Export CSV, verify data correctness
- Wait 60 seconds, verify auto-refresh
- Click longest workflow, verify detail panel opens
- Test keyboard navigation
- Test screen reader announcements

### Performance

- Metrics fetch time: <300ms (aggregating 1000 workflows)
- Dashboard render time: <500ms
- Chart render time: <200ms per chart
- CSV export time: <100ms
- Auto-refresh overhead: <50ms

## Dependencies

- Story 39.20: Workflow Execution Timeline (data source)
- Story 39.21: Workflow Detail Panel (integration)
- Epic 27: WorkflowExecution model

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] GET /api/workflows/metrics endpoint implemented
- [ ] Metrics calculation algorithms implemented (success rate, avg duration, agent utilization)
- [ ] MetricsDashboard component with 7 sub-components
- [ ] All charts implemented using recharts
- [ ] Date range filter functional
- [ ] Auto-refresh every 60 seconds
- [ ] CSV export functional
- [ ] Keyboard navigation verified
- [ ] ARIA labels on all charts and metrics
- [ ] Screen reader support verified (data table fallback)
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
