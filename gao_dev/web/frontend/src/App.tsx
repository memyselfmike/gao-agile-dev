/**
 * GAO-Dev Web Interface - Main Application
 */
import { useEffect, useState } from 'react';
import { createWebSocketClient, WebSocketClient } from './lib/websocket';
import { useChatStore } from './stores/chatStore';
import { useActivityStore } from './stores/activityStore';
import { useSessionStore } from './stores/sessionStore';
import type { WebSocketMessage } from './types';

function App() {
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
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
      }
    };

    initWebSocket();

    // Cleanup on unmount
    return () => {
      wsClient?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">GAO-Dev Web Interface</h1>
            <div className="flex items-center gap-2">
              <div
                className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
              />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-semibold text-gray-900">Welcome to GAO-Dev</h2>
            <p className="text-gray-600">
              The autonomous AI development orchestration system is ready. This is the initial
              frontend setup.
            </p>
            <div className="mt-4">
              <p className="text-sm text-gray-500">
                WebSocket Status: {isConnected ? '✓ Connected' : '✗ Disconnected'}
              </p>
              <p className="text-sm text-gray-500">
                API URL: {import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000'}
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            GAO-Dev v1.0.0 - Autonomous AI Development System
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
