/**
 * Chat Store - Manages chat messages and active agent
 */
import { create } from 'zustand';
import type { ChatMessage, Agent } from '../types';

interface ChatState {
  messages: ChatMessage[];
  activeAgent: Agent | null;
  isTyping: boolean;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setActiveAgent: (agent: Agent | null) => void;
  setIsTyping: (isTyping: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  activeAgent: null,
  isTyping: false,

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

  clearMessages: () => set({ messages: [] }),
}));
