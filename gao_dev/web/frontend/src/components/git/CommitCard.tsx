/**
 * CommitCard - Individual commit card component
 *
 * Displays:
 * - Author badge
 * - Commit message (first line)
 * - Timestamp (relative <7 days, absolute >=7 days)
 * - Short hash (clickable to copy full hash)
 * - File statistics (+insertions, -deletions)
 */
import { formatDistanceToNow, format, differenceInDays, parseISO } from 'date-fns';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import type { Commit } from '@/types/git';
import { AuthorBadge } from './AuthorBadge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface CommitCardProps {
  commit: Commit;
  onClick?: () => void;
  searchTerm?: string;
}

/**
 * Highlight search term in text with yellow background
 */
function highlightText(text: string, searchTerm?: string): React.ReactNode {
  if (!searchTerm || !searchTerm.trim()) {
    return text;
  }

  const regex = new RegExp(`(${searchTerm})`, 'gi');
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (part.toLowerCase() === searchTerm.toLowerCase()) {
      return (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-900 px-0.5 rounded">
          {part}
        </mark>
      );
    }
    return part;
  });
}

export function CommitCard({ commit, onClick, searchTerm }: CommitCardProps) {
  const [copied, setCopied] = useState(false);

  // Parse timestamp
  const commitDate = parseISO(commit.timestamp);
  const daysSinceCommit = differenceInDays(new Date(), commitDate);

  // Format timestamp: relative if <7 days, absolute if >=7 days
  const formattedTime =
    daysSinceCommit < 7
      ? formatDistanceToNow(commitDate, { addSuffix: true })
      : format(commitDate, 'MMM d, yyyy HH:mm');

  // Handle commit card click
  const handleCardClick = () => {
    if (onClick) {
      onClick();
    }
    // Note: No default navigation since we're in a tab-based UI
  };

  // Handle hash copy (stop propagation to prevent card click)
  const handleCopyHash = async (e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      await navigator.clipboard.writeText(commit.hash);
      setCopied(true);
      toast.success(`Commit hash copied: ${commit.short_hash}...`);

      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy commit hash');
    }
  };

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-muted/50"
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Author badge */}
          <AuthorBadge author={commit.author} />

          {/* Commit content */}
          <div className="flex-1 min-w-0">
            {/* Commit message (first line only) with search highlighting */}
            <p className="text-sm font-medium mb-1 truncate">
              {highlightText(commit.message.split('\n')[0], searchTerm)}
            </p>

            {/* Metadata row */}
            <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
              {/* Timestamp */}
              <span>{formattedTime}</span>

              {/* Short hash with copy button */}
              <Button
                variant="ghost"
                size="sm"
                className="h-auto p-0 hover:bg-transparent"
                onClick={handleCopyHash}
                title="Click to copy full hash"
              >
                <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono hover:bg-muted/80 flex items-center gap-1">
                  {commit.short_hash}
                  {copied ? (
                    <Check className="h-3 w-3 text-green-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </code>
              </Button>

              {/* File statistics */}
              {commit.files_changed > 0 && (
                <span className="flex items-center gap-1">
                  <span className="text-green-600">+{commit.insertions}</span>
                  <span className="text-red-600">-{commit.deletions}</span>
                  <span className="text-muted-foreground">
                    ({commit.files_changed} {commit.files_changed === 1 ? 'file' : 'files'})
                  </span>
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
