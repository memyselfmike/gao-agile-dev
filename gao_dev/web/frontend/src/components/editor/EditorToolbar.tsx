/**
 * EditorToolbar - Toolbar with Save, Diff, Format buttons
 * Story 39.14: Monaco Edit Mode with Commit Enforcement
 */
import { useState } from 'react';
import { Save, GitCompare, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useFilesStore } from '@/stores/filesStore';
import { useSessionStore } from '@/stores/sessionStore';
import { CommitMessageDialog } from './CommitMessageDialog';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

export function EditorToolbar() {
  const { openFiles, activeFilePath, markFileSaved } = useFilesStore();
  const { isReadOnly } = useSessionStore();
  const [showCommitDialog, setShowCommitDialog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const activeFile = openFiles.find((f) => f.path === activeFilePath);
  const hasUnsavedChanges = activeFile?.modified || false;

  const handleSave = async (commitMessage: string) => {
    if (!activeFile) return;

    setIsSaving(true);

    try {
      const response = await fetch(`${API_URL}/api/files/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          path: activeFile.path,
          content: activeFile.content,
          commit_message: commitMessage,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save file');
      }

      const result = await response.json();

      // Mark file as saved
      markFileSaved(activeFile.path);

      // Show success toast
      toast.success('File saved and committed', {
        description: `${result.commitHash?.slice(0, 8)}: ${commitMessage}`,
      });

      setShowCommitDialog(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to save file', {
        description: message,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiffView = async () => {
    if (!activeFile) return;

    try {
      const response = await fetch(
        `${API_URL}/api/files/diff?path=${encodeURIComponent(activeFile.path)}`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get diff');
      }

      const result = await response.json();

      // Show diff in a simple alert (future: could be a modal with syntax highlighting)
      if (result.diff) {
        alert(`Diff for ${activeFile.path}:\n\n${result.diff}`);
      } else {
        toast.info('No changes detected');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to get diff', {
        description: message,
      });
    }
  };

  if (!activeFile) {
    return null;
  }

  return (
    <>
      <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-2">
        {/* File path */}
        <span className="text-sm text-muted-foreground">{activeFile.path}</span>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Read-only banner */}
          {isReadOnly && (
            <div className="flex items-center gap-1 text-sm text-amber-600">
              <AlertCircle className="h-4 w-4" />
              <span>Read-only (CLI active)</span>
            </div>
          )}

          {/* Diff button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDiffView}
            disabled={!hasUnsavedChanges}
          >
            <GitCompare className="mr-2 h-4 w-4" />
            Diff
          </Button>

          {/* Save button */}
          <Button
            variant="default"
            size="sm"
            onClick={() => setShowCommitDialog(true)}
            disabled={isReadOnly || !hasUnsavedChanges || isSaving}
          >
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      {/* Commit message dialog */}
      {showCommitDialog && (
        <CommitMessageDialog
          open={showCommitDialog}
          onClose={() => setShowCommitDialog(false)}
          onConfirm={handleSave}
          fileName={activeFile.path.split('/').pop() || activeFile.path}
        />
      )}
    </>
  );
}
