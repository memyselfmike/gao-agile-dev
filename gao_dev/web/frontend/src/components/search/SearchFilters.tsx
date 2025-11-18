/**
 * SearchFilters - Filter controls for search results
 *
 * Story 39.36: Message Search Across DMs and Channels
 */
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useSearchStore } from '@/stores/searchStore';
import { Filter, User, Calendar } from 'lucide-react';

const AGENTS = [
  { id: 'brian', name: 'Brian' },
  { id: 'mary', name: 'Mary' },
  { id: 'john', name: 'John' },
  { id: 'winston', name: 'Winston' },
  { id: 'sally', name: 'Sally' },
  { id: 'bob', name: 'Bob' },
  { id: 'amelia', name: 'Amelia' },
  { id: 'murat', name: 'Murat' },
];

export function SearchFilters() {
  const { filters, setFilters } = useSearchStore();

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Filter className="h-4 w-4" />
        <span className="font-medium">Filters:</span>
      </div>

      {/* Message Type Filter */}
      <Select value={filters.type} onValueChange={(value: 'all' | 'dm' | 'channel') => setFilters({ type: value })}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Message type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Messages</SelectItem>
          <SelectItem value="dm">DMs Only</SelectItem>
          <SelectItem value="channel">Channels Only</SelectItem>
        </SelectContent>
      </Select>

      {/* Agent Filter */}
      <Select
        value={filters.agent || 'all'}
        onValueChange={(value) => setFilters({ agent: value === 'all' ? null : value })}
      >
        <SelectTrigger className="w-[140px]">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4" />
            <SelectValue placeholder="Agent" />
          </div>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Agents</SelectItem>
          {AGENTS.map((agent) => (
            <SelectItem key={agent.id} value={agent.id}>
              {agent.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Date Range Filter */}
      <Select
        value={filters.dateRange}
        onValueChange={(value) => setFilters({ dateRange: value as '7d' | '30d' | 'all' })}
      >
        <SelectTrigger className="w-[160px]">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <SelectValue placeholder="Date range" />
          </div>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Time</SelectItem>
          <SelectItem value="7d">Last 7 Days</SelectItem>
          <SelectItem value="30d">Last 30 Days</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
