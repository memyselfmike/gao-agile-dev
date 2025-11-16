/**
 * EditorTabs - Tab management for open files
 * Story 39.12: Monaco Editor Integration
 */
import { X, Circle } from 'lucide-react';
import { useFilesStore } from '@/stores/filesStore';
import { cn } from '@/lib/utils';

export function EditorTabs() {
  const { openFiles, activeFilePath, setActiveFile, closeFile } = useFilesStore();

  const handleCloseTab = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();

    // Check for unsaved changes
    const file = openFiles.find((f) => f.path === path);
    if (file?.modified) {
      const confirmed = window.confirm(
        'This file has unsaved changes. Are you sure you want to close it?'
      );
      if (!confirmed) return;
    }

    closeFile(path);
  };

  const handleKeyDown = (path: string, e: React.KeyboardEvent) => {
    // Cmd+W or Ctrl+W to close tab
    if ((e.metaKey || e.ctrlKey) && e.key === 'w') {
      e.preventDefault();
      handleCloseTab(path, e as unknown as React.MouseEvent);
    }
  };

  if (openFiles.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-1 border-b bg-muted/30 px-2 py-1 overflow-x-auto">
      {openFiles.map((file) => {
        const isActive = activeFilePath === file.path;
        const fileName = file.path.split('/').pop() || file.path;

        return (
          <div
            key={file.path}
            role="button"
            tabIndex={0}
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-1.5 text-sm cursor-pointer',
              'hover:bg-accent transition-colors',
              isActive && 'bg-background border border-border'
            )}
            onClick={() => setActiveFile(file.path)}
            onKeyDown={(e) => handleKeyDown(file.path, e)}
          >
            {/* File name */}
            <span className={cn('max-w-[150px] truncate', isActive && 'font-medium')}>
              {fileName}
            </span>

            {/* Unsaved indicator or close button */}
            {file.modified ? (
              <Circle className="h-3 w-3 flex-shrink-0 fill-orange-500 text-orange-500" />
            ) : (
              <button
                onClick={(e) => handleCloseTab(file.path, e)}
                className="flex-shrink-0 rounded-sm hover:bg-muted-foreground/20 p-0.5"
                aria-label="Close tab"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
