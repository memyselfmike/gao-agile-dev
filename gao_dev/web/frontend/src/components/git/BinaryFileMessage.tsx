/**
 * BinaryFileMessage - Placeholder for binary files in diff view
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { FileIcon } from 'lucide-react';
import type { FileChange } from '@/types/git';

interface BinaryFileMessageProps {
  file: FileChange;
}

export function BinaryFileMessage({ file }: BinaryFileMessageProps) {
  // Format file size (simplified - we don't have actual byte counts)
  const formatSize = (lines: number) => {
    // Rough estimate: assume ~50 bytes per line for text files
    const bytes = lines * 50;
    if (bytes < 1024) return `${bytes} bytes`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const originalSize = formatSize(file.deletions || 0);
  const modifiedSize = formatSize(file.insertions || 0);

  return (
    <div className="flex items-center justify-center h-full p-8">
      <Alert className="max-w-lg">
        <FileIcon className="h-4 w-4" />
        <AlertTitle>Binary file changed</AlertTitle>
        <AlertDescription className="mt-2">
          <p className="text-sm">
            This file is binary and cannot be displayed in the diff viewer.
          </p>
          {file.change_type === 'modified' && (
            <p className="text-sm text-muted-foreground mt-2">
              Size: {originalSize} → {modifiedSize}
            </p>
          )}
          {file.change_type === 'added' && (
            <p className="text-sm text-muted-foreground mt-2">
              File added ({modifiedSize})
            </p>
          )}
          {file.change_type === 'deleted' && (
            <p className="text-sm text-muted-foreground mt-2">
              File deleted ({originalSize})
            </p>
          )}
        </AlertDescription>
      </Alert>
    </div>
  );
}
