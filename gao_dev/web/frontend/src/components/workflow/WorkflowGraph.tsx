/**
 * WorkflowGraph - DAG visualization of workflow dependencies using vis-network
 *
 * Story 39.22: Workflow Dependency Graph
 */
import { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { useWorkflowGraphStore } from '../../stores/workflowGraphStore';
import { GraphControls } from './GraphControls';
import { GraphLegend } from './GraphLegend';
import { LoadingSpinner } from '../LoadingSpinner';
import { Alert, AlertDescription } from '../ui/alert';
import { AlertCircle } from 'lucide-react';
import 'vis-network/styles/vis-network.css';

interface WorkflowGraphProps {
  epic?: number;
  storyNum?: number;
  includeCompleted?: boolean;
  onNodeClick?: (nodeId: string) => void;
}

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({
  epic,
  storyNum,
  includeCompleted = true,
  onNodeClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  const {
    nodes: storeNodes,
    edges: storeEdges,
    criticalPath,
    loading,
    error,
    layout,
    fetchGraph,
    selectNode,
    setLayout,
  } = useWorkflowGraphStore();

  // Fetch graph data on mount
  useEffect(() => {
    fetchGraph(epic, storyNum, includeCompleted);
  }, [fetchGraph, epic, storyNum, includeCompleted]);

  // Initialize and update vis-network
  useEffect(() => {
    if (!containerRef.current || storeNodes.length === 0) return;

    // Map store nodes to vis-network format
    const visNodes = storeNodes.map((node) => {
      const nodeData = node.data as {
        label: string;
        status: string;
        duration: number | null;
        isOnCriticalPath?: boolean;
      };

      const statusColors: Record<string, string> = {
        pending: '#9CA3AF',
        running: '#3B82F6',
        completed: '#10B981',
        failed: '#EF4444',
        cancelled: '#F59E0B',
      };

      const color = statusColors[nodeData.status] || statusColors.pending;
      const borderWidth = nodeData.isOnCriticalPath ? 4 : 2;
      const borderColor = nodeData.isOnCriticalPath ? '#6366F1' : color;

      return {
        id: node.id,
        label: nodeData.label,
        color: {
          background: color,
          border: borderColor,
          highlight: {
            background: color,
            border: '#000000',
          },
        },
        borderWidth,
        font: { color: '#ffffff', size: 14 },
        shape: 'box',
      };
    });

    // Map store edges to vis-network format
    const visEdges = storeEdges.map((edge) => {
      const edgeData = edge.data as { isOnCriticalPath?: boolean };
      const isOnCriticalPath = edgeData?.isOnCriticalPath || false;

      return {
        id: edge.id,
        from: edge.source,
        to: edge.target,
        arrows: 'to',
        color: isOnCriticalPath ? '#6366F1' : '#999999',
        width: isOnCriticalPath ? 3 : 1,
      };
    });

    const data = {
      nodes: visNodes,
      edges: visEdges,
    };

    const options = {
      layout: {
        hierarchical: {
          enabled: true,
          direction: layout === 'TB' ? 'UD' : 'LR',
          sortMethod: 'directed',
          nodeSpacing: 150,
          levelSeparation: 200,
        },
      },
      physics: {
        enabled: false,
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        keyboard: {
          enabled: true,
          bindToWindow: false,
        },
      },
      nodes: {
        shape: 'box',
        widthConstraint: {
          minimum: 150,
          maximum: 250,
        },
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'cubicBezier',
          roundness: 0.5,
        },
      },
    };

    // Create or update network
    if (!networkRef.current) {
      networkRef.current = new Network(containerRef.current, data, options);

      // Handle node clicks
      networkRef.current.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0] as string;
          selectNode(nodeId);
          onNodeClick?.(nodeId);
        }
      });
    } else {
      networkRef.current.setData(data);
      networkRef.current.setOptions(options);
    }

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [storeNodes, storeEdges, layout, criticalPath, selectNode, onNodeClick]);

  // Handle zoom controls
  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleFitView = () => {
    if (networkRef.current) {
      networkRef.current.fit({
        animation: {
          duration: 500,
          easingFunction: 'easeInOutQuad',
        },
      });
    }
  };

  const handleLayoutChange = (newLayout: 'TB' | 'LR') => {
    setLayout(newLayout);
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <GraphControls
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFitView={handleFitView}
        onLayoutChange={handleLayoutChange}
      />
      <GraphLegend />
      <div
        ref={containerRef}
        className="h-full w-full"
        role="img"
        aria-label="Workflow dependency graph"
      />
    </div>
  );
};
