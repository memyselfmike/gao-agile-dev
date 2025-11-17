/**
 * WorkflowTimeline - Main timeline visualization component
 *
 * Story 39.20: Workflow Execution Timeline
 */
import React, { useEffect, useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useWorkflowStore } from '../../stores/workflowStore';
import { WorkflowBar } from './WorkflowBar';
import { TimelineFilters } from './TimelineFilters';
import { Loader2 } from 'lucide-react';

export const WorkflowTimeline: React.FC = () => {
  const {
    workflows,
    loading,
    error,
    fetchTimeline,
    selectWorkflow,
    clearError,
  } = useWorkflowStore();

  const parentRef = useRef<HTMLDivElement>(null);

  // Virtual scrolling for 1000+ workflows
  const rowVirtualizer = useVirtualizer({
    count: workflows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Height estimate for each workflow bar
    overscan: 5, // Render 5 extra items above/below viewport
  });

  // Fetch timeline on mount
  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  // Auto-scroll to current time when workflows are running
  useEffect(() => {
    const hasRunningWorkflows = workflows.some((wf) => wf.status === 'running');
    if (hasRunningWorkflows && parentRef.current) {
      // Scroll to top to show most recent workflows
      parentRef.current.scrollTop = 0;
    }
  }, [workflows]);

  const handleWorkflowClick = (workflowId: string) => {
    selectWorkflow(workflowId);
    // Note: Detail panel will be implemented in Story 39.21
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-red-800 font-medium">Error loading timeline</h3>
                <p className="text-red-600 text-sm mt-1">{error}</p>
              </div>
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Workflow Timeline</h1>
          <p className="text-gray-600 mt-1">
            View and track all workflow executions over time
          </p>
        </div>

        {/* Layout: Filters (left) + Timeline (right) */}
        <div className="grid grid-cols-12 gap-6">
          {/* Filters Sidebar */}
          <div className="col-span-3">
            <TimelineFilters />
          </div>

          {/* Timeline Content */}
          <div className="col-span-9">
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              {/* Timeline Header */}
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">
                    {workflows.length === 0
                      ? 'No workflows found'
                      : `Showing ${workflows.length} workflow${workflows.length === 1 ? '' : 's'}`}
                  </h2>
                  {loading && (
                    <div className="flex items-center gap-2 text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Loading...</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Timeline Body - Virtual Scrolling */}
              <div
                ref={parentRef}
                role="region"
                aria-label="Workflow Timeline"
                className="h-[600px] overflow-auto px-6 py-4"
                style={{ position: 'relative' }}
              >
                {workflows.length === 0 && !loading ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <p className="text-gray-500 mb-2">No workflow executions found</p>
                    <p className="text-sm text-gray-400">
                      Workflow executions will appear here as they run
                    </p>
                  </div>
                ) : (
                  <div
                    style={{
                      height: `${rowVirtualizer.getTotalSize()}px`,
                      width: '100%',
                      position: 'relative',
                    }}
                  >
                    {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                      const workflow = workflows[virtualRow.index];
                      return (
                        <div
                          key={workflow.workflow_id}
                          style={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: `${virtualRow.size}px`,
                            transform: `translateY(${virtualRow.start}px)`,
                          }}
                        >
                          <div className="pb-3">
                            <WorkflowBar
                              workflow={workflow}
                              onClick={handleWorkflowClick}
                              tabIndex={virtualRow.index}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
