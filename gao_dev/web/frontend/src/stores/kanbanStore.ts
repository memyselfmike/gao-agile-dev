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
  owner: string | null;
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

// Pending move operation (for confirmation dialog)
export interface PendingMove {
  cardId: string;
  fromStatus: ColumnState;
  toStatus: ColumnState;
  card: StoryCard | EpicCard;
}

// Filter state (Story 39.18)
export interface FilterState {
  search: string;
  epicNums: number[];
  owners: string[];
  priorities: string[];
}

// Kanban board state
interface KanbanState {
  // Data
  columns: Record<ColumnState, (StoryCard | EpicCard)[]>;
  isLoading: boolean;
  error: string | null;
  loadingCards: Set<string>; // Cards currently being moved

  // Filter state (Story 39.18)
  filters: FilterState;

  // Scroll positions (Story 39.19)
  scrollPositions: Record<ColumnState, number>;

  // Actions
  fetchBoard: () => Promise<void>;
  clearError: () => void;
  reset: () => void;

  // Filter actions (Story 39.18)
  setFilters: (filters: FilterState) => void;
  getFilteredCards: (status: ColumnState) => (StoryCard | EpicCard)[];
  getTotalCardCount: () => number;
  getFilteredCardCount: () => number;

  // Drag-and-drop actions (Story 39.17)
  moveCardOptimistic: (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => void;
  rollbackMove: (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => void;
  setCardLoading: (cardId: string, loading: boolean) => void;
  moveCardServer: (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => Promise<void>;

  // Scroll position actions (Story 39.19)
  setScrollPosition: (status: ColumnState, position: number) => void;
  getScrollPosition: (status: ColumnState) => number;
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
  loadingCards: new Set<string>(),
  filters: {
    search: '',
    epicNums: [],
    owners: [],
    priorities: [],
  },
  scrollPositions: {
    backlog: 0,
    ready: 0,
    in_progress: 0,
    in_review: 0,
    done: 0,
  },
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

  // Story 39.18: Filter actions
  setFilters: (filters: FilterState) => set({ filters }),

  getFilteredCards: (status: ColumnState): (StoryCard | EpicCard)[] => {
    const state = useKanbanStore.getState() as KanbanState;
    const { columns, filters } = state;
    let cards: (StoryCard | EpicCard)[] = columns[status];

    // Apply search filter (case-insensitive partial match)
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      cards = cards.filter((card: StoryCard | EpicCard) =>
        card.title.toLowerCase().includes(searchLower)
      );
    }

    // Apply epic filter (multi-select with OR logic)
    if (filters.epicNums.length > 0) {
      cards = cards.filter((card: StoryCard | EpicCard) => {
        if (card.type === 'epic') {
          return filters.epicNums.includes(parseInt(card.number));
        } else if (card.type === 'story') {
          return filters.epicNums.includes((card as StoryCard).epicNumber);
        }
        return false;
      });
    }

    // Apply owner filter (multi-select with OR logic, stories only)
    if (filters.owners.length > 0) {
      cards = cards.filter((card: StoryCard | EpicCard) => {
        if (card.type === 'story') {
          const owner = (card as StoryCard).owner;
          return owner && filters.owners.includes(owner);
        }
        // Epics don't have owners, exclude them when owner filter is active
        return false;
      });
    }

    // Apply priority filter (multi-select with OR logic, stories only)
    if (filters.priorities.length > 0) {
      cards = cards.filter((card: StoryCard | EpicCard) => {
        if (card.type === 'story') {
          return filters.priorities.includes((card as StoryCard).priority);
        }
        // Epics don't have priorities, exclude them when priority filter is active
        return false;
      });
    }

    return cards;
  },

  getTotalCardCount: (): number => {
    const state = useKanbanStore.getState() as KanbanState;
    return Object.values(state.columns).flat().length;
  },

  getFilteredCardCount: (): number => {
    const state = useKanbanStore.getState() as KanbanState;
    let total = 0;
    COLUMN_STATES.forEach((status: ColumnState) => {
      total += state.getFilteredCards(status).length;
    });
    return total;
  },

  // Story 39.17: Drag-and-drop actions
  moveCardOptimistic: (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => {
    set((state) => {
      // Find the card in the source column
      const sourceCards = state.columns[fromStatus];
      const card = sourceCards.find((c) => c.id === cardId);

      if (!card) {
        console.error(`Card ${cardId} not found in column ${fromStatus}`);
        return state;
      }

      // Create updated card with new status
      const updatedCard = { ...card, status: toStatus };

      // Remove from source column, add to destination column
      return {
        columns: {
          ...state.columns,
          [fromStatus]: sourceCards.filter((c) => c.id !== cardId),
          [toStatus]: [...state.columns[toStatus], updatedCard],
        },
      };
    });
  },

  rollbackMove: (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => {
    // Note: fromStatus is the ORIGINAL status, toStatus is where it was moved TO
    // So we need to reverse: move from toStatus back to fromStatus
    set((state) => {
      const currentCards = state.columns[toStatus];
      const card = currentCards.find((c) => c.id === cardId);

      if (!card) {
        console.error(`Card ${cardId} not found in column ${toStatus} for rollback`);
        return state;
      }

      // Restore original status
      const restoredCard = { ...card, status: fromStatus };

      return {
        columns: {
          ...state.columns,
          [toStatus]: currentCards.filter((c) => c.id !== cardId),
          [fromStatus]: [...state.columns[fromStatus], restoredCard],
        },
      };
    });
  },

  setCardLoading: (cardId: string, loading: boolean) => {
    set((state) => {
      const newLoadingCards = new Set(state.loadingCards);
      if (loading) {
        newLoadingCards.add(cardId);
      } else {
        newLoadingCards.delete(cardId);
      }
      return { loadingCards: newLoadingCards };
    });
  },

  moveCardServer: async (cardId: string, fromStatus: ColumnState, toStatus: ColumnState) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

    try {
      const response = await fetch(`${apiUrl}/api/kanban/cards/${cardId}/move`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          fromStatus,
          toStatus,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to move card: ${response.statusText}`);
      }

      // Return success (optimistic update already applied)
      return;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to move card:', errorMessage);
      throw error;
    }
  },

  // Story 39.19: Scroll position management
  setScrollPosition: (status: ColumnState, position: number) =>
    set((state) => ({
      scrollPositions: {
        ...state.scrollPositions,
        [status]: position,
      },
    })),

  getScrollPosition: (status: ColumnState): number => {
    const state = useKanbanStore.getState() as KanbanState;
    return state.scrollPositions[status];
  },
}));
