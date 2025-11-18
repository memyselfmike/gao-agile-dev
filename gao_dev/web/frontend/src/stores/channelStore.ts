/**
 * Channel Store - Manages ceremony channel state
 *
 * Story 39.33: Channels Section - Ceremony Channels UI
 */
import { create } from 'zustand';
import type { Channel, ChannelMessage } from '../types';

interface ChannelState {
  activeChannel: Channel | null;
  channels: Channel[];
  messages: ChannelMessage[];
  // Channel selection
  selectChannel: (channel: Channel) => void;
  // Message management
  setMessages: (messages: ChannelMessage[]) => void;
  addMessage: (message: ChannelMessage) => void;
  // Channel list management
  setChannels: (channels: Channel[]) => void;
  updateChannel: (channelId: string, updates: Partial<Channel>) => void;
}

export const useChannelStore = create<ChannelState>((set) => ({
  activeChannel: null,
  channels: [],
  messages: [],

  selectChannel: (channel) =>
    set({
      activeChannel: channel,
      messages: [], // Clear messages on channel switch (will be loaded by ChannelView)
    }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  setChannels: (channels) => set({ channels }),

  updateChannel: (channelId, updates) =>
    set((state) => ({
      channels: state.channels.map((ch) =>
        ch.id === channelId ? { ...ch, ...updates } : ch
      ),
      activeChannel:
        state.activeChannel?.id === channelId
          ? { ...state.activeChannel, ...updates }
          : state.activeChannel,
    })),
}));
