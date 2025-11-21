/**
 * Chat Store - Manages chat messages and active agent
 *
 * Story 39.7: Enhanced with streaming and reasoning support
 * Story 39.8: Multi-agent chat switching with per-agent history
 */
import { create } from 'zustand';
import type { ChatMessage, Agent } from '../types';

interface ChatState {
  messages: ChatMessage[];
  activeAgent: Agent | null;
  isTyping: boolean;
  streamingMessageId: string | null;
  streamingContent: string;
  isThinking: boolean;
  thinkingContent: string;
  // Per-agent message history
  agentHistory: Record<string, ChatMessage[]>;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setActiveAgent: (agent: Agent | null) => void;
  setIsTyping: (isTyping: boolean) => void;
  addStreamingChunk: (chunk: string) => void;
  finishStreamingMessage: (agentName?: string) => void;
  setThinking: (isThinking: boolean, content?: string) => void;
  clearMessages: () => void;
  // Switch agent and load their history
  switchAgent: (agent: Agent) => void;
}

// Validate that an agent object has all required properties
const isValidAgent = (agent: any): agent is Agent => {
  return (
    agent &&
    typeof agent === 'object' &&
    typeof agent.id === 'string' &&
    typeof agent.name === 'string' &&
    typeof agent.role === 'string' &&
    typeof agent.status === 'string'
  );
};

// Load from localStorage on init
const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem('gao-dev-chat-storage');
    if (stored) {
      const parsed = JSON.parse(stored);
      // Validate activeAgent structure before using it
      const activeAgent = isValidAgent(parsed.activeAgent) ? parsed.activeAgent : null;
      return {
        activeAgent,
        agentHistory: parsed.agentHistory || {},
      };
    }
  } catch (e) {
    console.error('Failed to load chat storage:', e);
    // Clear corrupted storage
    localStorage.removeItem('gao-dev-chat-storage');
  }
  return { activeAgent: null, agentHistory: {} };
};

const initialStorage = loadFromStorage();

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  activeAgent: initialStorage.activeAgent,
  isTyping: false,
  streamingMessageId: null,
  streamingContent: '',
  isThinking: false,
  thinkingContent: '',
  agentHistory: initialStorage.agentHistory,

  addMessage: (message) =>
    set((state) => {
      const newMessage: ChatMessage = {
        ...message,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };

      const updatedMessages = [...state.messages, newMessage];

      // Save to current agent's history
      const agentId = state.activeAgent?.id || 'brian';
      const updatedHistory = {
        ...state.agentHistory,
        [agentId]: updatedMessages,
      };

      // Persist to localStorage
      localStorage.setItem(
        'gao-dev-chat-storage',
        JSON.stringify({
          activeAgent: state.activeAgent,
          agentHistory: updatedHistory,
        })
      );

      return {
        messages: updatedMessages,
        agentHistory: updatedHistory,
      };
    }),

  setActiveAgent: (agent) => set({ activeAgent: agent }),

  setIsTyping: (isTyping) => set({ isTyping }),

  addStreamingChunk: (chunk: string) =>
    set((state) => {
      const agentName = state.activeAgent?.name || 'Brian';

      // If no streaming message, create one
      if (!state.streamingMessageId) {
        const newId = crypto.randomUUID();
        const newMessage: ChatMessage = {
          id: newId,
          role: 'agent' as const,
          content: chunk,
          timestamp: Date.now(),
          agentName,
        };

        return {
          streamingMessageId: newId,
          streamingContent: chunk,
          messages: [...state.messages, newMessage],
        };
      }

      // Update existing streaming message
      const updatedContent = state.streamingContent + chunk;
      return {
        streamingContent: updatedContent,
        messages: state.messages.map((msg) =>
          msg.id === state.streamingMessageId ? { ...msg, content: updatedContent } : msg
        ),
      };
    }),

  finishStreamingMessage: (agentName?: string) =>
    set((state) => {
      if (!state.streamingMessageId) return state;

      const updatedMessages = state.messages.map((msg) =>
        msg.id === state.streamingMessageId && agentName ? { ...msg, agentName } : msg
      );

      // Save to current agent's history
      const agentId = state.activeAgent?.id || 'brian';
      const updatedHistory = {
        ...state.agentHistory,
        [agentId]: updatedMessages,
      };

      // Persist to localStorage
      localStorage.setItem(
        'gao-dev-chat-storage',
        JSON.stringify({
          activeAgent: state.activeAgent,
          agentHistory: updatedHistory,
        })
      );

      return {
        streamingMessageId: null,
        streamingContent: '',
        isTyping: false,
        messages: updatedMessages,
        agentHistory: updatedHistory,
      };
    }),

  setThinking: (isThinking: boolean, content: string = '') =>
    set({ isThinking, thinkingContent: content }),

  clearMessages: () =>
    set({
      messages: [],
      streamingMessageId: null,
      streamingContent: '',
      isThinking: false,
      thinkingContent: '',
    }),

  switchAgent: (agent: Agent) =>
    set((state) => {
      // Save current messages to current agent's history
      const currentAgentId = state.activeAgent?.id || 'brian';
      const updatedHistory = {
        ...state.agentHistory,
        [currentAgentId]: state.messages,
      };

      // Load new agent's history or start fresh
      const newMessages = updatedHistory[agent.id] || [];

      // Persist to localStorage
      localStorage.setItem(
        'gao-dev-chat-storage',
        JSON.stringify({
          activeAgent: agent,
          agentHistory: updatedHistory,
        })
      );

      return {
        activeAgent: agent,
        messages: newMessages,
        agentHistory: updatedHistory,
        streamingMessageId: null,
        streamingContent: '',
        isTyping: false,
        isThinking: false,
        thinkingContent: '',
      };
    }),
}));
