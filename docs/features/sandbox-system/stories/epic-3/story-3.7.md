# Story 3.7: Workflow Metrics Tracking

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer tracking workflow
**I want** automatic tracking of stories, phases, and cycle times
**So that** I can analyze workflow efficiency

---

## Acceptance Criteria

### AC1: Story Tracking
- [ ] Stories created count
- [ ] Stories completed count
- [ ] Stories in progress count
- [ ] Story completion rate

### AC2: Cycle Time Tracking
- [ ] Per-story cycle time
- [ ] Average cycle time
- [ ] Cycle time by phase
- [ ] Cycle time trends

### AC3: Phase Distribution
- [ ] Time spent in each phase
- [ ] Phase distribution percentages
- [ ] Phase transition tracking
- [ ] Bottleneck identification

### AC4: Rework Tracking
- [ ] Rework count
- [ ] Rework reasons
- [ ] Stories requiring rework
- [ ] Rework impact on cycle time

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/workflow_tracker.py`

```python
"""Workflow metrics tracking."""

import time
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from .collector import MetricsCollector


@dataclass
class StoryMetrics:
    """Metrics for a single story."""
    story_id: str
    start_time: float
    end_time: Optional[float] = None
    phase_times: Dict[str, float] = field(default_factory=dict)
    rework_count: int = 0
    completed: bool = False


class WorkflowTracker:
    """
    Tracks workflow metrics during benchmark execution.
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """Initialize workflow tracker."""
        self.collector = collector or MetricsCollector()
        self.stories: Dict[str, StoryMetrics] = {}
        self.phase_start_times: Dict[str, float] = {}

    def start_story(self, story_id: str) -> None:
        """Start tracking a new story."""
        self.stories[story_id] = StoryMetrics(
            story_id=story_id,
            start_time=time.time()
        )
        self.collector.increment_counter("stories_created")

    def complete_story(self, story_id: str) -> None:
        """Mark story as completed."""
        if story_id in self.stories:
            story = self.stories[story_id]
            story.end_time = time.time()
            story.completed = True

            # Calculate cycle time
            cycle_time = story.end_time - story.start_time
            self.collector.set_value(f"story_{story_id}_cycle_time", cycle_time)
            self.collector.increment_counter("stories_completed")

            # Update average cycle time
            self._update_average_cycle_time()

    def record_rework(self, story_id: str, reason: str) -> None:
        """Record story rework."""
        if story_id in self.stories:
            self.stories[story_id].rework_count += 1
            self.collector.increment_counter("rework_total")
            self.collector.record_event("rework", {
                "story_id": story_id,
                "reason": reason
            })

    def start_phase(self, phase_name: str) -> None:
        """Start tracking a workflow phase."""
        self.phase_start_times[phase_name] = time.time()

    def end_phase(self, phase_name: str) -> None:
        """End tracking a workflow phase."""
        if phase_name in self.phase_start_times:
            elapsed = time.time() - self.phase_start_times[phase_name]
            self.collector.set_value(f"phase_{phase_name}_time", elapsed)
            del self.phase_start_times[phase_name]

            # Update phase distribution
            self._update_phase_distribution()

    def _update_average_cycle_time(self) -> None:
        """Calculate and update average cycle time."""
        completed_stories = [s for s in self.stories.values() if s.completed]
        if completed_stories:
            cycle_times = [s.end_time - s.start_time for s in completed_stories]
            avg_cycle_time = sum(cycle_times) / len(cycle_times)
            self.collector.set_value("avg_cycle_time", avg_cycle_time)

    def _update_phase_distribution(self) -> None:
        """Calculate phase time distribution."""
        phase_times = {}
        total_time = 0.0

        for key, value in self.collector.values.items():
            if key.startswith("phase_") and key.endswith("_time"):
                phase_name = key.replace("phase_", "").replace("_time", "")
                phase_times[phase_name] = value
                total_time += value

        if total_time > 0:
            phase_distribution = {
                phase: (time_spent / total_time * 100)
                for phase, time_spent in phase_times.items()
            }
            self.collector.set_value("phase_distribution", phase_distribution)

    def get_workflow_summary(self) -> Dict:
        """Get workflow metrics summary."""
        return {
            "stories_created": self.collector.counters.get("stories_created", 0),
            "stories_completed": self.collector.counters.get("stories_completed", 0),
            "avg_cycle_time": self.collector.values.get("avg_cycle_time", 0.0),
            "rework_count": self.collector.counters.get("rework_total", 0),
            "phase_distribution": self.collector.values.get("phase_distribution", {}),
        }
```

### Usage Example

```python
tracker = WorkflowTracker()

# Track story lifecycle
tracker.start_story("story_3_1")
# ... work on story ...
tracker.complete_story("story_3_1")

# Track phase timing
tracker.start_phase("planning")
# ... planning work ...
tracker.end_phase("planning")

# Record rework
tracker.record_rework("story_3_2", "Failed acceptance criteria")

# Get summary
summary = tracker.get_workflow_summary()
```

---

## Testing Requirements

### Unit Tests

```python
def test_story_lifecycle():
    """Test story start/complete."""
    pass

def test_cycle_time_calculation():
    """Test cycle time tracking."""
    pass

def test_phase_tracking():
    """Test phase timing."""
    pass

def test_phase_distribution():
    """Test phase distribution calculation."""
    pass

def test_rework_tracking():
    """Test rework recording."""
    pass

def test_workflow_summary():
    """Test summary generation."""
    pass
```

---

## Definition of Done

- [ ] WorkflowTracker implemented
- [ ] All tracking methods working
- [ ] Cycle time calculation correct
- [ ] Unit tests passing (>85% coverage)
- [ ] Documentation complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.3 (MetricsCollector exists)
- **Blocks**: Story 3.8 (storage)

---

*Created as part of Epic 3: Metrics Collection System*
