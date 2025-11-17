/**
 * SummaryMetrics - Display key metric cards
 *
 * Story 39.23: Workflow Metrics Dashboard - AC2
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import type { MetricsSummary } from '../../stores/metricsStore';
import { formatDuration, formatNumber, getSuccessRateBgColor, getSuccessRateColor } from './utils';
import { CheckCircle, Clock, PlayCircle, TrendingUp } from 'lucide-react';

interface SummaryMetricsProps {
  summary: MetricsSummary;
}

export const SummaryMetrics: React.FC<SummaryMetricsProps> = ({ summary }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Workflows */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Workflows</CardTitle>
          <PlayCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatNumber(summary.total_workflows)}</div>
          <p className="text-xs text-muted-foreground">
            {summary.running} running, {summary.pending} pending
          </p>
        </CardContent>
      </Card>

      {/* Success Rate */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${getSuccessRateColor(summary.success_rate)}`}>
            {summary.success_rate.toFixed(1)}%
          </div>
          <div
            className={`inline-block px-2 py-1 rounded text-xs mt-1 ${getSuccessRateBgColor(
              summary.success_rate
            )}`}
          >
            {summary.completed} completed, {summary.failed} failed
          </div>
        </CardContent>
      </Card>

      {/* Average Duration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatDuration(summary.average_duration)}</div>
          <p className="text-xs text-muted-foreground">Per workflow</p>
        </CardContent>
      </Card>

      {/* Total Duration */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Duration</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatDuration(summary.total_duration)}</div>
          <p className="text-xs text-muted-foreground">Cumulative time</p>
        </CardContent>
      </Card>
    </div>
  );
};
