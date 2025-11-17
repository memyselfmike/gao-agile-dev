/**
 * Highlighted Text - Component to highlight search matches
 *
 * Story 39.18: Kanban Filters and Search
 */
import { memo } from 'react';

interface HighlightedTextProps {
  text: string;
  search: string;
  className?: string;
}

export const HighlightedText = memo(({ text, search, className }: HighlightedTextProps) => {
  if (!search) {
    return <span className={className}>{text}</span>;
  }

  // Escape regex special characters in search string
  const escapeRegex = (str: string) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const escapedSearch = escapeRegex(search);

  // Split text by search term (case-insensitive)
  const parts = text.split(new RegExp(`(${escapedSearch})`, 'gi'));

  return (
    <span className={className}>
      {parts.map((part, index) =>
        part.toLowerCase() === search.toLowerCase() ? (
          <mark
            key={index}
            className="bg-yellow-200 dark:bg-yellow-800 font-medium"
            data-testid="search-highlight"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </span>
  );
});

HighlightedText.displayName = 'HighlightedText';
