/**
 * EmptyFileTree - Empty state for file tree when no files exist
 *
 * Story 39.40: Empty States
 */
import { FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyFileTreeProps {
  onCreateFile?: () => void;
}

export function EmptyFileTree({ onCreateFile }: EmptyFileTreeProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mb-4 rounded-full bg-primary/10 p-6">
        <FolderOpen className="h-12 w-12 text-primary" />
      </div>
      <h3 className="mb-2 text-lg font-semibold">No files yet</h3>
      <p className="mb-6 max-w-sm text-sm text-muted-foreground">
        Your project is empty. Files will appear here as agents create them or you can create files
        manually.
      </p>
      {onCreateFile && (
        <Button onClick={onCreateFile} size="lg">
          Create a file
        </Button>
      )}
    </div>
  );
}
