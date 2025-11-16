/**
 * Read-Only Banner - Displays when CLI holds lock
 */
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useSessionStore } from '@/stores/sessionStore';
import { Lock } from 'lucide-react';

export function ReadOnlyBanner() {
  const isReadOnly = useSessionStore((state) => state.isReadOnly);
  const isLocked = useSessionStore((state) => state.isLocked);
  const lockedBy = useSessionStore((state) => state.lockedBy);

  if (!isReadOnly && !isLocked) {
    return null;
  }

  return (
    <Alert variant="default" className="border-yellow-500 bg-yellow-50">
      <Lock className="h-4 w-4 text-yellow-600" />
      <AlertTitle className="text-yellow-900">Read-Only Mode</AlertTitle>
      <AlertDescription className="text-yellow-800">
        {lockedBy
          ? `This session is locked by ${lockedBy}. You can view but not make changes.`
          : 'This session is in read-only mode. You can view but not make changes.'}
      </AlertDescription>
    </Alert>
  );
}
