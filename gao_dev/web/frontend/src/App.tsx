/**
 * GAO-Dev Web Interface - Main Application
 */
import { useEffect, useState } from 'react';
import { createWebSocketClient, WebSocketClient } from './lib/websocket';
import { useChatStore } from './stores/chatStore';
import { useActivityStore } from './stores/activityStore';
import { useSessionStore } from './stores/sessionStore';
import { useFilesStore } from './stores/filesStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { RootLayout } from './components/layout/RootLayout';
import { LoadingSpinner } from './components/LoadingSpinner';
import { toast } from 'sonner';
import type { WebSocketMessage } from './types';

function App() {
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const addActivity = useActivityStore((state) => state.addEvent);
  const addEventWithSequence = useActivityStore((state) => state.addEventWithSequence);
  const addMessage = useChatStore((state) => state.addMessage);
  const setSessionToken = useSessionStore((state) => state.setSessionToken);
  const { addRecentlyChanged, setFileTree, closeFile, openFiles } = useFilesStore();

  useEffect(() => {
    // Create WebSocket connection on mount
    const initWebSocket = async () => {
      try {
        const client = await createWebSocketClient(
          (message: WebSocketMessage) => {
            // Handle incoming WebSocket messages
            switch (message.type) {
              case 'chat_message':
                addMessage(message.payload as never);
                break;
              case 'activity':
                // Use addEventWithSequence for events with sequence numbers
                const event = message.payload as never;
                if ((event as { sequence?: number }).sequence !== undefined) {
                  addEventWithSequence(event);
                } else {
                  addActivity(event);
                }
                break;

              // File events (Story 39.13)
              case 'file.created':
              case 'file.modified': {
                const payload = message.payload as { path: string; agent?: string; commitMessage?: string };

                // Mark as recently changed
                addRecentlyChanged(payload.path);

                // Reload file tree
                const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
                fetch(`${apiUrl}/api/files/tree`, { credentials: 'include' })
                  .then((res) => res.json())
                  .then((data) => setFileTree(data.tree || []))
                  .catch(() => {
                    // Failed to reload file tree - ignore
                  });

                // Show toast notification
                const fileName = payload.path.split('/').pop();
                const actionText = message.type === 'file.created' ? 'created' : 'modified';
                toast.info(`File ${actionText}`, {
                  description: `${payload.agent || 'Agent'} ${actionText} ${fileName}`,
                });
                break;
              }

              case 'file.deleted': {
                const payload = message.payload as { path: string; agent?: string };

                // Close file if open
                const isOpen = openFiles.some((f) => f.path === payload.path);
                if (isOpen) {
                  closeFile(payload.path);
                  toast.warning('File deleted', {
                    description: `${payload.path} was deleted by ${payload.agent || 'an agent'}`,
                  });
                }

                // Reload file tree
                const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
                fetch(`${apiUrl}/api/files/tree`, { credentials: 'include' })
                  .then((res) => res.json())
                  .then((data) => setFileTree(data.tree || []))
                  .catch(() => {
                    // Failed to reload file tree - ignore
                  });
                break;
              }

              default:
                addActivity({
                  type: 'Workflow',
                  agent: 'System',
                  action: 'received unknown message',
                  summary: `Unknown message type: ${message.type}`,
                  severity: 'info',
                });
            }
          },
          () => {
            setIsConnected(true);
            addActivity({
              type: 'Workflow',
              agent: 'System',
              action: 'established connection',
              summary: 'Connected to GAO-Dev backend',
              severity: 'success',
            });
          },
          () => {
            setIsConnected(false);
            addActivity({
              type: 'Workflow',
              agent: 'System',
              action: 'lost connection',
              summary: 'Disconnected from GAO-Dev backend',
              severity: 'warning',
            });
          },
          (error) => {
            addActivity({
              type: 'Workflow',
              agent: 'System',
              action: 'encountered error',
              summary: `WebSocket error: ${error.type}`,
              severity: 'error',
            });
          }
        );

        setWsClient(client);

        // Fetch session token
        const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
        const response = await fetch(`${apiUrl}/api/session/token`, {
          credentials: 'include',
        });
        if (response.ok) {
          const data = (await response.json()) as { token: string };
          setSessionToken(data.token);
        }
      } catch (error) {
        addActivity({
          type: 'Workflow',
          agent: 'System',
          action: 'failed to initialize',
          summary: `Failed to initialize WebSocket: ${error}`,
          severity: 'error',
        });
      } finally {
        setIsInitializing(false);
      }
    };

    initWebSocket();

    // Cleanup on unmount
    return () => {
      wsClient?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isInitializing) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <LoadingSpinner size="lg" message="Connecting to GAO-Dev..." />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <RootLayout isConnected={isConnected} projectName="GAO-Dev" />
    </ErrorBoundary>
  );
}

export default App;
