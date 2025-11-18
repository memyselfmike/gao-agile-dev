/**
 * SearchBar - Top bar search input with keyboard shortcut
 *
 * Story 39.36: Message Search Across DMs and Channels
 */
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useSearchStore } from '@/stores/searchStore';
import { useCallback, useEffect, useRef } from 'react';

interface SearchBarProps {
  className?: string;
}

export function SearchBar({ className = '' }: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { query, setQuery, setIsOpen, isOpen } = useSearchStore();

  // Handle Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        inputRef.current?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setIsOpen]);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newQuery = e.target.value;
      setQuery(newQuery);

      // Open results panel if query is not empty
      if (newQuery.trim()) {
        setIsOpen(true);
      }
    },
    [setQuery, setIsOpen]
  );

  const handleFocus = useCallback(() => {
    // Open if there's a query
    if (query.trim()) {
      setIsOpen(true);
    }
  }, [query, setIsOpen]);

  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        type="text"
        placeholder="Search messages... (Cmd+K)"
        value={query}
        onChange={handleChange}
        onFocus={handleFocus}
        className="w-full pl-9 pr-4"
        data-testid="search-input"
      />
    </div>
  );
}
