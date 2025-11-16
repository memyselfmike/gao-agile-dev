/**
 * Session Status - Displays session connection status
 */
import { Badge } from '@/components/ui/badge';
import { useSessionStore } from '@/stores/sessionStore';
import { Circle } from 'lucide-react';

type SessionStatusType = 'Active' | 'Read-Only' | 'Disconnected';

interface SessionStatusProps {
  isConnected: boolean;
}

export function SessionStatus({ isConnected }: SessionStatusProps) {
  const isReadOnly = useSessionStore((state) => state.isReadOnly);
  const isLocked = useSessionStore((state) => state.isLocked);

  let status: SessionStatusType;
  let variant: 'default' | 'secondary' | 'destructive' | 'outline';
  let indicatorColor: string;

  if (!isConnected) {
    status = 'Disconnected';
    variant = 'destructive';
    indicatorColor = 'text-destructive';
  } else if (isReadOnly || isLocked) {
    status = 'Read-Only';
    variant = 'secondary';
    indicatorColor = 'text-yellow-500';
  } else {
    status = 'Active';
    variant = 'default';
    indicatorColor = 'text-green-500';
  }

  return (
    <Badge variant={variant} className="flex items-center gap-1.5">
      <Circle className={`h-2 w-2 fill-current ${indicatorColor}`} />
      <span>{status}</span>
    </Badge>
  );
}
