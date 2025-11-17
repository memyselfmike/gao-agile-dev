/**
 * MonacoDiffViewer - Monaco diff editor wrapper for commit diffs
 * Story 39.26: Monaco Diff Viewer for Commits
 */
import { useEffect, useRef, useState } from 'react';
import * as monaco from 'monaco-editor';
import { useTheme } from 'next-themes';
import type { FileChange } from '@/types/git';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MonacoDiffViewerProps {
  file: FileChange | undefined;
  viewMode: 'split' | 'unified';
}

export function MonacoDiffViewer({ file, viewMode }: MonacoDiffViewerProps) {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<monaco.editor.IStandaloneDiffEditor | null>(null);
  const [showLargeDiff, setShowLargeDiff] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !file) return;

    // Check if diff is large
    const totalLines = (file.insertions || 0) + (file.deletions || 0);
    const isLargeDiff = totalLines > 1000;

    // Don't render large diffs unless user explicitly expands
    if (isLargeDiff && !showLargeDiff) {
      return;
    }

    // Detect language from file extension
    const fileExtension = '.' + (file.path.split('.').pop() || '');
    const languages = monaco.languages.getLanguages();
    const detectedLanguage =
      languages.find((lang) => lang.extensions?.includes(fileExtension))?.id || 'plaintext';

    // Create Monaco diff editor
    const diffEditor = monaco.editor.createDiffEditor(containerRef.current, {
      enableSplitViewResizing: true,
      renderSideBySide: viewMode === 'split',
      readOnly: true,
      automaticLayout: true,
      scrollBeyondLastLine: false,
      minimap: { enabled: false },
      lineNumbers: 'on',
      theme: theme === 'dark' ? 'vs-dark' : 'vs-light',
      fontSize: 14,
      wordWrap: 'off',
      renderOverviewRuler: true,
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
      },
    });

    // Create original and modified models
    const originalModel = monaco.editor.createModel(
      file.original_content || '',
      detectedLanguage
    );
    const modifiedModel = monaco.editor.createModel(
      file.modified_content || '',
      detectedLanguage
    );

    // Set models
    diffEditor.setModel({
      original: originalModel,
      modified: modifiedModel,
    });

    editorRef.current = diffEditor;

    // Cleanup on unmount
    return () => {
      originalModel.dispose();
      modifiedModel.dispose();
      diffEditor.dispose();
      editorRef.current = null;
    };
  }, [file, viewMode, theme, showLargeDiff]);

  // Update view mode dynamically
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        renderSideBySide: viewMode === 'split',
      });
    }
  }, [viewMode]);

  if (!file) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Select a file to view diff
      </div>
    );
  }

  const totalLines = (file.insertions || 0) + (file.deletions || 0);
  const isLargeDiff = totalLines > 1000;

  return (
    <div className="relative h-full w-full flex flex-col">
      {/* Large diff warning */}
      {isLargeDiff && !showLargeDiff && (
        <div className="flex h-full items-center justify-center p-8">
          <Alert className="max-w-lg">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="flex flex-col gap-4">
              <div>
                <p className="font-semibold">Large diff detected ({totalLines.toLocaleString()} lines)</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Rendering this diff may be slow. Performance may be affected.
                </p>
              </div>
              <Button onClick={() => setShowLargeDiff(true)} variant="default" size="sm">
                Expand anyway
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Monaco diff editor */}
      {(!isLargeDiff || showLargeDiff) && (
        <div ref={containerRef} className="flex-1 w-full" />
      )}
    </div>
  );
}
