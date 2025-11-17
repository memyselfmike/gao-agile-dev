/**
 * GitTimeline - Main git commit timeline component
 *
 * Features:
 * - Real-time updates via WebSocket (git.commit events)
 * - Filtering support
 * - Infinite scroll pagination
 * - Performance optimized for large repositories
 */
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Commit, GitTimelineFilters } from '@/types/git';
import { CommitList } from './CommitList';
import { useWebSocket } from '@/hooks/useWebSocket';

interface GitTimelineProps {
  filters?: GitTimelineFilters;
  onCommitClick?: (commit: Commit) => void;
}

export function GitTimeline({ filters, onCommitClick }: GitTimelineProps) {
  const queryClient = useQueryClient();
  const websocket = useWebSocket();

  // Subscribe to real-time git commit events
  useEffect(() => {
    if (!websocket) return;

    const handleGitCommit = (event: any) => {
      // Invalidate commit list query to refetch and show new commit
      queryClient.invalidateQueries({ queryKey: ['git-commits'] });
    };

    // Subscribe to git.commit events
    // Note: Actual WebSocket event structure may vary based on backend implementation
    const unsubscribe = websocket.subscribe?.('git.commit', handleGitCommit);

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [websocket, queryClient]);

  return (
    <div className="h-full overflow-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">Commit History</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Track changes over time and understand project evolution
          </p>
        </div>

        <CommitList filters={filters} onCommitClick={onCommitClick} />
      </div>
    </div>
  );
}
