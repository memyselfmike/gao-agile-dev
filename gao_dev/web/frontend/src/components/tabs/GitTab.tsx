/**
 * Git Tab - Git commit timeline and operations
 *
 * Story 39.25: Git Timeline Commit History
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { useState } from 'react';
import { GitTimeline, DiffPanel } from '@/components/git';

export function GitTab() {
  const [selectedCommitHash, setSelectedCommitHash] = useState<string | null>(null);

  if (selectedCommitHash) {
    return <DiffPanel commitHash={selectedCommitHash} onBack={() => setSelectedCommitHash(null)} />;
  }

  return <GitTimeline onCommitClick={(hash) => setSelectedCommitHash(hash)} />;
}
