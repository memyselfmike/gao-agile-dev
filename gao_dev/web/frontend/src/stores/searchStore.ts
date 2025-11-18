/**
 * Search Store - Manages message search state
 *
 * Story 39.36: Message Search Across DMs and Channels
 */
import { create } from 'zustand';

export interface SearchResult {
  messageId: string;
  conversationId: string;
  conversationType: 'dm' | 'channel';
  content: string;
  sender: string;
  timestamp: string;
  highlights: string[];
}

export interface SearchFilters {
  type: 'all' | 'dm' | 'channel';
  agent: string | null;
  dateRange: '7d' | '30d' | 'all' | string;
}

interface SearchState {
  // Search query and results
  query: string;
  results: SearchResult[];
  total: number;
  isSearching: boolean;
  error: string | null;

  // Filters
  filters: SearchFilters;

  // UI state
  isOpen: boolean;
  selectedResultIndex: number;

  // Actions
  setQuery: (query: string) => void;
  setResults: (results: SearchResult[], total: number) => void;
  setIsSearching: (isSearching: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  setIsOpen: (isOpen: boolean) => void;
  setSelectedResultIndex: (index: number) => void;
  clearSearch: () => void;
  nextResult: () => void;
  previousResult: () => void;
}

const defaultFilters: SearchFilters = {
  type: 'all',
  agent: null,
  dateRange: 'all',
};

export const useSearchStore = create<SearchState>((set) => ({
  // Initial state
  query: '',
  results: [],
  total: 0,
  isSearching: false,
  error: null,
  filters: defaultFilters,
  isOpen: false,
  selectedResultIndex: -1,

  // Actions
  setQuery: (query) => set({ query }),

  setResults: (results, total) =>
    set({
      results,
      total,
      isSearching: false,
      error: null,
      selectedResultIndex: results.length > 0 ? 0 : -1,
    }),

  setIsSearching: (isSearching) => set({ isSearching }),

  setError: (error) =>
    set({
      error,
      isSearching: false,
      results: [],
      total: 0,
      selectedResultIndex: -1,
    }),

  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    })),

  setIsOpen: (isOpen) =>
    set({
      isOpen,
      // Clear on close
      ...(isOpen ? {} : { query: '', results: [], total: 0, selectedResultIndex: -1, error: null }),
    }),

  setSelectedResultIndex: (index) => set({ selectedResultIndex: index }),

  clearSearch: () =>
    set({
      query: '',
      results: [],
      total: 0,
      isSearching: false,
      error: null,
      selectedResultIndex: -1,
    }),

  nextResult: () =>
    set((state) => ({
      selectedResultIndex:
        state.results.length > 0 ? (state.selectedResultIndex + 1) % state.results.length : -1,
    })),

  previousResult: () =>
    set((state) => ({
      selectedResultIndex:
        state.results.length > 0
          ? (state.selectedResultIndex - 1 + state.results.length) % state.results.length
          : -1,
    })),
}));
