/**
 * Activity Store - Manages activity stream events
 *
 * Story 39.9: Enhanced for real-time activity stream with virtual scrolling
 * Story 39.10: Filters and search support
 */
import { create } from 'zustand';
import type { ActivityEvent } from '../types';

interface ActivityState {
  events: ActivityEvent[];
  maxEvents: number;
  nextSequence: number;
  lastReceivedSequence: number | null;
  addEvent: (event: Omit<ActivityEvent, 'id' | 'timestamp' | 'sequence'>) => void;
  addEventWithSequence: (event: ActivityEvent) => void;
  clearEvents: () => void;
  detectMissedEvents: (sequence: number) => boolean;
}

export const useActivityStore = create<ActivityState>((set, get) => ({
  events: [],
  maxEvents: 10000, // Support 10k+ events for virtual scrolling
  nextSequence: 1,
  lastReceivedSequence: null,

  addEvent: (event) =>
    set((state) => {
      const newEvent: ActivityEvent = {
        ...event,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        sequence: state.nextSequence,
      };
      const events = [newEvent, ...state.events].slice(0, state.maxEvents);
      return {
        events,
        nextSequence: state.nextSequence + 1,
        lastReceivedSequence: newEvent.sequence,
      };
    }),

  addEventWithSequence: (event) =>
    set((state) => {
      const events = [event, ...state.events].slice(0, state.maxEvents);
      return {
        events,
        nextSequence: Math.max(state.nextSequence, (event.sequence || 0) + 1),
        lastReceivedSequence: event.sequence || state.lastReceivedSequence,
      };
    }),

  clearEvents: () =>
    set({
      events: [],
      nextSequence: 1,
      lastReceivedSequence: null,
    }),

  detectMissedEvents: (sequence: number): boolean => {
    const { lastReceivedSequence } = get();
    if (lastReceivedSequence === null) return false;
    return sequence > lastReceivedSequence + 1;
  },
}));
