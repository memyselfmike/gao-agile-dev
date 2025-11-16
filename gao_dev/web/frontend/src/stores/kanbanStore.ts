/**
 * Kanban Store - State management for Kanban board
 *
 * Story 39.15: Kanban Board Layout and State Columns
 */
import { create } from 'zustand';

// Kanban card types
export interface KanbanCard {
  id: string;
  type: 'epic' | 'story';
  number: string; // "1" for epic, "1.1" for story
  title: string;
  status: string;
}

export interface StoryCard extends KanbanCard {
  type: 'story';
  epicNumber: number;
  storyNumber: number;
  owner?: string;
  points: number;
  priority: string;
}

export interface EpicCard extends KanbanCard {
  type: 'epic';
  progress: number;
  totalPoints: number;
  completedPoints: number;
  storyCounts: {
    total: number;
    done: number;
    in_progress: number;
    backlog: number;
  };
}

// Column state mapping
export type ColumnState = 'backlog' | 'ready' | 'in_progress' | 'in_review' | 'done';

export const COLUMN_STATES: ColumnState[] = ['backlog', 'ready', 'in_progress', 'in_review', 'done'];

export const COLUMN_LABELS: Record<ColumnState, string> = {
  backlog: 'Backlog',
  ready: 'Ready',
  in_progress: 'In Progress',
  in_review: 'In Review',
  done: 'Done',
};

export const COLUMN_COLORS: Record<ColumnState, string> = {
  backlog: 'gray',
  ready: 'blue',
  in_progress: 'yellow',
  in_review: 'purple',
  done: 'green',
};

// Kanban board state
interface KanbanState {
  // Data
  columns: Record<ColumnState, (StoryCard | EpicCard)[]>;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBoard: () => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  columns: {
    backlog: [],
    ready: [],
    in_progress: [],
    in_review: [],
    done: [],
  },
  isLoading: false,
  error: null,
};

export const useKanbanStore = create<KanbanState>((set) => ({
  ...initialState,

  fetchBoard: async () => {
    set({ isLoading: true, error: null });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
      const response = await fetch(`${apiUrl}/api/kanban/board`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch board: ${response.statusText}`);
      }

      const data = (await response.json()) as {
        columns: Record<ColumnState, (StoryCard | EpicCard)[]>;
      };

      set({
        columns: data.columns,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({
        error: errorMessage,
        isLoading: false,
      });
    }
  },

  clearError: () => set({ error: null }),

  reset: () => set(initialState),
}));
