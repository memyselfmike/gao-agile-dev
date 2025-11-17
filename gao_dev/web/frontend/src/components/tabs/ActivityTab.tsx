/**
 * Activity Tab - Unified observability with activity stream and workflow visualization
 *
 * Story 39.9: Real-time activity stream
 * Story 39.10: Filters and search
 * Epic 39.6: Workflow Visualization
 */
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ActivityStream } from '@/components/activity/ActivityStream';
import { WorkflowTimeline } from '@/components/workflow/WorkflowTimeline';
import { MetricsDashboard } from '@/components/metrics/MetricsDashboard';
import { WorkflowHistory } from '@/components/history/WorkflowHistory';
import { WorkflowGraph } from '@/components/workflow/WorkflowGraph';
import { Activity, Clock, BarChart3, History, GitBranch } from 'lucide-react';

type ActivityView = 'feed' | 'timeline' | 'metrics' | 'history' | 'graph';

export function ActivityTab() {
  const [activeView, setActiveView] = useState<ActivityView>('feed');

  return (
    <div className="h-full">
      <Tabs value={activeView} onValueChange={(value) => setActiveView(value as ActivityView)} className="h-full flex flex-col">
        <div className="px-6 pt-4 pb-2 border-b">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="feed" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Feed
            </TabsTrigger>
            <TabsTrigger value="timeline" className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Timeline
            </TabsTrigger>
            <TabsTrigger value="metrics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Metrics
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              History
            </TabsTrigger>
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Dependencies
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-auto">
          <TabsContent value="feed" className="h-full m-0 p-0">
            <ActivityStream className="h-full" />
          </TabsContent>

          <TabsContent value="timeline" className="h-full m-0 p-0">
            <WorkflowTimeline />
          </TabsContent>

          <TabsContent value="metrics" className="h-full m-0 p-0">
            <MetricsDashboard />
          </TabsContent>

          <TabsContent value="history" className="h-full m-0 p-0">
            <WorkflowHistory />
          </TabsContent>

          <TabsContent value="graph" className="h-full m-0 p-0">
            <WorkflowGraph />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
