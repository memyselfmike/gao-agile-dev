/**
 * WorkflowBar - Single workflow bar component for timeline visualization
 *
 * Story 39.20: Workflow Execution Timeline
 */
import React from 'react';
import type { WorkflowExecution } from '../../stores/workflowStore';
import { formatDistanceToNow } from 'date-fns';

interface WorkflowBarProps {
  workflow: WorkflowExecution;
  onClick: (workflowId: string) => void;
  tabIndex: number;
}

// Status color mapping
const STATUS_COLORS = {
  pending: 'bg-gray-400',
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  cancelled: 'bg-orange-500',
};

const STATUS_LABELS = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

export const WorkflowBar: React.FC<WorkflowBarProps> = ({ workflow, onClick, tabIndex }) => {
  const statusColor = STATUS_COLORS[workflow.status] || 'bg-gray-400';

  // Format duration
  const formatDuration = (seconds: number | null): string => {
    if (seconds === null) return 'In progress...';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Format timestamp
  const formatTimestamp = (isoString: string): string => {
    try {
      const date = new Date(isoString);
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return isoString;
    }
  };

  const handleClick = () => {
    onClick(workflow.workflow_id);
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick(workflow.workflow_id);
    }
  };

  return (
    <div
      role="button"
      tabIndex={tabIndex}
      onClick={handleClick}
      onKeyPress={handleKeyPress}
      aria-label={`${workflow.workflow_name} - ${STATUS_LABELS[workflow.status]} - ${formatDuration(workflow.duration)}`}
      className={`
        flex items-center gap-3 p-3 rounded-lg border border-gray-200
        hover:shadow-md hover:border-gray-300 transition-all cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
      `}
    >
      {/* Status indicator bar */}
      <div className={`w-1 h-12 rounded ${statusColor}`} />

      {/* Workflow info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-sm text-gray-900 truncate">
            {workflow.workflow_name}
          </h3>
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColor} text-white`}
          >
            {STATUS_LABELS[workflow.status]}
          </span>
        </div>

        <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
          <span>Epic {workflow.epic}.{workflow.story_num}</span>
          <span>•</span>
          <span>{formatTimestamp(workflow.started_at)}</span>
          {workflow.duration !== null && (
            <>
              <span>•</span>
              <span>{formatDuration(workflow.duration)}</span>
            </>
          )}
        </div>
      </div>

      {/* Agent badge */}
      <div className="flex-shrink-0">
        <div className="px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-700">
          {workflow.agent}
        </div>
      </div>
    </div>
  );
};
