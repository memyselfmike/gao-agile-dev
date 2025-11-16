/**
 * Files Store - Manages file tree and open files
 */
import { create } from 'zustand';
import type { FileNode, OpenFile } from '../types';

interface FilesState {
  fileTree: FileNode[];
  openFiles: OpenFile[];
  activeFilePath: string | null;
  setFileTree: (tree: FileNode[]) => void;
  openFile: (file: OpenFile) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  updateFileContent: (path: string, content: string) => void;
}

export const useFilesStore = create<FilesState>((set) => ({
  fileTree: [],
  openFiles: [],
  activeFilePath: null,

  setFileTree: (tree) => set({ fileTree: tree }),

  openFile: (file) =>
    set((state) => {
      const exists = state.openFiles.find((f) => f.path === file.path);
      if (exists) {
        return { activeFilePath: file.path };
      }
      return {
        openFiles: [...state.openFiles, file],
        activeFilePath: file.path,
      };
    }),

  closeFile: (path) =>
    set((state) => ({
      openFiles: state.openFiles.filter((f) => f.path !== path),
      activeFilePath: state.activeFilePath === path ? null : state.activeFilePath,
    })),

  setActiveFile: (path) => set({ activeFilePath: path }),

  updateFileContent: (path, content) =>
    set((state) => ({
      openFiles: state.openFiles.map((f) =>
        f.path === path ? { ...f, content, modified: true } : f
      ),
    })),
}));
