/**
 * Workflow Artifacts Component
 *
 * Story 39.21: Workflow Detail Panel - AC8
 *
 * Lists created files with:
 * - File icon by type
 * - File size display
 * - Link to Files tab
 */
import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import type { WorkflowArtifact } from '@/stores/workflowStore';
import { getFileIcon, formatFileSize } from './utils';

export interface WorkflowArtifactsProps {
  artifacts: WorkflowArtifact[];
  onOpenFile?: (filePath: string) => void;
}

export function WorkflowArtifacts({ artifacts, onOpenFile }: WorkflowArtifactsProps) {
  if (artifacts.length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-4">
        No artifacts created by this workflow.
      </div>
    );
  }

  const handleOpenFile = (filePath: string) => {
    if (onOpenFile) {
      onOpenFile(filePath);
    }
  };

  return (
    <div className="space-y-2">
      {artifacts.map((artifact, index) => (
        <div
          key={`artifact-${index}`}
          className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
        >
          {/* File icon */}
          <div className="text-2xl flex-shrink-0">{getFileIcon(artifact.path)}</div>

          {/* File info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono font-semibold truncate">{artifact.path}</span>
              <Badge variant="secondary" className="text-xs">
                {artifact.type}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {formatFileSize(artifact.size)} •{' '}
              {format(new Date(artifact.created_at), 'PPpp')}
            </div>
          </div>

          {/* Open file button */}
          {onOpenFile && (
            <Button
              variant="ghost"
              size="sm"
              className="flex-shrink-0"
              onClick={() => handleOpenFile(artifact.path)}
              aria-label={`Open ${artifact.path} in Files tab`}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}
