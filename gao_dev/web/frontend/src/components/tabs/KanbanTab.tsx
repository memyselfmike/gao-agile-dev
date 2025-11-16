/**
 * Kanban Tab - Placeholder for kanban board
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LayoutDashboard } from 'lucide-react';

export function KanbanTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5 text-primary" />
            <CardTitle>Kanban Board</CardTitle>
          </div>
          <CardDescription>Visual project management</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Kanban board will be implemented in a future story. This will provide a visual board
            with stories in different states (Planned, In Progress, Complete).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
