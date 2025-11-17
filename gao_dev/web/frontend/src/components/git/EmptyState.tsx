/**
 * EmptyState - Display when no commits are available
 */
import { GitBranch } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface EmptyStateProps {
  message?: string;
}

export function EmptyState({ message = 'No commits yet. Start coding to see history!' }: EmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <GitBranch className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground max-w-sm">{message}</p>
      </CardContent>
    </Card>
  );
}
