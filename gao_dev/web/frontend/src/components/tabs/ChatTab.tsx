/**
 * Chat Tab - Placeholder for chat interface
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare } from 'lucide-react';

export function ChatTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <CardTitle>Chat Interface</CardTitle>
          </div>
          <CardDescription>Interactive chat with GAO-Dev agents</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Chat functionality will be implemented in a future story. This is a placeholder for the
            conversational interface with Brian and other agents.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
