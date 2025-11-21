/**
 * GAO-Dev Web Interface - Main Application
 */
import { useEffect, useState, useRef } from 'react';
import { createWebSocketClient, WebSocketClient } from './lib/websocket';
import { apiRequest } from './lib/api';
import { useChatStore } from './stores/chatStore';
import { useActivityStore } from './stores/activityStore';
import { useSessionStore } from './stores/sessionStore';
import { useFilesStore } from './stores/filesStore';
import { useWorkflowStore } from './stores/workflowStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { RootLayout } from './components/layout/RootLayout';
import { LoadingSpinner } from './components/LoadingSpinner';
import { SearchResults } from './components/search';
import { OnboardingWizard } from './components/onboarding';
import { toast } from 'sonner';
import type { WebSocketMessage } from './types';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [needsOnboarding, setNeedsOnboarding] = useState<boolean | null>(null);
  const wsClientRef = useRef<WebSocketClient | null>(null);
  const addActivity = useActivityStore((state) => state.addEvent);
  const addEventWithSequence = useActivityStore((state) => state.addEventWithSequence);
  const addMessage = useChatStore((state) => state.addMessage);
  const setSessionToken = useSessionStore((state) => state.setSessionToken);
  const { addRecentlyChanged, setFileTree, closeFile, openFiles } = useFilesStore();
  const { addWorkflow, updateWorkflow } = useWorkflowStore();

  useEffect(() => {
    // Flag to prevent state updates after unmount (StrictMode fix)
    let isActive = true;

    // Check onboarding status first
    const checkOnboardingStatus = async () => {
      try {
        const response = await apiRequest('/api/onboarding/status');
        if (response.ok) {
          const data = await response.json();
          // Check if onboarding is complete
          const isComplete = data.data?.is_complete ?? false;
          if (isActive) {
            setNeedsOnboarding(!isComplete);
          }
        } else {
          // If onboarding API fails, assume we need onboarding
          if (isActive) {
            setNeedsOnboarding(true);
          }
        }
      } catch (error) {
        // If error, assume we need onboarding (fail-safe)
        console.error('Failed to check onboarding status:', error);
        if (isActive) {
          setNeedsOnboarding(true);
        }
      }
    };

    // Create WebSocket connection after onboarding check
    const initWebSocket = async () => {
      try {
        const client = await createWebSocketClient(
          (message: WebSocketMessage) => {
            // Handle incoming WebSocket messages
            switch (message.type) {
              // Chat events (Story 39.7) - using message.data from backend WebEvent
              case 'chat.message_sent': {
                const data = (message as { data?: { role: string; content: string; agentName?: string } }).data;
                if (data) {
                  addMessage({
                    role: data.role as 'user' | 'agent',
                    content: data.content,
                    agentName: data.agentName,
                  });
                }
                break;
              }

              case 'chat.streaming_chunk': {
                const data = (message as { data?: { chunk: string; role: string; agentName: string } }).data;
                if (data) {
                  const chatState = useChatStore.getState();
                  chatState.setIsTyping(true);
                  chatState.addStreamingChunk(data.chunk);
                }
                break;
              }

              case 'chat.message_received': {
                const data = (message as { data?: { role: string; content: string; agentName: string } }).data;
                if (data) {
                  const chatState = useChatStore.getState();
                  chatState.finishStreamingMessage(data.agentName);
                }
                break;
              }

              case 'chat.thinking_started': {
                const chatState = useChatStore.getState();
                chatState.setThinking(true, 'Analyzing your request...');
                break;
              }

              case 'chat.thinking_finished': {
                const chatState = useChatStore.getState();
                chatState.setThinking(false);
                break;
              }

              // Note: Legacy 'chat_message' event removed - using new chat.message_sent/received events

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
                apiRequest('/api/files/tree')
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
                apiRequest('/api/files/tree')
                  .then((res) => res.json())
                  .then((data) => setFileTree(data.tree || []))
                  .catch(() => {
                    // Failed to reload file tree - ignore
                  });
                break;
              }

              // Workflow events (Story 39.20)
              case 'workflow.started': {
                const payload = message.payload as {
                  workflow_id: string;
                  workflow_name: string;
                  agent: string;
                  started_at: string;
                  epic?: number;
                  story_num?: number;
                };

                // Add new workflow to timeline
                addWorkflow({
                  id: 0, // Will be set by backend
                  workflow_id: payload.workflow_id,
                  workflow_name: payload.workflow_name,
                  status: 'running',
                  started_at: payload.started_at,
                  completed_at: null,
                  duration: null,
                  agent: payload.agent,
                  epic: payload.epic || 0,
                  story_num: payload.story_num || 0,
                });

                // Show toast notification
                toast.info('Workflow started', {
                  description: `${payload.workflow_name} started by ${payload.agent}`,
                });
                break;
              }

              case 'workflow.completed': {
                const payload = message.payload as {
                  workflow_id: string;
                  completed_at: string;
                  duration?: number;
                };

                // Update workflow status
                updateWorkflow(payload.workflow_id, {
                  status: 'completed',
                  completed_at: payload.completed_at,
                  duration: payload.duration || null,
                });

                // Show toast notification
                toast.success('Workflow completed', {
                  description: `Workflow ${payload.workflow_id} finished successfully`,
                });
                break;
              }

              case 'workflow.failed': {
                const payload = message.payload as {
                  workflow_id: string;
                  error?: string;
                };

                // Update workflow status
                updateWorkflow(payload.workflow_id, {
                  status: 'failed',
                });

                // Show toast notification
                toast.error('Workflow failed', {
                  description: payload.error || `Workflow ${payload.workflow_id} failed`,
                });
                break;
              }

              case 'workflow.cancelled': {
                const payload = message.payload as {
                  workflow_id: string;
                };

                // Update workflow status
                updateWorkflow(payload.workflow_id, {
                  status: 'cancelled',
                });

                // Show toast notification
                toast.warning('Workflow cancelled', {
                  description: `Workflow ${payload.workflow_id} was cancelled`,
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

        // Check if component was unmounted during async operation (StrictMode)
        if (!isActive) {
          client.disconnect();
          return;
        }

        wsClientRef.current = client;

        // Fetch session token
        const response = await apiRequest('/api/session/token');
        if (response.ok && isActive) {
          const data = (await response.json()) as { token: string };
          setSessionToken(data.token);
        } else if (!response.ok) {
          console.error('Failed to fetch session token:', response.status);
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
        if (isActive) {
          setIsInitializing(false);
        }
      }
    };

    // Initialize app
    const init = async () => {
      await checkOnboardingStatus();
      // Only init WebSocket if onboarding is complete
      const statusResponse = await apiRequest('/api/onboarding/status');
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        const isComplete = statusData.data?.is_complete ?? false;
        if (isComplete) {
          await initWebSocket();
        } else {
          // Onboarding needed - just stop loading spinner
          if (isActive) {
            setIsInitializing(false);
          }
        }
      }
    };

    init();

    // Cleanup on unmount - use ref to access current client
    return () => {
      isActive = false;
      wsClientRef.current?.disconnect();
      wsClientRef.current = null;
    };
    // eslint-disable-next-line react-hooks-rules-of-hooks
  }, []);

  if (isInitializing) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <LoadingSpinner size="lg" message="Connecting to GAO-Dev..." />
      </div>
    );
  }

  // Show onboarding wizard if needed
  if (needsOnboarding) {
    return (
      <ErrorBoundary>
        <OnboardingWizard
          onComplete={() => {
            // Onboarding complete, reload to initialize main app
            window.location.reload();
          }}
        />
      </ErrorBoundary>
    );
  }

  // Show main application
  return (
    <ErrorBoundary>
      <RootLayout isConnected={isConnected} projectName="GAO-Dev" />
      <SearchResults />
    </ErrorBoundary>
  );
}

export default App;
