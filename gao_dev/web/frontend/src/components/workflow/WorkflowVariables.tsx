/**
 * Workflow Variables Component
 *
 * Story 39.21: Workflow Detail Panel - AC7
 *
 * Displays workflow input variables as key-value table with:
 * - Searchable/filterable
 * - Copy variable value button
 */
import { useState } from 'react';
import { Copy, Check, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { copyToClipboard } from './utils';

export interface WorkflowVariablesProps {
  variables: Record<string, any>;
}

export function WorkflowVariables({ variables }: WorkflowVariablesProps) {
  const [search, setSearch] = useState('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = async (key: string, value: any) => {
    const textValue = typeof value === 'string' ? value : JSON.stringify(value);
    await copyToClipboard(textValue);
    setCopiedKey(key);
    toast.success(`Copied ${key} to clipboard`);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filter variables by search term
  const entries = Object.entries(variables).filter(([key, value]) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    const keyMatch = key.toLowerCase().includes(searchLower);
    const valueMatch = String(value).toLowerCase().includes(searchLower);
    return keyMatch || valueMatch;
  });

  if (Object.keys(variables).length === 0) {
    return (
      <div className="text-center text-sm text-muted-foreground py-4">
        No variables recorded for this workflow.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search variables..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8"
        />
      </div>

      {/* Variables table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-1/3">Key</TableHead>
              <TableHead>Value</TableHead>
              <TableHead className="w-16"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-sm text-muted-foreground">
                  No variables match your search.
                </TableCell>
              </TableRow>
            ) : (
              entries.map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell className="font-mono text-xs font-semibold">{key}</TableCell>
                  <TableCell className="font-mono text-xs max-w-md truncate">
                    {typeof value === 'string' ? value : JSON.stringify(value)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleCopy(key, value)}
                      aria-label={`Copy ${key}`}
                    >
                      {copiedKey === key ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
