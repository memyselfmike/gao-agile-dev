/**
 * Workflow Detail Panel Component
 *
 * Story 39.21: Workflow Detail Panel - AC2-12
 *
 * Slide-out drawer from right side displaying:
 * - Workflow metadata, steps, variables, artifacts, errors
 * - Tabbed navigation: Overview, Steps, Variables, Artifacts, Errors
 * - Close on X button and Escape key
 * - Focus trap and keyboard navigation
 */
import { useEffect, useCallback } from 'react';
import { X, Loader2 } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { useWorkflowStore } from '@/stores/workflowStore';
import { WorkflowMetadata } from './WorkflowMetadata';
import { WorkflowSteps } from './WorkflowSteps';
import { WorkflowVariables } from './WorkflowVariables';
import { WorkflowArtifacts } from './WorkflowArtifacts';
import { WorkflowErrors } from './WorkflowErrors';

export function WorkflowDetailPanel() {
  const {
    selectedWorkflowId,
    workflowDetails,
    detailsLoading,
    detailsError,
    closePanel,
  } = useWorkflowStore();

  const isOpen = selectedWorkflowId !== null;

  // Close panel on Escape key (AC11)
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closePanel();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closePanel]);

  // Handle opening Files tab for artifact links (AC8)
  const handleOpenFile = useCallback((filePath: string) => {
    // TODO: Implement navigation to Files tab with file path
    // This will be integrated in a future story when Files tab is enhanced
    console.log('Open file in Files tab:', filePath);
  }, []);

  // Handle jump to failed step (AC9)
  const handleJumpToStep = useCallback((stepName: string) => {
    // Switch to Steps tab and highlight the step
    // For now, just log - full implementation would require tab switching logic
    console.log('Jump to step:', stepName);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900 dark:text-green-300';
      case 'failed':
        return 'bg-red-100 text-red-700 border-red-300 dark:bg-red-900 dark:text-red-300';
      case 'running':
        return 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-900 dark:text-blue-300';
      case 'pending':
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && closePanel()}>
      <SheetContent
        className="w-full sm:max-w-2xl p-0 overflow-hidden"
        aria-modal="true"
        aria-labelledby="workflow-title"
      >
        {/* Loading state */}
        {detailsLoading && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Error state */}
        {detailsError && !detailsLoading && (
          <div className="p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{detailsError}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Content */}
        {workflowDetails && !detailsLoading && (
          <div className="flex flex-col h-full">
            {/* Header (AC3) */}
            <SheetHeader className="border-b px-6 py-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  <SheetTitle id="workflow-title" className="text-xl">
                    {workflowDetails.workflow.workflow_name}
                  </SheetTitle>
                  <SheetDescription className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={getStatusColor(workflowDetails.workflow.status)}
                    >
                      {workflowDetails.workflow.status.toUpperCase()}
                    </Badge>
                  </SheetDescription>
                </div>

                {/* Close button (AC11) */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={closePanel}
                  aria-label="Close workflow details"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </SheetHeader>

            {/* Tabbed content (AC4-9) */}
            <ScrollArea className="flex-1">
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="w-full justify-start rounded-none border-b px-6">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="steps">
                    Steps ({workflowDetails.steps.length})
                  </TabsTrigger>
                  <TabsTrigger value="variables">
                    Variables ({Object.keys(workflowDetails.variables).length})
                  </TabsTrigger>
                  <TabsTrigger value="artifacts">
                    Artifacts ({workflowDetails.artifacts.length})
                  </TabsTrigger>
                  {workflowDetails.errors && workflowDetails.errors.length > 0 && (
                    <TabsTrigger value="errors" className="text-red-600 dark:text-red-400">
                      Errors ({workflowDetails.errors.length})
                    </TabsTrigger>
                  )}
                </TabsList>

                {/* Overview Tab (AC4) */}
                <TabsContent value="overview" className="px-6 py-4">
                  <WorkflowMetadata workflow={workflowDetails.workflow} />
                </TabsContent>

                {/* Steps Tab (AC5-6, AC10) */}
                <TabsContent value="steps" className="px-6 py-4">
                  <WorkflowSteps steps={workflowDetails.steps} />
                </TabsContent>

                {/* Variables Tab (AC7) */}
                <TabsContent value="variables" className="px-6 py-4">
                  <WorkflowVariables variables={workflowDetails.variables} />
                </TabsContent>

                {/* Artifacts Tab (AC8) */}
                <TabsContent value="artifacts" className="px-6 py-4">
                  <WorkflowArtifacts
                    artifacts={workflowDetails.artifacts}
                    onOpenFile={handleOpenFile}
                  />
                </TabsContent>

                {/* Errors Tab (AC9, AC10) */}
                {workflowDetails.errors && workflowDetails.errors.length > 0 && (
                  <TabsContent value="errors" className="px-6 py-4">
                    <WorkflowErrors
                      errors={workflowDetails.errors}
                      onJumpToStep={handleJumpToStep}
                    />
                  </TabsContent>
                )}
              </Tabs>
            </ScrollArea>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
