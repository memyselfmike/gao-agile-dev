/**
 * Git Tab - Placeholder for git operations
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GitBranch } from 'lucide-react';

export function GitTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            <CardTitle>Git Operations</CardTitle>
          </div>
          <CardDescription>Manage git branches, commits, and PRs</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Git interface will be implemented in a future story. This will show branches, commit
            history, staged changes, and allow creating commits and pull requests.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
