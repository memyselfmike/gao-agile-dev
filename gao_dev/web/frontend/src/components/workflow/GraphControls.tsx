/**
 * GraphControls - Controls for workflow graph visualization
 *
 * Story 39.22: Workflow Dependency Graph
 */
import React from 'react';
import { Button } from '../ui/button';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  ArrowDown,
  ArrowRight,
} from 'lucide-react';
import { useWorkflowGraphStore } from '../../stores/workflowGraphStore';
import type { LayoutDirection } from '../../stores/workflowGraphStore';

interface GraphControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  onLayoutChange: (layout: LayoutDirection) => void;
}

export const GraphControls: React.FC<GraphControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onFitView,
  onLayoutChange,
}) => {
  const { layout } = useWorkflowGraphStore();

  return (
    <div className="absolute top-4 right-4 z-10 flex flex-col gap-2 bg-white rounded-lg shadow-lg p-2">
      <div className="flex flex-col gap-1">
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomIn}
          aria-label="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onZoomOut}
          aria-label="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onFitView}
          aria-label="Fit view"
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="border-t pt-2">
        <p className="text-xs text-gray-500 mb-1 px-1">Layout</p>
        <Button
          variant={layout === 'TB' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onLayoutChange('TB')}
          aria-label="Top to bottom layout"
        >
          <ArrowDown className="h-4 w-4" />
        </Button>
        <Button
          variant={layout === 'LR' ? 'default' : 'outline'}
          size="sm"
          onClick={() => onLayoutChange('LR')}
          className="mt-1"
          aria-label="Left to right layout"
        >
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
