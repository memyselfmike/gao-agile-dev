/**
 * Completion Step - Configuration summary and finish
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle, Folder, GitBranch, Cpu, Key } from 'lucide-react';
import type { ProjectStepData, GitStepData, ProviderInfo } from './types';

interface CompletionStepProps {
  projectData: ProjectStepData;
  gitData: GitStepData;
  provider: ProviderInfo | null;
  useEnvVar: boolean;
}

export function CompletionStep({
  projectData,
  gitData,
  provider,
  useEnvVar,
}: CompletionStepProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Announce completion
  useEffect(() => {
    // Focus the container to announce the summary
    containerRef.current?.focus();
  }, []);

  return (
    <div ref={containerRef} className="space-y-6" tabIndex={-1}>
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
          <CheckCircle
            className="h-8 w-8 text-green-600 dark:text-green-400"
            aria-hidden="true"
          />
        </div>
        <h2 className="text-xl font-semibold">Setup Complete</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Review your configuration before starting
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <h3 className="mb-4 font-medium">Configuration Summary</h3>

          <div className="space-y-4">
            {/* Project */}
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                <Folder className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Project</p>
                <p className="text-sm text-muted-foreground">{projectData.name}</p>
                {projectData.language && (
                  <p className="text-xs text-muted-foreground">
                    Type: {projectData.language}
                  </p>
                )}
                {projectData.description && (
                  <p className="text-xs text-muted-foreground">
                    {projectData.description}
                  </p>
                )}
              </div>
            </div>

            {/* Git */}
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                <GitBranch className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Git Identity</p>
                <p className="text-sm text-muted-foreground">{gitData.name}</p>
                <p className="text-xs text-muted-foreground">{gitData.email}</p>
              </div>
            </div>

            {/* Provider */}
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                <Cpu className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">AI Provider</p>
                <p className="text-sm text-muted-foreground">
                  {provider?.name || 'Not selected'}
                </p>
                {provider?.description && (
                  <p className="text-xs text-muted-foreground">
                    {provider.description}
                  </p>
                )}
              </div>
            </div>

            {/* Credentials */}
            {provider?.requires_api_key && (
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                  <Key className="h-4 w-4" aria-hidden="true" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Credentials</p>
                  <p className="text-sm text-muted-foreground">
                    {useEnvVar
                      ? `Using environment variable (${provider.api_key_env_var})`
                      : 'API key configured'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          Click "Start Building" to complete setup and begin your project.
        </p>
      </div>
    </div>
  );
}
