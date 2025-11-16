/**
 * Files Tab - File tree and Monaco editor
 * Epic 39.4: File Management
 */
import { useEffect, useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { FileTree } from '@/components/files/FileTree';
import { MonacoEditor } from '@/components/editor/MonacoEditor';
import { EditorTabs } from '@/components/editor/EditorTabs';
import { EditorToolbar } from '@/components/editor/EditorToolbar';
import { useFilesStore } from '@/stores/filesStore';
import { FileText } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

export function FilesTab() {
  const { setFileTree, openFile, activeFilePath, openFiles, updateFileContent } = useFilesStore();
  const [isLoading, setIsLoading] = useState(true);

  // Load file tree on mount
  useEffect(() => {
    const loadFileTree = async () => {
      try {
        const response = await fetch(`${API_URL}/api/files/tree`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to load file tree');
        }

        const data = await response.json();
        setFileTree(data.tree || []);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        toast.error('Failed to load file tree', {
          description: message,
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadFileTree();
  }, [setFileTree]);

  // Handle file selection from tree
  const handleFileSelect = async (path: string) => {
    // Check if already open
    const existing = openFiles.find((f) => f.path === path);
    if (existing) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/files/content?path=${encodeURIComponent(path)}`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load file content');
      }

      const data = await response.json();

      openFile({
        path: data.path,
        content: data.content,
        language: data.language || 'plaintext',
        modified: false,
        saved: true,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to open file', {
        description: message,
      });
    }
  };

  // Get active file
  const activeFile = openFiles.find((f) => f.path === activeFilePath);

  return (
    <div className="flex h-full flex-col">
      <PanelGroup direction="horizontal">
        {/* File tree panel */}
        <Panel defaultSize={25} minSize={15} maxSize={40}>
          <div className="h-full border-r">
            {isLoading ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">Loading files...</p>
              </div>
            ) : (
              <FileTree onFileSelect={handleFileSelect} />
            )}
          </div>
        </Panel>

        {/* Resize handle */}
        <PanelResizeHandle className="w-1 bg-border hover:bg-primary/20 transition-colors" />

        {/* Editor panel */}
        <Panel defaultSize={75}>
          <div className="flex h-full flex-col">
            {openFiles.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-4">
                <FileText className="h-16 w-16 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">
                  Select a file from the tree to view or edit
                </p>
              </div>
            ) : (
              <>
                {/* Editor tabs */}
                <EditorTabs />

                {/* Editor toolbar */}
                {activeFile && <EditorToolbar />}

                {/* Monaco editor */}
                <div className="flex-1 overflow-hidden">
                  {activeFile && (
                    <MonacoEditor
                      key={activeFile.path}
                      content={activeFile.content}
                      language={activeFile.language}
                      onChange={(value) => updateFileContent(activeFile.path, value)}
                    />
                  )}
                </div>
              </>
            )}
          </div>
        </Panel>
      </PanelGroup>
    </div>
  );
}
