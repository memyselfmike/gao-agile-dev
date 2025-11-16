/**
 * Files Store - Manages file tree and open files with LRU eviction
 */
import { create } from 'zustand';
import type { FileNode, OpenFile } from '../types';

const MAX_OPEN_FILES = 10; // Editor pooling limit

interface FilesState {
  fileTree: FileNode[];
  openFiles: OpenFile[];
  activeFilePath: string | null;
  recentlyChangedPaths: Set<string>;
  expandedFolders: Set<string>; // Persisted in localStorage

  // Actions
  setFileTree: (tree: FileNode[]) => void;
  openFile: (file: OpenFile) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  updateFileContent: (path: string, content: string) => void;
  markFileSaved: (path: string) => void;
  addRecentlyChanged: (path: string) => void;
  removeRecentlyChanged: (path: string) => void;
  toggleFolder: (path: string) => void;
  loadExpandedFolders: () => void;
  saveExpandedFolders: () => void;
}

export const useFilesStore = create<FilesState>((set, get) => ({
  fileTree: [],
  openFiles: [],
  activeFilePath: null,
  recentlyChangedPaths: new Set(),
  expandedFolders: new Set(),

  setFileTree: (tree) => set({ fileTree: tree }),

  openFile: (file) =>
    set((state) => {
      const exists = state.openFiles.find((f) => f.path === file.path);
      if (exists) {
        // File already open - just activate it
        return { activeFilePath: file.path };
      }

      let newOpenFiles = [...state.openFiles];

      // LRU eviction: If max limit reached, close least recently used (first in array)
      if (newOpenFiles.length >= MAX_OPEN_FILES) {
        // Find LRU (not active, no unsaved changes)
        const lruIndex = newOpenFiles.findIndex(
          (f) => f.path !== state.activeFilePath && !f.modified
        );

        if (lruIndex !== -1) {
          // Remove LRU file
          newOpenFiles.splice(lruIndex, 1);
        } else {
          // All files have unsaved changes or are active - can't evict
          // In this case, don't open new file
          return state;
        }
      }

      // Add new file to end (most recently used)
      newOpenFiles.push(file);

      return {
        openFiles: newOpenFiles,
        activeFilePath: file.path,
      };
    }),

  closeFile: (path) =>
    set((state) => ({
      openFiles: state.openFiles.filter((f) => f.path !== path),
      activeFilePath: state.activeFilePath === path ? null : state.activeFilePath,
    })),

  setActiveFile: (path) =>
    set((state) => {
      // Move active file to end of array (most recently used)
      if (path === null) {
        return { activeFilePath: null };
      }

      const fileIndex = state.openFiles.findIndex((f) => f.path === path);
      if (fileIndex === -1) {
        return { activeFilePath: path };
      }

      const newOpenFiles = [...state.openFiles];
      const [file] = newOpenFiles.splice(fileIndex, 1);
      newOpenFiles.push(file);

      return {
        openFiles: newOpenFiles,
        activeFilePath: path,
      };
    }),

  updateFileContent: (path, content) =>
    set((state) => ({
      openFiles: state.openFiles.map((f) =>
        f.path === path ? { ...f, content, modified: true, saved: false } : f
      ),
    })),

  markFileSaved: (path) =>
    set((state) => ({
      openFiles: state.openFiles.map((f) =>
        f.path === path ? { ...f, modified: false, saved: true } : f
      ),
    })),

  addRecentlyChanged: (path) =>
    set((state) => {
      const newSet = new Set(state.recentlyChangedPaths);
      newSet.add(path);

      // Auto-remove after 5 minutes
      setTimeout(() => {
        get().removeRecentlyChanged(path);
      }, 5 * 60 * 1000);

      return { recentlyChangedPaths: newSet };
    }),

  removeRecentlyChanged: (path) =>
    set((state) => {
      const newSet = new Set(state.recentlyChangedPaths);
      newSet.delete(path);
      return { recentlyChangedPaths: newSet };
    }),

  toggleFolder: (path) =>
    set((state) => {
      const newSet = new Set(state.expandedFolders);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }

      // Persist to localStorage
      get().saveExpandedFolders();

      return { expandedFolders: newSet };
    }),

  loadExpandedFolders: () => {
    try {
      const stored = localStorage.getItem('expandedFolders');
      if (stored) {
        const folders = JSON.parse(stored) as string[];
        set({ expandedFolders: new Set(folders) });
      }
    } catch {
      // Failed to load expanded folders - ignore
    }
  },

  saveExpandedFolders: () => {
    try {
      const folders = Array.from(get().expandedFolders);
      localStorage.setItem('expandedFolders', JSON.stringify(folders));
    } catch {
      // Failed to save expanded folders - ignore
    }
  },
}));
