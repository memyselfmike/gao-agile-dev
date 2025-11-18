/**
 * EmptyChat - Empty state for chat when no messages exist
 *
 * Story 39.40: Empty States
 */
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyChatProps {
  onStartConversation?: () => void;
}

export function EmptyChat({ onStartConversation }: EmptyChatProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="mb-4 rounded-full bg-primary/10 p-6">
        <MessageSquare className="h-12 w-12 text-primary" />
      </div>
      <h3 className="mb-2 text-lg font-semibold">No messages yet</h3>
      <p className="mb-6 max-w-sm text-sm text-muted-foreground">
        Start a conversation with Brian, your GAO-Dev Workflow Coordinator. Ask about workflows,
        project status, or get help with development tasks.
      </p>
      {onStartConversation && (
        <Button onClick={onStartConversation} size="lg">
          Start a conversation
        </Button>
      )}
    </div>
  );
}
