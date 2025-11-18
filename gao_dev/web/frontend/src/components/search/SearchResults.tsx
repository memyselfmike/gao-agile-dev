/**
 * SearchResults - Search results modal/panel
 *
 * Story 39.36: Message Search Across DMs and Channels
 */
import { useEffect, useCallback } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useSearchStore } from '@/stores/searchStore';
import { SearchFilters } from './SearchFilters';
import { SearchResult } from './SearchResult';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { useNavigationStore } from '@/stores/navigationStore';
import { useChatStore } from '@/stores/chatStore';

// Debounce helper
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

import * as React from 'react';

export function SearchResults() {
  const {
    query,
    results,
    total,
    isSearching,
    error,
    filters,
    isOpen,
    selectedResultIndex,
    setIsOpen,
    setResults,
    setIsSearching,
    setError,
    setSelectedResultIndex,
    nextResult,
    previousResult,
  } = useSearchStore();

  const { setPrimaryView } = useNavigationStore();
  const { switchAgent } = useChatStore();

  // Debounce search query (300ms)
  const debouncedQuery = useDebounce(query, 300);

  // Perform search when debounced query or filters change
  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([], 0);
      return;
    }

    const performSearch = async () => {
      setIsSearching(true);
      setError(null);

      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';
        const params = new URLSearchParams({
          q: debouncedQuery,
          type: filters.type,
          date_range: filters.dateRange,
        });

        if (filters.agent) {
          params.append('agent', filters.agent);
        }

        const response = await fetch(`${apiUrl}/api/search/messages?${params}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Search failed');
        }

        const data = (await response.json()) as {
          results: Array<{
            messageId: string;
            conversationId: string;
            conversationType: 'dm' | 'channel';
            content: string;
            sender: string;
            timestamp: string;
            highlights: string[];
          }>;
          total: number;
        };

        setResults(data.results, data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
      }
    };

    performSearch();
  }, [debouncedQuery, filters, setResults, setIsSearching, setError]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        nextResult();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        previousResult();
      } else if (e.key === 'Enter' && selectedResultIndex >= 0) {
        e.preventDefault();
        handleResultClick(results[selectedResultIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedResultIndex, results, nextResult, previousResult, setIsOpen]);

  const handleResultClick = useCallback(
    (result: (typeof results)[0]) => {
      // Navigate to the conversation
      if (result.conversationType === 'dm') {
        // Switch to DMs view and select agent
        setPrimaryView('dms');

        // Find and switch to agent
        const agentId = result.conversationId;
        // We need to fetch agents or use a mapping
        // For now, create a minimal agent object
        const agent = {
          id: agentId,
          name: agentId.charAt(0).toUpperCase() + agentId.slice(1),
          role: 'Agent',
          description: '',
          icon: 'user',
        };
        switchAgent(agent);
      } else {
        // Navigate to channels view
        setPrimaryView('channels');
        // TODO: Select specific channel (Story 39.33)
        console.log('Navigate to channel:', result.conversationId);
      }

      // Close search
      setIsOpen(false);
    },
    [setPrimaryView, switchAgent, setIsOpen]
  );

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50" onClick={() => setIsOpen(false)}>
      <div
        className="absolute left-1/2 top-20 w-full max-w-2xl -translate-x-1/2 overflow-hidden rounded-lg border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">
              Search Results
              {total > 0 && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  {total} {total === 1 ? 'message' : 'messages'} found
                </span>
              )}
            </h2>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setIsOpen(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Filters */}
        <SearchFilters />

        {/* Results */}
        <ScrollArea className="h-[500px]">
          <div className="p-4">
            {isSearching && (
              <div className="flex items-center justify-center py-12">
                <LoadingSpinner size="md" message="Searching..." />
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-center text-red-500">
                {error}
              </div>
            )}

            {!isSearching && !error && results.length === 0 && query && (
              <div className="rounded-lg border border-border p-12 text-center text-muted-foreground">
                <p className="text-lg font-medium">No messages found</p>
                <p className="mt-2 text-sm">
                  No messages found for <span className="font-mono">{query}</span>
                </p>
                <p className="mt-2 text-xs">Try adjusting your filters or search query</p>
              </div>
            )}

            {!isSearching && results.length > 0 && (
              <div className="space-y-2">
                {results.map((result, index) => (
                  <SearchResult
                    key={result.messageId}
                    result={result}
                    isSelected={index === selectedResultIndex}
                    onClick={() => {
                      setSelectedResultIndex(index);
                      handleResultClick(result);
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer with keyboard hints */}
        <div className="border-t border-border bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span>
              <kbd className="rounded bg-background px-1.5 py-0.5">↑↓</kbd> Navigate
            </span>
            <span>
              <kbd className="rounded bg-background px-1.5 py-0.5">Enter</kbd> Select
            </span>
            <span>
              <kbd className="rounded bg-background px-1.5 py-0.5">Esc</kbd> Close
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
