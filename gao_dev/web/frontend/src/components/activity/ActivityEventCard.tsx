/**
 * Activity Event Card - Displays a single activity event with progressive disclosure
 *
 * Story 39.9: Real-time activity stream
 */
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { ActivityEvent } from '@/types';

interface ActivityEventCardProps {
  event: ActivityEvent;
}

const EVENT_TYPE_COLORS = {
  Workflow: 'bg-blue-500/10 text-blue-700 dark:text-blue-400',
  Chat: 'bg-green-500/10 text-green-700 dark:text-green-400',
  File: 'bg-purple-500/10 text-purple-700 dark:text-purple-400',
  State: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400',
  Ceremony: 'bg-pink-500/10 text-pink-700 dark:text-pink-400',
  Git: 'bg-orange-500/10 text-orange-700 dark:text-orange-400',
};

const SEVERITY_COLORS = {
  info: 'border-l-blue-500',
  success: 'border-l-green-500',
  warning: 'border-l-yellow-500',
  error: 'border-l-red-500',
};

export function ActivityEventCard({ event }: ActivityEventCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const timeAgo = formatDistanceToNow(event.timestamp, { addSuffix: true });
  const severityColor = SEVERITY_COLORS[event.severity || 'info'];
  const typeColor = EVENT_TYPE_COLORS[event.type];

  return (
    <Card className={`border-l-4 ${severityColor} transition-all hover:shadow-md`}>
      <CardContent className="p-4">
        {/* Header: Shallow View */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-1">
            {/* Event Type Badge */}
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className={`text-xs ${typeColor}`}>
                {event.type}
              </Badge>
              {event.sequence && (
                <span className="font-mono text-xs text-muted-foreground">#{event.sequence}</span>
              )}
            </div>

            {/* Summary */}
            <p className="text-sm font-medium text-foreground">
              <span className="text-primary">{event.agent}</span> {event.action}
            </p>
            <p className="text-sm text-muted-foreground">{event.summary}</p>

            {/* Timestamp */}
            <p className="text-xs text-muted-foreground">{timeAgo}</p>
          </div>

          {/* Expand/Collapse Button */}
          {event.details && Object.keys(event.details).length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          )}
        </div>

        {/* Deep View: Details */}
        {isExpanded && event.details && (
          <div className="mt-4 space-y-3 border-t pt-3">
            {/* Reasoning */}
            {event.details.reasoning && (
              <div>
                <h4 className="mb-1 text-xs font-semibold text-foreground">Reasoning</h4>
                <p className="text-xs text-muted-foreground">{event.details.reasoning}</p>
              </div>
            )}

            {/* Tool Calls */}
            {event.details.toolCalls && event.details.toolCalls.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs font-semibold text-foreground">Tool Calls</h4>
                <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
                  {event.details.toolCalls.map((tool, idx) => (
                    <li key={idx}>{tool}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* File Diffs */}
            {event.details.fileDiffs && (
              <div>
                <h4 className="mb-1 text-xs font-semibold text-foreground">File Changes</h4>
                <pre className="rounded bg-muted p-2 text-xs text-muted-foreground overflow-x-auto">
                  {event.details.fileDiffs}
                </pre>
              </div>
            )}

            {/* Other Details */}
            {Object.entries(event.details).map(([key, value]) => {
              if (['reasoning', 'toolCalls', 'fileDiffs'].includes(key)) return null;
              return (
                <div key={key}>
                  <h4 className="mb-1 text-xs font-semibold text-foreground capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
