/**
 * Thread Store - Manages message threading state
 *
 * Story 39.35: Thread Panel UI (Slide-In from Right)
 *
 * Handles thread panel state, thread messages, and real-time updates
 */
import { create } from 'zustand';
import type { ChatMessage } from '../types';

export interface Thread {
  id: string;
  parentMessageId: string;
  parentMessage: ChatMessage;
  replies: ChatMessage[];
  replyCount: number;
  conversationId: string; // Agent ID or channel ID
  conversationType: 'dm' | 'channel';
  createdAt: string;
  updatedAt: string;
}

interface ThreadState {
  // Active thread (null when panel closed)
  activeThread: Thread | null;

  // Thread panel loading state
  isLoading: boolean;

  // Thread reply sending state
  isSendingReply: boolean;

  // Error state
  error: string | null;

  // Thread counts for all messages (message_id -> count)
  threadCounts: Record<string, number>;

  // Actions
  openThread: (parentMessageId: string, conversationId: string, conversationType: 'dm' | 'channel') => Promise<void>;
  closeThread: () => void;
  addThreadReply: (content: string) => Promise<void>;
  updateThreadCount: (messageId: string, count: number) => void;
  setThreadCounts: (counts: Record<string, number>) => void;

  // Real-time updates
  handleThreadReply: (reply: ChatMessage) => void;
  handleThreadUpdated: (threadId: string, replyCount: number) => void;
}

export const useThreadStore = create<ThreadState>((set, get) => ({
  activeThread: null,
  isLoading: false,
  isSendingReply: false,
  error: null,
  threadCounts: {},

  openThread: async (parentMessageId, conversationId, conversationType) => {
    set({ isLoading: true, error: null });

    try {
      // First, create or get thread
      const createResponse = await fetch('/api/threads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parentMessageId,
          conversationId,
          conversationType,
        }),
      });

      if (!createResponse.ok) {
        throw new Error('Failed to create thread');
      }

      const { threadId } = await createResponse.json();

      // Then fetch thread details and messages
      const fetchResponse = await fetch(`/api/threads/${threadId}`);

      if (!fetchResponse.ok) {
        throw new Error('Failed to load thread');
      }

      const thread: Thread = await fetchResponse.json();

      set({
        activeThread: thread,
        isLoading: false,
        error: null,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      set({
        error: errorMessage,
        isLoading: false,
        activeThread: null,
      });
    }
  },

  closeThread: () => {
    set({
      activeThread: null,
      error: null,
    });
  },

  addThreadReply: async (content: string) => {
    const { activeThread } = get();
    if (!activeThread) return;

    set({ isSendingReply: true, error: null });

    try {
      const response = await fetch(`/api/threads/${activeThread.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (!response.ok) {
        throw new Error('Failed to send reply');
      }

      const newReply: ChatMessage = await response.json();

      // Add reply to active thread
      set((state) => ({
        activeThread: state.activeThread
          ? {
              ...state.activeThread,
              replies: [...state.activeThread.replies, newReply],
              replyCount: state.activeThread.replyCount + 1,
            }
          : null,
        isSendingReply: false,
        // Update thread count
        threadCounts: {
          ...state.threadCounts,
          [activeThread.parentMessageId]: (state.activeThread?.replyCount || 0) + 1,
        },
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      set({
        error: errorMessage,
        isSendingReply: false,
      });
    }
  },

  updateThreadCount: (messageId: string, count: number) => {
    set((state) => ({
      threadCounts: {
        ...state.threadCounts,
        [messageId]: count,
      },
    }));
  },

  setThreadCounts: (counts: Record<string, number>) => {
    set({ threadCounts: counts });
  },

  // Handle real-time thread reply via WebSocket
  handleThreadReply: (reply: ChatMessage) => {
    set((state) => {
      if (!state.activeThread) return state;

      // Only update if reply is for active thread
      return {
        activeThread: {
          ...state.activeThread,
          replies: [...state.activeThread.replies, reply],
          replyCount: state.activeThread.replyCount + 1,
        },
        threadCounts: {
          ...state.threadCounts,
          [state.activeThread.parentMessageId]: state.activeThread.replyCount + 1,
        },
      };
    });
  },

  // Handle real-time thread count update via WebSocket
  handleThreadUpdated: (threadId: string, replyCount: number) => {
    set((state) => {
      // Update active thread if it matches
      if (state.activeThread && state.activeThread.id === threadId) {
        return {
          activeThread: {
            ...state.activeThread,
            replyCount,
          },
        };
      }
      return state;
    });
  },
}));
