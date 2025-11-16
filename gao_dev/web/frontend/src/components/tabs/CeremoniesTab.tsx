/**
 * Ceremonies Tab - Placeholder for agile ceremonies
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';

export function CeremoniesTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            <CardTitle>Agile Ceremonies</CardTitle>
          </div>
          <CardDescription>Sprint planning, retrospectives, and reviews</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Ceremonies interface will be implemented in a future story. This will show upcoming and
            past ceremonies, allow scheduling new ones, and view ceremony artifacts.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
