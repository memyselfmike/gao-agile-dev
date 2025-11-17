# Story 39.22: Workflow Dependency Graph

**Epic**: 39.6 - Workflow Visualization
**Story Points**: 5
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING

---

## Description

As a **technical architect**, I want to **see a directed acyclic graph (DAG) of workflow dependencies** so that **I can understand workflow execution order and identify critical paths**.

## Acceptance Criteria

1. **AC1**: GET /api/workflows/graph endpoint returns workflow nodes with dependencies (edges) as DAG structure
2. **AC2**: DAG visualization displays workflows as nodes with title, status color, and duration badge
3. **AC3**: Edges (arrows) connect workflows showing execution order (prerequisite → dependent workflow)
4. **AC4**: Nodes are color-coded by status (pending=gray, running=blue, completed=green, failed=red, cancelled=orange)
5. **AC5**: Interactive graph: drag nodes, zoom with mouse wheel, pan with click-and-drag
6. **AC6**: Nodes are auto-laid out using hierarchical layout algorithm (top-to-bottom or left-to-right)
7. **AC7**: Critical path highlighting: longest sequence of workflows from start to finish displayed in bold edges
8. **AC8**: Parallel workflows displayed side-by-side at same hierarchical level
9. **AC9**: Click node to open workflow detail panel (Story 39.21)
10. **AC10**: Collapsible workflow groups: Click epic node to expand/collapse all workflows in that epic
11. **AC11**: Layout toggle: Switch between top-to-bottom (TB) and left-to-right (LR) layouts
12. **AC12**: Accessibility: Keyboard navigation (Tab to focus nodes, Arrow keys to traverse graph), ARIA labels, screen reader support

## Technical Notes

### Backend Implementation

**File**: `gao_dev/web/server.py`

**Endpoint**: `GET /api/workflows/graph`

**Query Parameters**:
- `epic` (optional): Filter by epic number
- `story_num` (optional): Filter by story number
- `include_completed` (default: true): Include completed workflows

**Response Structure**:
```json
{
  "nodes": [
    {
      "id": "wf-1",
      "label": "PRD Creation",
      "type": "workflow",
      "status": "completed",
      "duration": 323,
      "agent": "John",
      "epic": 39,
      "story_num": null,
      "data": {
        "workflow_id": "wf-1",
        "workflow_name": "PRD Creation",
        "started_at": "2025-01-16T10:00:00Z",
        "completed_at": "2025-01-16T10:05:23Z"
      }
    },
    {
      "id": "wf-2",
      "label": "Architecture Design",
      "type": "workflow",
      "status": "completed",
      "duration": 456,
      "agent": "Winston",
      "epic": 39,
      "story_num": null,
      "data": { ... }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "wf-1",
      "target": "wf-2",
      "label": "prerequisite",
      "type": "dependency"
    }
  ],
  "groups": [
    {
      "id": "epic-39",
      "label": "Epic 39: Web Interface",
      "nodes": ["wf-1", "wf-2", "wf-3"],
      "collapsed": false
    }
  ],
  "critical_path": ["wf-1", "wf-2", "wf-5", "wf-8"]  // Longest sequence
}
```

**Dependency Detection**:
- Parse workflow execution order from timestamps
- Detect dependencies from workflow variables (e.g., `prd_location` → PRD workflow)
- Use WorkflowExecutor's prerequisite definitions
- Calculate critical path using longest path algorithm

**Critical Path Algorithm**:
```python
def calculate_critical_path(nodes, edges):
    # Topological sort + longest path (max duration sum)
    # Returns list of workflow IDs on critical path
```

### Frontend Implementation

**Components Created**:

1. **WorkflowGraph.tsx** (250 lines)
   - DAG visualization using @xyflow/react (formerly react-flow)
   - Custom node components for workflows
   - Custom edge components with arrows
   - Auto-layout using Dagre algorithm
   - Interactive: drag, zoom, pan
   - Critical path highlighting
   - Layout toggle button (TB/LR)

2. **WorkflowNode.tsx** (120 lines)
   - Custom node component
   - Displays workflow name, status icon, duration badge
   - Color-coded border by status
   - Hover effect: elevation shadow
   - Click handler to open detail panel
   - Handle for connecting edges

3. **WorkflowEdge.tsx** (60 lines)
   - Custom edge component with arrow
   - Bold style for critical path edges
   - Animated edge for running workflows
   - Label: "prerequisite" or dependency type

4. **GraphControls.tsx** (80 lines)
   - Layout toggle (TB/LR buttons)
   - Zoom controls (+/- buttons)
   - Fit view button (auto-zoom to fit all nodes)
   - Download as PNG button
   - Collapse all / Expand all groups

5. **GraphLegend.tsx** (40 lines)
   - Color legend for node statuses
   - Icon legend for edge types
   - Critical path explanation

**Graph Library**: @xyflow/react

**Why @xyflow/react?**
- Battle-tested for DAG visualization
- Built-in support for custom nodes/edges
- Auto-layout via Dagre
- Interactive features (drag, zoom, pan)
- TypeScript support
- Excellent documentation

**Auto-Layout Algorithm**: Dagre

**Layout Configuration**:
```typescript
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));
dagreGraph.setGraph({
  rankdir: direction,  // 'TB' or 'LR'
  nodesep: 80,         // Horizontal spacing
  ranksep: 120         // Vertical spacing
});

nodes.forEach(node => {
  dagreGraph.setNode(node.id, { width: 200, height: 80 });
});

edges.forEach(edge => {
  dagreGraph.setEdge(edge.source, edge.target);
});

dagre.layout(dagreGraph);

// Apply calculated positions to React Flow nodes
```

**State Management**:
```typescript
interface WorkflowGraphState {
  nodes: Node[];
  edges: Edge[];
  groups: Group[];
  criticalPath: string[];
  loading: boolean;
  error: string | null;
  layout: 'TB' | 'LR';
  fetchGraph: (epic?: number, storyNum?: number) => Promise<void>;
  setLayout: (layout: 'TB' | 'LR') => void;
  toggleGroup: (groupId: string) => void;
  selectNode: (nodeId: string) => void;
}
```

**Node Color Mapping**:
```typescript
const nodeColors = {
  pending: '#9CA3AF',    // gray-400
  running: '#3B82F6',    // blue-500
  completed: '#10B981',  // green-500
  failed: '#EF4444',     // red-500
  cancelled: '#F59E0B'   // orange-500
};
```

**Critical Path Highlighting**:
- Edges on critical path: `strokeWidth: 3`, `stroke: '#6366F1'` (indigo-500)
- Nodes on critical path: `borderWidth: 3`, `borderColor: '#6366F1'`
- Label badge: "Critical Path" (yellow badge)

### Collapsible Groups

**Epic Grouping**:
- Group workflows by epic
- Epic node: rounded rectangle with epic number and title
- Click epic node to collapse/expand
- Collapsed: show count badge ("5 workflows")
- Expanded: show all workflows as child nodes

**Implementation**:
```typescript
// Collapsed epic node
{
  id: 'epic-39',
  type: 'epicGroup',
  data: { label: 'Epic 39', count: 5, collapsed: true },
  position: { x: 100, y: 100 }
}

// Expanded: replace epic node with workflow child nodes
```

### Accessibility

**ARIA Attributes**:
- Graph container: `role="img"`, `aria-label="Workflow dependency graph"`
- Nodes: `role="button"`, `aria-label="[workflow_name] - [status]"`
- Edges: `aria-hidden="true"` (decorative)

**Keyboard Navigation**:
- Tab: Focus next node
- Shift+Tab: Focus previous node
- Arrow keys: Traverse graph (follow edges)
- Enter: Open workflow detail panel
- +/-: Zoom in/out
- Space: Toggle node group collapse

**Screen Reader Support**:
- Announce node count: "Graph has 15 workflows"
- Announce critical path: "Critical path includes 5 workflows"
- Announce node focus: "Focused on [workflow_name], status [status]"

### Dependencies

**NPM Packages**:
```json
{
  "@xyflow/react": "^12.0.0",  // DAG visualization (formerly react-flow)
  "dagre": "^0.8.5",           // Auto-layout algorithm
  "@types/dagre": "^0.7.52",   // TypeScript types
  "html-to-image": "^1.11.11"  // Download as PNG
}
```

**Backend Dependencies**:
- Story 39.20: Workflow timeline data
- Epic 27: WorkflowExecution model
- WorkflowExecutor: Prerequisite definitions

**Frontend Dependencies**:
- Story 39.21: Workflow detail panel (integration)
- Epic 39.2: Frontend Foundation
- shadcn/ui: Button, Badge, Tooltip components

### Testing

**Unit Tests**: `tests/e2e/test_workflow_graph.py` (12 tests)
1. GET /api/workflows/graph endpoint registration
2. Graph returns nodes and edges
3. Dependency detection from workflow order
4. Critical path calculation correctness
5. Graph grouping by epic
6. Frontend node rendering
7. Frontend edge rendering
8. Auto-layout algorithm applied
9. Critical path highlighting functional
10. Collapsible groups functional
11. Keyboard navigation works
12. All 12 acceptance criteria validated

**Test Coverage**: >95% of new code

**E2E Tests**: Manual validation
- Load graph with 20+ workflows
- Verify auto-layout (no overlapping nodes)
- Drag nodes, verify position updates
- Zoom in/out, verify graph scales
- Click node, verify detail panel opens
- Toggle layout (TB → LR), verify re-layout
- Collapse epic group, verify workflows hidden
- Verify critical path highlighted
- Test keyboard navigation (Tab, Arrow keys)
- Test screen reader announcements

### Performance

- Graph render time: <500ms (50 nodes, 80 edges)
- Auto-layout time: <200ms
- Drag performance: 60fps
- Zoom/pan performance: 60fps
- Memory usage: <20MB for 100 nodes

### Alternative Libraries Considered

1. **D3.js** (Low-level)
   - Pros: Full control, highly customizable
   - Cons: Steep learning curve, manual implementation of zoom/pan/drag

2. **vis-network** (Mid-level)
   - Pros: Simple API, good for small graphs
   - Cons: Limited customization, physics-based layout (not hierarchical)

3. **@xyflow/react** (High-level) **← RECOMMENDED**
   - Pros: React-native, Dagre integration, excellent docs, TypeScript support
   - Cons: Larger bundle size (~100KB)

**Decision**: @xyflow/react for rapid development and excellent UX.

## Dependencies

- Story 39.20: Workflow Execution Timeline (data source)
- Story 39.21: Workflow Detail Panel (integration)
- Epic 27: WorkflowExecution model
- WorkflowExecutor: Prerequisite definitions

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] GET /api/workflows/graph endpoint implemented
- [ ] Dependency detection algorithm implemented
- [ ] Critical path calculation implemented
- [ ] WorkflowGraph component with @xyflow/react
- [ ] Auto-layout using Dagre algorithm
- [ ] Custom WorkflowNode and WorkflowEdge components
- [ ] Interactive features (drag, zoom, pan) functional
- [ ] Critical path highlighting functional
- [ ] Collapsible epic groups functional
- [ ] Layout toggle (TB/LR) functional
- [ ] Keyboard navigation verified
- [ ] ARIA labels on all nodes
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
