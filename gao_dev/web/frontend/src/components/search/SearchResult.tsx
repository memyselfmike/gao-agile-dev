/**
 * SearchResult - Individual search result item
 *
 * Story 39.36: Message Search Across DMs and Channels
 */
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Hash, User } from 'lucide-react';
import type { SearchResult as SearchResultType } from '@/stores/searchStore';

interface SearchResultProps {
  result: SearchResultType;
  isSelected: boolean;
  onClick: () => void;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

function highlightText(text: string, highlights: string[]): React.JSX.Element {
  if (!highlights.length) {
    return <>{text}</>;
  }

  // Create regex pattern for all highlights (case-insensitive)
  const pattern = highlights.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const regex = new RegExp(`(${pattern})`, 'gi');

  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, index) => {
        const isHighlight = highlights.some((h) => h.toLowerCase() === part.toLowerCase());
        return isHighlight ? (
          <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 font-medium">
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        );
      })}
    </>
  );
}

export function SearchResult({ result, isSelected, onClick }: SearchResultProps) {
  const conversationContext =
    result.conversationType === 'dm'
      ? `DM with ${result.sender}`
      : `#${result.conversationId}`;

  return (
    <Card
      className={`cursor-pointer p-3 transition-colors hover:bg-accent ${
        isSelected ? 'border-primary bg-accent' : ''
      }`}
      onClick={onClick}
      data-testid="search-result"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="mt-1">
          {result.conversationType === 'dm' ? (
            <MessageSquare className="h-4 w-4 text-blue-500" />
          ) : (
            <Hash className="h-4 w-4 text-purple-500" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-1 overflow-hidden">
          {/* Header: Sender + Context */}
          <div className="flex items-center gap-2 text-sm">
            <div className="flex items-center gap-1 font-medium">
              <User className="h-3 w-3" />
              <span className="capitalize">{result.sender}</span>
            </div>
            <span className="text-muted-foreground">in</span>
            <Badge variant="outline" className="text-xs">
              {conversationContext}
            </Badge>
            <span className="ml-auto text-xs text-muted-foreground">
              {formatTimestamp(result.timestamp)}
            </span>
          </div>

          {/* Message Content with Highlights */}
          <div className="line-clamp-2 text-sm text-foreground">
            {highlightText(result.content, result.highlights)}
          </div>
        </div>
      </div>
    </Card>
  );
}
