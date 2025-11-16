/**
 * Files Tab - Placeholder for file explorer
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FolderTree } from 'lucide-react';

export function FilesTab() {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <Card className="max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FolderTree className="h-5 w-5 text-primary" />
            <CardTitle>File Explorer</CardTitle>
          </div>
          <CardDescription>Browse and manage project files</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            File explorer will be implemented in a future story. This will provide a tree view of
            project files with ability to view, edit, and create files.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
