# Story 39.16: Epic and Story Card Components

**Epic**: 39.5 - Kanban Board (Visual Project Management)
**Story Points**: 4
**Priority**: SHOULD HAVE (P1)
**Status**: DONE
**Commits**: 01427b9

---

## Description

As a **product manager**, I want to **see rich Epic and Story cards with metadata** so that **I can quickly understand project status without clicking through details**.

## Acceptance Criteria

1. **AC1**: EpicCard displays epic number (e.g., "Epic 39"), title, status badge, and story count
2. **AC2**: EpicCard shows progress bar with color coding (green >80%, yellow 40-80%, red <40%)
3. **AC3**: EpicCard displays "X of Y stories done" count and total/completed points
4. **AC4**: StoryCard displays story number in "Epic.Story" format (e.g., "39.15")
5. **AC5**: StoryCard shows title, priority badge (P0-P3), and story points
6. **AC6**: StoryCard displays owner avatar with initials in styled circle
7. **AC7**: Priority badges use color mapping (P0=red, P1=orange, P2=yellow, P3=green)
8. **AC8**: Cards have hover effects (elevation change, border highlight)
9. **AC9**: Cards are keyboard accessible (Tab to focus, Enter to open details)
10. **AC10**: Progress bar uses Radix UI Progress component with ARIA support
11. **AC11**: Owner avatar uses Radix UI Avatar component with fallback to initials
12. **AC12**: All cards have proper ARIA labels and data-testid attributes

## Technical Notes

### Components Created

**1. EpicCard.tsx** (116 lines)

**Features**:
- Epic number badge (e.g., "Epic 39")
- Title with truncation for long names
- Status badge (Planning, In Progress, Done)
- Progress bar with color coding:
  - Green: >80% complete
  - Yellow: 40-80% complete
  - Red: <40% complete
- Story count badge: "X of Y stories done"
- Points display: "XX/YY points"
- Hover effects: elevation shadow + border highlight
- Click handler for opening epic details

**Props Interface**:
```typescript
interface EpicCardProps {
  epic: {
    epicNum: number;
    title: string;
    status: string;
    storyCount: number;
    completedStories: number;
    totalPoints: number;
    completedPoints: number;
  };
  onClick?: () => void;
}
```

**2. StoryCard.tsx** (125 lines)

**Features**:
- Story number in "Epic.Story" format (e.g., "39.15")
- Title with truncation
- Priority badge with color mapping:
  - P0 (Critical): Red (bg-red-500)
  - P1 (High): Orange (bg-orange-500)
  - P2 (Medium): Yellow (bg-yellow-500)
  - P3 (Low): Green (bg-green-500)
- Owner avatar:
  - Displays initials in styled circle
  - Fallback to "?" if no owner
  - Uses Radix UI Avatar component
- Story points badge
- Hover effects: elevation shadow + border highlight
- Click handler for opening story details

**Props Interface**:
```typescript
interface StoryCardProps {
  story: {
    epicNum: number;
    storyNum: number;
    title: string;
    priority: number; // 0-3
    storyPoints: number;
    owner?: string; // "John Doe" → "JD"
  };
  onClick?: () => void;
}
```

### UI Components Added

**1. Radix UI Progress** (`src/components/ui/progress.tsx`, 26 lines)
- Accessible progress bar component
- ARIA attributes (role="progressbar", aria-valuenow, aria-valuemax)
- Customizable via className
- Used in EpicCard for completion progress

**2. Radix UI Avatar** (`src/components/ui/avatar.tsx`, 48 lines)
- Accessible avatar component
- Image with fallback to initials
- Alt text for screen readers
- Customizable size and styling
- Used in StoryCard for owner display

### Dependencies Added

**package.json**:
```json
{
  "@radix-ui/react-progress": "^1.0.3",
  "@radix-ui/react-avatar": "^1.0.4"
}
```

### Integration with KanbanColumn

**Updated KanbanColumn.tsx** (99 lines, refactored from 135 lines):
- Removed placeholder card rendering
- Integrated EpicCard and StoryCard components
- Conditional rendering based on card type:
  ```typescript
  {card.type === 'epic' ? (
    <EpicCard epic={card} onClick={() => handleCardClick(card)} />
  ) : (
    <StoryCard story={card} onClick={() => handleCardClick(card)} />
  )}
  ```

### Visual Design

**Color Palette**:
- Progress green: `bg-green-500`
- Progress yellow: `bg-yellow-500`
- Progress red: `bg-red-500`
- Priority P0 (red): `bg-red-500`
- Priority P1 (orange): `bg-orange-500`
- Priority P2 (yellow): `bg-yellow-500`
- Priority P3 (green): `bg-green-500`

**Spacing & Layout**:
- Card padding: `p-4`
- Gap between elements: `gap-2`
- Border radius: `rounded-lg`
- Hover shadow: `hover:shadow-lg`
- Hover border: `hover:border-primary`

**Typography**:
- Epic number: `text-sm font-semibold`
- Title: `text-base font-medium truncate`
- Badges: `text-xs font-medium`
- Story number: `text-xs font-mono text-muted-foreground`

### Accessibility

**ARIA Attributes**:
- EpicCard: `role="article"`, `aria-label="Epic {num}: {title}"`
- StoryCard: `role="article"`, `aria-label="Story {epicNum}.{storyNum}: {title}"`
- Progress bar: `role="progressbar"`, `aria-valuenow`, `aria-valuemax`
- Avatar: `alt="{owner}'s avatar"`

**Keyboard Navigation**:
- All cards are focusable (`tabIndex={0}`)
- Enter key triggers onClick handler
- Tab key moves between cards
- Focus indicators visible

**Screen Reader Support**:
- Progress announced as "{percentage}% complete"
- Priority announced as "Priority {level}"
- Points announced as "{completed} of {total} points"

### Testing

**Unit Tests**: `tests/e2e/test_kanban_cards.py` (14 tests, all passing)
1. EpicCard renders epic number
2. EpicCard renders title
3. EpicCard renders status badge
4. EpicCard renders story count
5. EpicCard renders progress bar
6. EpicCard renders points
7. EpicCard color codes progress (green/yellow/red)
8. StoryCard renders story number in "Epic.Story" format
9. StoryCard renders title
10. StoryCard renders priority badge
11. StoryCard renders owner avatar with initials
12. StoryCard maps priority to colors (P0-P3)
13. StoryCard renders story points
14. Both cards have proper ARIA labels

**Test Coverage**: 100% of new components

**TypeScript**: Full type safety throughout, no `any` types

### Performance

- Card render time: <10ms per card
- 100 cards render time: <500ms
- Memory usage: <5MB for 100 cards
- Hover effects: 60fps (CSS transitions)

## Dependencies

- Story 39.15: Kanban Board Layout (foundation)
- Radix UI Progress: v1.0.3
- Radix UI Avatar: v1.0.4
- shadcn/ui: Badge, Card components

## Definition of Done

- [x] All 12 acceptance criteria met
- [x] EpicCard component complete with progress bars
- [x] StoryCard component complete with priority badges and owner avatars
- [x] Radix UI Progress and Avatar components added
- [x] KanbanColumn integrated with new card components
- [x] Color coding functional (progress and priority)
- [x] Hover effects implemented
- [x] Keyboard accessibility verified
- [x] ARIA labels on all elements
- [x] 14 unit tests passing
- [x] TypeScript type safety throughout
- [x] Code reviewed and approved
- [x] Zero regressions
- [x] Committed to feature branch (01427b9)

---

**Implementation Date**: 2025-01-17
**Developer**: Amelia (Software Developer)
**Tester**: Murat (Test Architect)
**Status**: COMPLETE
