/**
 * FileChangeItem - Individual file change card
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { FileChange } from '@/types/git';
import { FileIcon, FilePlusIcon, FileMinusIcon, FileEditIcon } from 'lucide-react';

interface FileChangeItemProps {
  file: FileChange;
  isSelected: boolean;
  onClick: () => void;
}

export function FileChangeItem({ file, isSelected, onClick }: FileChangeItemProps) {
  // Determine badge color and icon based on change type
  const changeConfig = {
    added: {
      label: 'Added',
      variant: 'default' as const,
      icon: FilePlusIcon,
      className: 'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20',
    },
    modified: {
      label: 'Modified',
      variant: 'secondary' as const,
      icon: FileEditIcon,
      className: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20',
    },
    deleted: {
      label: 'Deleted',
      variant: 'destructive' as const,
      icon: FileMinusIcon,
      className: 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20',
    },
  }[file.change_type] || {
    label: 'Unknown',
    variant: 'outline' as const,
    icon: FileIcon,
    className: '',
  };

  const Icon = changeConfig.icon;

  // Extract file name from path
  const fileName = file.path.split('/').pop() || file.path;
  const directory = file.path.substring(0, file.path.lastIndexOf('/')) || '';

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-3 rounded-lg border transition-colors hover:bg-muted/50',
        isSelected && 'bg-muted border-primary'
      )}
    >
      <div className="flex items-start gap-2">
        {/* File icon */}
        <Icon className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />

        {/* File info */}
        <div className="flex-1 min-w-0">
          {/* File name */}
          <div className="font-medium text-sm truncate">{fileName}</div>

          {/* Directory path */}
          {directory && (
            <div className="text-xs text-muted-foreground truncate mt-0.5">{directory}</div>
          )}

          {/* Metadata row */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {/* Change type badge */}
            <Badge variant={changeConfig.variant} className={cn('text-xs', changeConfig.className)}>
              {changeConfig.label}
            </Badge>

            {/* Stats */}
            {!file.is_binary && (
              <span className="text-xs text-muted-foreground">
                <span className="text-green-600 dark:text-green-400">+{file.insertions}</span>
                {' '}
                <span className="text-red-600 dark:text-red-400">-{file.deletions}</span>
              </span>
            )}

            {/* Binary indicator */}
            {file.is_binary && (
              <span className="text-xs text-muted-foreground italic">Binary file</span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}
