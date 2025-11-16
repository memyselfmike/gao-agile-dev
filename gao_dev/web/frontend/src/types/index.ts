/**
 * GAO-Dev Web Interface - Type Definitions
 */

// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: number;
  agentName?: string;
}

export interface Agent {
  name: string;
  role: string;
  status: 'idle' | 'active' | 'busy';
}

// Activity types
export interface ActivityEvent {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: number;
  details?: Record<string, unknown>;
}

// File types
export interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

export interface OpenFile {
  path: string;
  content: string;
  modified: boolean;
}

// Session types
export interface SessionState {
  isLocked: boolean;
  isReadOnly: boolean;
  sessionToken: string | null;
  lockedBy?: string;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: unknown;
}
