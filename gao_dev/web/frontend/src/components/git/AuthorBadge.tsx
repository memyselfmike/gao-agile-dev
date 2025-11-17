/**
 * AuthorBadge - Visual badge component for commit authors
 *
 * Displays author name with appropriate icon:
 * - Blue robot icon for agent commits
 * - Purple user icon for user commits
 */
import { Bot, User } from 'lucide-react';
import type { CommitAuthor } from '@/types/git';
import { Badge } from '@/components/ui/badge';

interface AuthorBadgeProps {
  author: CommitAuthor;
  className?: string;
}

export function AuthorBadge({ author, className = '' }: AuthorBadgeProps) {
  const Icon = author.is_agent ? Bot : User;
  const variant = author.is_agent ? 'default' : 'secondary';
  const iconColor = author.is_agent ? 'text-blue-600' : 'text-purple-600';

  return (
    <Badge variant={variant} className={`flex items-center gap-1.5 ${className}`}>
      <Icon className={`h-3.5 w-3.5 ${iconColor}`} />
      <span className="text-xs font-medium">{author.name}</span>
    </Badge>
  );
}
