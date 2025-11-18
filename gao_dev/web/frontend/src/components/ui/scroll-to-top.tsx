/**
 * ScrollToTop - Floating button that appears after scrolling down
 *
 * Story 39.40: Micro-interactions - Scroll-to-top button
 */
import { useEffect, useState, type RefObject } from 'react';
import { ArrowUp } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface ScrollToTopProps {
  scrollContainerRef: RefObject<HTMLElement>;
  threshold?: number;
  className?: string;
}

export function ScrollToTop({
  scrollContainerRef,
  threshold = 300,
  className,
}: ScrollToTopProps) {
  const [show, setShow] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      setShow(container.scrollTop > threshold);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [scrollContainerRef, threshold]);

  const scrollToTop = () => {
    const container = scrollContainerRef.current;
    if (!container) return;

    container.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  };

  if (!show) return null;

  return (
    <Button
      size="icon"
      onClick={scrollToTop}
      className={cn(
        'fixed bottom-4 right-4 shadow-lg transition-opacity',
        'hover:scale-105 active:scale-95',
        className
      )}
      aria-label="Scroll to top"
    >
      <ArrowUp className="h-4 w-4" />
    </Button>
  );
}
