/**
 * Workflow Steps Component
 *
 * Story 39.21: Workflow Detail Panel - AC5-6
 *
 * Accordion list of workflow steps with:
 * - Step header: name, status icon, duration
 * - Expanded view: tool calls, outputs, error messages
 */
import { CheckCircle2, Circle, XCircle, Loader2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import type { WorkflowStep } from '@/stores/workflowStore';
import { formatDuration } from './utils';

export interface WorkflowStepsProps {
  steps: WorkflowStep[];
}

export function WorkflowSteps({ steps }: WorkflowStepsProps) {
  if (steps.length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-4">
        No steps recorded for this workflow.
      </div>
    );
  }

  const getStatusIcon = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Circle className="h-4 w-4 text-gray-400" />;
      default:
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
    }
  };

  const getStatusColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'failed':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300';
      case 'pending':
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300';
      default:
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
    }
  };

  return (
    <Accordion type="single" collapsible className="w-full space-y-2">
      {steps.map((step, index) => (
        <AccordionItem
          key={`step-${index}`}
          value={`step-${index}`}
          className="border rounded-lg px-4"
        >
          <AccordionTrigger className="hover:no-underline">
            <div className="flex items-center gap-3 flex-1">
              {/* Status icon */}
              {getStatusIcon(step.status)}

              {/* Step name */}
              <span className="text-sm font-medium text-left flex-1">{step.name}</span>

              {/* Duration */}
              {step.duration !== null && (
                <Badge variant="outline" className="ml-auto mr-2">
                  {formatDuration(step.duration)}
                </Badge>
              )}

              {/* Status badge */}
              <Badge className={getStatusColor(step.status)}>{step.status}</Badge>
            </div>
          </AccordionTrigger>

          <AccordionContent className="space-y-4 pt-2">
            {/* Tool Calls */}
            {step.tool_calls && step.tool_calls.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2">Tool Calls</h4>
                <div className="space-y-2">
                  {step.tool_calls.map((toolCall, toolIndex) => (
                    <div
                      key={`tool-${index}-${toolIndex}`}
                      className="bg-muted rounded p-2 text-xs"
                    >
                      <div className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                        {toolCall.tool}
                      </div>
                      <SyntaxHighlighter
                        language="json"
                        style={oneDark}
                        customStyle={{
                          margin: 0,
                          fontSize: '11px',
                          borderRadius: '4px',
                          padding: '8px',
                        }}
                        wrapLines
                        wrapLongLines
                      >
                        {JSON.stringify(toolCall.args, null, 2)}
                      </SyntaxHighlighter>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Outputs */}
            {step.outputs && step.outputs.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2">Outputs</h4>
                <div className="space-y-1">
                  {step.outputs.map((output, outputIndex) => (
                    <div
                      key={`output-${index}-${outputIndex}`}
                      className="bg-muted rounded p-2 text-xs font-mono"
                    >
                      {output}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamps */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>Started: {new Date(step.started_at).toLocaleString()}</div>
              {step.completed_at && (
                <div>Completed: {new Date(step.completed_at).toLocaleString()}</div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
