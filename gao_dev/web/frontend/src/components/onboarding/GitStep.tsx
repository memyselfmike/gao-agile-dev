/**
 * Git Step - Git configuration (name and email)
 *
 * Story 41.3: Web Wizard Frontend Components
 */
import { useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import type { GitStepData } from './types';

interface GitStepProps {
  data: GitStepData;
  errors: Record<string, string>;
  onChange: (data: GitStepData) => void;
}

export function GitStep({ data, errors, onChange }: GitStepProps) {
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Focus first field on mount
  useEffect(() => {
    nameInputRef.current?.focus();
  }, []);

  const handleChange = (field: keyof GitStepData, value: string) => {
    onChange({
      ...data,
      [field]: value,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Git Configuration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Set up your Git identity for commits
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="git-name">
            Git User Name
            <span className="text-destructive" aria-hidden="true">
              {' '}
              *
            </span>
          </Label>
          <Input
            ref={nameInputRef}
            id="git-name"
            type="text"
            value={data.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Your Name"
            aria-required="true"
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? 'git-name-error' : 'git-name-hint'}
            className={cn(errors.name && 'border-destructive')}
          />
          {errors.name ? (
            <p
              id="git-name-error"
              className="text-sm text-destructive"
              role="alert"
            >
              {errors.name}
            </p>
          ) : (
            <p id="git-name-hint" className="text-xs text-muted-foreground">
              This will appear in your Git commits
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="git-email">
            Git Email
            <span className="text-destructive" aria-hidden="true">
              {' '}
              *
            </span>
          </Label>
          <Input
            id="git-email"
            type="email"
            value={data.email}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="your@email.com"
            aria-required="true"
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? 'git-email-error' : 'git-email-hint'}
            className={cn(errors.email && 'border-destructive')}
          />
          {errors.email ? (
            <p
              id="git-email-error"
              className="text-sm text-destructive"
              role="alert"
            >
              {errors.email}
            </p>
          ) : (
            <p id="git-email-hint" className="text-xs text-muted-foreground">
              Used to associate commits with your account
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
