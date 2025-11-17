/**
 * Virtualized Column - Virtual scrolling for Kanban columns
 *
 * Story 39.19: Virtual Scrolling for Large Boards
 * Uses @tanstack/react-virtual for efficient rendering of 1,000+ cards
 *
 * Performance Targets:
 * - 60 FPS scrolling with 1,000+ cards
 * - <200ms initial render
 * - <200MB memory usage
 * - Only 10-30 DOM nodes rendered at a time
 */
import { useRef, useEffect, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { ColumnState, StoryCard as StoryCardType, EpicCard as EpicCardType } from '@/stores/kanbanStore';
import { useKanbanStore } from '@/stores/kanbanStore';
import { EpicCard } from './EpicCard';
import { StoryCard } from './StoryCard';
import { DraggableCard } from './DraggableCard';
import { JumpToTopButton } from './JumpToTopButton';
import { cn } from '@/lib/utils';

export interface VirtualizedColumnProps {
  status: ColumnState;
  cards: (StoryCardType | EpicCardType)[];
}

export function VirtualizedColumn({ status, cards }: VirtualizedColumnProps) {
  const scrollElementRef = useRef<HTMLDivElement>(null);
  const [showJumpTop, setShowJumpTop] = useState(false);
  const { loadingCards, setScrollPosition, getScrollPosition } = useKanbanStore();

  // AC2: Virtual scrolling with dynamic height estimation
  const virtualizer = useVirtualizer({
    count: cards.length,
    getScrollElement: () => scrollElementRef.current,
    // AC7: Dynamic height estimation based on card type
    estimateSize: (index) => {
      const card = cards[index];
      if (card.type === 'epic') {
        return 140; // Epic cards typically taller (progress bars, story counts)
      }
      return 100; // Story cards typically shorter
    },
    // AC8: Overscan renders 5 extra cards above/below viewport
    overscan: 5,
    // AC7: Measure actual rendered height for accurate scrolling
    measureElement:
      typeof window !== 'undefined' && navigator.userAgent.indexOf('Firefox') === -1
        ? (element) => element?.getBoundingClientRect().height
        : undefined,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // AC6: Restore scroll position on mount
  useEffect(() => {
    if (scrollElementRef.current) {
      const savedPosition = getScrollPosition(status);
      if (savedPosition > 0) {
        scrollElementRef.current.scrollTop = savedPosition;
      }
    }
  }, [status, getScrollPosition]);

  // AC10: Track scroll position and show "Jump to Top" button at 500px
  useEffect(() => {
    const scrollElement = scrollElementRef.current;
    if (!scrollElement) return;

    const handleScroll = () => {
      const scrollTop = scrollElement.scrollTop;

      // AC6: Save scroll position for persistence
      setScrollPosition(status, scrollTop);

      // AC10: Show jump button when scrolled >500px
      setShowJumpTop(scrollTop > 500);
    };

    scrollElement.addEventListener('scroll', handleScroll, { passive: true });
    return () => scrollElement.removeEventListener('scroll', handleScroll);
  }, [status, setScrollPosition]);

  // AC10: Jump to top with smooth scroll
  const scrollToTop = () => {
    scrollElementRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // AC11: Keyboard navigation (Page Up/Down)
  useEffect(() => {
    const scrollElement = scrollElementRef.current;
    if (!scrollElement) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'PageDown') {
        event.preventDefault();
        const viewportHeight = scrollElement.clientHeight;
        scrollElement.scrollBy({ top: viewportHeight, behavior: 'smooth' });
      } else if (event.key === 'PageUp') {
        event.preventDefault();
        const viewportHeight = scrollElement.clientHeight;
        scrollElement.scrollBy({ top: -viewportHeight, behavior: 'smooth' });
      }
    };

    scrollElement.addEventListener('keydown', handleKeyDown);
    return () => scrollElement.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Empty column handling
  if (cards.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">No items</p>
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col">
      {/* AC12: Screen reader announces total card count and scroll position */}
      <div className="sr-only" id={`${status}-description`} aria-live="polite">
        {cards.length} cards. Use Page Up and Page Down to scroll.
        {virtualItems.length > 0 &&
          ` Currently viewing cards ${virtualItems[0].index + 1} to ${virtualItems[virtualItems.length - 1].index + 1}.`}
      </div>

      {/* Virtual scroll area */}
      <div
        ref={scrollElementRef}
        data-virtual-scroll-area="true"
        data-testid={`virtual-scroll-area-${status}`}
        role="region"
        aria-label={`${status} column with ${cards.length} cards`}
        aria-describedby={`${status}-description`}
        tabIndex={0}
        className={cn(
          'h-full overflow-auto p-2 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
          // AC12: Smooth scroll behavior
          'scroll-smooth'
        )}
      >
        {/* Virtual container with total height */}
        <div
          data-virtual-container="true"
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            position: 'relative',
          }}
        >
          {/* AC2: Only render visible items (10-30 cards) */}
          {virtualItems.map((virtualItem) => {
            const card = cards[virtualItem.index];
            const isLoading = loadingCards.has(card.id);

            return (
              <div
                key={card.id}
                data-index={virtualItem.index}
                data-virtualized-card="true"
                data-testid={`virtualized-card-${card.id}`}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  // AC7: Dynamic positioning with translateY for smooth scrolling
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                className="px-1 py-1"
              >
                {/* AC9: Works with drag-and-drop (Story 39.17) */}
                <DraggableCard card={card} isLoading={isLoading}>
                  {/* Render appropriate card component based on type */}
                  {card.type === 'epic' ? (
                    <EpicCard epic={card} onClick={() => console.log('Epic clicked:', card.id)} />
                  ) : (
                    <StoryCard story={card} onClick={() => console.log('Story clicked:', card.id)} />
                  )}
                </DraggableCard>
              </div>
            );
          })}
        </div>
      </div>

      {/* AC10: Jump to top button */}
      <JumpToTopButton visible={showJumpTop} onClick={scrollToTop} />
    </div>
  );
}
