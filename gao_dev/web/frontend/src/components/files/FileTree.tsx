/**
 * FileTree - Hierarchical file tree with virtual scrolling
 * Story 39.11: File Tree Navigation Component
 */
import { useEffect, useState, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { FileTreeNode } from './FileTreeNode';
import { Search } from 'lucide-react';
import type { FileNode } from '@/types';
import { useFilesStore } from '@/stores/filesStore';
import Fuse from 'fuse.js';

interface FileTreeProps {
  onFileSelect: (path: string) => void;
}

// Flatten tree for virtual scrolling
interface FlatNode extends FileNode {
  depth: number;
  isExpanded: boolean;
}

function flattenTree(
  nodes: FileNode[],
  expandedFolders: Set<string>,
  depth: number = 0
): FlatNode[] {
  const flat: FlatNode[] = [];

  for (const node of nodes) {
    const isExpanded = expandedFolders.has(node.path);
    flat.push({ ...node, depth, isExpanded });

    // Add children if folder is expanded
    if (node.type === 'directory' && node.children && isExpanded) {
      flat.push(...flattenTree(node.children, expandedFolders, depth + 1));
    }
  }

  return flat;
}

export function FileTree({ onFileSelect }: FileTreeProps) {
  const { fileTree, expandedFolders, recentlyChangedPaths, loadExpandedFolders } =
    useFilesStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('all');

  // Load expanded folders from localStorage on mount
  useEffect(() => {
    loadExpandedFolders();
  }, [loadExpandedFolders]);

  // Flatten tree for virtual scrolling
  const flatNodes = useMemo(() => {
    return flattenTree(fileTree, expandedFolders);
  }, [fileTree, expandedFolders]);

  // Filter nodes based on search query and file type
  const filteredNodes = useMemo(() => {
    let nodes = flatNodes;

    // File type filter
    if (fileTypeFilter !== 'all') {
      nodes = nodes.filter((node) => {
        if (node.type === 'directory') return true; // Keep directories
        return node.icon === fileTypeFilter;
      });
    }

    // Search filter (fuzzy search on file names)
    if (searchQuery.trim()) {
      const fuse = new Fuse(nodes, {
        keys: ['name', 'path'],
        threshold: 0.3,
      });
      const results = fuse.search(searchQuery);
      return results.map((r) => r.item);
    }

    return nodes;
  }, [flatNodes, searchQuery, fileTypeFilter]);

  // Virtual scrolling
  const virtualizer = useVirtualizer({
    count: filteredNodes.length,
    getScrollElement: () => document.getElementById('file-tree-scroll-area'),
    estimateSize: () => 32, // Estimated row height in pixels
    overscan: 10,
  });

  // File type options for dropdown
  const fileTypeOptions = useMemo(() => {
    const types = new Set<string>();
    flatNodes.forEach((node) => {
      if (node.type === 'file' && node.icon) {
        types.add(node.icon);
      }
    });
    return Array.from(types).sort();
  }, [flatNodes]);

  return (
    <div className="flex h-full flex-col">
      {/* Search and filter */}
      <div className="space-y-2 p-2">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>

        <select
          value={fileTypeFilter}
          onChange={(e) => setFileTypeFilter(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="all">All Files</option>
          {fileTypeOptions.map((type) => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* File tree with virtual scrolling */}
      <ScrollArea className="flex-1" id="file-tree-scroll-area">
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualizer.getVirtualItems().map((virtualItem) => {
            const node = filteredNodes[virtualItem.index];
            return (
              <div
                key={virtualItem.key}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualItem.size}px`,
                  transform: `translateY(${virtualItem.start}px)`,
                }}
              >
                <FileTreeNode
                  node={node}
                  depth={node.depth}
                  isExpanded={node.isExpanded}
                  recentlyChanged={recentlyChangedPaths.has(node.path)}
                  onSelect={onFileSelect}
                />
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* File count */}
      <div className="border-t px-2 py-1 text-xs text-muted-foreground">
        {filteredNodes.length} {filteredNodes.length === 1 ? 'item' : 'items'}
      </div>
    </div>
  );
}
