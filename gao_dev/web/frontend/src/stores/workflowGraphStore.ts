/**
 * Workflow Graph Store - State management for workflow dependency graph
 *
 * Story 39.22: Workflow Dependency Graph
 */
import { create } from 'zustand';

// Define node and edge types for vis-network compatibility
export interface GraphNode {
  id: string;
  data: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  data?: Record<string, unknown>;
}

// Workflow graph group
export interface WorkflowGroup {
  id: string;
  label: string;
  nodes: string[];
  collapsed: boolean;
}

// Layout direction
export type LayoutDirection = 'TB' | 'LR';

// Workflow graph state
interface WorkflowGraphState {
  // Data
  nodes: GraphNode[];
  edges: GraphEdge[];
  groups: WorkflowGroup[];
  criticalPath: string[];
  loading: boolean;
  error: string | null;

  // View state
  layout: LayoutDirection;
  selectedNode: string | null;

  // Actions
  fetchGraph: (epic?: number, storyNum?: number, includeCompleted?: boolean) => Promise<void>;
  setLayout: (layout: LayoutDirection) => void;
  toggleGroup: (groupId: string) => void;
  selectNode: (nodeId: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  nodes: [],
  edges: [],
  groups: [],
  criticalPath: [],
  loading: false,
  error: null,
  layout: 'TB' as LayoutDirection,
  selectedNode: null,
};

export const useWorkflowGraphStore = create<WorkflowGraphState>((set) => ({
  ...initialState,

  fetchGraph: async (epic?: number, storyNum?: number, includeCompleted: boolean = true) => {
    set({ loading: true, error: null });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

      // Build query params
      const params = new URLSearchParams();
      if (epic !== undefined) params.append('epic', epic.toString());
      if (storyNum !== undefined) params.append('story_num', storyNum.toString());
      params.append('include_completed', includeCompleted.toString());

      const response = await fetch(`${apiUrl}/api/workflows/graph?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch graph: ${response.statusText}`);
      }

      const data = (await response.json()) as {
        nodes: any[];
        edges: any[];
        groups: WorkflowGroup[];
        critical_path: string[];
      };

      // Transform nodes to graph format
      const nodes: GraphNode[] = data.nodes.map((node) => ({
        id: node.id,
        data: {
          label: node.label,
          status: node.status,
          duration: node.duration,
          agent: node.agent,
          epic: node.epic,
          storyNum: node.story_num,
          workflowId: node.data.workflow_id,
          workflowName: node.data.workflow_name,
          startedAt: node.data.started_at,
          completedAt: node.data.completed_at,
          isOnCriticalPath: data.critical_path.includes(node.id),
        },
      }));

      // Transform edges to graph format
      const edges: GraphEdge[] = data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        data: {
          label: edge.label,
          isOnCriticalPath:
            data.critical_path.includes(edge.source) && data.critical_path.includes(edge.target),
        },
      }));

      set({
        nodes,
        edges,
        groups: data.groups,
        criticalPath: data.critical_path,
        loading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({
        error: errorMessage,
        loading: false,
      });
    }
  },

  setLayout: (layout: LayoutDirection) => set({ layout }),

  toggleGroup: (groupId: string) => {
    set((state) => ({
      groups: state.groups.map((g) =>
        g.id === groupId ? { ...g, collapsed: !g.collapsed } : g
      ),
    }));
  },

  selectNode: (nodeId: string | null) => set({ selectedNode: nodeId }),

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));
