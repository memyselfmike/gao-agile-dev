/**
 * GraphLegend - Legend for workflow graph visualization
 *
 * Story 39.22: Workflow Dependency Graph
 */
import React from 'react';
import { CheckCircle2, XCircle, Clock, Circle, AlertCircle } from 'lucide-react';

export const GraphLegend: React.FC = () => {
  return (
    <div
      className="absolute bottom-4 left-4 z-10 rounded-lg border bg-white p-3 shadow-lg dark:bg-gray-800"
      role="region"
      aria-label="Graph legend"
    >
      <h3 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">Legend</h3>

      {/* Node statuses */}
      <div className="mb-3 space-y-1">
        <div className="flex items-center gap-2">
          <Circle className="h-3 w-3 text-gray-400" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Pending</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="h-3 w-3 text-blue-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Running</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-3 w-3 text-green-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <XCircle className="h-3 w-3 text-red-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Failed</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-3 w-3 text-orange-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">Cancelled</span>
        </div>
      </div>

      {/* Edge types */}
      <div className="space-y-1 border-t pt-2">
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-6 bg-gray-400"></div>
          <span className="text-xs text-gray-600 dark:text-gray-400">Dependency</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-1 w-6 bg-indigo-500"></div>
          <span className="text-xs text-gray-600 dark:text-gray-400">Critical Path</span>
        </div>
      </div>
    </div>
  );
};
