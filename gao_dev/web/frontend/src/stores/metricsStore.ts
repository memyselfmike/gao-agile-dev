/**
 * Metrics Store - State management for workflow metrics dashboard
 *
 * Story 39.23: Workflow Metrics Dashboard
 */
import { create } from 'zustand';

// Type definitions
export interface MetricsSummary {
  total_workflows: number;
  completed: number;
  failed: number;
  cancelled: number;
  running: number;
  pending: number;
  success_rate: number;
  average_duration: number;
  total_duration: number;
}

export interface WorkflowTypeMetrics {
  workflow_type: string;
  count: number;
  average_duration: number;
  success_rate: number;
  min_duration: number;
  max_duration: number;
}

export interface AgentUtilization {
  agent: string;
  workflow_count: number;
  total_duration: number;
  percentage: number;
  [key: string]: string | number; // Index signature for recharts compatibility
}

export interface WorkflowRecord {
  workflow_id: string;
  workflow_name: string;
  duration: number;
  status: string;
  agent: string;
  started_at: string;
}

export interface FailureAnalysis {
  most_failed_workflows: {
    workflow_type: string;
    failure_count: number;
    total_count: number;
    failure_rate: number;
  }[];
  most_failed_steps: {
    step_name: string;
    failure_count: number;
    error_message: string;
  }[];
  common_errors: {
    error_message: string;
    count: number;
  }[];
}

export interface TimeSeriesData {
  date: string;
  completed: number;
  failed: number;
  cancelled: number;
}

export interface DateRange {
  start: Date | null;
  end: Date | null;
}

// Metrics state interface
interface MetricsState {
  // Data
  summary: MetricsSummary;
  workflowTypeMetrics: WorkflowTypeMetrics[];
  agentUtilization: AgentUtilization[];
  longestWorkflows: WorkflowRecord[];
  failureAnalysis: FailureAnalysis;
  workflowsOverTime: TimeSeriesData[];
  loading: boolean;
  error: string | null;

  // View state
  dateRange: DateRange;
  autoRefresh: boolean;
  refreshInterval: number; // seconds

  // Actions
  fetchMetrics: (epic?: number) => Promise<void>;
  setDateRange: (range: DateRange) => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (seconds: number) => void;
  exportCSV: () => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  summary: {
    total_workflows: 0,
    completed: 0,
    failed: 0,
    cancelled: 0,
    running: 0,
    pending: 0,
    success_rate: 0,
    average_duration: 0,
    total_duration: 0,
  },
  workflowTypeMetrics: [],
  agentUtilization: [],
  longestWorkflows: [],
  failureAnalysis: {
    most_failed_workflows: [],
    most_failed_steps: [],
    common_errors: [],
  },
  workflowsOverTime: [],
  loading: false,
  error: null,
  dateRange: { start: null, end: null },
  autoRefresh: true,
  refreshInterval: 60,
};

export const useMetricsStore = create<MetricsState>((set, get) => ({
  ...initialState,

  fetchMetrics: async (epic?: number) => {
    set({ loading: true, error: null });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

      // Build query params
      const params = new URLSearchParams();
      const { dateRange } = get();

      if (dateRange.start) {
        params.append('start_date', dateRange.start.toISOString());
      }
      if (dateRange.end) {
        params.append('end_date', dateRange.end.toISOString());
      }
      if (epic !== undefined) {
        params.append('epic', epic.toString());
      }

      const response = await fetch(`${apiUrl}/api/workflows/metrics?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }

      const data = (await response.json()) as {
        summary: MetricsSummary;
        workflow_type_metrics: WorkflowTypeMetrics[];
        agent_utilization: AgentUtilization[];
        longest_workflows: WorkflowRecord[];
        failure_analysis: FailureAnalysis;
        workflows_over_time: TimeSeriesData[];
      };

      set({
        summary: data.summary,
        workflowTypeMetrics: data.workflow_type_metrics,
        agentUtilization: data.agent_utilization,
        longestWorkflows: data.longest_workflows,
        failureAnalysis: data.failure_analysis,
        workflowsOverTime: data.workflows_over_time,
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

  setDateRange: (range: DateRange) => {
    set({ dateRange: range });
    // Auto-fetch metrics when date range changes
    get().fetchMetrics();
  },

  setAutoRefresh: (enabled: boolean) => set({ autoRefresh: enabled }),

  setRefreshInterval: (seconds: number) => set({ refreshInterval: seconds }),

  exportCSV: () => {
    const { summary, workflowTypeMetrics, agentUtilization, longestWorkflows } = get();

    // Build CSV content
    const csvRows: string[][] = [
      ['Workflow Metrics Export', ''],
      ['Generated', new Date().toISOString()],
      ['', ''],
      ['Summary Metrics', ''],
      ['Total Workflows', summary.total_workflows.toString()],
      ['Completed', summary.completed.toString()],
      ['Failed', summary.failed.toString()],
      ['Cancelled', summary.cancelled.toString()],
      ['Running', summary.running.toString()],
      ['Pending', summary.pending.toString()],
      ['Success Rate', `${summary.success_rate.toFixed(2)}%`],
      ['Average Duration (seconds)', summary.average_duration.toFixed(2)],
      ['Total Duration (seconds)', summary.total_duration.toFixed(2)],
      ['', ''],
      ['Workflow Type Metrics', ''],
      [
        'Workflow Type',
        'Count',
        'Avg Duration (s)',
        'Success Rate (%)',
        'Min Duration (s)',
        'Max Duration (s)',
      ],
      ...workflowTypeMetrics.map((m) => [
        m.workflow_type,
        m.count.toString(),
        m.average_duration.toFixed(2),
        m.success_rate.toFixed(2),
        m.min_duration.toFixed(2),
        m.max_duration.toFixed(2),
      ]),
      ['', ''],
      ['Agent Utilization', ''],
      ['Agent', 'Workflow Count', 'Total Duration (s)', 'Percentage (%)'],
      ...agentUtilization.map((a) => [
        a.agent,
        a.workflow_count.toString(),
        a.total_duration.toFixed(2),
        a.percentage.toFixed(2),
      ]),
      ['', ''],
      ['Longest Workflows', ''],
      ['Workflow ID', 'Workflow Name', 'Duration (s)', 'Status', 'Agent', 'Started At'],
      ...longestWorkflows.map((w) => [
        w.workflow_id,
        w.workflow_name,
        w.duration.toFixed(2),
        w.status,
        w.agent,
        w.started_at,
      ]),
    ];

    // Convert to CSV string
    const csvContent = csvRows.map((row) => row.join(',')).join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workflow-metrics-${new Date().toISOString()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  },

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));
