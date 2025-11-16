/**
 * Session Store - Manages session lock state and read-only mode
 */
import { create } from 'zustand';
import type { SessionState } from '../types';

interface SessionStoreState extends SessionState {
  setLocked: (isLocked: boolean, lockedBy?: string) => void;
  setReadOnly: (isReadOnly: boolean) => void;
  setSessionToken: (token: string | null) => void;
}

export const useSessionStore = create<SessionStoreState>((set) => ({
  isLocked: false,
  isReadOnly: false,
  sessionToken: null,
  lockedBy: undefined,

  setLocked: (isLocked, lockedBy) => set({ isLocked, lockedBy }),

  setReadOnly: (isReadOnly) => set({ isReadOnly }),

  setSessionToken: (token) => set({ sessionToken: token }),
}));
