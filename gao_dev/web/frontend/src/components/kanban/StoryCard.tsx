/**
 * Story Card - Individual story card for Kanban board
 *
 * Story 39.16: Epic and Story Card Components
 */
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

export interface StoryCardProps {
  story: {
    id: string;
    number: string;
    epicNumber: number;
    storyNumber: number;
    title: string;
    owner: string | null;
    points: number;
    priority: string;
  };
  onClick?: () => void;
}

export function StoryCard({ story, onClick }: StoryCardProps) {
  // Priority color mapping (P0=red, P1=orange, P2=yellow, P3=green)
  const getPriorityColor = (priority: string): string => {
    const normalizedPriority = priority.toUpperCase();
    switch (normalizedPriority) {
      case 'P0':
      case 'CRITICAL':
        return 'bg-red-100 text-red-700 border-red-300 dark:bg-red-900 dark:text-red-300';
      case 'P1':
      case 'HIGH':
        return 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-900 dark:text-orange-300';
      case 'P2':
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300 dark:bg-yellow-900 dark:text-yellow-300';
      case 'P3':
      case 'LOW':
        return 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900 dark:text-green-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  // Get owner initials for avatar
  const getOwnerInitials = (owner: string | null): string => {
    if (!owner) return '?';

    const words = owner.trim().split(/\s+/);
    if (words.length >= 2) {
      return `${words[0][0]}${words[1][0]}`.toUpperCase();
    }
    return owner[0].toUpperCase();
  };

  const priorityColor = getPriorityColor(story.priority);
  const ownerInitials = getOwnerInitials(story.owner);

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:border-blue-300 dark:hover:border-blue-700"
      onClick={onClick}
      role="listitem"
      tabIndex={0}
      aria-label={`Story ${story.number}: ${story.title}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <CardContent className="p-3 space-y-2">
        {/* Header with story number and points badge */}
        <div className="flex items-start justify-between gap-2">
          <Badge
            variant="secondary"
            className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
          >
            Story {story.number}
          </Badge>
          <Badge
            variant="outline"
            className="ml-auto font-semibold"
            aria-label={`${story.points} story points`}
          >
            {story.points} {story.points === 1 ? 'pt' : 'pts'}
          </Badge>
        </div>

        {/* Story title */}
        <h4 className="text-sm font-medium leading-tight line-clamp-2">
          {story.title}
        </h4>

        {/* Footer with priority and owner */}
        <div className="flex items-center justify-between gap-2 pt-1">
          {/* Priority badge */}
          <Badge
            variant="outline"
            className={cn('text-xs font-medium border', priorityColor)}
          >
            {story.priority.toUpperCase()}
          </Badge>

          {/* Owner avatar */}
          {story.owner && (
            <div className="flex items-center gap-1.5">
              <Avatar className="h-6 w-6">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
                  {ownerInitials}
                </AvatarFallback>
              </Avatar>
              <span className="text-xs text-muted-foreground truncate max-w-[80px]">
                {story.owner}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
