/**
 * Chat Store - Manages chat messages and active agent
 *
 * Story 39.7: Enhanced with streaming and reasoning support
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
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setActiveAgent: (agent: Agent | null) => void;
  setIsTyping: (isTyping: boolean) => void;
  addStreamingChunk: (chunk: string) => void;
  finishStreamingMessage: (agentName?: string) => void;
  setThinking: (isThinking: boolean, content?: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  activeAgent: null,
  isTyping: false,
  streamingMessageId: null,
  streamingContent: '',
  isThinking: false,
  thinkingContent: '',

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: Date.now(),
        },
      ],
    })),

  setActiveAgent: (agent) => set({ activeAgent: agent }),

  setIsTyping: (isTyping) => set({ isTyping }),

  addStreamingChunk: (chunk: string) =>
    set((state) => {
      // If no streaming message, create one
      if (!state.streamingMessageId) {
        const newId = crypto.randomUUID();
        return {
          streamingMessageId: newId,
          streamingContent: chunk,
          messages: [
            ...state.messages,
            {
              id: newId,
              role: 'agent' as const,
              content: chunk,
              timestamp: Date.now(),
              agentName: 'Brian',
            },
          ],
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

      return {
        streamingMessageId: null,
        streamingContent: '',
        isTyping: false,
        messages: state.messages.map((msg) =>
          msg.id === state.streamingMessageId && agentName
            ? { ...msg, agentName }
            : msg
        ),
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
}));
