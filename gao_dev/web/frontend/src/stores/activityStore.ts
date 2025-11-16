/**
 * Activity Store - Manages activity stream events
 */
import { create } from 'zustand';
import type { ActivityEvent } from '../types';

interface ActivityState {
  events: ActivityEvent[];
  maxEvents: number;
  addEvent: (event: Omit<ActivityEvent, 'id' | 'timestamp'>) => void;
  clearEvents: () => void;
}

export const useActivityStore = create<ActivityState>((set) => ({
  events: [],
  maxEvents: 100,

  addEvent: (event) =>
    set((state) => {
      const newEvent: ActivityEvent = {
        ...event,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };
      const events = [newEvent, ...state.events].slice(0, state.maxEvents);
      return { events };
    }),

  clearEvents: () => set({ events: [] }),
}));
