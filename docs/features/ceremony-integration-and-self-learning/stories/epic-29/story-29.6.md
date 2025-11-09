# Story 29.6: Learning Decay & Confidence

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P2 (Medium)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Story 29.1 (Schema), Story 29.2 (LearningApplicationService)

---

## User Story

**As a** learning system
**I want** learnings to decay over time and update confidence based on outcomes
**So that** old/obsolete learnings don't pollute workflow decisions

---

## Acceptance Criteria

### AC1: Learning Maintenance Job Created

- [ ] Create `gao_dev/core/services/learning_maintenance_job.py` (~250 lines)
- [ ] Class `LearningMaintenanceJob` with methods:
  - `run_maintenance() -> MaintenanceReport`
  - `_update_decay_factors()`
  - `_deactivate_low_confidence_learnings()`
  - `_supersede_outdated_learnings()`
  - `_prune_old_applications()`
- [ ] Scheduled execution: Daily at 02:00 UTC
- [ ] Performance: <5 seconds for 1000 learnings

### AC2: Decay Factor Updates (C10 Fix)

- [ ] Update `decay_factor` column for all active learnings
- [ ] Smooth exponential decay (C2 fix):
  ```python
  decay = 0.5 + 0.5 * exp(-days / 180)
  ```
- [ ] Results: 0d=1.0, 30d=0.92, 90d=0.81, 180d=0.68, 365d=0.56
- [ ] Never drops below 0.5

### AC3: Low Confidence Deactivation

- [ ] Deactivate learnings with:
  - confidence_score < 0.2
  - success_rate < 0.3
  - application_count >= 5
- [ ] Log reason in metadata

### AC4: Supersede Outdated Learnings

- [ ] Mark older learnings superseded by newer ones
- [ ] Criteria: same category, newer has confidence > old + 0.2

### AC5: Prune Old Applications

- [ ] Delete `learning_applications` older than 1 year

### AC6: CLI Command

- [ ] Create: `gao-dev learning maintain`
- [ ] Supports: --dry-run, --verbose

### AC7: Unit Tests

- [ ] Create `tests/core/services/test_learning_maintenance_job.py` (~200 lines)
- [ ] Test coverage >95%

---

## Technical Details

### Decay Formula (C2, C10 Fixes)

**Smooth Exponential Curve**:
```python
import math

def calculate_decay(indexed_at: str) -> float:
    """
    Smooth exponential decay - no cliffs.

    Formula: decay = 0.5 + 0.5 * exp(-days / 180)
    """
    indexed = datetime.fromisoformat(indexed_at)
    days_old = (datetime.now() - indexed).days

    decay = 0.5 + 0.5 * math.exp(-days_old / 180)

    return max(decay, 0.5)  # Floor at 0.5
```

### Files to Create

1. `gao_dev/core/services/learning_maintenance_job.py` (~250 lines)
2. `gao_dev/cli/learning_commands.py` (+50 lines)
3. `tests/core/services/test_learning_maintenance_job.py` (~200 lines)

---

## Testing Strategy

### Unit Tests

**Test 1: Decay Calculation**
```python
def test_decay_smooth_curve():
    """Test smooth exponential decay (C2, C10 fix)."""
    # 30 days: ~0.92
    decay = calculate_decay(thirty_days_ago)
    assert 0.91 <= decay <= 0.93

    # 365 days: ~0.56
    decay = calculate_decay(one_year_ago)
    assert 0.55 <= decay <= 0.57
```

**Test 2: Low Confidence Deactivation**
```python
def test_low_confidence_deactivated():
    """Test learnings with low confidence deactivated."""
    # 5 apps, 20% success, 0.15 confidence
    learning = create_learning(
        confidence_score=0.15,
        success_rate=0.2,
        application_count=5
    )

    deactivated = job._deactivate_low_confidence_learnings()

    assert deactivated == 1
    assert not learning_is_active(learning.id)
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] C10 fix applied: Decay implemented
- [ ] Maintenance job working
- [ ] CLI command created
- [ ] Unit tests passing (>95% coverage)
- [ ] Performance target met (<5s)
- [ ] Code reviewed and approved
- [ ] Changes committed
- [ ] Story marked complete

---

## Dependencies

**Upstream**: Stories 29.1, 29.2
**Downstream**: Story 29.7

**External**: APScheduler

---

## Notes

- **C10 Fix**: Learning decay implementation
- **C2 Enhancement**: Smooth exponential curve
- Keeps database clean and relevant
- Performance critical for daily execution

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md`
- Critical Fixes: `CRITICAL_FIXES.md` (C2, C10)
