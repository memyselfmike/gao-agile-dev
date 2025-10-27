# Story 3.5: Autonomy Metrics Tracking

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer measuring autonomy
**I want** automatic tracking of manual interventions and success rates
**So that** I can quantify GAO-Dev's autonomous capabilities

---

## Acceptance Criteria

### AC1: Intervention Tracking
- [ ] Count manual interventions
- [ ] Categorize intervention types
- [ ] Track which agent/phase needed intervention
- [ ] Record intervention reasons

### AC2: Success Rate Tracking
- [ ] One-shot success rate calculation
- [ ] Error recovery rate tracking
- [ ] First-attempt vs. retry tracking
- [ ] Success criteria completion rate

### AC3: Agent Handoff Tracking
- [ ] Successful handoff count
- [ ] Failed handoff count
- [ ] Handoff timing
- [ ] Agent transition tracking

### AC4: Prompts Tracking
- [ ] Initial prompts count
- [ ] Follow-up prompts count
- [ ] Clarification requests count
- [ ] User corrections count

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/autonomy_tracker.py`

```python
"""Autonomy metrics tracking."""

from typing import Optional, List
from enum import Enum

from .collector import MetricsCollector


class InterventionType(Enum):
    """Types of manual interventions."""
    CLARIFICATION = "clarification"
    ERROR_FIX = "error_fix"
    DIRECTION_CHANGE = "direction_change"
    BLOCKED = "blocked"
    USER_CORRECTION = "user_correction"


class AutonomyTracker:
    """
    Tracks autonomy metrics during benchmark execution.
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize autonomy tracker."""
        self.collector = collector or MetricsCollector()
        self.interventions: List[dict] = []

    def record_intervention(
        self,
        intervention_type: InterventionType,
        agent_name: str,
        phase: str,
        reason: str
    ) -> None:
        """Record a manual intervention."""
        self.collector.increment_counter("interventions_total")
        self.collector.increment_counter(f"interventions_{intervention_type.value}")

        intervention = {
            "type": intervention_type.value,
            "agent": agent_name,
            "phase": phase,
            "reason": reason,
        }
        self.interventions.append(intervention)
        self.collector.record_event("intervention", intervention)

    def record_prompt(self, is_initial: bool = True) -> None:
        """Record user prompt."""
        if is_initial:
            self.collector.increment_counter("prompts_initial")
        else:
            self.collector.increment_counter("prompts_followup")

    def record_one_shot_success(self, task_name: str, success: bool) -> None:
        """Record whether task succeeded on first attempt."""
        key = "one_shot_successes" if success else "one_shot_failures"
        self.collector.increment_counter(key)

    def record_error_recovery(self, recovered: bool) -> None:
        """Record error recovery attempt."""
        key = "errors_recovered" if recovered else "errors_unrecovered"
        self.collector.increment_counter(key)

    def record_handoff(self, from_agent: str, to_agent: str, success: bool) -> None:
        """Record agent handoff."""
        key = "handoffs_successful" if success else "handoffs_failed"
        self.collector.increment_counter(key)

        self.collector.record_event("handoff", {
            "from": from_agent,
            "to": to_agent,
            "success": success
        })

    def calculate_autonomy_score(self) -> float:
        """Calculate overall autonomy score (0-100)."""
        # Simple formula: 100 - (interventions * 10) - (failures * 5)
        interventions = self.collector.counters.get("interventions_total", 0)
        failures = self.collector.counters.get("one_shot_failures", 0)
        score = max(0, 100 - (interventions * 10) - (failures * 5))
        return score
```

### Usage Example

```python
tracker = AutonomyTracker()

# Record intervention
tracker.record_intervention(
    InterventionType.CLARIFICATION,
    agent_name="amelia",
    phase="implementation",
    reason="Unclear acceptance criteria"
)

# Record prompt
tracker.record_prompt(is_initial=True)
tracker.record_prompt(is_initial=False)

# Record one-shot success
tracker.record_one_shot_success("story_3_1", success=True)

# Record agent handoff
tracker.record_handoff("bob", "amelia", success=True)
```

---

## Testing Requirements

### Unit Tests

```python
def test_intervention_recording():
    """Test recording interventions."""
    pass

def test_prompt_tracking():
    """Test prompt counting."""
    pass

def test_one_shot_success_tracking():
    """Test success rate calculation."""
    pass

def test_handoff_tracking():
    """Test agent handoff recording."""
    pass

def test_autonomy_score_calculation():
    """Test autonomy score formula."""
    pass
```

---

## Definition of Done

- [ ] AutonomyTracker implemented
- [ ] All tracking methods working
- [ ] Autonomy score calculation correct
- [ ] Unit tests passing (>85% coverage)
- [ ] Documentation complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.3 (MetricsCollector exists)
- **Blocks**: Story 3.8 (storage)

---

*Created as part of Epic 3: Metrics Collection System*
