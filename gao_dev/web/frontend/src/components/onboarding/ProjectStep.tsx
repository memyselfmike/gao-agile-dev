/**
 * Project Step - Project name, type, and description inputs
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import type { ProjectStepData } from './types';

interface ProjectStepProps {
  data: ProjectStepData;
  errors: Record<string, string>;
  onChange: (data: ProjectStepData) => void;
}

export function ProjectStep({ data, errors, onChange }: ProjectStepProps) {
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Focus first field on mount
  useEffect(() => {
    nameInputRef.current?.focus();
  }, []);

  const handleChange = (field: keyof ProjectStepData, value: string) => {
    onChange({
      ...data,
      [field]: value,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Project Setup</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure your project details
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="project-name">
            Project Name
            <span className="text-destructive" aria-hidden="true">
              {' '}
              *
            </span>
          </Label>
          <Input
            ref={nameInputRef}
            id="project-name"
            type="text"
            value={data.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="my-awesome-project"
            aria-required="true"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'project-name-error' : undefined}
            className={cn(errors.name && 'border-destructive')}
          />
          {errors.name && (
            <p
              id="project-name-error"
              className="text-sm text-destructive"
              role="alert"
            >
              {errors.name}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="project-type">Project Type</Label>
          <Input
            id="project-type"
            type="text"
            value={data.type}
            onChange={(e) => handleChange('type', e.target.value)}
            placeholder="web-app"
            aria-describedby="project-type-hint"
          />
          <p id="project-type-hint" className="text-xs text-muted-foreground">
            e.g., web-app, cli-tool, api-service
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="project-description">Description</Label>
          <Input
            id="project-description"
            type="text"
            value={data.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="A brief description of your project"
            aria-describedby="project-description-hint"
          />
          <p id="project-description-hint" className="text-xs text-muted-foreground">
            Optional: Describe what your project does
          </p>
        </div>
      </div>
    </div>
  );
}
