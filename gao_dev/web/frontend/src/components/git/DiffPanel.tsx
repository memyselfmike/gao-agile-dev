/**
 * DiffPanel - Main diff panel container
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileList } from './FileList';
import { MonacoDiffViewer } from './MonacoDiffViewer';
import { DiffToolbar } from './DiffToolbar';
import { BinaryFileMessage } from './BinaryFileMessage';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';
import type { CommitDiffResponse } from '@/types/git';

interface DiffPanelProps {
  commitHash: string;
  onBack: () => void;
}

export function DiffPanel({ commitHash, onBack }: DiffPanelProps) {
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  // Fetch commit diff
  const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
  const { data, isLoading, error } = useQuery<CommitDiffResponse>({
    queryKey: ['commit-diff', commitHash],
    queryFn: async () => {
      const response = await fetch(`${apiUrl}/api/git/commits/${commitHash}/diff`, {
        credentials: 'include',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch commit diff');
      }
      return response.json();
    },
    enabled: !!commitHash,
  });

  const selectedFile = data?.files[selectedFileIndex];

  // Navigation handlers
  const handleNextFile = () => {
    if (selectedFileIndex < (data?.files.length || 0) - 1) {
      setSelectedFileIndex((prev) => prev + 1);
    }
  };

  const handlePreviousFile = () => {
    if (selectedFileIndex > 0) {
      setSelectedFileIndex((prev) => prev - 1);
    }
  };

  const handleToggleView = () => {
    setViewMode((prev) => (prev === 'split' ? 'unified' : 'split'));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle if not typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'n':
          handleNextFile();
          break;
        case 'p':
          handlePreviousFile();
          break;
        case 't':
          handleToggleView();
          break;
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [selectedFileIndex, data]);

  // Reset selected file when data changes
  useEffect(() => {
    setSelectedFileIndex(0);
  }, [commitHash]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner size="lg" message="Loading commit diff..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">Failed to load commit diff</p>
          <Button onClick={onBack} variant="outline">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Go back
          </Button>
        </div>
      </div>
    );
  }

  if (!data || data.files.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">No files changed in this commit</p>
          <Button onClick={onBack} variant="outline">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Go back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with back button */}
      <div className="flex items-center gap-2 p-3 border-b">
        <Button onClick={onBack} variant="ghost" size="sm">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to timeline
        </Button>
        <div className="flex-1 text-sm text-muted-foreground">
          Commit: <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">{commitHash.substring(0, 7)}</code>
        </div>
      </div>

      {/* Toolbar */}
      <DiffToolbar
        viewMode={viewMode}
        onToggleView={handleToggleView}
        onNext={handleNextFile}
        onPrevious={handlePreviousFile}
        hasNext={selectedFileIndex < data.files.length - 1}
        hasPrevious={selectedFileIndex > 0}
      />

      {/* Main content: File list + Diff viewer */}
      <div className="flex flex-1 overflow-hidden">
        {/* File list sidebar */}
        <div className="w-80 border-r bg-muted/20">
          <FileList
            files={data.files}
            selectedIndex={selectedFileIndex}
            onSelectFile={setSelectedFileIndex}
          />
        </div>

        {/* Diff viewer */}
        <div className="flex-1 overflow-hidden">
          {selectedFile?.is_binary ? (
            <BinaryFileMessage file={selectedFile} />
          ) : (
            <MonacoDiffViewer file={selectedFile} viewMode={viewMode} />
          )}
        </div>
      </div>
    </div>
  );
}
