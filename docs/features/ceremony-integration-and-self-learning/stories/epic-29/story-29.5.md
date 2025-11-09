# Story 29.5: Action Item Integration

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Story 29.4 (Workflow Adjustment Logic), Epic 24 (ActionItemService)

---

## User Story

**As a** Bob (scrum master)
**I want** high-priority action items from ceremonies to flow into next sprint
**So that** improvements actually happen and aren't forgotten

---

## Acceptance Criteria

### AC1: ActionItemIntegrationService Created

- [ ] Create `gao_dev/core/services/action_item_integration_service.py` (~300 lines)
- [ ] Class with methods:
  - `process_action_items(ceremony_id) -> Dict[str, int]`
  - `convert_to_story(action_item_id, epic_num) -> int`
  - `get_pending_action_items(epic_num) -> List[ActionItem]`
  - `mark_action_item_complete(action_item_id)`
  - `auto_complete_stale_items(days_old=30)`
- [ ] Integration with CeremonyOrchestrator
- [ ] Integration with StoryStateService

### AC2: Action Item Priority Filter (C8 Fix - CRITICAL)

- [ ] **STRICT LIMIT**: Only CRITICAL priority items auto-convert to stories
- [ ] **MAX 1 per epic**: Maximum 1 action item can convert to story per epic
- [ ] Priority levels:
  ```python
  class ActionItemPriority(Enum):
      CRITICAL = "critical"  # ONLY this level auto-converts
      HIGH = "high"          # Manual review required
      MEDIUM = "medium"      # Track only
      LOW = "low"            # Track only, auto-complete after 30 days
  ```
- [ ] Prevent noise: High/Medium/Low items tracked but NOT auto-converted
- [ ] Manual override: User can manually promote high-priority items if needed

### AC3: Auto-Conversion Logic (C8 Fix Applied)

- [ ] After ceremony completes, process action items:
  ```python
  def process_action_items(self, ceremony_id: int) -> Dict[str, int]:
      """
      Process action items from ceremony with strict conversion rules.

      Rules (C8 Fix):
      - Only CRITICAL priority converts automatically
      - Maximum 1 conversion per epic
      - All others tracked for manual review

      Returns:
          Dict with counts: {"converted": N, "tracked": M}
      """
      action_items = self.action_item_service.get_by_ceremony(ceremony_id)

      converted = 0
      tracked = 0

      # Check if epic already has a converted action item
      epic_num = self._get_epic_num_from_ceremony(ceremony_id)
      if self._has_converted_action_item(epic_num):
          logger.warning(
              f"Epic {epic_num} already has 1 converted action item (C8 limit)"
          )
          # Track all items, convert none
          for item in action_items:
              self._mark_for_manual_review(item.id)
              tracked += 1
          return {"converted": 0, "tracked": tracked}

      # Process items by priority
      for item in action_items:
          if item.priority == ActionItemPriority.CRITICAL:
              # Auto-convert first CRITICAL item only
              if converted == 0:
                  self.convert_to_story(item.id, epic_num)
                  converted += 1
              else:
                  # Additional CRITICAL items marked for manual review
                  self._mark_for_manual_review(item.id)
                  tracked += 1
          else:
              # HIGH/MEDIUM/LOW tracked only
              tracked += 1

      return {"converted": converted, "tracked": tracked}
  ```

### AC4: Story Creation from Action Item

- [ ] Convert action item to story with proper metadata:
  ```python
  def convert_to_story(
      self,
      action_item_id: int,
      epic_num: int
  ) -> int:
      """
      Convert CRITICAL action item to story.

      Args:
          action_item_id: Action item to convert
          epic_num: Epic to add story to

      Returns:
          Story number created

      Raises:
          MaxConversionsExceededError: If epic already has 1 converted item
      """
      # Check limit (C8 fix)
      if self._has_converted_action_item(epic_num):
          raise MaxConversionsExceededError(
              f"Epic {epic_num} already has 1 converted action item"
          )

      # Get action item
      action_item = self.action_item_service.get_by_id(action_item_id)

      # Get next story number
      story_num = self._get_next_story_num(epic_num)

      # Create story content
      story_content = self._generate_story_content(action_item)

      # Create story file
      story_path = self._get_story_path(epic_num, story_num)
      story_path.write_text(story_content)

      # Register in database
      self.story_service.create_story(
          epic_num=epic_num,
          story_num=story_num,
          file_path=story_path,
          content=story_content,
          metadata={
              "source": "action_item",
              "action_item_id": action_item_id,
              "ceremony_id": action_item.ceremony_id,
              "priority": action_item.priority,
              "converted_at": datetime.now().isoformat()
          }
      )

      # Mark action item as converted
      self.action_item_service.mark_converted(action_item_id, story_num)

      # Git commit
      self.git_manager.add(str(story_path))
      self.git_manager.commit(
          f"feat(epic-{epic_num}): add Story {epic_num}.{story_num} from action item"
      )

      return story_num
  ```

### AC5: Story Content Template

- [ ] Generate story content from action item:
  ```markdown
  # Story {epic_num}.{story_num}: {action_item_title}

  **Epic**: Epic {epic_num}
  **Status**: Not Started
  **Priority**: P0 (from CRITICAL action item)
  **Estimated Effort**: {estimated_points} story points
  **Owner**: TBD
  **Created**: {timestamp}
  **Source**: Action Item from {ceremony_type} ceremony

  ---

  ## User Story

  **As a** {role}
  **I want** {action_item_description}
  **So that** {benefit}

  ---

  ## Context

  This story was created from a CRITICAL action item identified during
  {ceremony_type} ceremony on {ceremony_date}.

  **Original Action Item**:
  {action_item_content}

  **Why Critical**: {criticality_reason}

  ---

  ## Acceptance Criteria

  {acceptance_criteria}

  ---

  ## Definition of Done

  - [ ] Action item requirements met
  - [ ] Tests passing
  - [ ] Code reviewed
  - [ ] Documentation updated
  - [ ] Committed to git
  ```

### AC6: Stale Action Item Cleanup

- [ ] Auto-complete low-priority items after 30 days:
  ```python
  def auto_complete_stale_items(self, days_old: int = 30) -> int:
      """
      Auto-complete LOW priority items older than N days.

      Args:
          days_old: Age threshold in days (default: 30)

      Returns:
          Number of items auto-completed
      """
      stale_items = self.action_item_service.get_stale_items(
          priority=ActionItemPriority.LOW,
          days_old=days_old
      )

      for item in stale_items:
          self.action_item_service.mark_complete(
              item.id,
              completed_by="system",
              reason="Auto-completed after 30 days (low priority)"
          )

      return len(stale_items)
  ```
- [ ] Run as part of daily maintenance job
- [ ] Only affects LOW priority items
- [ ] MEDIUM/HIGH tracked indefinitely

### AC7: Manual Review Interface

- [ ] CLI command for manual review:
  ```bash
  gao-dev action-items list --epic 5 --pending
  gao-dev action-items promote <item-id>  # Convert HIGH to story manually
  gao-dev action-items complete <item-id>
  gao-dev action-items defer <item-id> --days 30
  ```
- [ ] List shows:
  - Action item ID
  - Priority
  - Content
  - Source ceremony
  - Age (days)
  - Conversion eligibility (C8 limits)

### AC8: Integration with CeremonyOrchestrator

- [ ] After ceremony completes, trigger action item processing:
  ```python
  # In CeremonyOrchestrator
  def hold_retrospective(self, epic_num: int):
      # ... ceremony execution ...

      # Process action items (NEW)
      if action_items:
          result = self.action_item_integration.process_action_items(
              ceremony_id=ceremony.id
          )
          logger.info(
              "action_items_processed",
              ceremony_id=ceremony.id,
              converted=result["converted"],
              tracked=result["tracked"]
          )
  ```

### AC9: Unit Tests

- [ ] Create `tests/core/services/test_action_item_integration_service.py` (~250 lines)
- [ ] Tests:
  - Process action items with various priorities
  - C8 fix: Only CRITICAL converts automatically
  - C8 fix: Max 1 conversion per epic enforced
  - Story creation from action item
  - Story content template rendering
  - Stale item cleanup (30 days)
  - Manual promotion of HIGH priority items
  - Integration with CeremonyOrchestrator
- [ ] Test coverage >95%

---

## Technical Details

### Files to Create/Modify

**1. ActionItemIntegrationService** (new):
- `gao_dev/core/services/action_item_integration_service.py` (~300 lines)

**2. CLI Commands** (new):
- `gao_dev/cli/action_item_commands.py` (~150 lines)

**3. CeremonyOrchestrator Integration** (modify):
- `gao_dev/orchestrator/ceremony_orchestrator.py` (+30 lines)

**4. Exception Classes** (modify):
- `gao_dev/core/exceptions.py` (+10 lines)
  - `MaxConversionsExceededError`

**5. Unit Tests** (new):
- `tests/core/services/test_action_item_integration_service.py` (~250 lines)

### Action Item Priority Assignment

**Assignment Criteria**:
```python
def assign_priority(action_item_content: str) -> ActionItemPriority:
    """
    Assign priority based on content analysis.

    CRITICAL indicators:
    - "blocking", "blocker", "critical"
    - "security vulnerability", "data loss"
    - "production down", "system unavailable"

    HIGH indicators:
    - "important", "should", "high priority"
    - "quality gate failed", "tests failing"

    MEDIUM indicators:
    - "improve", "enhance", "consider"
    - "technical debt", "refactor"

    LOW indicators:
    - "nice to have", "minor", "cosmetic"
    - "documentation", "cleanup"
    """
    content_lower = action_item_content.lower()

    # CRITICAL
    critical_keywords = [
        "blocking", "blocker", "critical", "urgent",
        "security vulnerability", "data loss",
        "production", "down", "outage"
    ]
    if any(kw in content_lower for kw in critical_keywords):
        return ActionItemPriority.CRITICAL

    # HIGH
    high_keywords = [
        "important", "should", "high priority",
        "quality gate", "test fail"
    ]
    if any(kw in content_lower for kw in high_keywords):
        return ActionItemPriority.HIGH

    # MEDIUM
    medium_keywords = [
        "improve", "enhance", "consider",
        "technical debt", "refactor"
    ]
    if any(kw in content_lower for kw in medium_keywords):
        return ActionItemPriority.MEDIUM

    # Default: LOW
    return ActionItemPriority.LOW
```

### C8 Fix Implementation

**Problem**: Too many action items converting to stories creates noise and overhead.

**Solution**:
1. **Strict Priority Filter**: Only CRITICAL auto-converts
2. **Max 1 Per Epic**: Prevents epic scope explosion
3. **Manual Review**: HIGH/MEDIUM require explicit promotion

**Implementation**:
```python
# Database tracking
CREATE TABLE action_item_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_num INTEGER NOT NULL,
    action_item_id INTEGER NOT NULL,
    story_num INTEGER NOT NULL,
    converted_at TEXT NOT NULL,
    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num),
    FOREIGN KEY (action_item_id) REFERENCES action_items(id)
);

# Check conversion limit
def _has_converted_action_item(self, epic_num: int) -> bool:
    """Check if epic already has a converted action item (C8 fix)."""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM action_item_conversions WHERE epic_num = ?",
            (epic_num,)
        )
        count = cursor.fetchone()[0]
        return count >= 1  # Max 1 per epic
```

### Workflow Diagram

```
Ceremony Completes
    “
Extract Action Items (with priority)
    “
ActionItemIntegrationService.process_action_items()
    “
     ’ Check: Epic already has 1 conversion? (C8 Fix)
           Yes ’ Track all items, convert none
           No  ’ Continue
    “
Filter by Priority
     ’ CRITICAL (first one only)
           “
       convert_to_story()
           “
       Create Story File
           “
       Register in DB
           “
       Git Commit
           “
       Mark Action Item as Converted
    
     ’ HIGH/MEDIUM/LOW
           “
       Mark for Manual Review
           “
       User can manually promote if needed
    
     ’ LOW + >30 days
            “
        Auto-Complete (cleanup)
```

---

## Testing Strategy

### Unit Tests

**Test 1: CRITICAL Action Item Auto-Converts**
```python
def test_critical_action_item_converts_to_story():
    """Test CRITICAL priority action item converts to story."""
    action_item = create_action_item(priority=ActionItemPriority.CRITICAL)

    result = service.process_action_items(ceremony_id=1)

    assert result["converted"] == 1
    assert result["tracked"] == 0
    # Verify story created
    assert story_exists(epic_num=1, story_num=expected_num)
```

**Test 2: C8 Fix - Max 1 Conversion Per Epic**
```python
def test_max_one_conversion_per_epic():
    """Test max 1 action item converts per epic (C8 fix)."""
    # Create 2 CRITICAL action items for same epic
    item1 = create_action_item(priority=ActionItemPriority.CRITICAL)
    item2 = create_action_item(priority=ActionItemPriority.CRITICAL)

    # Process first ceremony - should convert 1
    result1 = service.process_action_items(ceremony_id=1)
    assert result1["converted"] == 1

    # Process second ceremony - should convert 0 (limit hit)
    result2 = service.process_action_items(ceremony_id=2)
    assert result2["converted"] == 0
    assert result2["tracked"] == 1  # Tracked for manual review
```

**Test 3: C8 Fix - HIGH/MEDIUM/LOW Don't Auto-Convert**
```python
def test_non_critical_items_do_not_auto_convert():
    """Test HIGH/MEDIUM/LOW priority items don't auto-convert (C8 fix)."""
    items = [
        create_action_item(priority=ActionItemPriority.HIGH),
        create_action_item(priority=ActionItemPriority.MEDIUM),
        create_action_item(priority=ActionItemPriority.LOW),
    ]

    result = service.process_action_items(ceremony_id=1)

    # None should convert
    assert result["converted"] == 0
    assert result["tracked"] == 3
```

**Test 4: Stale Item Cleanup**
```python
def test_stale_low_priority_items_auto_complete():
    """Test LOW priority items auto-complete after 30 days."""
    # Create items 35 days old
    old_items = create_old_action_items(days_old=35, priority=ActionItemPriority.LOW)

    completed = service.auto_complete_stale_items(days_old=30)

    assert completed == len(old_items)
    # Verify items marked complete
    for item in old_items:
        assert is_complete(item.id)
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] ActionItemIntegrationService created
- [ ] C8 fix applied: Only CRITICAL converts, max 1 per epic
- [ ] Story creation from action items working
- [ ] Stale item cleanup implemented
- [ ] CLI commands created
- [ ] Integration with CeremonyOrchestrator complete
- [ ] Unit tests passing (>95% coverage)
- [ ] No linting errors (ruff)
- [ ] Type hints complete, mypy passes
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Epic 24 (ActionItemService) - Database backend
- Story 29.4 (Workflow Adjustment) - Complementary feature

**Downstream**:
- Story 29.7 (Testing & Validation)

---

## Notes

- **C8 Fix Applied**: Strict limits prevent noise (only CRITICAL, max 1 per epic)
- Manual review interface critical for HIGH priority items
- Auto-cleanup of stale items keeps database clean
- Story content template ensures consistency
- This story complements workflow adjustment (29.4)

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md`
- Critical Fixes: `CRITICAL_FIXES.md` (C8)
- Epic 29: `epics/epic-29-self-learning-feedback-loop.md`
