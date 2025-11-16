/**
 * CommitMessageDialog - Commit message input with validation
 * Story 39.14: Monaco Edit Mode with Commit Enforcement
 */
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle } from 'lucide-react';

interface CommitMessageDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (message: string) => void;
  fileName: string;
}

const COMMIT_TYPES = ['feat', 'fix', 'docs', 'refactor', 'test', 'chore', 'style', 'perf'];

export function CommitMessageDialog({
  open,
  onClose,
  onConfirm,
  fileName,
}: CommitMessageDialogProps) {
  const [commitType, setCommitType] = useState('feat');
  const [scope, setScope] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleConfirm = () => {
    // Validate
    if (!scope.trim()) {
      setError('Scope is required');
      return;
    }

    if (!description.trim()) {
      setError('Description is required');
      return;
    }

    // Build commit message
    const message = `${commitType}(${scope.trim()}): ${description.trim()}`;

    // Validate format (regex check)
    const pattern = /^(feat|fix|docs|refactor|test|chore|style|perf)\([^)]+\):.+/;
    if (!pattern.test(message)) {
      setError('Invalid commit message format');
      return;
    }

    onConfirm(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleConfirm();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Commit Changes</DialogTitle>
          <DialogDescription>
            All file edits require a commit message. This ensures humans follow the same quality
            standards as autonomous agents.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* File name */}
          <div>
            <Label className="text-sm font-medium">File</Label>
            <p className="text-sm text-muted-foreground">{fileName}</p>
          </div>

          {/* Commit type */}
          <div className="space-y-2">
            <Label htmlFor="commit-type">Type</Label>
            <select
              id="commit-type"
              value={commitType}
              onChange={(e) => setCommitType(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {COMMIT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Scope */}
          <div className="space-y-2">
            <Label htmlFor="scope">Scope</Label>
            <Input
              id="scope"
              placeholder="e.g., auth, ui, api"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              placeholder="Brief description of changes"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>

          {/* Preview */}
          <div className="rounded-md bg-muted p-3">
            <p className="text-xs font-medium text-muted-foreground mb-1">Preview:</p>
            <code className="text-sm">
              {commitType}({scope || 'scope'}): {description || 'description'}
            </code>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Template hint */}
          <p className="text-xs text-muted-foreground">
            Format: <code>&lt;type&gt;(&lt;scope&gt;): &lt;description&gt;</code>
          </p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleConfirm}>Commit & Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
