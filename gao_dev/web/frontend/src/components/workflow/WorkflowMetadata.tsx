/**
 * Workflow Metadata Component
 *
 * Story 39.21: Workflow Detail Panel - AC4
 *
 * Displays workflow metadata in key-value grid:
 * - workflow_id, agent, epic/story numbers
 * - start time, end time, duration
 */
import { format } from 'date-fns';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import type { WorkflowExecution } from '@/stores/workflowStore';
import { formatDuration, copyToClipboard } from './utils';

export interface WorkflowMetadataProps {
  workflow: WorkflowExecution;
}

export function WorkflowMetadata({ workflow }: WorkflowMetadataProps) {
  const [copiedWorkflowId, setCopiedWorkflowId] = useState(false);

  const handleCopyWorkflowId = async () => {
    await copyToClipboard(workflow.workflow_id);
    setCopiedWorkflowId(true);
    toast.success('Workflow ID copied to clipboard');
    setTimeout(() => setCopiedWorkflowId(false), 2000);
  };

  const formatTimestamp = (timestamp: string | null): string => {
    if (!timestamp) return 'N/A';
    try {
      return format(new Date(timestamp), 'PPpp'); // e.g., "Jan 16, 2025 at 10:00:00 AM"
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="space-y-3">
      {/* Workflow ID */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">Workflow ID</span>
        <div className="flex items-center gap-2">
          <code className="text-sm bg-muted px-2 py-1 rounded">{workflow.workflow_id}</code>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={handleCopyWorkflowId}
            aria-label="Copy workflow ID"
          >
            {copiedWorkflowId ? (
              <Check className="h-4 w-4 text-green-600" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Agent */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">Agent</span>
        <span className="text-sm font-semibold">{workflow.agent}</span>
      </div>

      {/* Epic/Story */}
      {workflow.epic > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Epic / Story</span>
          <span className="text-sm">
            Epic {workflow.epic}
            {workflow.story_num > 0 && ` / Story ${workflow.story_num}`}
          </span>
        </div>
      )}

      {/* Start Time */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">Started</span>
        <span className="text-sm">{formatTimestamp(workflow.started_at)}</span>
      </div>

      {/* End Time */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">Completed</span>
        <span className="text-sm">{formatTimestamp(workflow.completed_at)}</span>
      </div>

      {/* Duration */}
      {workflow.duration !== null && (
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Duration</span>
          <span className="text-sm font-mono">{formatDuration(workflow.duration)}</span>
        </div>
      )}
    </div>
  );
}
