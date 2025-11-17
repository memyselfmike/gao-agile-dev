/**
 * MetricsDashboard - Main metrics dashboard container
 *
 * Story 39.23: Workflow Metrics Dashboard
 */
import React, { useEffect } from 'react';
import { useMetricsStore } from '../../stores/metricsStore';
import { SummaryMetrics } from './SummaryMetrics';
import { Button } from '../ui/button';
import { Download, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { LoadingSpinner } from '../LoadingSpinner';
import { Alert, AlertDescription } from '../ui/alert';
import { AlertCircle } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { formatDuration } from './utils';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Badge } from '../ui/badge';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export const MetricsDashboard: React.FC = () => {
  const {
    summary,
    workflowTypeMetrics,
    agentUtilization,
    longestWorkflows,
    failureAnalysis,
    workflowsOverTime,
    loading,
    error,
    autoRefresh,
    refreshInterval,
    fetchMetrics,
    setDateRange,
    exportCSV,
  } = useMetricsStore();

  // Fetch metrics on mount
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchMetrics();
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchMetrics]);

  // Handle date range change
  const handleDateRangeChange = (preset: string) => {
    const end = new Date();
    let start: Date | null = null;

    switch (preset) {
      case '7':
        start = new Date();
        start.setDate(start.getDate() - 7);
        break;
      case '30':
        start = new Date();
        start.setDate(start.getDate() - 30);
        break;
      case '90':
        start = new Date();
        start.setDate(start.getDate() - 90);
        break;
      case 'all':
        start = null;
        break;
    }

    setDateRange({ start, end: start ? end : null });
  };

  if (loading && summary.total_workflows === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6" role="region" aria-label="Workflow Metrics Dashboard">
      {/* Header with filters */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Workflow Metrics</h1>
        <div className="flex gap-2">
          <select
            onChange={(e) => handleDateRangeChange(e.target.value)}
            defaultValue="all"
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="all">All time</option>
          </select>
          <Button variant="outline" onClick={() => fetchMetrics()} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportCSV}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Metrics */}
      <SummaryMetrics summary={summary} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workflow Type Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Average Duration by Workflow Type</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={workflowTypeMetrics.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="workflow_type" angle={-45} textAnchor="end" height={100} />
                <YAxis label={{ value: 'Duration (min)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  formatter={(value: number) => formatDuration(value)}
                  labelStyle={{ color: '#000' }}
                />
                <Bar dataKey="average_duration" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agent Utilization */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Utilization</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={agentUtilization}
                  dataKey="workflow_count"
                  nameKey="agent"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {agentUtilization.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Workflows Over Time */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Workflows Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={workflowsOverTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="completed" stroke="#10B981" name="Completed" />
                <Line type="monotone" dataKey="failed" stroke="#EF4444" name="Failed" />
                <Line type="monotone" dataKey="cancelled" stroke="#F59E0B" name="Cancelled" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Longest Workflows Table */}
      <Card>
        <CardHeader>
          <CardTitle>Top 10 Longest-Running Workflows</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Workflow Name</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Started At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {longestWorkflows.map((wf) => (
                <TableRow key={wf.workflow_id}>
                  <TableCell className="font-medium">{wf.workflow_name}</TableCell>
                  <TableCell>{formatDuration(wf.duration)}</TableCell>
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
                  <TableCell>{wf.agent}</TableCell>
                  <TableCell>{new Date(wf.started_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Failure Analysis */}
      {failureAnalysis.most_failed_workflows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Failure Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold mb-2">Most Failed Workflows</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={failureAnalysis.most_failed_workflows.slice(0, 5)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="workflow_type" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="failure_rate" fill="#EF4444" name="Failure Rate (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {failureAnalysis.common_errors.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">Common Errors</h3>
                  <div className="space-y-2">
                    {failureAnalysis.common_errors.slice(0, 5).map((err, idx) => (
                      <div key={idx} className="flex justify-between items-center p-2 bg-red-50 rounded">
                        <span className="text-sm text-red-900 truncate flex-1">{err.error_message}</span>
                        <Badge variant="destructive">{err.count}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
