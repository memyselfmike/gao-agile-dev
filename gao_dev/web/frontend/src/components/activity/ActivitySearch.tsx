/**
 * Activity Search - Fuzzy search within activity stream
 *
 * Story 39.10: Activity stream filters and search
 */
import { Input } from '@/components/ui/input';
import { Search, X } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface ActivitySearchProps {
  query: string;
  onChange: (query: string) => void;
}

export function ActivitySearch({ query, onChange }: ActivitySearchProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcut: Cmd+F or Ctrl+F
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'f' && !e.shiftKey) {
        // Check if we're not already in an input
        if (
          document.activeElement?.tagName !== 'INPUT' &&
          document.activeElement?.tagName !== 'TEXTAREA'
        ) {
          e.preventDefault();
          inputRef.current?.focus();
        }
      }

      // ESC to clear search
      if (e.key === 'Escape' && inputRef.current === document.activeElement) {
        onChange('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChange]);

  return (
    <div className="relative flex-1 max-w-md">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        type="text"
        placeholder="Search activity... (⌘F)"
        value={query}
        onChange={(e) => onChange(e.target.value)}
        className="h-9 pl-9 pr-9 text-sm"
      />
      {query && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
