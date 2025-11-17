/**
 * Workflow Store - State management for workflow timeline visualization
 *
 * Story 39.20: Workflow Execution Timeline
 */
import { create } from 'zustand';

// Workflow execution types
export interface WorkflowExecution {
  id: number;
  workflow_id: string;
  workflow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string; // ISO 8601
  completed_at: string | null; // ISO 8601
  duration: number | null; // seconds
  agent: string;
  epic: number;
  story_num: number;
}

// Filter state
export interface TimelineFilters {
  workflowType: string | null;
  startDate: Date | null;
  endDate: Date | null;
  statuses: string[];
}

// Timeline metadata
export interface TimelineMetadata {
  workflow_types: string[];
  date_range: {
    min: string | null;
    max: string | null;
  };
  statuses: string[];
}

// Workflow timeline state
interface WorkflowTimelineState {
  // Data
  workflows: WorkflowExecution[];
  metadata: TimelineMetadata | null;
  loading: boolean;
  error: string | null;

  // Selected workflow for detail panel (Story 39.21)
  selectedWorkflowId: string | null;

  // Filters
  filters: TimelineFilters;

  // Actions
  fetchTimeline: () => Promise<void>;
  applyFilters: (filters: Partial<TimelineFilters>) => void;
  clearFilters: () => void;
  selectWorkflow: (workflowId: string | null) => void;
  clearError: () => void;
  reset: () => void;

  // Real-time updates (WebSocket)
  addWorkflow: (workflow: WorkflowExecution) => void;
  updateWorkflow: (workflowId: string, updates: Partial<WorkflowExecution>) => void;
}

const initialFilters: TimelineFilters = {
  workflowType: null,
  startDate: null,
  endDate: null,
  statuses: [],
};

const initialState = {
  workflows: [],
  metadata: null,
  loading: false,
  error: null,
  selectedWorkflowId: null,
  filters: initialFilters,
};

export const useWorkflowStore = create<WorkflowTimelineState>((set, get) => ({
  ...initialState,

  fetchTimeline: async () => {
    set({ loading: true, error: null });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
      const { filters } = get();

      // Build query parameters
      const params = new URLSearchParams();

      if (filters.workflowType) {
        params.append('workflow_type', filters.workflowType);
      }

      if (filters.startDate) {
        params.append('start_date', filters.startDate.toISOString());
      }

      if (filters.endDate) {
        params.append('end_date', filters.endDate.toISOString());
      }

      if (filters.statuses.length > 0) {
        params.append('status', filters.statuses.join(','));
      }

      const url = `${apiUrl}/api/workflows/timeline?${params.toString()}`;
      const response = await fetch(url, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch timeline: ${response.statusText}`);
      }

      const data = (await response.json()) as {
        workflows: WorkflowExecution[];
        total: number;
        filters: TimelineMetadata;
      };

      set({
        workflows: data.workflows,
        metadata: data.filters,
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

  applyFilters: (newFilters: Partial<TimelineFilters>) => {
    set((state) => ({
      filters: {
        ...state.filters,
        ...newFilters,
      },
    }));

    // Auto-fetch with new filters
    get().fetchTimeline();
  },

  clearFilters: () => {
    set({ filters: initialFilters });
    get().fetchTimeline();
  },

  selectWorkflow: (workflowId: string | null) => {
    set({ selectedWorkflowId: workflowId });
  },

  clearError: () => set({ error: null }),

  reset: () => set(initialState),

  // Real-time updates via WebSocket
  addWorkflow: (workflow: WorkflowExecution) => {
    set((state) => ({
      workflows: [workflow, ...state.workflows],
    }));
  },

  updateWorkflow: (workflowId: string, updates: Partial<WorkflowExecution>) => {
    set((state) => ({
      workflows: state.workflows.map((wf) =>
        wf.workflow_id === workflowId ? { ...wf, ...updates } : wf
      ),
    }));
  },
}));
