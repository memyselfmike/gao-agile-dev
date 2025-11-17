/**
 * WorkflowHistory - Workflow execution history with replay and comparison
 *
 * Story 39.24: Workflow Replay and History
 */
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Download, Search, RefreshCw, GitCompare } from 'lucide-react';
import { formatDuration } from '../metrics/utils';
import { LoadingSpinner } from '../LoadingSpinner';
import { Alert, AlertDescription } from '../ui/alert';
import { AlertCircle } from 'lucide-react';

interface WorkflowExecution {
  id: number;
  workflow_id: string;
  workflow_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration: number | null;
  agent: string;
  epic: number | null;
  story_num: number | null;
}

interface ComparisonData {
  workflow_1: WorkflowExecution & { duration: number };
  workflow_2: WorkflowExecution & { duration: number };
  diff: {
    duration_delta: number;
    status_changed: boolean;
    performance_improvement: boolean;
  };
}

export const WorkflowHistory: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkflows, setSelectedWorkflows] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonData | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:3000';

  const fetchHistory = async (currentPage: number, search?: string) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20',
      });
      if (search) params.append('search', search);

      const response = await fetch(`${apiUrl}/api/workflows/history?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch workflow history');
      }

      const data = await response.json();
      setWorkflows(data.workflows);
      setPages(data.pages);
      setPage(data.page);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(1);
  }, []);

  const handleSearch = () => {
    fetchHistory(1, searchQuery);
  };

  const handleExport = async (workflowId: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/workflows/${workflowId}/export`, {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `workflow-${workflowId}-${new Date().toISOString()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const handleSelectWorkflow = (workflowId: string) => {
    setSelectedWorkflows((prev) => {
      if (prev.includes(workflowId)) {
        return prev.filter((id) => id !== workflowId);
      } else if (prev.length < 2) {
        return [...prev, workflowId];
      }
      return prev;
    });
  };

  const handleCompare = async () => {
    if (selectedWorkflows.length !== 2) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${apiUrl}/api/workflows/compare?workflow_id_1=${selectedWorkflows[0]}&workflow_id_2=${selectedWorkflows[1]}`,
        { credentials: 'include' }
      );

      if (!response.ok) throw new Error('Comparison failed');

      const data = await response.json();
      setComparison(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  if (comparison) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">Workflow Comparison</h1>
          <Button onClick={() => setComparison(null)}>Back to History</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Workflow 1 */}
          <Card>
            <CardHeader>
              <CardTitle>Workflow 1</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2">
                <div>
                  <dt className="font-semibold">ID:</dt>
                  <dd>{comparison.workflow_1.workflow_id}</dd>
                </div>
                <div>
                  <dt className="font-semibold">Name:</dt>
                  <dd>{comparison.workflow_1.workflow_name}</dd>
                </div>
                <div>
                  <dt className="font-semibold">Status:</dt>
                  <dd>
                    <Badge
                      variant={
                        comparison.workflow_1.status === 'completed' ? 'default' : 'destructive'
                      }
                    >
                      {comparison.workflow_1.status}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="font-semibold">Duration:</dt>
                  <dd>{formatDuration(comparison.workflow_1.duration)}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {/* Workflow 2 */}
          <Card>
            <CardHeader>
              <CardTitle>Workflow 2</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-2">
                <div>
                  <dt className="font-semibold">ID:</dt>
                  <dd>{comparison.workflow_2.workflow_id}</dd>
                </div>
                <div>
                  <dt className="font-semibold">Name:</dt>
                  <dd>{comparison.workflow_2.workflow_name}</dd>
                </div>
                <div>
                  <dt className="font-semibold">Status:</dt>
                  <dd>
                    <Badge
                      variant={
                        comparison.workflow_2.status === 'completed' ? 'default' : 'destructive'
                      }
                    >
                      {comparison.workflow_2.status}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="font-semibold">Duration:</dt>
                  <dd>{formatDuration(comparison.workflow_2.duration)}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>

        {/* Diff Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Comparison Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="font-semibold">Duration Delta:</span>{' '}
                <Badge
                  variant={comparison.diff.duration_delta < 0 ? 'default' : 'destructive'}
                >
                  {comparison.diff.duration_delta > 0 ? '+' : ''}
                  {formatDuration(Math.abs(comparison.diff.duration_delta))}
                </Badge>
              </div>
              <div>
                <span className="font-semibold">Status Changed:</span>{' '}
                {comparison.diff.status_changed ? 'Yes' : 'No'}
              </div>
              <div>
                <span className="font-semibold">Performance:</span>{' '}
                <Badge
                  variant={comparison.diff.performance_improvement ? 'default' : 'secondary'}
                >
                  {comparison.diff.performance_improvement ? 'Improved' : 'No Change'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" role="region" aria-label="Workflow History">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Workflow History</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fetchHistory(page)}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {selectedWorkflows.length === 2 && (
            <Button onClick={handleCompare}>
              <GitCompare className="h-4 w-4 mr-2" />
              Compare
            </Button>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="flex gap-2">
        <Input
          placeholder="Search by workflow name or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1"
        />
        <Button onClick={handleSearch}>
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && workflows.length === 0 ? (
        <div className="flex justify-center">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>
                Showing {workflows.length} workflows (Page {page} of {pages})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12"></TableHead>
                    <TableHead>Workflow Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Started</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Agent</TableHead>
                    <TableHead>Epic/Story</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workflows.map((wf) => (
                    <TableRow key={wf.workflow_id}>
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedWorkflows.includes(wf.workflow_id)}
                          onChange={() => handleSelectWorkflow(wf.workflow_id)}
                          disabled={
                            selectedWorkflows.length === 2 &&
                            !selectedWorkflows.includes(wf.workflow_id)
                          }
                        />
                      </TableCell>
                      <TableCell className="font-medium">{wf.workflow_name}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            wf.status === 'completed'
                              ? 'default'
                              : wf.status === 'failed'
                              ? 'destructive'
                              : 'secondary'
                          }
                        >
                          {wf.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(wf.started_at).toLocaleString()}</TableCell>
                      <TableCell>
                        {wf.duration ? formatDuration(wf.duration) : 'N/A'}
                      </TableCell>
                      <TableCell>{wf.agent}</TableCell>
                      <TableCell>
                        {wf.epic && wf.story_num
                          ? `${wf.epic}.${wf.story_num}`
                          : wf.epic || 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleExport(wf.workflow_id)}
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Pagination */}
          <div className="flex justify-center gap-2">
            <Button
              variant="outline"
              disabled={page === 1}
              onClick={() => fetchHistory(page - 1, searchQuery)}
            >
              Previous
            </Button>
            <span className="flex items-center px-4">
              Page {page} of {pages}
            </span>
            <Button
              variant="outline"
              disabled={page === pages}
              onClick={() => fetchHistory(page + 1, searchQuery)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
