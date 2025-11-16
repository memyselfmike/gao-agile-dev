/**
 * Activity Tab - Placeholder for activity stream
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity } from 'lucide-react';

export function ActivityTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            <CardTitle>Activity Stream</CardTitle>
          </div>
          <CardDescription>Real-time view of agent activities</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Activity stream will be implemented in a future story. This will show real-time updates
            of what agents are doing (creating files, running tests, etc.).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
