/**
 * EmptyState - Display when no commits are available
 *
 * Shows different messages based on whether filters are active
 */
import { GitBranch, FilterX } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useSearchParams } from 'react-router-dom';

interface EmptyStateProps {
  hasFilters?: boolean;
  message?: string;
}

export function EmptyState({ hasFilters = false, message }: EmptyStateProps) {
  const [, setSearchParams] = useSearchParams();

  const handleClearFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  // Determine message and icon based on filter state
  const displayMessage = message || (hasFilters
    ? 'No commits match your filters. Try adjusting your criteria.'
    : 'No commits yet. Start coding to see history!');

  const Icon = hasFilters ? FilterX : GitBranch;

  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Icon className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground max-w-sm mb-4">{displayMessage}</p>

        {hasFilters && (
          <Button onClick={handleClearFilters} variant="outline" size="sm">
            Clear all filters
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
