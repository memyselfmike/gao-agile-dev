/**
 * Workflow Store - State management for workflow timeline visualization
 *
 * Story 39.20: Workflow Execution Timeline
 * Story 39.21: Workflow Detail Panel
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

// Workflow step type (Story 39.21)
export interface WorkflowStep {
  name: string;
  status: 'completed' | 'pending' | 'failed';
  started_at: string;
  completed_at: string | null;
  duration: number | null;
  tool_calls: Array<{
    tool: string;
    args: Record<string, any>;
  }>;
  outputs: string[];
}

// Workflow artifact type (Story 39.21)
export interface WorkflowArtifact {
  path: string;
  type: string;
  size: number;
  created_at: string;
}

// Workflow error type (Story 39.21)
export interface WorkflowError {
  timestamp: string;
  message: string;
  stack_trace: string;
  step: string;
}

// Workflow details type (Story 39.21)
export interface WorkflowDetails {
  workflow: WorkflowExecution;
  steps: WorkflowStep[];
  variables: Record<string, any>;
  artifacts: WorkflowArtifact[];
  errors: WorkflowError[] | null;
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
  workflowDetails: WorkflowDetails | null;
  detailsLoading: boolean;
  detailsError: string | null;

  // Filters
  filters: TimelineFilters;

  // Actions
  fetchTimeline: () => Promise<void>;
  applyFilters: (filters: Partial<TimelineFilters>) => void;
  clearFilters: () => void;
  selectWorkflow: (workflowId: string | null) => void;
  fetchDetails: (workflowId: string) => Promise<void>;
  closePanel: () => void;
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
  workflowDetails: null,
  detailsLoading: false,
  detailsError: null,
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
    // Auto-fetch details when workflow is selected
    if (workflowId) {
      get().fetchDetails(workflowId);
    }
  },

  fetchDetails: async (workflowId: string) => {
    set({ detailsLoading: true, detailsError: null });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
      const url = `${apiUrl}/api/workflows/${workflowId}/details`;

      const response = await fetch(url, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Workflow ${workflowId} not found`);
        }
        throw new Error(`Failed to fetch workflow details: ${response.statusText}`);
      }

      const data = (await response.json()) as WorkflowDetails;

      set({
        workflowDetails: data,
        detailsLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({
        detailsError: errorMessage,
        detailsLoading: false,
        workflowDetails: null,
      });
    }
  },

  closePanel: () => {
    set({
      selectedWorkflowId: null,
      workflowDetails: null,
      detailsError: null,
    });
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
