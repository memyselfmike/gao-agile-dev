/**
 * FileList - List of changed files in a commit
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { ScrollArea } from '@/components/ui/scroll-area';
import type { FileChange } from '@/types/git';
import { FileChangeItem } from './FileChangeItem';

interface FileListProps {
  files: FileChange[];
  selectedIndex: number;
  onSelectFile: (index: number) => void;
}

export function FileList({ files, selectedIndex, onSelectFile }: FileListProps) {
  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No files changed
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-3 space-y-2">
        {/* Summary header */}
        <div className="text-xs text-muted-foreground font-medium mb-3">
          {files.length} {files.length === 1 ? 'file' : 'files'} changed
        </div>

        {/* File list */}
        {files.map((file, index) => (
          <FileChangeItem
            key={file.path}
            file={file}
            isSelected={index === selectedIndex}
            onClick={() => onSelectFile(index)}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
