/**
 * GAO-Dev Web Interface - Main Application
 */
import { useEffect, useState } from 'react';
import { createWebSocketClient, WebSocketClient } from './lib/websocket';
import { useChatStore } from './stores/chatStore';
import { useActivityStore } from './stores/activityStore';
import { useSessionStore } from './stores/sessionStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { RootLayout } from './components/layout/RootLayout';
import { LoadingSpinner } from './components/LoadingSpinner';
import type { WebSocketMessage } from './types';

function App() {
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const addActivity = useActivityStore((state) => state.addEvent);
  const addMessage = useChatStore((state) => state.addMessage);
  const setSessionToken = useSessionStore((state) => state.setSessionToken);

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
                addActivity(message.payload as never);
                break;
              default:
                addActivity({
                  type: 'info',
                  message: `Unknown message type: ${message.type}`,
                });
            }
          },
          () => {
            setIsConnected(true);
            addActivity({
              type: 'success',
              message: 'Connected to GAO-Dev backend',
            });
          },
          () => {
            setIsConnected(false);
            addActivity({
              type: 'warning',
              message: 'Disconnected from GAO-Dev backend',
            });
          },
          (error) => {
            addActivity({
              type: 'error',
              message: `WebSocket error: ${error.type}`,
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
          type: 'error',
          message: `Failed to initialize WebSocket: ${error}`,
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
