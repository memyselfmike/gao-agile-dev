# Story 39.17: Drag-and-Drop State Transitions

**Epic**: 39.5 - Kanban Board (Visual Project Management)
**Story Points**: 5
**Priority**: SHOULD HAVE (P1)
**Status**: PENDING
**Commits**: N/A

---

## Description

As a **product manager**, I want to **drag-and-drop cards between columns to change story state** so that **I can manage project workflow visually without CLI commands**.

## Acceptance Criteria

1. **AC1**: Cards are draggable within their column and to other columns using @dnd-kit/core library
2. **AC2**: Dragging shows visual feedback (ghost image, drop zone highlighting)
3. **AC3**: Dropping card in new column triggers confirmation modal: "Move Story X.Y to {status}? [Confirm] [Cancel]"
4. **AC4**: Confirming transition calls PATCH /api/kanban/cards/{cardId}/move endpoint
5. **AC5**: Backend performs atomic state transition (DB update + git commit) via GitIntegratedStateManager
6. **AC6**: Optimistic UI update shows card in new column immediately, rollback on error
7. **AC7**: Loading indicator shows on card during transition (spinner overlay)
8. **AC8**: Error toast displays if transition fails with actionable message
9. **AC9**: WebSocket broadcasts `state.story_transitioned` event to all connected clients
10. **AC10**: Real-time update: All browser sessions see card move to new column (<100ms latency)
11. **AC11**: Touch device support: Long press to drag on mobile/tablet browsers
12. **AC12**: Keyboard accessibility: Shift+Arrow keys move card, Enter confirms, Escape cancels

## Technical Notes

### Technology Stack

**Drag-and-Drop Library**: @dnd-kit/core

**Rationale**:
- Modern, accessible drag-and-drop
- Built-in keyboard navigation
- Touch device support
- Better performance than react-dnd
- Smaller bundle size
- Active maintenance

**Dependencies to Add**:
```json
{
  "@dnd-kit/core": "^6.0.8",
  "@dnd-kit/sortable": "^7.0.2",
  "@dnd-kit/utilities": "^3.2.1"
}
```

### Backend API

**New Endpoint**: `PATCH /api/kanban/cards/{cardId}/move`

**Request Body**:
```json
{
  "cardId": "story-1.1",
  "fromStatus": "ready",
  "toStatus": "in_progress"
}
```

**Response**:
```json
{
  "success": true,
  "card": {
    "id": "story-1.1",
    "status": "in_progress",
    "transitionedAt": "2025-01-17T10:30:00Z",
    "gitCommit": "abc123def"
  }
}
```

**Implementation**:
```python
@app.patch("/api/kanban/cards/{card_id}/move")
async def move_kanban_card(
    card_id: str,
    request: Request,
    body: MoveCardRequest
) -> JSONResponse:
    """
    Move card to new status (drag-and-drop transition).

    Performs atomic state transition:
    1. Parse card_id (epic-N or story-N.M)
    2. Call GitIntegratedStateManager.transition_story()
    3. Atomic: DB update + git commit
    4. Emit WebSocket event
    5. Return updated card
    """
    try:
        # Parse card ID
        if card_id.startswith("epic-"):
            epic_num = int(card_id.split("-")[1])
            story_num = None
        else:  # story-N.M
            parts = card_id.split("-")[1].split(".")
            epic_num = int(parts[0])
            story_num = int(parts[1])

        # Validate transition
        if not is_valid_transition(body.fromStatus, body.toStatus):
            raise HTTPException(400, "Invalid state transition")

        # Atomic state transition
        state_manager.transition_story(
            epic_num=epic_num,
            story_num=story_num,
            new_state=body.toStatus
        )

        # Emit WebSocket event
        await event_bus.publish(WebEvent(
            type="state.story_transitioned",
            data={
                "cardId": card_id,
                "fromStatus": body.fromStatus,
                "toStatus": body.toStatus,
                "timestamp": datetime.now().isoformat()
            }
        ))

        return JSONResponse({"success": True, ...})

    except Exception as e:
        logger.error(f"Card move failed: {e}")
        raise HTTPException(500, str(e))
```

### Frontend Implementation

**1. Update KanbanBoard.tsx**

**Add DnD Context**:
```typescript
import { DndContext, DragOverlay, closestCorners } from '@dnd-kit/core';

function KanbanBoard() {
  const [activeCard, setActiveCard] = useState<KanbanCard | null>(null);
  const [pendingMove, setPendingMove] = useState<PendingMove | null>(null);

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    setActiveCard(active.data.current as KanbanCard);
  };

  const handleDragOver = (event: DragOverEvent) => {
    // Highlight drop zone
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const fromStatus = active.data.current.status;
      const toStatus = over.id as string;

      // Show confirmation modal
      setPendingMove({
        cardId: active.id,
        fromStatus,
        toStatus,
        card: active.data.current
      });
    }

    setActiveCard(null);
  };

  return (
    <DndContext
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      {/* Kanban columns */}

      <DragOverlay>
        {activeCard ? <CardGhost card={activeCard} /> : null}
      </DragOverlay>

      {pendingMove && (
        <ConfirmMoveDialog
          move={pendingMove}
          onConfirm={handleConfirmMove}
          onCancel={() => setPendingMove(null)}
        />
      )}
    </DndContext>
  );
}
```

**2. Update KanbanColumn.tsx**

**Make Column a Drop Zone**:
```typescript
import { useDroppable } from '@dnd-kit/core';

function KanbanColumn({ status, cards }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { status }
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "kanban-column",
        isOver && "bg-accent/50 border-accent"
      )}
    >
      {/* Column content */}
    </div>
  );
}
```

**3. Make Cards Draggable**

**Update EpicCard and StoryCard**:
```typescript
import { useDraggable } from '@dnd-kit/core';

function StoryCard({ story }: StoryCardProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `story-${story.epicNum}.${story.storyNum}`,
    data: { type: 'story', status: story.status, ...story }
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={cn(
        "story-card",
        isDragging && "opacity-50"
      )}
    >
      {/* Card content */}
    </div>
  );
}
```

**4. Confirmation Modal**

**Component**: `ConfirmMoveDialog.tsx`
```typescript
function ConfirmMoveDialog({ move, onConfirm, onCancel }: Props) {
  return (
    <Dialog open={true} onOpenChange={onCancel}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm State Transition</DialogTitle>
          <DialogDescription>
            Move {move.card.title} from {move.fromStatus} to {move.toStatus}?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button onClick={() => onConfirm(move)}>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**5. Optimistic Updates**

**Zustand Store Update**:
```typescript
const useKanbanStore = create<KanbanState>((set) => ({
  // ...
  moveCardOptimistic: (cardId, fromStatus, toStatus) => {
    set((state) => {
      const card = findCard(state.columns[fromStatus], cardId);
      return {
        columns: {
          ...state.columns,
          [fromStatus]: state.columns[fromStatus].filter(c => c.id !== cardId),
          [toStatus]: [...state.columns[toStatus], { ...card, status: toStatus }]
        }
      };
    });
  },

  rollbackMove: (cardId, fromStatus, toStatus) => {
    // Reverse the optimistic update
    set((state) => { /* ... */ });
  }
}));
```

**6. API Integration**

```typescript
async function handleConfirmMove(move: PendingMove) {
  // Optimistic update
  moveCardOptimistic(move.cardId, move.fromStatus, move.toStatus);
  setLoading(move.cardId, true);

  try {
    const response = await fetch(`/api/kanban/cards/${move.cardId}/move`, {
      method: 'PATCH',
      body: JSON.stringify({
        fromStatus: move.fromStatus,
        toStatus: move.toStatus
      })
    });

    if (!response.ok) throw new Error('Transition failed');

    toast.success(`Moved to ${move.toStatus}`);
  } catch (error) {
    // Rollback optimistic update
    rollbackMove(move.cardId, move.fromStatus, move.toStatus);
    toast.error(`Failed to move card: ${error.message}`);
  } finally {
    setLoading(move.cardId, false);
    setPendingMove(null);
  }
}
```

### Keyboard Accessibility

**Keyboard Shortcuts**:
- `Shift + →`: Move card to next column
- `Shift + ←`: Move card to previous column
- `Enter`: Open card details
- `Escape`: Cancel drag operation
- `Space`: Pick up / drop card (alternative to mouse drag)

**Implementation**:
```typescript
const handleKeyDown = (event: KeyboardEvent, card: KanbanCard) => {
  if (event.shiftKey && event.key === 'ArrowRight') {
    const nextStatus = getNextStatus(card.status);
    if (nextStatus) {
      setPendingMove({ cardId: card.id, fromStatus: card.status, toStatus: nextStatus });
    }
  }
  // Similar for ArrowLeft
};
```

### Touch Device Support

**@dnd-kit automatically handles touch events**:
- Long press to activate drag (500ms)
- Touch move to drag
- Touch release to drop
- Visual feedback for touch gestures

### WebSocket Real-Time Updates

**Subscribe to Events**:
```typescript
useEffect(() => {
  const ws = connectWebSocket();

  ws.on('state.story_transitioned', (event) => {
    // Update card position in other browser sessions
    moveCardOptimistic(event.data.cardId, event.data.fromStatus, event.data.toStatus);
  });

  return () => ws.disconnect();
}, []);
```

### Error Handling

**Error Scenarios**:
1. **Invalid transition**: "Cannot move from {from} to {to}"
2. **Permission denied**: "Read-only mode: CLI is active"
3. **Network error**: "Connection lost. Changes not saved. [Retry]"
4. **Git conflict**: "Git conflict detected. Refresh and try again."
5. **Concurrent update**: "Card was modified by another user. Refresh to see latest."

**Error Toast**:
```typescript
toast.error('Failed to move card', {
  description: error.message,
  action: {
    label: 'Retry',
    onClick: () => handleConfirmMove(move)
  }
});
```

### Performance Considerations

- Debounce drag events (60fps cap)
- Throttle WebSocket updates (100ms)
- Cancel pending transitions on unmount
- Limit concurrent transitions (1 at a time per card)

### Testing Strategy

**Unit Tests**:
- Drag start/end handlers
- Optimistic update logic
- Rollback on error
- Keyboard event handlers

**Integration Tests**:
- API endpoint calls
- WebSocket event handling
- State manager integration

**E2E Tests** (Playwright):
1. Drag card from Backlog to Ready
2. Confirm modal appears
3. Click Confirm
4. Verify API call made
5. Verify card moves to Ready column
6. Verify git commit created
7. Open second browser window
8. Verify real-time update in second window
9. Test keyboard navigation (Shift+Arrow)
10. Test touch drag on mobile simulator
11. Test error handling (network failure)
12. Test read-only mode (drag disabled)

## Dependencies

- Story 39.15: Kanban Board Layout (foundation)
- Story 39.16: Epic and Story Card Components (draggable items)
- Epic 27: GitIntegratedStateManager.transition_story()
- @dnd-kit/core: v6.0.8
- @dnd-kit/sortable: v7.0.2
- @dnd-kit/utilities: v3.2.1

## Definition of Done

- [ ] All 12 acceptance criteria met
- [ ] @dnd-kit library integrated
- [ ] Backend PATCH /api/kanban/cards/{cardId}/move endpoint implemented
- [ ] Drag-and-drop works smoothly (60fps)
- [ ] Confirmation modal functional
- [ ] Optimistic updates with rollback
- [ ] Loading indicators during transition
- [ ] Error handling with actionable messages
- [ ] WebSocket real-time updates working
- [ ] Keyboard accessibility (Shift+Arrow keys)
- [ ] Touch device support verified
- [ ] Unit tests passing (10+ tests)
- [ ] E2E tests passing (12 scenarios)
- [ ] Read-only mode prevents dragging
- [ ] Code reviewed and approved
- [ ] Zero regressions

---

**Priority**: High
**Complexity**: High (concurrent updates, optimistic UI, WebSocket sync)
**Risk**: Medium (race conditions, WebSocket disconnection)
**Mitigation**: Operation queue, conflict detection, retry logic
