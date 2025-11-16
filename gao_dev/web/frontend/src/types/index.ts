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
  id: string;
  name: string;
  role: string;
  description: string;
  icon?: string;
  status?: 'idle' | 'active' | 'busy';
}

// Activity types
export type ActivityEventType = 'Workflow' | 'Chat' | 'File' | 'State' | 'Ceremony' | 'Git';

export interface ActivityEvent {
  id: string;
  sequence?: number; // For detecting missed events
  type: ActivityEventType;
  agent: string;
  action: string;
  summary: string;
  timestamp: number;
  details?: {
    reasoning?: string;
    toolCalls?: string[];
    fileDiffs?: string;
    [key: string]: unknown;
  };
  severity?: 'info' | 'success' | 'warning' | 'error';
}

// File types
export interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  icon?: string; // File icon type (for files only)
  size?: number; // File size in bytes (for files only)
  modified?: string; // ISO timestamp (for files only)
  recentlyChanged?: boolean; // Highlighted if changed in last 5 minutes
}

export interface OpenFile {
  path: string;
  content: string;
  language: string; // Monaco language/mode
  modified: boolean; // User has unsaved changes
  saved: boolean; // File saved to disk
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
