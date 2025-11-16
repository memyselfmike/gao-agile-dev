/**
 * FileTreeNode - Single node in file tree (file or directory)
 * Story 39.11: File Tree Navigation Component
 */
import { ChevronRight, ChevronDown, Folder, Circle } from 'lucide-react';
import type { FileNode } from '@/types';
import { useFilesStore } from '@/stores/filesStore';
import { cn } from '@/lib/utils';

interface FileTreeNodeProps {
  node: FileNode;
  depth: number;
  isExpanded: boolean;
  recentlyChanged: boolean;
  onSelect: (path: string) => void;
}

// File icon mapping
const FILE_ICONS: Record<string, string> = {
  python: '🐍',
  javascript: '📜',
  typescript: '📘',
  react: '⚛️',
  markdown: '📝',
  json: '{ }',
  yaml: '⚙️',
  html: '🌐',
  css: '🎨',
  shell: '💻',
  text: '📄',
  file: '📄',
};

export function FileTreeNode({
  node,
  depth,
  isExpanded,
  recentlyChanged,
  onSelect,
}: FileTreeNodeProps) {
  const { toggleFolder, activeFilePath } = useFilesStore();

  const isActive = activeFilePath === node.path;
  const isDirectory = node.type === 'directory';

  const handleClick = () => {
    if (isDirectory) {
      toggleFolder(node.path);
    } else {
      onSelect(node.path);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleClick();
    } else if (e.key === 'ArrowRight' && isDirectory && !isExpanded) {
      toggleFolder(node.path);
    } else if (e.key === 'ArrowLeft' && isDirectory && isExpanded) {
      toggleFolder(node.path);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        'flex items-center gap-1 px-2 py-1 cursor-pointer hover:bg-accent',
        isActive && 'bg-accent',
        recentlyChanged && 'border-l-2 border-green-500'
      )}
      style={{ paddingLeft: `${depth * 12 + 8}px` }}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      {/* Expand/collapse chevron for directories */}
      {isDirectory && (
        <span className="flex-shrink-0">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </span>
      )}

      {/* Icon */}
      <span className="flex-shrink-0">
        {isDirectory ? (
          <Folder className="h-4 w-4 text-blue-500" />
        ) : (
          <span className="text-sm">{FILE_ICONS[node.icon || 'file'] || '📄'}</span>
        )}
      </span>

      {/* File/folder name */}
      <span className={cn('truncate text-sm', isActive && 'font-semibold')}>{node.name}</span>

      {/* Recently changed indicator */}
      {recentlyChanged && (
        <Circle className="ml-auto h-2 w-2 flex-shrink-0 fill-green-500 text-green-500" />
      )}
    </div>
  );
}
