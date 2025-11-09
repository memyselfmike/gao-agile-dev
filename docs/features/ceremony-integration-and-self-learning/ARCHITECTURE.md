# Technical Architecture: Ceremony Integration & Self-Learning System

**Feature**: Ceremony Integration & Self-Learning System
**Version**: 1.0
**Date**: 2025-11-09
**Architect**: Winston
**Status**: Design Approved

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Models](#data-models)
4. [Ceremony Trigger System](#ceremony-trigger-system)
5. [Self-Learning Loop](#self-learning-loop)
6. [Document Structure Manager](#document-structure-manager)
7. [API Design](#api-design)
8. [Performance Characteristics](#performance-characteristics)
9. [Testing Strategy](#testing-strategy)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER PROMPT                              │
└───────────────────────────────┬─────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BrianOrchestrator                            │
│  (Enhanced with Learning Integration)                          │
│                                                                 │
│  Methods:                                                       │
│  - select_workflows_with_learning() ← NEW                      │
│  - _build_context_with_learnings() ← NEW                       │
│  - _apply_learning_adjustments() ← NEW                         │
└───────────────┬────────────────────────────┬────────────────────┘
                │                            │
        ┌───────▼────────┐          ┌───────▼────────────┐
        │ Workflow       │          │ Learning           │
        │ Selector       │          │ Application        │
        │ (Enhanced)     │          │ Service            │
        └───────┬────────┘          └────────┬───────────┘
                │                            │
                │  ┌─────────────────────────┘
                │  │
                ↓  ↓
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced Workflow Sequence                         │
│  [create-prd] → [ceremony-planning] → [create-stories]         │
│  → [implement-stories] → [ceremony-standup]                    │
│  → [test-feature] → [ceremony-retrospective]                   │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   WorkflowCoordinator                           │
│  (Executes Sequence with Trigger Evaluation)                   │
└───────┬───────────────────────────────┬─────────────────────────┘
        │                               │
        │                       ┌───────▼────────────┐
        │                       │ CeremonyTrigger    │
        │                       │ Engine             │
        │                       │ (Evaluates When)   │
        │                       └───────┬────────────┘
        │                               │
        ↓                               ↓
┌─────────────────┐          ┌─────────────────────┐
│ Regular         │          │ Ceremony            │
│ Workflows       │          │ Orchestrator        │
│ (Agent Tasks)   │          │ (Ceremonies)        │
└────────┬────────┘          └─────────┬───────────┘
         │                             │
         ↓                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Outcome Processing                           │
│                                                                 │
│  Regular Workflow → Artifacts → GitCommit                      │
│  Ceremony → Transcript + ActionItems + Learnings → GitCommit   │
└────────┬──────────────────────────────────────┬─────────────────┘
         │                                      │
         ↓                                      ↓
┌─────────────────┐                  ┌─────────────────────┐
│ Document        │                  │ Learning            │
│ Lifecycle       │                  │ Index               │
│ (Track Docs)    │                  │ (Track Learnings)   │
└─────────────────┘                  └──────────┬──────────┘
                                                │
                        FEEDBACK LOOP ──────────┘
                        (Feeds back to Brian)
```

### Core Architectural Principles

1. **Event-Driven Triggers**: Ceremonies trigger based on workflow state events
2. **Learning Feedback**: Closed-loop learning from retrospectives to workflow selection
3. **Systematic Structure**: Document patterns enforced by DocumentStructureManager
4. **Zero Breaking Changes**: All enhancements backward compatible

### Design Patterns

**Pattern 1: Strategy Pattern (Trigger Evaluation)**
- TriggerStrategy interface
- Concrete strategies: EpicLifecycleTrigger, StoryIntervalTrigger, QualityGateTrigger

**Pattern 2: Observer Pattern (Workflow Events)**
- WorkflowCoordinator emits events
- CeremonyTriggerEngine observes and evaluates

**Pattern 3: Scoring Algorithm (Learning Relevance)**
- LearningApplicationService scores learnings
- Multiple factors: base relevance, success rate, confidence, recency, context similarity

**Pattern 4: Template Method (Document Structure)**
- DocumentStructureManager provides templates
- Subclasses for Level 0-4 work types

---

## System Components

### Component 1: CeremonyTriggerEngine

**Location**: `gao_dev/core/services/ceremony_trigger_engine.py`
**Estimated LOC**: ~350

**Purpose**: Evaluate when ceremonies should trigger based on workflow state

**Safety Mechanisms (C1, C9 Fixes)**:
- Max 10 ceremonies per epic (prevents infinite loops)
- 24-hour cooldowns for planning/retrospective, 12-hour for standup
- 10-minute timeout per ceremony
- Failure handling policies: ABORT, RETRY, CONTINUE, SKIP
- Cycle detection to prevent ceremony → learning → more ceremonies loops

**Class Diagram**:
```python
class TriggerType(Enum):
    EPIC_START = "epic_start"
    EPIC_COMPLETION = "epic_completion"
    MID_EPIC_CHECKPOINT = "mid_epic_checkpoint"
    STORY_INTERVAL = "story_interval"
    STORY_COUNT_THRESHOLD = "story_count_threshold"
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    REPEATED_FAILURE = "repeated_failure"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    DAILY = "daily"
    PHASE_END = "phase_end"

@dataclass
class TriggerContext:
    """Context for trigger evaluation."""
    epic_num: int
    story_num: Optional[int]
    scale_level: ScaleLevel
    stories_completed: int
    total_stories: int
    quality_gates_passed: bool
    last_standup: Optional[datetime]
    failure_count: int
    project_type: str

class CeremonyTriggerEngine:
    """
    Evaluates trigger conditions for ceremonies with safety mechanisms.

    Methods:
        should_trigger_planning(context) -> bool
        should_trigger_standup(context) -> bool
        should_trigger_retrospective(context) -> bool
        evaluate_all_triggers(context) -> List[CeremonyType]
        check_safety_limits(epic_num) -> bool  # C1 Fix
        get_last_ceremony_time(epic_num, ceremony_type) -> Optional[datetime]  # C1 Fix
    """

    # C1 Fix: Safety limits
    MAX_CEREMONIES_PER_EPIC = 10
    COOLDOWN_HOURS = {
        "planning": 24,
        "standup": 12,
        "retrospective": 24
    }
    TIMEOUT_MINUTES = 10

    def __init__(self, db_path: Path):
        self.ceremony_service = CeremonyService(db_path)
        self.story_service = StoryStateService(db_path)
        self.epic_service = EpicStateService(db_path)
        self.ceremony_counts = {}  # Track counts per epic
        self.last_ceremony_times = {}  # Track last run times

    def should_trigger_planning(
        self,
        context: TriggerContext
    ) -> bool:
        """
        Evaluate if planning ceremony should trigger.

        Rules:
        - Level 2: Optional (return False unless explicitly requested)
        - Level 3+: Required at epic start
        - Check: Has planning already occurred for this epic?
        """
        if context.scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return False

        if context.scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Required for Level 3+
            has_planning = self.ceremony_service.has_ceremony(
                epic_num=context.epic_num,
                ceremony_type="planning"
            )
            return not has_planning

        return False  # Optional for Level 2

    def should_trigger_standup(
        self,
        context: TriggerContext
    ) -> bool:
        """
        Evaluate if standup should trigger.

        Rules by Scale Level:
        - Level 0-1: Never
        - Level 2: Every 3 stories (if >3 total stories)
        - Level 3: Every 2 stories OR quality gate failure
        - Level 4: Every story OR daily (whichever first)
        """
        if context.scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return False

        # Quality gate failure always triggers (Level 2+)
        if not context.quality_gates_passed:
            return True

        # Level-specific intervals
        if context.scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE:
            # Every 3 stories, only if >3 total
            if context.total_stories <= 3:
                return False
            return context.stories_completed % 3 == 0

        elif context.scale_level == ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Every 2 stories
            return context.stories_completed % 2 == 0

        elif context.scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            # Every story OR daily
            if context.last_standup is None:
                return True

            # Check if 24 hours since last standup
            hours_since = (datetime.now() - context.last_standup).total_seconds() / 3600
            if hours_since >= 24:
                return True

            # Or every story
            return context.stories_completed > 0

        return False

    def should_trigger_retrospective(
        self,
        context: TriggerContext
    ) -> bool:
        """
        Evaluate if retrospective should trigger.

        Rules:
        - Level 0: Never
        - Level 1: Only on repeated failure (2+ times)
        - Level 2: Epic completion
        - Level 3: Mid-epic checkpoint (50%) + epic completion
        - Level 4: Phase end + epic completion
        """
        if context.scale_level == ScaleLevel.LEVEL_0_CHORE:
            return False

        if context.scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            # Only if failed 2+ times
            return context.failure_count >= 2

        # Check epic completion (all levels 2+)
        progress = context.stories_completed / max(context.total_stories, 1)
        if progress >= 1.0:
            return True

        # Mid-epic checkpoint for Level 3+
        if context.scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # At 50% completion
            if 0.48 <= progress <= 0.52:  # Within 2% of 50%
                has_mid_retro = self.ceremony_service.has_ceremony(
                    epic_num=context.epic_num,
                    ceremony_type="retrospective",
                    metadata_contains={"checkpoint": "mid"}
                )
                return not has_mid_retro

        return False

    def evaluate_all_triggers(
        self,
        context: TriggerContext
    ) -> List[CeremonyType]:
        """
        Evaluate all trigger conditions with safety checks (C1 Fix).

        Safety checks:
        1. Max ceremonies per epic limit
        2. Cooldown periods
        3. Cycle detection

        Returns:
            List of ceremony types that should trigger
        """
        # C1 Fix: Check safety limits first
        if not self._check_safety_limits(context.epic_num):
            return []  # Hit safety limit

        ceremonies = []

        if self.should_trigger_planning(context):
            if self._check_cooldown(context.epic_num, "planning"):
                ceremonies.append(CeremonyType.PLANNING)

        if self.should_trigger_standup(context):
            if self._check_cooldown(context.epic_num, "standup"):
                ceremonies.append(CeremonyType.STANDUP)

        if self.should_trigger_retrospective(context):
            if self._check_cooldown(context.epic_num, "retrospective"):
                ceremonies.append(CeremonyType.RETROSPECTIVE)

        return ceremonies

    def _check_safety_limits(self, epic_num: int) -> bool:
        """C1 Fix: Check if epic has hit ceremony limits."""
        count = self.ceremony_counts.get(epic_num, 0)
        return count < self.MAX_CEREMONIES_PER_EPIC

    def _check_cooldown(self, epic_num: int, ceremony_type: str) -> bool:
        """C1 Fix: Check if cooldown period has elapsed."""
        key = (epic_num, ceremony_type)
        last_run = self.last_ceremony_times.get(key)

        if last_run is None:
            return True  # Never run before

        cooldown_hours = self.COOLDOWN_HOURS[ceremony_type]
        elapsed = (datetime.now() - last_run).total_seconds() / 3600

        return elapsed >= cooldown_hours
```

**Integration Points**:
- WorkflowCoordinator calls `evaluate_all_triggers()` after each workflow step
- Context built from StateCoordinator (epic/story state)
- Results trigger CeremonyOrchestrator execution

---

### Component 2: LearningApplicationService

**Location**: `gao_dev/core/services/learning_application_service.py`
**Estimated LOC**: ~400

**Purpose**: Score learnings by relevance and apply them to workflow selection

**Class Diagram**:
```python
@dataclass
class ScoredLearning:
    """Learning with relevance score."""
    learning: Dict[str, Any]
    relevance_score: float
    reason: str  # Why it's relevant

class LearningApplicationService:
    """
    Applies learnings to workflow selection.

    Scoring algorithm:
    score = base_relevance
            * success_rate
            * confidence_score
            * decay_factor
            * context_similarity
    """

    def __init__(self, db_path: Path):
        self.learning_service = LearningIndexService(db_path)
        self.db_path = db_path

    def get_relevant_learnings(
        self,
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[ScoredLearning]:
        """
        Get top N relevant learnings for current context.

        Args:
            scale_level: Current project scale level
            project_type: Project type (greenfield, feature, bugfix)
            context: Additional context (tags, requirements, etc.)
            limit: Max learnings to return (default: 5)

        Returns:
            List of scored learnings, sorted by relevance (highest first)
        """
        # Get candidate learnings from database
        category = self._map_scale_to_category(scale_level)
        candidates = self.learning_service.search(
            category=category,
            active_only=True,
            limit=50  # Get more candidates, filter to top N
        )

        # Score each learning
        scored = []
        for learning in candidates:
            score = self._calculate_relevance_score(
                learning, scale_level, project_type, context
            )

            if score > 0.3:  # Relevance threshold
                reason = self._generate_relevance_reason(
                    learning, score
                )
                scored.append(ScoredLearning(
                    learning=learning,
                    relevance_score=score,
                    reason=reason
                ))

        # Sort by score descending
        scored.sort(key=lambda x: x.relevance_score, reverse=True)

        return scored[:limit]

    def _calculate_relevance_score(
        self,
        learning: Dict,
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict
    ) -> float:
        """
        Calculate relevance score for a learning.

        Formula (ADDITIVE WEIGHTED - C2 Fix):
        score = 0.30 * base_relevance
              + 0.20 * success_rate
              + 0.20 * confidence_score
              + 0.15 * decay_factor
              + 0.15 * context_similarity

        This prevents any single low factor from zeroing the entire score
        (previous multiplicative formula was unstable).

        Each factor is normalized to 0.0-1.0, final score is 0.0-1.0
        """
        # Base relevance (from learning itself)
        base = learning.get('relevance_score', 0.5)

        # Success rate (from past applications)
        success = learning.get('success_rate', 1.0)

        # Confidence (increases with successful applications)
        confidence = learning.get('confidence_score', 0.5)

        # Recency decay (newer = higher score)
        decay = self._calculate_decay(learning['indexed_at'])

        # Context similarity (how similar is current context?)
        similarity = self._context_similarity(
            learning, scale_level, project_type, context
        )

        # ADDITIVE WEIGHTED FORMULA (C2 Fix)
        score = (
            0.30 * base +
            0.20 * success +
            0.20 * confidence +
            0.15 * decay +
            0.15 * similarity
        )

        return min(max(score, 0.0), 1.0)  # Clamp to [0.0, 1.0]

    def _calculate_decay(self, indexed_at: str) -> float:
        """
        Calculate recency decay factor.

        Decay formula:
        - 0-30 days: 1.0 (full strength)
        - 30-90 days: Linear decay from 1.0 to 0.8
        - 90-180 days: Linear decay from 0.8 to 0.6
        - 180+ days: 0.5 (half strength)

        Learnings never decay below 0.5 to retain historical wisdom.
        """
        indexed = datetime.fromisoformat(indexed_at)
        days_old = (datetime.now() - indexed).days

        if days_old <= 30:
            return 1.0
        elif days_old <= 90:
            # Linear decay from 1.0 to 0.8
            return 1.0 - (days_old - 30) / 60 * 0.2
        elif days_old <= 180:
            # Linear decay from 0.8 to 0.6
            return 0.8 - (days_old - 90) / 90 * 0.2
        else:
            return 0.5

    def _context_similarity(
        self,
        learning: Dict,
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict
    ) -> float:
        """
        Calculate context similarity score (C11 Fix - Enhanced Logic).

        Compares:
        - Scale level match (with adjacency bonus)
        - Project type match (with category fallback)
        - Tag overlap (Jaccard similarity)
        - Category relevance (smart scoring)
        - Temporal context (similar project phases)
        """
        score = 0.0

        # Scale level match (25% weight) - C11 Fix
        learning_scale = learning.get('metadata', {}).get('scale_level')
        if learning_scale is not None:
            if learning_scale == scale_level.value:
                score += 0.25  # Exact match
            elif abs(learning_scale - scale_level.value) == 1:
                score += 0.15  # Adjacent levels
            elif abs(learning_scale - scale_level.value) == 2:
                score += 0.05  # Near levels
        else:
            score += 0.1  # Unknown scale gets base score

        # Project type match (20% weight) - C11 Fix
        learning_type = learning.get('metadata', {}).get('project_type')
        if learning_type == project_type:
            score += 0.20  # Exact match
        elif learning_type in ['any', 'general']:
            score += 0.15  # General learnings apply broadly

        # Tag overlap (30% weight) - Jaccard similarity
        learning_tags = set(learning.get('tags', []))
        context_tags = set(context.get('tags', []))
        if learning_tags and context_tags:
            overlap = len(learning_tags & context_tags)
            total = len(learning_tags | context_tags)
            score += 0.30 * (overlap / total)  # Jaccard index
        elif not learning_tags:
            score += 0.10  # Untagged learnings get small bonus

        # Category relevance (15% weight) - Smart scoring
        learning_category = learning.get('category')
        category_scores = {
            'quality': 0.15,      # Always relevant
            'architectural': 0.15,
            'process': 0.12,
            'technical': 0.10,
            'communication': 0.08,
            'tooling': 0.05
        }
        score += category_scores.get(learning_category, 0.05)

        # Temporal context (10% weight) - Similar phases
        learning_phase = learning.get('metadata', {}).get('phase')
        context_phase = context.get('phase')
        if learning_phase and context_phase:
            if learning_phase == context_phase:
                score += 0.10
            elif learning_phase in ['any', 'all_phases']:
                score += 0.05

        return min(score, 1.0)

    def record_application(
        self,
        learning_id: int,
        epic_num: int,
        story_num: Optional[int],
        outcome: str,  # 'success', 'failure', 'partial'
        context: str
    ) -> None:
        """
        Record a learning application and update statistics.

        Updates:
        - Insert into learning_applications table
        - Increment application_count
        - Recalculate success_rate
        - Adjust confidence_score
        """
        # Record application
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO learning_applications (
                    learning_id, epic_num, story_num,
                    outcome, application_context, applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (learning_id, epic_num, story_num,
                 outcome, context, datetime.now().isoformat())
            )

        # Update learning statistics
        stats = self._calculate_updated_stats(learning_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE learning_index
                SET application_count = ?,
                    success_rate = ?,
                    confidence_score = ?
                WHERE id = ?
                """,
                (stats['count'], stats['success_rate'],
                 stats['confidence'], learning_id)
            )

    def _calculate_updated_stats(
        self,
        learning_id: int
    ) -> Dict[str, float]:
        """
        Calculate updated statistics for a learning.

        Returns:
            Dict with count, success_rate, confidence
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT outcome
                FROM learning_applications
                WHERE learning_id = ?
                """,
                (learning_id,)
            )
            applications = [row[0] for row in cursor.fetchall()]

        count = len(applications)
        if count == 0:
            return {'count': 0, 'success_rate': 1.0, 'confidence': 0.5}

        # Calculate success rate
        successes = applications.count('success')
        partials = applications.count('partial')
        success_rate = (successes + 0.5 * partials) / count

        # Calculate confidence (increases with applications)
        # Formula: base (0.5) + bonus for applications (max +0.4)
        # Plateaus at ~20 applications
        confidence = 0.5 + (0.4 * (1 - math.exp(-count / 10)))

        # Reduce confidence if success rate is low
        if success_rate < 0.5:
            confidence *= success_rate * 2  # Halve confidence at 0% success

        return {
            'count': count,
            'success_rate': success_rate,
            'confidence': confidence
        }
```

---

### Component 3: Enhanced WorkflowSelector

**Location**: `gao_dev/methodologies/adaptive_agile/workflow_selector.py` (modified)
**Additional LOC**: ~200 (adds ceremony injection)

**Purpose**: Inject ceremonies into workflow sequences based on scale level

**Key Changes**:
```python
class WorkflowSelector:
    """Enhanced workflow selector with ceremony integration."""

    def __init__(self):
        self.base_workflows = {}  # Original workflows
        self.ceremony_configs = self._load_ceremony_configs()

    def select_workflows(
        self,
        scale_level: ScaleLevel,
        include_ceremonies: bool = True
    ) -> List[WorkflowStep]:
        """
        Select workflows with optional ceremony injection.

        Args:
            scale_level: Scale level (0-4)
            include_ceremonies: Whether to inject ceremonies (default: True)

        Returns:
            List of WorkflowSteps including ceremonies
        """
        # Get base workflows
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            workflows = self._level_0_workflows()
        elif scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            workflows = self._level_1_workflows()
        elif scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE:
            workflows = self._level_2_workflows()
        elif scale_level == ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            workflows = self._level_3_workflows()
        elif scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            workflows = self._level_4_workflows()
        else:
            raise ValueError(f"Invalid scale level: {scale_level}")

        # Inject ceremonies if requested
        if include_ceremonies:
            workflows = self._inject_ceremonies(workflows, scale_level)

        return workflows

    def _inject_ceremonies(
        self,
        workflows: List[WorkflowStep],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        """
        Inject ceremony workflows at appropriate points.

        Injection strategy:
        - Planning: After PRD/epics creation
        - Standup: After implementation workflows
        - Retrospective: After testing/completion
        """
        if scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return workflows  # No ceremonies for Level 0-1

        enhanced = []

        for workflow in workflows:
            enhanced.append(workflow)

            # Inject planning ceremony after PRD/epics
            if workflow.workflow_name in ['create-prd', 'create-epics']:
                if self._should_have_planning(scale_level):
                    enhanced.append(self._create_planning_ceremony(
                        scale_level, depends_on=[workflow.workflow_name]
                    ))

            # Inject standup after implementation
            if workflow.workflow_name == 'implement-stories':
                if self._should_have_standup(scale_level):
                    enhanced.append(self._create_standup_ceremony(
                        scale_level, depends_on=[workflow.workflow_name]
                    ))

            # Inject retrospective after testing
            if workflow.workflow_name in ['test-feature', 'integration-testing']:
                if self._should_have_retrospective(scale_level):
                    enhanced.append(self._create_retrospective_ceremony(
                        scale_level, depends_on=[workflow.workflow_name]
                    ))

        return enhanced

    def _create_planning_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create planning ceremony workflow step."""
        return WorkflowStep(
            workflow_name="ceremony-planning",
            phase="planning",
            required=(scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE),
            depends_on=depends_on,
            metadata={
                "ceremony_type": "planning",
                "participants": ["John", "Winston", "Bob"],
                "trigger": TriggerType.EPIC_START
            }
        )

    def _create_standup_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create standup ceremony workflow step."""
        # Interval varies by scale level
        interval = {
            ScaleLevel.LEVEL_2_SMALL_FEATURE: 3,
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE: 2,
            ScaleLevel.LEVEL_4_GREENFIELD: 1,
        }.get(scale_level, 2)

        return WorkflowStep(
            workflow_name="ceremony-standup",
            phase="implementation",
            required=False,  # Conditional based on trigger
            depends_on=depends_on,
            metadata={
                "ceremony_type": "standup",
                "participants": ["Bob", "Amelia", "Murat"],
                "trigger": TriggerType.STORY_INTERVAL,
                "interval": interval
            }
        )

    def _create_retrospective_ceremony(
        self,
        scale_level: ScaleLevel,
        depends_on: List[str]
    ) -> WorkflowStep:
        """Create retrospective ceremony workflow step."""
        return WorkflowStep(
            workflow_name="ceremony-retrospective",
            phase="retrospective",
            required=True,  # Always required for Level 2+
            depends_on=depends_on,
            metadata={
                "ceremony_type": "retrospective",
                "participants": ["team"],
                "trigger": TriggerType.EPIC_COMPLETION
            }
        )
```

---

### Component 4: DocumentStructureManager

**Location**: `gao_dev/core/services/document_structure_manager.py`
**Estimated LOC**: ~300

**Purpose**: Systematically initialize and maintain document structure by work type

**Class Diagram**:
```python
class DocumentStructureManager:
    """
    Manages document structure based on work type and scale level.

    Responsibilities:
    - Initialize feature folders
    - Create document templates
    - Update global docs
    - Enforce structure consistency
    """

    def __init__(
        self,
        project_root: Path,
        doc_lifecycle: DocumentLifecycleManager,
        git_manager: GitManager
    ):
        self.project_root = project_root
        self.doc_lifecycle = doc_lifecycle
        self.git = git_manager

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel
    ) -> Path:
        """
        Initialize feature folder based on scale level.

        Structure varies by level:
        - Level 0: None (no folder)
        - Level 1: Optional docs/bugs/<bug-id>.md
        - Level 2: docs/features/<name>/ with PRD, stories, CHANGELOG
        - Level 3: Full structure with epics, retrospectives
        - Level 4: Root docs + feature folders

        Returns:
            Path to created folder
        """
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            return None  # No docs for chores

        if scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            # Optional bug report
            bug_path = self.project_root / "docs" / "bugs"
            bug_path.mkdir(parents=True, exist_ok=True)
            return bug_path

        # Level 2+ get feature folders
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=True)

        # Level 2: Basic structure
        if scale_level >= ScaleLevel.LEVEL_2_SMALL_FEATURE:
            self._create_file(
                feature_path / "PRD.md",
                self._prd_template(feature_name, "lightweight")
            )
            (feature_path / "stories").mkdir(exist_ok=True)
            self._create_file(
                feature_path / "CHANGELOG.md",
                "# Changelog\n\n## Unreleased\n"
            )

        # Level 3: Rich structure
        if scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            self._create_file(
                feature_path / "ARCHITECTURE.md",
                self._architecture_template(feature_name)
            )
            (feature_path / "epics").mkdir(exist_ok=True)
            (feature_path / "retrospectives").mkdir(exist_ok=True)

        # Level 4: Additional structure
        if scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            (feature_path / "ceremonies").mkdir(exist_ok=True)
            self._create_file(
                feature_path / "MIGRATION_GUIDE.md",
                "# Migration Guide\n\nTBD\n"
            )

        # Register with document lifecycle
        self.doc_lifecycle.register_document(
            path=feature_path / "PRD.md",
            doc_type=DocumentType.PRD,
            metadata={
                "feature": feature_name,
                "scale_level": scale_level.value
            }
        )

        # Git commit
        self.git.add_all()
        self.git.commit(
            f"docs({feature_name}): initialize feature folder (Level {scale_level.value})"
        )

        return feature_path

    def update_global_docs(
        self,
        feature_name: str,
        epic_num: int,
        update_type: str  # 'planned', 'architected', 'completed'
    ) -> None:
        """
        Update global PRD and ARCHITECTURE docs.

        Args:
            feature_name: Name of feature
            epic_num: Epic number
            update_type: Type of update
        """
        if update_type == 'planned':
            self._update_global_prd(feature_name, epic_num, status="Planned")
        elif update_type == 'architected':
            self._update_global_architecture(feature_name, epic_num)
        elif update_type == 'completed':
            self._update_global_prd(feature_name, epic_num, status="Completed")
            self._update_changelog(feature_name, epic_num)

    def _update_global_prd(
        self,
        feature_name: str,
        epic_num: int,
        status: str
    ) -> None:
        """Update docs/PRD.md with feature section."""
        prd_path = self.project_root / "docs" / "PRD.md"
        if not prd_path.exists():
            return

        content = prd_path.read_text()

        # Add feature section if not exists
        feature_section = f"\n## Feature: {feature_name}\n\n"
        feature_section += f"**Status**: {status}\n"
        feature_section += f"**Epic**: {epic_num}\n"
        feature_section += f"**Docs**: [Feature Folder](./features/{feature_name}/)\n\n"

        if f"## Feature: {feature_name}" not in content:
            # Add before "## Future Work" or at end
            if "## Future Work" in content:
                content = content.replace(
                    "## Future Work",
                    feature_section + "## Future Work"
                )
            else:
                content += "\n" + feature_section
        else:
            # Update status
            import re
            pattern = rf"(## Feature: {feature_name}.*?\*\*Status\*\*:) \w+"
            content = re.sub(pattern, rf"\1 {status}", content)

        prd_path.write_text(content)

        # Git commit
        self.git.add(str(prd_path))
        self.git.commit(f"docs(prd): update {feature_name} status to {status}")
```

---

## Data Models

### Schema Changes (Migration 006)

```sql
-- Add columns to learning_index table
ALTER TABLE learning_index ADD COLUMN application_count INTEGER DEFAULT 0;
ALTER TABLE learning_index ADD COLUMN success_rate REAL DEFAULT 1.0;
ALTER TABLE learning_index ADD COLUMN confidence_score REAL DEFAULT 0.5;
ALTER TABLE learning_index ADD COLUMN decay_factor REAL DEFAULT 1.0;

-- New table: learning_applications
CREATE TABLE learning_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_id INTEGER NOT NULL REFERENCES learning_index(id),
    epic_num INTEGER,
    story_num INTEGER,
    outcome TEXT CHECK(outcome IN ('success', 'failure', 'partial')) NOT NULL,
    application_context TEXT,
    applied_at TEXT NOT NULL,
    metadata JSON,
    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num)
);

CREATE INDEX idx_learning_applications_learning_id
    ON learning_applications(learning_id);
CREATE INDEX idx_learning_applications_epic
    ON learning_applications(epic_num);
CREATE INDEX idx_learning_applications_applied_at
    ON learning_applications(applied_at);
```

### Migration Rollback Strategy (C6 Fix)

**Rollback Capability**: Full rollback supported via table rebuild

**Strategy**:
```python
def rollback_migration_006(conn):
    """
    Rollback migration 006 by rebuilding tables without new columns.

    Steps:
    1. Create backup tables with old schema
    2. Copy data (excluding new columns)
    3. Drop new tables
    4. Rename backup tables to original names
    5. Recreate original indexes
    6. Git revert migration commit
    """
    # Step 1: Create backup with old schema
    conn.execute("""
        CREATE TABLE learning_index_backup AS
        SELECT id, epic_num, story_num, category, content,
               relevance_score, tags, indexed_at, metadata, active
        FROM learning_index
    """)

    # Step 2: Drop new table
    conn.execute("DROP TABLE learning_applications")

    # Step 3: Drop current table and rename backup
    conn.execute("DROP TABLE learning_index")
    conn.execute("ALTER TABLE learning_index_backup RENAME TO learning_index")

    # Step 4: Recreate original indexes
    conn.execute("""
        CREATE INDEX idx_learning_index_category
        ON learning_index(category)
    """)
    # ... other indexes ...

    # Step 5: Git revert
    # Handled by GitMigrationManager.rollback()
```

**Validation After Rollback**:
- Verify all learning_index records preserved
- Confirm indexes recreated
- Test learning search queries
- Check no orphaned references

---

## Ceremony Trigger System

### Trigger Evaluation Flow

```
1. WorkflowCoordinator completes workflow step
        ↓
2. Emit WorkflowStepCompleted event
        ↓
3. CeremonyTriggerEngine observes event
        ↓
4. Build TriggerContext from:
   - StateCoordinator (epic/story state)
   - WorkflowCoordinator (completion status)
   - QualityGateManager (quality results)
        ↓
5. Evaluate triggers:
   - should_trigger_planning()
   - should_trigger_standup()
   - should_trigger_retrospective()
        ↓
6. Return List[CeremonyType] to trigger
        ↓
7. For each ceremony:
   - WorkflowCoordinator invokes CeremonyOrchestrator
   - C3 Fix: Wrap in GitIntegratedStateManager.transaction()
   - Ceremony executes (transcript, action items, learnings)
   - C3 Fix: All artifacts committed atomically (file + DB + git)
   - C9 Fix: On failure, apply failure policy (ABORT/RETRY/CONTINUE/SKIP)
        ↓
8. Continue workflow execution
```

### Trigger Configuration

```yaml
# config/ceremony_triggers.yaml
triggers:
  planning:
    level_2:
      required: false
      trigger: epic_start
      participants: [John, Winston, Bob]
    level_3:
      required: true
      trigger: epic_start
      participants: [John, Winston, Bob]
    level_4:
      required: true
      trigger: epic_start
      participants: [team]

  standup:
    level_2:
      interval: 3  # Every 3 stories
      threshold: 3  # Only if >3 total stories
      participants: [Bob, Amelia, Murat]
    level_3:
      interval: 2  # Every 2 stories
      quality_gate_trigger: true
      participants: [Bob, Amelia, Murat]
    level_4:
      interval: 1  # Every story
      daily: true  # Or daily, whichever first
      participants: [team]

  retrospective:
    level_1:
      trigger: repeated_failure
      failure_threshold: 2
      participants: [team]
    level_2:
      trigger: epic_completion
      required: true
      participants: [team]
    level_3:
      triggers:
        - mid_epic_checkpoint: 0.5  # At 50%
        - epic_completion: 1.0
      required: true
      participants: [team]
    level_4:
      triggers:
        - phase_end: [analysis, planning, solutioning, implementation]
        - epic_completion: 1.0
      required: true
      participants: [team]
```

---

## Self-Learning Loop

### Learning Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: COLLECTION (During Retrospective)                │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
    Retrospective Ceremony
         │
         ├─→ Transcript saved
         ├─→ Action items extracted
         └─→ Learnings extracted
                 │
                 ↓
    ┌──────────────────────┐
    │ LearningIndexService │
    │ index()              │
    └──────────┬───────────┘
               │
               ↓
    Learning Stored in DB
    - Initial relevance_score: 0.5-1.0 (based on category)
    - Initial confidence: 0.5
    - Application count: 0
    - Success rate: 1.0 (optimistic)
         │
         │
┌────────▼────────────────────────────────────────────────────┐
│  PHASE 2: APPLICATION (During New Project)                 │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
    New Project Starts
         │
         ↓
    ┌──────────────────────┐
    │ BrianOrchestrator    │
    │ analyze()            │
    └──────────┬───────────┘
               │
               ↓
    ┌─────────────────────────┐
    │ LearningApplication     │
    │ Service                 │
    │ get_relevant_learnings()│
    └──────────┬──────────────┘
               │
               ├─→ Query candidate learnings
               ├─→ Calculate relevance scores
               ├─→ Filter by threshold (>0.3)
               └─→ Return top 5
                       │
                       ↓
    ┌─────────────────────────┐
    │ Brian's Context         │
    │ Augmented with Learnings│
    └──────────┬──────────────┘
               │
               ↓
    ┌─────────────────────────┐
    │ Workflow Selection      │
    │ (Adjusted by Learnings) │
    └──────────┬──────────────┘
               │
               ├─→ Quality learnings → Add extra testing
               ├─→ Process learnings → More ceremonies
               └─→ Architectural learnings → Review step
                       │
                       ↓
    Workflows Execute
         │
         │
┌────────▼────────────────────────────────────────────────────┐
│  PHASE 3: FEEDBACK (After Epic Completion)                 │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
    Epic Completes
         │
         ↓
    ┌─────────────────────────┐
    │ Evaluate Outcome        │
    │ - Tests passed?         │
    │ - Quality gates met?    │
    │ - Learnings helpful?    │
    └──────────┬──────────────┘
               │
               ↓
    ┌─────────────────────────┐
    │ LearningApplication     │
    │ Service                 │
    │ record_application()    │
    └──────────┬──────────────┘
               │
               ├─→ Record outcome (success/failure/partial)
               ├─→ Update application_count++
               ├─→ Recalculate success_rate
               └─→ Adjust confidence_score
                       │
                       ↓
    Learning Stats Updated:
    - application_count: N + 1
    - success_rate: (successes + 0.5*partials) / count
    - confidence: 0.5 + (0.4 * (1 - exp(-count/10)))
         │
         │
         └──→ Learning Becomes Stronger (or Weaker)
                  ↓
              LOOP CONTINUES
```

---

## API Design

### Public APIs

**CeremonyTriggerEngine**:
```python
# Evaluate triggers
ceremonies = trigger_engine.evaluate_all_triggers(
    TriggerContext(
        epic_num=1,
        story_num=3,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=3,
        total_stories=8,
        quality_gates_passed=True,
        last_standup=datetime.now() - timedelta(days=2),
        failure_count=0,
        project_type="feature"
    )
)
# Returns: [CeremonyType.STANDUP]
```

**LearningApplicationService**:
```python
# Get relevant learnings
learnings = learning_app.get_relevant_learnings(
    scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
    project_type="greenfield",
    context={"tags": ["authentication", "api"], "requirements": ["security"]},
    limit=5
)
# Returns: List[ScoredLearning] with top 5 relevant learnings

# Record application
learning_app.record_application(
    learning_id=42,
    epic_num=5,
    story_num=3,
    outcome="success",
    context="Applied learning about JWT token validation"
)
```

**DocumentStructureManager**:
```python
# Initialize feature folder
feature_path = doc_mgr.initialize_feature_folder(
    feature_name="user-authentication",
    scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE
)
# Creates: docs/features/user-authentication/ with PRD, stories, CHANGELOG

# Update global docs
doc_mgr.update_global_docs(
    feature_name="user-authentication",
    epic_num=5,
    update_type="completed"
)
# Updates: docs/PRD.md, docs/CHANGELOG.md
```

---

## Performance Characteristics

**Ceremony Trigger Evaluation**: <10ms
- Database queries cached
- Context building optimized
- Simple boolean logic

**Learning Relevance Scoring**: <50ms for 50 candidates
- Simple arithmetic scoring (additive formula)
- No external API calls
- Database indexed queries

**Context Augmentation**: <500ms (C5 Fix - Realistic Target)
- Top 5 learnings retrieval: ~50ms
- Template rendering: ~100ms
- Brian context building: ~200ms
- Network RTT for 19K tokens: ~150ms
- Previous <100ms target was unrealistic

**Document Structure Init**: <500ms
- File system operations
- Template instantiation
- Git commit (batched)

**Ceremony Execution**: 30-120 seconds (user-dependent)
- C1 Fix: 10-minute timeout enforced
- Includes LLM API calls and user interaction
- Atomic git transaction: <1 second

**Overall Overhead**: <2% of workflow execution time
- Ceremonies: Optional/conditional (max 10 per epic)
- Learning queries: Once per project (~50ms)
- Document ops: Batched with git
- Safety mechanisms: Negligible (<5ms)

---

## Ceremony Failure Handling (C9 Fix)

**Failure Policy Enum**:
```python
class CeremonyFailurePolicy(Enum):
    ABORT = "abort"       # Stop epic execution, escalate to user
    RETRY = "retry"       # Retry ceremony up to 3 times
    CONTINUE = "continue" # Log error, continue without ceremony
    SKIP = "skip"         # Skip this ceremony, mark as skipped
```

**Policy Assignment by Ceremony Type**:
```yaml
failure_policies:
  planning:
    policy: ABORT           # Planning failure is critical
    max_retries: 2
    escalate: true

  standup:
    policy: CONTINUE        # Standup failure is non-critical
    max_retries: 1
    escalate: false

  retrospective:
    policy: RETRY           # Retry retro, then SKIP if fails
    max_retries: 3
    fallback: SKIP
    escalate: false
```

**Failure Handling Flow**:
```python
def execute_ceremony_with_policy(ceremony_type, context):
    """Execute ceremony with failure handling."""
    policy = FAILURE_POLICIES[ceremony_type]

    for attempt in range(policy.max_retries + 1):
        try:
            # C3 Fix: Wrap in transaction
            with git_state_manager.transaction() as txn:
                result = ceremony_orchestrator.hold_ceremony(
                    ceremony_type=ceremony_type,
                    context=context,
                    timeout=CeremonyTriggerEngine.TIMEOUT_MINUTES * 60
                )
                txn.commit()  # Atomic: files + DB + git
                return result

        except CeremonyTimeout:
            if attempt < policy.max_retries:
                log.warning(f"Ceremony {ceremony_type} timeout, retry {attempt+1}")
                continue
            else:
                return _handle_failure(policy, "timeout")

        except Exception as e:
            if attempt < policy.max_retries:
                log.error(f"Ceremony {ceremony_type} error: {e}, retry {attempt+1}")
                continue
            else:
                return _handle_failure(policy, str(e))

def _handle_failure(policy, reason):
    """Apply failure policy."""
    if policy.policy == CeremonyFailurePolicy.ABORT:
        raise CeremonyExecutionError(f"Critical ceremony failed: {reason}")

    elif policy.policy == CeremonyFailurePolicy.CONTINUE:
        log.warning(f"Ceremony failed but continuing: {reason}")
        return CeremonyResult(success=False, skipped=False)

    elif policy.policy == CeremonyFailurePolicy.SKIP:
        log.info(f"Ceremony skipped due to failure: {reason}")
        return CeremonyResult(success=False, skipped=True)

    elif policy.fallback:
        log.warning(f"Applying fallback policy: {policy.fallback}")
        return _handle_failure(PolicyConfig(policy=policy.fallback), reason)
```

**Error Categories**:
- **Timeout**: Ceremony exceeds 10-minute limit
- **LLM Failure**: API errors, rate limits
- **User Cancellation**: User exits ceremony
- **Validation Failure**: Ceremony output invalid
- **Transaction Failure**: Git/DB commit fails (auto-rollback)

---

## Transaction Boundaries (C3 Fix)

**Atomic Ceremony Execution**:

All ceremony operations wrapped in `GitIntegratedStateManager.transaction()` for atomicity:

```python
# Before (C3 blocker - no atomicity)
def hold_retrospective(epic_num):
    transcript_path = save_transcript(transcript)  # File write
    action_items = extract_action_items(transcript)  # DB insert
    learnings = extract_learnings(transcript)  # DB insert
    git_manager.commit("Add retrospective")  # Git commit
    # PROBLEM: If any step fails, partial state committed!

# After (C3 fix - atomic transaction)
def hold_retrospective(epic_num):
    with git_state_manager.transaction() as txn:
        # All operations atomic - rollback on any failure
        transcript_path = save_transcript(transcript)
        action_items = create_action_items_in_db(action_items)
        learnings = index_learnings_in_db(learnings)

        # Transaction automatically commits: file + DB + git
        txn.commit()
        # If ANY operation fails, ALL operations roll back
```

**Transaction Lifecycle**:
1. **Begin**: Create git branch `ceremony-temp-{timestamp}`
2. **Execute**: File writes, DB inserts, state updates
3. **Validate**: Check all operations succeeded
4. **Commit**: Atomic git commit with all changes
5. **Rollback** (on failure): Revert files, rollback DB, delete branch

**Benefits**:
- No partial ceremony artifacts
- No orphaned learnings
- No inconsistent state
- Automatic cleanup on failure

---

## Learning Maintenance (C10 Fix)

**Decay Maintenance Job**:

Scheduled job to update learning decay factors and deactivate stale learnings.

```python
class LearningMaintenanceJob:
    """
    Periodic maintenance of learning index.

    Runs: Daily at 02:00 UTC
    Duration: <5 seconds for 1000 learnings
    """

    def __init__(self, db_path: Path):
        self.learning_service = LearningIndexService(db_path)
        self.app_service = LearningApplicationService(db_path)

    def run_maintenance(self):
        """
        Run all maintenance tasks.

        Tasks:
        1. Update decay factors for all learnings
        2. Deactivate learnings with confidence < 0.2
        3. Supersede outdated learnings
        4. Prune learning_applications older than 1 year
        """
        with sqlite3.connect(self.db_path) as conn:
            # Task 1: Update decay factors
            self._update_decay_factors(conn)

            # Task 2: Deactivate low-confidence learnings
            self._deactivate_low_confidence(conn)

            # Task 3: Supersede outdated learnings
            self._supersede_outdated(conn)

            # Task 4: Prune old applications
            self._prune_old_applications(conn)

    def _update_decay_factors(self, conn):
        """Update decay_factor for all active learnings."""
        conn.execute("""
            UPDATE learning_index
            SET decay_factor = CASE
                WHEN julianday('now') - julianday(indexed_at) <= 30 THEN 1.0
                WHEN julianday('now') - julianday(indexed_at) <= 90 THEN
                    1.0 - ((julianday('now') - julianday(indexed_at) - 30) / 60 * 0.2)
                WHEN julianday('now') - julianday(indexed_at) <= 180 THEN
                    0.8 - ((julianday('now') - julianday(indexed_at) - 90) / 90 * 0.2)
                ELSE 0.5
            END
            WHERE active = 1
        """)

    def _deactivate_low_confidence(self, conn):
        """
        Deactivate learnings with confidence < 0.2.

        Criteria:
        - confidence_score < 0.2
        - success_rate < 0.3
        - application_count >= 5 (enough data)
        """
        conn.execute("""
            UPDATE learning_index
            SET active = 0,
                metadata = json_set(
                    metadata,
                    '$.deactivation_reason',
                    'Low confidence after ' || application_count || ' applications'
                )
            WHERE active = 1
              AND confidence_score < 0.2
              AND success_rate < 0.3
              AND application_count >= 5
        """)

    def _supersede_outdated(self, conn):
        """
        Mark older learnings as superseded by newer ones.

        Logic:
        - Same category + similar tags
        - Newer learning has higher confidence
        - Older learning gets marked superseded
        """
        conn.execute("""
            UPDATE learning_index AS old
            SET active = 0,
                metadata = json_set(
                    metadata,
                    '$.superseded_by',
                    (SELECT id FROM learning_index AS new
                     WHERE new.category = old.category
                       AND new.id != old.id
                       AND new.confidence_score > old.confidence_score + 0.2
                       AND new.indexed_at > old.indexed_at
                       AND new.active = 1
                     LIMIT 1)
                )
            WHERE active = 1
              AND EXISTS (
                SELECT 1 FROM learning_index AS new
                WHERE new.category = old.category
                  AND new.id != old.id
                  AND new.confidence_score > old.confidence_score + 0.2
                  AND new.indexed_at > old.indexed_at
                  AND new.active = 1
              )
        """)

    def _prune_old_applications(self, conn):
        """Delete learning_applications older than 1 year."""
        conn.execute("""
            DELETE FROM learning_applications
            WHERE julianday('now') - julianday(applied_at) > 365
        """)
```

**Scheduling**:
- Triggered by: `gao-dev learning maintain` CLI command
- Automated: Daily cron job (if daemon mode enabled)
- On-demand: After major epic completion

---

## Feature Flags

**Configuration** (`config/feature_flags.yaml`):
```yaml
feature_flags:
  # Epic 28: Ceremony Integration
  enable_ceremony_integration:
    enabled: true
    description: "Enable automatic ceremony triggers in workflows"
    rollout_percentage: 100  # Gradual rollout: 0-100

  enable_planning_ceremony:
    enabled: true
    parent: enable_ceremony_integration

  enable_standup_ceremony:
    enabled: true
    parent: enable_ceremony_integration

  enable_retrospective_ceremony:
    enabled: true
    parent: enable_ceremony_integration

  # Epic 29: Self-Learning
  enable_self_learning:
    enabled: true
    description: "Enable learning feedback loop"
    rollout_percentage: 100

  enable_learning_application:
    enabled: true
    parent: enable_self_learning

  enable_workflow_adjustment:
    enabled: true
    parent: enable_self_learning

  enable_learning_decay:
    enabled: true
    parent: enable_self_learning

  # Safety Features
  enforce_ceremony_limits:
    enabled: true
    description: "Enforce max 10 ceremonies per epic (C1 fix)"

  enforce_ceremony_cooldowns:
    enabled: true
    description: "Enforce cooldown periods between ceremonies (C1 fix)"

  enable_ceremony_timeouts:
    enabled: true
    description: "Enforce 10-minute ceremony timeout (C1 fix)"

  # Development Flags
  debug_ceremony_triggers:
    enabled: false
    description: "Log all ceremony trigger evaluations"

  debug_learning_scoring:
    enabled: false
    description: "Log learning relevance score calculations"
```

**Usage**:
```python
from gao_dev.core.feature_flags import FeatureFlags

flags = FeatureFlags.load()

# Check if feature enabled
if flags.is_enabled("enable_ceremony_integration"):
    ceremonies = trigger_engine.evaluate_all_triggers(context)

# Check with rollout percentage
if flags.is_enabled_for_project("enable_self_learning", project_id):
    learnings = learning_app.get_relevant_learnings(...)

# Nested flags (parent must be enabled)
if flags.is_enabled("enable_planning_ceremony"):
    # This checks both enable_planning_ceremony AND enable_ceremony_integration
    hold_planning()
```

---

## Testing Strategy

### Unit Tests (70+ tests)

**CeremonyTriggerEngine** (20 tests):
- Trigger evaluation for each scale level
- Edge cases (0 stories, 100% completion)
- Quality gate failure triggers
- Time-based triggers (daily)

**LearningApplicationService** (25 tests):
- Relevance scoring algorithm
- Decay calculation
- Confidence updates
- Application recording

**Enhanced WorkflowSelector** (15 tests):
- Ceremony injection for each level
- Dependency handling
- Optional vs required ceremonies

**DocumentStructureManager** (10 tests):
- Folder initialization by level
- Global doc updates
- Template rendering

### Integration Tests (30+ tests)

**Ceremony Integration** (10 tests):
- Full workflow with ceremonies
- Trigger evaluation in context
- Ceremony artifacts committed

**Self-Learning Loop** (15 tests):
- Learning application across 2 projects
- Workflow adjustment based on learnings
- Success rate updates

**Document Structure** (5 tests):
- Feature folder creation
- Global doc consistency
- Git commit atomicity

### End-to-End Tests (5+ tests)

**E2E Test 1**: Level 2 feature with ceremonies
- PRD → Planning → Stories → Standup → Retro
- Learnings extracted
- Documents structured correctly

**E2E Test 2**: Self-learning across projects
- Project 1: Quality issue → Retrospective → Learning
- Project 2: Brian applies learning → Extra testing added
- Outcome: Success → Confidence increased

**E2E Test 3**: Level 4 greenfield with full ceremonies
- Planning → Daily standups → Phase retros → Final retro
- 50+ learnings extracted
- Root docs + feature folders

---

## Deployment Plan

### Phase 1: Ceremony Integration (Epic 28)

**Week 1**:
1. Create ceremony workflows (Story 28.1)
2. Enhance WorkflowSelector (Story 28.2)

**Week 2**:
3. Implement CeremonyTriggerEngine (Story 28.3)
4. Integrate with orchestrator (Story 28.4)
5. CLI commands and tests (Story 28.5)

**Milestone**: `gao-dev run` with ceremonies triggering automatically

### Phase 2: Self-Learning (Epic 29)

**Week 3**:
1. Database migration (Story 29.1)
2. LearningApplicationService (Story 29.2)
3. Brian augmentation (Story 29.3)

**Week 4**:
4. Workflow adjustment (Story 29.4)
5. Action item integration (Story 29.5)
6. Learning decay (Story 29.6)
7. Testing (Story 29.7)

**Milestone**: Brian learns from past projects

### Rollout Strategy

**Beta Testing**:
- Run 3 benchmark projects with ceremonies
- Collect feedback on trigger accuracy
- Measure overhead (<2% target)

**Production Release**:
- Feature flag: `enable_ceremony_integration`
- Feature flag: `enable_self_learning`
- Gradual rollout with monitoring

---

## Conclusion

This architecture transforms GAO-Dev from a "workflow executor" to a "learning, self-improving autonomous developer" through:

1. **Automated Ceremonies**: Intelligent triggers at critical junctions
2. **Closed-Loop Learning**: Retrospectives → Learnings → Workflow Selection
3. **Systematic Structure**: Clear patterns for all work types
4. **Continuous Improvement**: System gets smarter with every project

**Key Innovation**: Feedback loop from ceremony outcomes to workflow selection creates true autonomy.

**Next Steps**: Begin implementation with Epic 28.1 (ceremony workflows).
