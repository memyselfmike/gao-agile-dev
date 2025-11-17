/**
 * Jump to Top Button - Floating button for scrolling to column top
 *
 * Story 39.19: Virtual Scrolling for Large Boards
 * AC10: "Jump to top" button appears when scrolled >500px, clicking scrolls to column top
 * AC12: Smooth scroll animations (60 FPS, no jank)
 */
import { ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface JumpToTopButtonProps {
  visible: boolean;
  onClick: () => void;
}

export function JumpToTopButton({ visible, onClick }: JumpToTopButtonProps) {
  return (
    <button
      onClick={onClick}
      data-testid="jump-to-top-button"
      aria-label="Jump to top"
      className={cn(
        'fixed bottom-4 right-4 z-50 rounded-full bg-primary p-3 text-primary-foreground shadow-lg',
        'transition-all duration-300 hover:scale-110 hover:shadow-xl',
        'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
        visible ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-4 opacity-0'
      )}
    >
      <ChevronUp className="h-5 w-5" />
    </button>
  );
}
