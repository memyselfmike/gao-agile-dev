/**
 * Workflow Errors Component
 *
 * Story 39.21: Workflow Detail Panel - AC9
 *
 * Displays error information (only if workflow failed):
 * - Error message in Alert component (destructive)
 * - Stack trace in collapsible code block (ScrollArea)
 * - Copy error message button
 * - Link to failed step in Steps tab
 */
import { useState } from 'react';
import { AlertCircle, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import type { WorkflowError } from '@/stores/workflowStore';
import { copyToClipboard } from './utils';

export interface WorkflowErrorsProps {
  errors: WorkflowError[];
  onJumpToStep?: (stepName: string) => void;
}

export function WorkflowErrors({ errors, onJumpToStep }: WorkflowErrorsProps) {
  const [expandedErrors, setExpandedErrors] = useState<Set<number>>(new Set([0])); // Expand first error by default
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  if (errors.length === 0) {
    return null;
  }

  const toggleError = (index: number) => {
    setExpandedErrors((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleCopyError = async (index: number, error: WorkflowError) => {
    const errorText = `Error: ${error.message}\nStep: ${error.step}\nTimestamp: ${error.timestamp}\n\nStack Trace:\n${error.stack_trace}`;
    await copyToClipboard(errorText);
    setCopiedIndex(index);
    toast.success('Error details copied to clipboard');
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-3">
      {errors.map((error, index) => {
        const isExpanded = expandedErrors.has(index);

        return (
          <Alert key={`error-${index}`} variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="flex items-center justify-between">
              <span>Error in Step: {error.step}</span>
              <div className="flex items-center gap-2">
                {/* Copy button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 hover:bg-red-100 dark:hover:bg-red-900"
                  onClick={() => handleCopyError(index, error)}
                  aria-label="Copy error details"
                >
                  {copiedIndex === index ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>

                {/* Toggle stack trace button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 hover:bg-red-100 dark:hover:bg-red-900"
                  onClick={() => toggleError(index)}
                  aria-label={isExpanded ? 'Hide stack trace' : 'Show stack trace'}
                >
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </AlertTitle>

            <AlertDescription className="space-y-2">
              {/* Error message */}
              <div className="text-sm">{error.message}</div>

              {/* Timestamp */}
              <div className="text-xs opacity-80">
                {new Date(error.timestamp).toLocaleString()}
              </div>

              {/* Stack trace (collapsible) */}
              {isExpanded && error.stack_trace && (
                <ScrollArea className="h-48 w-full border border-red-300 dark:border-red-800 rounded-md mt-2">
                  <pre className="p-3 text-xs font-mono whitespace-pre-wrap">
                    {error.stack_trace}
                  </pre>
                </ScrollArea>
              )}

              {/* Jump to step link */}
              {onJumpToStep && (
                <Button
                  variant="link"
                  size="sm"
                  className="h-auto p-0 text-xs text-red-700 dark:text-red-400"
                  onClick={() => onJumpToStep(error.step)}
                >
                  Jump to failed step →
                </Button>
              )}
            </AlertDescription>
          </Alert>
        );
      })}
    </div>
  );
}
