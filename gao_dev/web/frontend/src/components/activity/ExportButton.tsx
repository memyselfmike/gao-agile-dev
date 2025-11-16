/**
 * Export Button - Export filtered events to JSON/CSV
 *
 * Story 39.10: Activity stream filters and search
 */
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Download, FileJson, FileText } from 'lucide-react';
import type { ActivityEvent } from '@/types';

interface ExportButtonProps {
  events: ActivityEvent[];
}

export function ExportButton({ events }: ExportButtonProps) {
  const exportToJSON = () => {
    const dataStr = JSON.stringify(events, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    downloadFile(blob, `gao-dev-activity-${Date.now()}.json`);
  };

  const exportToCSV = () => {
    if (events.length === 0) return;

    // CSV Headers
    const headers = ['Sequence', 'Timestamp', 'Type', 'Agent', 'Action', 'Summary', 'Severity'];
    const csvRows = [headers.join(',')];

    // CSV Data
    events.forEach((event) => {
      const row = [
        event.sequence || '',
        new Date(event.timestamp).toISOString(),
        event.type,
        event.agent,
        `"${event.action.replace(/"/g, '""')}"`, // Escape quotes
        `"${event.summary.replace(/"/g, '""')}"`,
        event.severity || 'info',
      ];
      csvRows.push(row.join(','));
    });

    const csvStr = csvRows.join('\n');
    const blob = new Blob([csvStr], { type: 'text/csv' });
    downloadFile(blob, `gao-dev-activity-${Date.now()}.csv`);
  };

  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={exportToJSON} className="gap-2">
          <FileJson className="h-4 w-4" />
          Export as JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={exportToCSV} className="gap-2">
          <FileText className="h-4 w-4" />
          Export as CSV
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
