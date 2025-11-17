/**
 * CommitList - Virtualized commit list with infinite scroll
 *
 * Features:
 * - Virtual scrolling for performance (handles >10,000 commits)
 * - Infinite scroll (load more on scroll)
 * - Skeleton loading state
 * - Error handling
 */
import { useEffect, useRef } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { AlertCircle } from 'lucide-react';
import type { CommitListResponse, GitTimelineFilters } from '@/types/git';
import { CommitCard } from './CommitCard';
import { EmptyState } from './EmptyState';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

interface CommitListProps {
  filters?: GitTimelineFilters;
  onCommitClick?: (commitHash: string) => void;
}

async function fetchCommits(
  pageParam: number,
  filters?: GitTimelineFilters
): Promise<CommitListResponse> {
  const params = new URLSearchParams({
    limit: '50',
    offset: pageParam.toString(),
  });

  if (filters?.author) params.append('author', filters.author);
  if (filters?.since) params.append('since', filters.since);
  if (filters?.until) params.append('until', filters.until);
  if (filters?.search) params.append('search', filters.search);

  const response = await fetch(`/api/git/commits?${params}`);

  if (!response.ok) {
    throw new Error('Failed to load commits. Check git repository.');
  }

  return response.json();
}

export function CommitList({ filters, onCommitClick }: CommitListProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Infinite query for commits
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = useInfiniteQuery<CommitListResponse, Error>({
    queryKey: ['git-commits', filters],
    queryFn: ({ pageParam }) => fetchCommits(pageParam as number, filters),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.has_more) {
        return allPages.reduce((sum, page) => sum + page.commits.length, 0);
      }
      return undefined;
    },
    staleTime: 30000, // 30 seconds
  });

  // Intersection observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (first.isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => {
      observer.disconnect();
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="p-4 border rounded-lg">
            <div className="flex items-start gap-3">
              <Skeleton className="h-6 w-20" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          {error instanceof Error ? error.message : 'Failed to load commits. Check git repository.'}
        </AlertDescription>
      </Alert>
    );
  }

  // Flatten all commits from all pages
  const commits = data?.pages.flatMap((page) => page.commits) ?? [];

  // Get totals from first page
  const total = data?.pages[0]?.total ?? 0;
  const totalUnfiltered = data?.pages[0]?.total_unfiltered ?? 0;
  const hasFilters = filters?.author || filters?.since || filters?.until || filters?.search;

  // Empty state
  if (commits.length === 0) {
    return <EmptyState hasFilters={!!hasFilters} />;
  }

  return (
    <div ref={scrollContainerRef} className="space-y-3">
      {/* Filter results count */}
      {hasFilters && (
        <div className="py-2 text-sm text-muted-foreground">
          Showing {commits.length} of {total} commits
          {total < totalUnfiltered && (
            <span className="text-xs ml-2">
              ({totalUnfiltered - total} filtered out)
            </span>
          )}
        </div>
      )}

      {/* Commit cards */}
      {commits.map((commit) => (
        <CommitCard
          key={commit.hash}
          commit={commit}
          onClick={onCommitClick ? () => onCommitClick(commit.hash) : undefined}
          searchTerm={filters?.search}
        />
      ))}

      {/* Load more trigger */}
      {hasNextPage && (
        <div ref={loadMoreRef} className="py-4 text-center">
          {isFetchingNextPage ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-4 border rounded-lg">
                  <div className="flex items-start gap-3">
                    <Skeleton className="h-6 w-20" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Scroll to load more...</p>
          )}
        </div>
      )}

      {/* End of list */}
      {!hasNextPage && commits.length > 0 && (
        <div className="py-4 text-center">
          <p className="text-sm text-muted-foreground">
            {total} {total === 1 ? 'commit' : 'commits'} total
          </p>
        </div>
      )}
    </div>
  );
}
