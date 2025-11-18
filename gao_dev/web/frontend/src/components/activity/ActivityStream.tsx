/**
 * Activity Stream - Real-time feed of agent activities with virtual scrolling
 *
 * Story 39.9: Real-time activity stream
 * Story 39.10: Filters and search
 */
import { useVirtualizer } from '@tanstack/react-virtual';
import { useEffect, useRef, useState } from 'react';
import { ActivityEventCard } from './ActivityEventCard';
import { TimeWindowSelector, type TimeWindow } from './TimeWindowSelector';
import { ActivityFilters } from './ActivityFilters';
import { ActivitySearch } from './ActivitySearch';
import { ExportButton } from './ExportButton';
import { useActivityStore } from '@/stores/activityStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pause, Play, AlertTriangle } from 'lucide-react';
import { EmptyActivity } from '@/components/empty-states';
import queryString from 'query-string';
import type { ActivityEvent, ActivityEventType } from '@/types';

interface ActivityStreamProps {
  className?: string;
}

const TIME_WINDOW_MS: Record<TimeWindow, number> = {
  '1h': 60 * 60 * 1000,
  '6h': 6 * 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
  all: Infinity,
};

export function ActivityStream({ className }: ActivityStreamProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [timeWindow, setTimeWindow] = useState<TimeWindow>('1h');
  const [isAutoscrollPaused, setIsAutoscrollPaused] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<ActivityEventType[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredEvents, setFilteredEvents] = useState<ActivityEvent[]>([]);

  const allEvents = useActivityStore((state) => state.events);
  const detectMissedEvents = useActivityStore((state) => state.detectMissedEvents);
  const lastSequence = useActivityStore((state) => state.lastReceivedSequence);

  // Initialize from URL query params (Story 39.10)
  useEffect(() => {
    const params = queryString.parse(window.location.search);
    if (params.types && typeof params.types === 'string') {
      setSelectedTypes(params.types.split(',') as ActivityEventType[]);
    }
    if (params.agents && typeof params.agents === 'string') {
      setSelectedAgents(params.agents.split(','));
    }
    if (params.search && typeof params.search === 'string') {
      setSearchQuery(params.search);
    }
  }, []);

  // Update URL query params when filters change (Story 39.10)
  useEffect(() => {
    const params: Record<string, string> = {};
    if (selectedTypes.length > 0) {
      params.types = selectedTypes.join(',');
    }
    if (selectedAgents.length > 0) {
      params.agents = selectedAgents.join(',');
    }
    if (searchQuery.trim()) {
      params.search = searchQuery;
    }

    const newUrl = Object.keys(params).length > 0
      ? `${window.location.pathname}?${queryString.stringify(params)}`
      : window.location.pathname;

    window.history.replaceState({}, '', newUrl);
  }, [selectedTypes, selectedAgents, searchQuery]);

  // Filter events by time window, type, agent, and search
  useEffect(() => {
    const now = Date.now();
    const windowMs = TIME_WINDOW_MS[timeWindow];

    let filtered = allEvents.filter((event) => {
      // Time window filter
      if (windowMs !== Infinity && now - event.timestamp > windowMs) {
        return false;
      }

      // Type filter
      if (selectedTypes.length > 0 && !selectedTypes.includes(event.type)) {
        return false;
      }

      // Agent filter
      if (selectedAgents.length > 0 && !selectedAgents.includes(event.agent)) {
        return false;
      }

      // Search filter (fuzzy search happens in ActivitySearch component)
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return (
          event.summary.toLowerCase().includes(query) ||
          event.action.toLowerCase().includes(query) ||
          event.agent.toLowerCase().includes(query)
        );
      }

      return true;
    });

    setFilteredEvents(filtered);
  }, [allEvents, timeWindow, selectedTypes, selectedAgents, searchQuery]);

  // Virtual scrolling
  const rowVirtualizer = useVirtualizer({
    count: filteredEvents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimate card height
    overscan: 10,
  });

  // Auto-scroll to top when new events arrive (unless paused)
  useEffect(() => {
    if (!isAutoscrollPaused && parentRef.current) {
      parentRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [allEvents.length, isAutoscrollPaused]);

  // Detect missed events
  const hasMissedEvents =
    lastSequence !== null &&
    filteredEvents.length > 0 &&
    detectMissedEvents(filteredEvents[0]?.sequence || 0);

  const activeFilterCount =
    selectedTypes.length + selectedAgents.length + (searchQuery.trim() ? 1 : 0);

  return (
    <div className={`flex h-full flex-col ${className}`}>
      {/* Controls: Time Window, Filters, Search */}
      <div className="space-y-3 border-b border-border p-4">
        {/* Time Window */}
        <TimeWindowSelector selected={timeWindow} onChange={setTimeWindow} />

        {/* Filters and Search */}
        <div className="flex flex-wrap gap-2">
          <ActivityFilters
            selectedTypes={selectedTypes}
            selectedAgents={selectedAgents}
            onTypesChange={setSelectedTypes}
            onAgentsChange={setSelectedAgents}
          />
          <ActivitySearch query={searchQuery} onChange={setSearchQuery} />
        </div>

        {/* Active Filters + Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {activeFilterCount > 0 && (
              <Badge variant="secondary" className="gap-1">
                {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
              </Badge>
            )}
            {hasMissedEvents && (
              <Badge variant="destructive" className="gap-1">
                <AlertTriangle className="h-3 w-3" />
                Missed events detected
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <ExportButton events={filteredEvents} />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAutoscrollPaused(!isAutoscrollPaused)}
              className="gap-2"
            >
              {isAutoscrollPaused ? (
                <>
                  <Play className="h-3 w-3" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="h-3 w-3" />
                  Pause
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Event Stream - Virtualized with ARIA live region */}
      <div ref={parentRef} className="flex-1 overflow-auto p-4" role="log" aria-live="polite" aria-atomic="false">
        {filteredEvents.length === 0 ? (
          <EmptyActivity
            hasFilters={activeFilterCount > 0}
            onClearFilters={() => {
              setSelectedTypes([]);
              setSelectedAgents([]);
              setSearchQuery('');
            }}
          />
        ) : (
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const event = filteredEvents[virtualRow.index];
              return (
                <div
                  key={event.id}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                  className="pb-3"
                >
                  <ActivityEventCard event={event} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Load More (future: pagination for older events beyond time window) */}
      {/* This would be implemented in a future story */}
    </div>
  );
}
