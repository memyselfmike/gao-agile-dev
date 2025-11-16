/**
 * MonacoEditor - VS Code-style editor with syntax highlighting
 * Stories 39.12 & 39.14: Monaco Editor Integration
 */
import { useEffect, useRef } from 'react';
import Editor, { type Monaco } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { useSessionStore } from '@/stores/sessionStore';
import { useTheme } from 'next-themes';

interface MonacoEditorProps {
  content: string;
  language: string;
  onChange?: (value: string) => void;
}

export function MonacoEditor({ content, language, onChange }: MonacoEditorProps) {
  const { isReadOnly } = useSessionStore();
  const { theme } = useTheme();
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);

  const handleEditorDidMount = (
    editor: monaco.editor.IStandaloneCodeEditor,
    monacoInstance: Monaco
  ) => {
    editorRef.current = editor;
    monacoRef.current = monacoInstance;

    // Configure editor options
    editor.updateOptions({
      readOnly: isReadOnly,
      minimap: { enabled: true },
      lineNumbers: 'on',
      folding: true,
      wordWrap: 'on',
      automaticLayout: true,
    });
  };

  // Update read-only state when session lock changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        readOnly: isReadOnly,
      });
    }
  }, [isReadOnly]);

  // Cleanup Monaco model on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (editorRef.current) {
        const model = editorRef.current.getModel();
        if (model) {
          model.dispose();
        }
        editorRef.current.dispose();
        editorRef.current = null;
      }
    };
  }, []);

  return (
    <div className="h-full w-full">
      <Editor
        height="100%"
        language={language}
        value={content}
        theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
        onChange={(value) => {
          if (!isReadOnly && onChange && value !== undefined) {
            onChange(value);
          }
        }}
        onMount={handleEditorDidMount}
        options={{
          readOnly: isReadOnly,
          minimap: { enabled: true },
          lineNumbers: 'on',
          folding: true,
          wordWrap: 'on',
          automaticLayout: true,
          fontSize: 14,
          tabSize: 2,
          insertSpaces: true,
          scrollBeyondLastLine: false,
        }}
      />
    </div>
  );
}
