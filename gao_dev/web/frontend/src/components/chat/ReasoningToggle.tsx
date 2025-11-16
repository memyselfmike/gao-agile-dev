/**
 * ReasoningToggle - Toggle for showing/hiding Claude's thinking
 *
 * Story 39.7: Reasoning toggle component
 */
import { Brain } from 'lucide-react';
import { Button } from '../ui/button';

interface ReasoningToggleProps {
  showReasoning: boolean;
  onToggle: () => void;
}

export function ReasoningToggle({ showReasoning, onToggle }: ReasoningToggleProps) {
  return (
    <Button
      variant={showReasoning ? 'default' : 'outline'}
      size="sm"
      onClick={onToggle}
      className="gap-2"
    >
      <Brain className="h-4 w-4" />
      {showReasoning ? 'Hide Reasoning' : 'Show Reasoning'}
    </Button>
  );
}
