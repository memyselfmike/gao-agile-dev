# Critical Fixes & Risk Mitigations

**Document**: Critical Issues Resolution Plan
**Created**: 2025-11-09
**Status**: Implementation Plan
**Review Date**: 2025-11-09

---

## Executive Summary

This document addresses **12 critical blockers** identified in architectural review that must be resolved before Epic 28-29 implementation begins.

**Impact of Fixes**:
- Prevents infinite ceremony loops
- Stabilizes learning scoring algorithm
- Ensures data integrity with transactions
- Adds missing DocumentStructureManager component
- Sets realistic performance targets
- Provides database rollback capability

**Effort**: 1 week (~40 hours) to implement all fixes
**Return**: Prevents 3+ weeks of debugging and rework

---

## Table of Contents

1. [Critical Blocker Fixes (C1-C12)](#critical-blocker-fixes)
2. [Major Risk Mitigations (R1-R10)](#major-risk-mitigations)
3. [Architecture Updates](#architecture-updates)
4. [Story Changes](#story-changes)
5. [Implementation Checklist](#implementation-checklist)

---

## Critical Blocker Fixes

### C1: Ceremony Infinite Loop Prevention

**Problem**: Retrospectives could generate learnings that say "hold more ceremonies" → WorkflowAdjuster increases ceremony frequency → infinite loop

**Solution**: Multi-layered protection

**Fix 1: Maximum Ceremony Limit**
```python
# config/ceremony_limits.yaml
ceremony_limits:
  max_per_epic: 10
  max_per_type_per_epic:
    planning: 2      # Epic start + optional mid-epic
    standup: 8       # Generous for Level 4
    retrospective: 4 # Start, mid, end, emergency
```

**Fix 2: Cooldown Period**
```python
# gao_dev/core/services/ceremony_trigger_engine.py

class CeremonyTriggerEngine:
    COOLDOWN_HOURS = {
        "planning": 24,      # Min 24 hours between planning
        "standup": 12,       # Min 12 hours between standups
        "retrospective": 24  # Min 24 hours between retros
    }

    def should_trigger_ceremony(
        self,
        ceremony_type: str,
        context: TriggerContext
    ) -> bool:
        # Check cooldown
        last_ceremony = self.ceremony_service.get_last_ceremony(
            epic_num=context.epic_num,
            ceremony_type=ceremony_type
        )

        if last_ceremony:
            hours_since = (datetime.now() - last_ceremony.completed_at).total_seconds() / 3600
            if hours_since < self.COOLDOWN_HOURS[ceremony_type]:
                logger.info(
                    "ceremony_cooldown_active",
                    ceremony_type=ceremony_type,
                    hours_since=hours_since,
                    cooldown_required=self.COOLDOWN_HOURS[ceremony_type]
                )
                return False

        # Check max limit
        ceremony_count = self.ceremony_service.count_ceremonies(
            epic_num=context.epic_num,
            ceremony_type=ceremony_type
        )

        max_allowed = self.ceremony_service.get_max_limit(ceremony_type)
        if ceremony_count >= max_allowed:
            logger.warning(
                "ceremony_limit_reached",
                ceremony_type=ceremony_type,
                count=ceremony_count,
                max_allowed=max_allowed
            )
            return False

        # Proceed with normal trigger logic
        return self._evaluate_trigger_conditions(ceremony_type, context)
```

**Fix 3: Cycle Detection in WorkflowAdjuster**
```python
# gao_dev/methodologies/adaptive_agile/workflow_adjuster.py

class WorkflowAdjuster:
    def apply_adjustments(
        self,
        workflows: List[WorkflowStep],
        learnings: List[Learning],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        adjusted = workflows.copy()

        # Track ceremony adjustments to prevent loops
        ceremony_adjustments = 0
        MAX_CEREMONY_ADJUSTMENTS = 2  # Prevent runaway ceremony injection

        for learning in learnings:
            if learning['category'] == 'process':
                # Check if learning suggests more ceremonies
                if 'ceremony' in learning['learning'].lower() or 'standup' in learning['learning'].lower():
                    ceremony_adjustments += 1

                    if ceremony_adjustments > MAX_CEREMONY_ADJUSTMENTS:
                        logger.warning(
                            "ceremony_adjustment_limit_reached",
                            learning_id=learning['id'],
                            message="Skipping ceremony adjustment to prevent loop"
                        )
                        continue  # Skip this adjustment

                adjusted = self._adjust_ceremony_frequency(adjusted, learning)

            # Other adjustments...

        return adjusted
```

**Fix 4: Ceremony Timeout**
```python
# gao_dev/orchestrator/ceremony_orchestrator.py

class CeremonyOrchestrator:
    CEREMONY_TIMEOUT_SECONDS = 600  # 10 minutes max

    async def hold_ceremony(self, ceremony_type: str, **kwargs):
        try:
            result = await asyncio.wait_for(
                self._hold_ceremony_impl(ceremony_type, **kwargs),
                timeout=self.CEREMONY_TIMEOUT_SECONDS
            )
            return result
        except asyncio.TimeoutError:
            logger.error(
                "ceremony_timeout",
                ceremony_type=ceremony_type,
                epic_num=kwargs.get('epic_num'),
                timeout_seconds=self.CEREMONY_TIMEOUT_SECONDS
            )
            raise CeremonyTimeoutError(
                f"{ceremony_type} ceremony exceeded {self.CEREMONY_TIMEOUT_SECONDS}s timeout"
            )
```

**Validation**: Add test case for infinite loop prevention

---

### C2: Learning Scoring Formula Stability

**Problem**: Multiplicative formula `score = base × success × confidence × decay × similarity` produces unstable results where any single low factor kills the entire score.

**Solution**: Switch to weighted additive formula

**Fix: Additive Weighted Formula**
```python
# gao_dev/core/services/learning_application_service.py

def _calculate_relevance_score(
    self,
    learning: Dict,
    scale_level: ScaleLevel,
    project_type: str,
    context: Dict
) -> float:
    """
    Calculate relevance score using ADDITIVE weighted formula.

    NEW Formula (stable):
    score = 0.30 * base_relevance
          + 0.20 * success_rate
          + 0.20 * confidence_score
          + 0.15 * decay_factor
          + 0.15 * context_similarity

    Each factor weighted independently, so no single factor can zero out score.
    Result is always in [0, 1] range.
    """
    # Individual factors (each 0.0-1.0)
    base = learning.get('relevance_score', 0.5)
    success = learning.get('success_rate', 1.0)
    confidence = learning.get('confidence_score', 0.5)
    decay = self._calculate_decay(learning['indexed_at'])
    similarity = self._context_similarity(learning, scale_level, project_type, context)

    # Weighted sum
    score = (
        0.30 * base +
        0.20 * success +
        0.20 * confidence +
        0.15 * decay +
        0.15 * similarity
    )

    # Clamp to [0, 1] (should be automatic with correct inputs, but safe)
    return max(0.0, min(1.0, score))
```

**Fix: Smooth Decay Function**
```python
def _calculate_decay(self, indexed_at: str) -> float:
    """
    Calculate recency decay factor using smooth exponential decay.

    NEW Formula (no cliffs):
    decay = 0.5 + 0.5 * exp(-days/180)

    Results:
    - 0 days: 1.0 (full strength)
    - 30 days: 0.92
    - 90 days: 0.81
    - 180 days: 0.68
    - 365 days: 0.56
    - Never drops below 0.5 (always retains some value)
    """
    indexed = datetime.fromisoformat(indexed_at)
    days_old = (datetime.now() - indexed).days

    # Smooth exponential decay
    decay = 0.5 + 0.5 * math.exp(-days_old / 180)

    return decay
```

**Fix: Improved Confidence Formula**
```python
def _calculate_updated_stats(self, learning_id: int) -> Dict[str, float]:
    """
    Calculate updated statistics with improved confidence formula.

    NEW Confidence Formula:
    base_confidence = min(0.95, 0.5 + 0.45 * sqrt(successes / total))

    Then adjust for success rate:
    if success_rate < 0.5:
        confidence *= success_rate * 2  # Reduce if poor performance

    This gives smoother growth and never decreases on success.
    """
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute(
            "SELECT outcome FROM learning_applications WHERE learning_id = ?",
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

    # Calculate base confidence using sqrt (smoother growth)
    import math
    base_confidence = min(0.95, 0.5 + 0.45 * math.sqrt(successes / count))

    # Adjust for poor success rate
    if success_rate < 0.5:
        confidence = base_confidence * (success_rate * 2)
    else:
        confidence = base_confidence

    return {
        'count': count,
        'success_rate': success_rate,
        'confidence': confidence
    }
```

**Fix: Lower Threshold**
```python
# In get_relevant_learnings()

if score > 0.2:  # Lowered from 0.3 to catch edge cases
    scored.append(ScoredLearning(learning=learning, relevance_score=score, ...))
```

**Validation**: Add unit tests comparing old vs new formula with edge cases

---

### C3: Transaction Boundary for Ceremony Outcomes

**Problem**: Ceremony recording spans multiple database operations + file write + git commit with no transaction boundary → data corruption on failure

**Solution**: Wrap entire ceremony recording in atomic transaction using GitIntegratedStateManager

**Fix: CeremonyTransaction Wrapper**
```python
# gao_dev/orchestrator/ceremony_orchestrator.py

from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager

class CeremonyOrchestrator:
    def __init__(
        self,
        config: ConfigLoader,
        db_path: Path,
        project_root: Path,
        git_state_manager: Optional[GitIntegratedStateManager] = None
    ):
        self.config = config
        self.db_path = Path(db_path)
        self.project_root = Path(project_root)

        # Initialize services
        self.context_loader = FastContextLoader(db_path=self.db_path)
        self.ceremony_service = CeremonyService(db_path=self.db_path)
        self.action_service = ActionItemService(db_path=self.db_path)
        self.learning_service = LearningIndexService(db_path=self.db_path)

        # Git-integrated state manager for atomic operations
        self.git_state_manager = git_state_manager or GitIntegratedStateManager(
            db_path=self.db_path,
            project_path=self.project_root,
            auto_commit=True
        )

        self.logger = logger.bind(service="ceremony_orchestrator")

    def hold_ceremony(
        self,
        ceremony_type: str,
        epic_num: int,
        participants: List[str],
        story_num: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hold ceremony with ATOMIC transaction boundary.

        All operations wrapped in transaction:
        - Ceremony record creation
        - Action item creation
        - Learning indexing
        - Transcript file save
        - Git commit

        If ANY step fails, ALL rollback.
        """
        # Use git-integrated transaction
        try:
            with self.git_state_manager.transaction() as txn:
                # Phase 1: Prepare context
                context = self._prepare_ceremony_context(
                    ceremony_type, epic_num, story_num, additional_context
                )

                # Phase 2: Execute ceremony (simulated conversation)
                ceremony_result = self._execute_ceremony(
                    ceremony_type, participants, context
                )

                # Phase 3: Record outcomes (atomic)
                result = self._record_ceremony_atomic(
                    ceremony_type=ceremony_type,
                    epic_num=epic_num,
                    story_num=story_num,
                    participants=participants,
                    ceremony_result=ceremony_result,
                    transaction=txn  # Pass transaction context
                )

                # Transaction commits automatically on success
                return result

        except Exception as e:
            # Transaction rolls back automatically on exception
            self.logger.error(
                "ceremony_failed_with_rollback",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                error=str(e)
            )
            raise CeremonyExecutionError(
                f"Ceremony {ceremony_type} failed and was rolled back"
            ) from e

    def _record_ceremony_atomic(
        self,
        ceremony_type: str,
        epic_num: int,
        story_num: Optional[int],
        participants: List[str],
        ceremony_result: Dict,
        transaction: Any
    ) -> Dict[str, Any]:
        """
        Record ceremony outcomes within transaction context.

        Steps (all atomic):
        1. Create ceremony summary record
        2. Create action items
        3. Index learnings
        4. Save transcript file
        5. Git commit (handled by transaction)
        """
        # Step 1: Create ceremony summary
        ceremony_id = self.ceremony_service.create_summary(
            epic_num=epic_num,
            ceremony_type=ceremony_type,
            participants=participants,
            summary=ceremony_result['summary'],
            metadata=ceremony_result.get('metadata', {})
        )

        # Step 2: Create action items
        action_items = []
        for item_data in ceremony_result.get('action_items', []):
            item = self.action_service.create(
                epic_num=epic_num,
                story_num=story_num,
                title=item_data['title'],
                priority=item_data.get('priority', 'medium'),
                assignee=item_data.get('assignee'),
                source_ceremony_id=ceremony_id,
                source_ceremony_type=ceremony_type
            )
            action_items.append(item)

        # Step 3: Index learnings
        learnings = []
        for learning_data in ceremony_result.get('learnings', []):
            learning = self.learning_service.index(
                epic_num=epic_num,
                topic=learning_data['topic'],
                category=learning_data['category'],
                learning=learning_data['learning'],
                context=learning_data.get('context', ''),
                source_type='ceremony',
                source_ceremony_id=ceremony_id,
                relevance_score=learning_data.get('relevance_score', 1.0)
            )
            learnings.append(learning)

        # Step 4: Save transcript file
        transcript_path = self._save_transcript(
            ceremony_type=ceremony_type,
            epic_num=epic_num,
            ceremony_id=ceremony_id,
            transcript=ceremony_result['transcript']
        )

        # Step 5: Git commit (transaction handles this)
        # File already saved, will be included in transaction commit

        return {
            'ceremony_id': ceremony_id,
            'transcript_path': str(transcript_path),
            'action_items': action_items,
            'learnings': learnings,
            'summary': ceremony_result['summary']
        }
```

**Fix: Retry Logic**
```python
def hold_ceremony_with_retry(self, ceremony_type: str, **kwargs):
    """Hold ceremony with retry on transient failures."""
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            return self.hold_ceremony(ceremony_type, **kwargs)
        except CeremonyExecutionError as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "ceremony_retry",
                    ceremony_type=ceremony_type,
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES,
                    error=str(e)
                )
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

**Validation**: Integration test with simulated failures at each step

---

### C4: Add Story 28.6 - DocumentStructureManager

**Problem**: Epic 29.5 (Action Item Integration) depends on DocumentStructureManager but it's not in any story

**Solution**: Add new story to Epic 28

**Story 28.6: DocumentStructureManager Implementation**

**Points**: 5
**Owner**: Amelia
**Dependencies**: None (can be done in parallel with 28.1-28.5)

**Description**: Create DocumentStructureManager service to systematically initialize and maintain document structure based on work type and scale level.

**Acceptance Criteria**:
- [ ] Create `gao_dev/core/services/document_structure_manager.py` (~300 LOC)
- [ ] Implement `DocumentStructureManager` class with methods:
  - `initialize_feature_folder(feature_name, scale_level) -> Path`
  - `update_global_docs(feature_name, epic_num, update_type)`
  - `_create_file(path, content)` - Helper to create files
  - `_prd_template(feature_name, type)` - PRD template
  - `_architecture_template(feature_name)` - Architecture template
  - `_update_global_prd(feature_name, epic_num, status)`
  - `_update_changelog(feature_name, epic_num)`
- [ ] Feature folder structure by scale level:
  - Level 0: None
  - Level 1: Optional `docs/bugs/`
  - Level 2: `docs/features/<name>/` with PRD, stories, CHANGELOG
  - Level 3: Full structure with epics, retrospectives
  - Level 4: Root docs + feature folders
- [ ] Integration with DocumentLifecycleManager
- [ ] Git commit after folder initialization
- [ ] 10 unit tests (one per level, templates, global docs)

**Files Created**:
- `gao_dev/core/services/document_structure_manager.py` (~300 LOC)

**Updated Epic 28 Total**: 35 points (was 30)

---

### C5: Realistic Performance Targets

**Problem**: Claimed "<100ms context augmentation" but 19K token prompts take ~200ms RTT alone

**Solution**: Revise performance targets to realistic values

**Fix: Updated Performance Characteristics**

| Operation | Old Target | New Target | Rationale |
|-----------|-----------|------------|-----------|
| Ceremony trigger evaluation | <10ms | <10ms | ✅ Realistic (simple logic + cached queries) |
| Learning relevance scoring | <50ms | <50ms | ✅ Realistic (50 candidates, simple arithmetic) |
| Brian context augmentation | <100ms | <500ms | ⚠️ REVISED (19K tokens, RTT ~200ms, template rendering ~100ms, buffer ~200ms) |
| Workflow adjustment | <50ms | <50ms | ✅ Realistic (graph traversal + insertion) |
| Ceremony execution | N/A | <10 min | 🆕 NEW (timeout safety) |
| Database migration | N/A | <5 sec | 🆕 NEW (for 1000 learnings) |

**Document Updates**:
- Update ARCHITECTURE.md Section "Performance Characteristics"
- Update Story 29.3 acceptance criteria
- Add performance test suite expectations

---

### C6: Database Migration Rollback Plan

**Problem**: SQLite doesn't support `DROP COLUMN` → can't rollback Migration 006

**Solution**: Implement table rebuild strategy + backup

**Fix: Migration 006 with Rollback**

```python
# migrations/migration_006_learning_application_tracking.py

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def migrate_up(db_path: Path):
    """
    Apply Migration 006: Add learning application tracking.

    Strategy:
    1. Backup database
    2. Add columns with ALTER TABLE (SQLite 3.35+)
    3. Create learning_applications table
    4. Add indexes
    5. Validate
    """
    # Step 1: Backup
    backup_path = db_path.parent / f"{db_path.stem}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")

    with sqlite3.connect(db_path) as conn:
        try:
            # Step 2: Add columns to learning_index
            conn.execute("ALTER TABLE learning_index ADD COLUMN application_count INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE learning_index ADD COLUMN success_rate REAL DEFAULT 1.0")
            conn.execute("ALTER TABLE learning_index ADD COLUMN confidence_score REAL DEFAULT 0.5")
            conn.execute("ALTER TABLE learning_index ADD COLUMN decay_factor REAL DEFAULT 1.0")

            # Step 3: Create learning_applications table
            conn.execute("""
                CREATE TABLE learning_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_id INTEGER NOT NULL REFERENCES learning_index(id),
                    epic_num INTEGER,
                    story_num INTEGER,
                    outcome TEXT CHECK(outcome IN ('success', 'failure', 'partial')) NOT NULL,
                    application_context TEXT,
                    applied_at TEXT NOT NULL,
                    metadata JSON,
                    FOREIGN KEY (learning_id) REFERENCES learning_index(id),
                    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num)
                )
            """)

            # Step 4: Add indexes
            conn.execute("CREATE INDEX idx_learning_applications_learning_id ON learning_applications(learning_id)")
            conn.execute("CREATE INDEX idx_learning_applications_epic ON learning_applications(epic_num)")
            conn.execute("CREATE INDEX idx_learning_applications_applied_at ON learning_applications(applied_at)")

            # Additional indexes (from C6 Gap Analysis)
            conn.execute("CREATE INDEX idx_learning_index_category_active ON learning_index(category, is_active)")
            conn.execute("CREATE INDEX idx_learning_index_relevance ON learning_index(relevance_score DESC)")

            # Step 5: Validate
            cursor = conn.execute("PRAGMA table_info(learning_index)")
            columns = {row[1] for row in cursor.fetchall()}
            required = {'application_count', 'success_rate', 'confidence_score', 'decay_factor'}
            assert required.issubset(columns), f"Missing columns: {required - columns}"

            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_applications'")
            assert cursor.fetchone() is not None, "learning_applications table not created"

            print("Migration 006 completed successfully")

        except Exception as e:
            print(f"Migration failed: {e}")
            print(f"Restore from backup: {backup_path}")
            raise

def migrate_down(db_path: Path):
    """
    Rollback Migration 006.

    Strategy (SQLite doesn't support DROP COLUMN):
    1. Create backup
    2. Rebuild learning_index table without new columns
    3. Drop learning_applications table
    4. Validate
    """
    backup_path = db_path.parent / f"{db_path.stem}.rollback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Rollback backup created: {backup_path}")

    with sqlite3.connect(db_path) as conn:
        try:
            # Step 1: Create temporary table with old schema
            conn.execute("""
                CREATE TABLE learning_index_old AS
                SELECT
                    id, epic_num, topic, category, learning, context,
                    source_type, source_id, indexed_at, relevance_score,
                    tags, metadata, is_active
                FROM learning_index
            """)

            # Step 2: Drop original table
            conn.execute("DROP TABLE learning_index")

            # Step 3: Rename temp table
            conn.execute("ALTER TABLE learning_index_old RENAME TO learning_index")

            # Step 4: Recreate indexes
            conn.execute("CREATE INDEX idx_learning_index_epic ON learning_index(epic_num)")
            conn.execute("CREATE INDEX idx_learning_index_category ON learning_index(category)")
            # ... other original indexes ...

            # Step 5: Drop learning_applications table
            conn.execute("DROP TABLE IF EXISTS learning_applications")

            # Step 6: Validate
            cursor = conn.execute("PRAGMA table_info(learning_index)")
            columns = {row[1] for row in cursor.fetchall()}
            removed = {'application_count', 'success_rate', 'confidence_score', 'decay_factor'}
            assert not removed.intersection(columns), f"Columns not removed: {removed.intersection(columns)}"

            print("Migration 006 rolled back successfully")

        except Exception as e:
            print(f"Rollback failed: {e}")
            print(f"Restore from backup: {backup_path}")
            raise

def verify_migration(db_path: Path) -> bool:
    """Verify migration state."""
    with sqlite3.connect(db_path) as conn:
        # Check columns exist
        cursor = conn.execute("PRAGMA table_info(learning_index)")
        columns = {row[1] for row in cursor.fetchall()}
        required = {'application_count', 'success_rate', 'confidence_score', 'decay_factor'}

        if not required.issubset(columns):
            return False

        # Check table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_applications'")
        if cursor.fetchone() is None:
            return False

        # Check indexes exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        required_indexes = {
            'idx_learning_applications_learning_id',
            'idx_learning_applications_epic',
            'idx_learning_applications_applied_at'
        }

        return required_indexes.issubset(indexes)
```

**CLI Command**:
```bash
# Apply migration
python -m gao_dev.migrations.migration_006 up

# Verify
python -m gao_dev.migrations.migration_006 verify

# Rollback
python -m gao_dev.migrations.migration_006 down
```

**Story 29.1 Updates**: Add rollback testing to acceptance criteria

---

### C7: Workflow Dependency Validation

**Problem**: WorkflowAdjuster can inject workflows that break dependency graph

**Solution**: Implement dependency graph validation

**Fix: Dependency Validator**

```python
# gao_dev/methodologies/adaptive_agile/workflow_adjuster.py

from typing import Set, Dict, List
import networkx as nx

class WorkflowAdjuster:
    def apply_adjustments(
        self,
        workflows: List[WorkflowStep],
        learnings: List[Learning],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        """Apply learning-based adjustments with dependency validation."""
        adjusted = workflows.copy()

        for learning in learnings:
            if learning['category'] == 'quality':
                adjusted = self._insert_extra_testing(adjusted, learning)
            elif learning['category'] == 'process':
                adjusted = self._adjust_ceremony_frequency(adjusted, learning)
            elif learning['category'] == 'architectural':
                adjusted = self._add_architecture_review(adjusted, learning)

        # CRITICAL: Validate dependency graph
        if not self._validate_dependencies(adjusted):
            logger.error(
                "workflow_dependency_validation_failed",
                original_count=len(workflows),
                adjusted_count=len(adjusted)
            )
            # Fallback: Return original workflows
            return workflows

        return adjusted

    def _validate_dependencies(self, workflows: List[WorkflowStep]) -> bool:
        """
        Validate workflow dependency graph.

        Checks:
        1. All dependencies exist
        2. No cycles
        3. DAG is connected
        """
        # Build dependency graph
        graph = nx.DiGraph()
        workflow_names = {w.workflow_name for w in workflows}

        for workflow in workflows:
            graph.add_node(workflow.workflow_name)

            for dep in workflow.depends_on:
                if dep not in workflow_names:
                    logger.error(
                        "missing_dependency",
                        workflow=workflow.workflow_name,
                        missing_dep=dep
                    )
                    return False

                graph.add_edge(dep, workflow.workflow_name)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(graph):
            logger.error("workflow_cycle_detected")
            return False

        # All checks passed
        return True

    def _insert_extra_testing(
        self,
        workflows: List[WorkflowStep],
        learning: Learning
    ) -> List[WorkflowStep]:
        """
        Insert extra testing workflow with dependency safety.

        Strategy:
        1. Find anchor point (test-feature, integration-testing)
        2. If anchor exists, insert after it
        3. If anchor missing, append to testing phase
        """
        # Look for anchor points
        anchor_workflows = ['test-feature', 'integration-testing', 'unit-testing']
        anchor_found = None

        for i, workflow in enumerate(workflows):
            if workflow.workflow_name in anchor_workflows:
                anchor_found = (i, workflow.workflow_name)
                break

        extra_test = WorkflowStep(
            workflow_name="extra-integration-testing",
            phase="testing",
            required=True,
            depends_on=[anchor_found[1]] if anchor_found else [],
            metadata={
                "reason": "quality_learning",
                "learning_id": learning['id'],
                "learning": learning['learning']
            }
        )

        if anchor_found:
            # Insert after anchor
            workflows.insert(anchor_found[0] + 1, extra_test)
        else:
            # Append to end (no dependencies)
            logger.warning(
                "no_test_anchor_found",
                message="Appending extra testing to end of workflow"
            )
            workflows.append(extra_test)

        return workflows
```

**Validation**: Add unit tests with broken dependency scenarios

---

### C8: Action Item → Story Limits

**Problem**: High-priority action items auto-convert to stories with no limit → scope creep

**Solution**: Implement strict limits and deferral strategy

**Fix: Action Item Limits**

```python
# gao_dev/core/services/action_item_integration_service.py

class ActionItemIntegrationService:
    MAX_AUTO_STORIES_PER_EPIC = 1  # Conservative limit

    def auto_create_stories_from_action_items(
        self,
        epic_num: int,
        high_priority_only: bool = True,
        current_epic_only: bool = False  # NEW: Option to defer to next epic
    ) -> List[Story]:
        """
        Auto-create stories from high-priority action items.

        Rules:
        1. Max 1 auto-story per epic (prevent scope creep)
        2. Only CRITICAL priority (not just HIGH)
        3. Prefer deferring to next epic (not current)
        4. Require user approval if limit exceeded
        """
        # Get action items
        action_items = self.action_service.get_active(epic_num=epic_num)

        if high_priority_only:
            # CRITICAL priority only (stricter than HIGH)
            action_items = [
                a for a in action_items
                if a.get('priority', '').upper() == 'CRITICAL'
            ]

        # Filter to candidates
        candidates = [
            item for item in action_items
            if self._should_become_story(item) and not item.get('converted_to_story')
        ]

        if not candidates:
            return []

        # Check limit
        existing_auto_stories = self.story_service.count_auto_stories(epic_num=epic_num)

        if existing_auto_stories >= self.MAX_AUTO_STORIES_PER_EPIC:
            logger.warning(
                "auto_story_limit_reached",
                epic_num=epic_num,
                limit=self.MAX_AUTO_STORIES_PER_EPIC,
                pending_candidates=len(candidates)
            )

            # Defer to next epic (or backlog)
            for item in candidates:
                self._defer_to_next_epic(item, epic_num)

            return []

        # Create stories up to limit
        stories_to_create = min(len(candidates), self.MAX_AUTO_STORIES_PER_EPIC - existing_auto_stories)

        stories = []
        for item in candidates[:stories_to_create]:
            if current_epic_only:
                story = self._create_story_from_action_item(epic_num, item)
            else:
                # Defer to next epic by default (better practice)
                self._defer_to_next_epic(item, epic_num)
                continue

            stories.append(story)

        # Defer remaining candidates
        for item in candidates[stories_to_create:]:
            self._defer_to_next_epic(item, epic_num)

        return stories

    def _defer_to_next_epic(self, action_item: Dict, current_epic_num: int):
        """Defer action item to next epic (or backlog)."""
        self.action_service.update(
            action_item['id'],
            status='deferred',
            metadata={
                'deferred_from_epic': current_epic_num,
                'deferred_at': datetime.now().isoformat(),
                'reason': 'auto_story_limit_reached'
            }
        )

        logger.info(
            "action_item_deferred",
            action_item_id=action_item['id'],
            title=action_item['title'],
            from_epic=current_epic_num
        )

    def _should_become_story(self, item: Dict) -> bool:
        """
        Determine if action item should become a story.

        Criteria (STRICT):
        1. Priority CRITICAL (not just HIGH)
        2. Category process_improvement or quality_improvement
        3. Not already a story
        4. Clear, actionable title (>10 chars)
        5. Has assignee
        """
        return (
            item.get('priority', '').upper() == 'CRITICAL' and
            item.get('category') in ['process_improvement', 'quality_improvement'] and
            not item.get('converted_to_story') and
            len(item.get('title', '')) > 10 and
            item.get('assignee') is not None
        )
```

**Config Option**:
```yaml
# config/action_items.yaml
action_items:
  auto_conversion:
    enabled: false  # Opt-in, not default
    max_per_epic: 1
    priority_threshold: CRITICAL  # Not HIGH
    defer_to_next_epic: true  # Default behavior
```

**Validation**: Add tests for limit enforcement and deferral

---

### C9: Ceremony Failure Handling Policy

**Problem**: No specification for how to handle ceremony failures

**Solution**: Define clear failure policy with circuit breaker

**Fix: Failure Policy**

```python
# gao_dev/core/services/ceremony_failure_handler.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CeremonyFailurePolicy(Enum):
    ABORT_WORKFLOW = "abort"      # Stop workflow execution
    RETRY = "retry"                # Retry N times
    CONTINUE = "continue"          # Log warning, continue
    SKIP_FUTURE = "skip_future"    # Disable future ceremonies

@dataclass
class FailureConfig:
    policy: CeremonyFailurePolicy
    max_retries: int = 3
    retry_delay_seconds: int = 5
    circuit_breaker_threshold: int = 3

class CeremonyFailureHandler:
    """
    Handle ceremony failures with configurable policies.

    Policies by ceremony type:
    - Planning: ABORT (required ceremony)
    - Standup: CONTINUE (optional)
    - Retrospective: RETRY → CONTINUE (try to save learnings)
    """

    FAILURE_POLICIES = {
        "planning": FailureConfig(
            policy=CeremonyFailurePolicy.ABORT_WORKFLOW,
            max_retries=3  # Try hard, planning is critical
        ),
        "standup": FailureConfig(
            policy=CeremonyFailurePolicy.CONTINUE,
            max_retries=0  # Don't retry, not critical
        ),
        "retrospective": FailureConfig(
            policy=CeremonyFailurePolicy.RETRY,
            max_retries=3  # Try to save learnings
        )
    }

    def __init__(self):
        self.failure_counts = {}  # Track consecutive failures
        self.circuit_open = {}     # Circuit breaker state

    def handle_failure(
        self,
        ceremony_type: str,
        epic_num: int,
        error: Exception
    ) -> CeremonyFailurePolicy:
        """
        Handle ceremony failure according to policy.

        Returns: Policy to apply (ABORT, RETRY, CONTINUE, SKIP_FUTURE)
        """
        config = self.FAILURE_POLICIES.get(
            ceremony_type,
            FailureConfig(policy=CeremonyFailurePolicy.CONTINUE)
        )

        # Check circuit breaker
        key = f"{ceremony_type}_{epic_num}"
        if self.circuit_open.get(key, False):
            logger.warning(
                "ceremony_circuit_breaker_open",
                ceremony_type=ceremony_type,
                epic_num=epic_num
            )
            return CeremonyFailurePolicy.SKIP_FUTURE

        # Track consecutive failures
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1

        # Check circuit breaker threshold
        if self.failure_counts[key] >= config.circuit_breaker_threshold:
            self.circuit_open[key] = True
            logger.error(
                "ceremony_circuit_breaker_triggered",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                consecutive_failures=self.failure_counts[key]
            )
            return CeremonyFailurePolicy.SKIP_FUTURE

        # Return configured policy
        return config.policy

    def reset_failures(self, ceremony_type: str, epic_num: int):
        """Reset failure count on success."""
        key = f"{ceremony_type}_{epic_num}"
        self.failure_counts[key] = 0
        self.circuit_open[key] = False
```

**Integration with WorkflowCoordinator**:
```python
# gao_dev/core/services/workflow_coordinator.py

class WorkflowCoordinator:
    def __init__(self, ...):
        # ...
        self.ceremony_failure_handler = CeremonyFailureHandler()

    def execute_ceremonies(self, ceremonies: List[CeremonyType], context):
        """Execute ceremonies with failure handling."""
        for ceremony_type in ceremonies:
            try:
                result = self.ceremony_orchestrator.hold_ceremony(
                    ceremony_type=ceremony_type.value,
                    epic_num=context.epic_num,
                    participants=self._get_participants(ceremony_type)
                )

                # Success: Reset failure count
                self.ceremony_failure_handler.reset_failures(
                    ceremony_type.value,
                    context.epic_num
                )

                # Update context with results
                self._update_context_with_ceremony(result)

            except CeremonyExecutionError as e:
                policy = self.ceremony_failure_handler.handle_failure(
                    ceremony_type=ceremony_type.value,
                    epic_num=context.epic_num,
                    error=e
                )

                if policy == CeremonyFailurePolicy.ABORT_WORKFLOW:
                    logger.error("workflow_aborted_due_to_ceremony_failure")
                    raise WorkflowAbortedError(f"Planning ceremony failed") from e

                elif policy == CeremonyFailurePolicy.RETRY:
                    # Retry logic handled by ceremony_orchestrator.hold_ceremony_with_retry()
                    pass

                elif policy == CeremonyFailurePolicy.CONTINUE:
                    logger.warning(
                        "ceremony_failed_continuing",
                        ceremony_type=ceremony_type.value
                    )
                    # Continue with next ceremony

                elif policy == CeremonyFailurePolicy.SKIP_FUTURE:
                    logger.error(
                        "ceremonies_disabled_for_epic",
                        epic_num=context.epic_num
                    )
                    break  # Stop all future ceremonies
```

**Validation**: Add integration tests for each failure scenario

---

### C10: Learning Decay Maintenance Job

**Problem**: Decay calculated at query time → performance degradation, no archival

**Solution**: Implement nightly maintenance job

**Fix: Maintenance Job**

```python
# gao_dev/core/services/learning_maintenance.py

from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

class LearningMaintenanceService:
    """
    Nightly maintenance for learning decay and archival.

    Tasks:
    1. Update decay_factor for all active learnings
    2. Archive learnings >1 year old
    3. Clean up orphaned learning_applications
    4. Optimize database (VACUUM)
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run_maintenance(self):
        """Run all maintenance tasks."""
        logger.info("learning_maintenance_started")

        start = time.time()

        # Task 1: Update decay factors
        updated = self._update_decay_factors()
        logger.info("decay_factors_updated", count=updated)

        # Task 2: Archive old learnings
        archived = self._archive_old_learnings()
        logger.info("learnings_archived", count=archived)

        # Task 3: Clean orphans
        cleaned = self._clean_orphaned_applications()
        logger.info("orphaned_applications_cleaned", count=cleaned)

        # Task 4: Optimize database
        self._optimize_database()

        duration = time.time() - start
        logger.info("learning_maintenance_completed", duration_seconds=duration)

    def _update_decay_factors(self) -> int:
        """Update decay_factor for all active learnings."""
        with sqlite3.connect(self.db_path) as conn:
            # Get all active learnings
            cursor = conn.execute(
                "SELECT id, indexed_at FROM learning_index WHERE is_active = 1"
            )
            learnings = cursor.fetchall()

            # Update decay for each
            count = 0
            for learning_id, indexed_at in learnings:
                days_old = (datetime.now() - datetime.fromisoformat(indexed_at)).days
                decay = 0.5 + 0.5 * math.exp(-days_old / 180)

                conn.execute(
                    "UPDATE learning_index SET decay_factor = ? WHERE id = ?",
                    (decay, learning_id)
                )
                count += 1

            return count

    def _archive_old_learnings(self, max_age_days: int = 365) -> int:
        """Archive learnings older than max_age_days."""
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE learning_index
                SET is_active = 0,
                    metadata = json_set(
                        COALESCE(metadata, '{}'),
                        '$.archived_at',
                        ?
                    )
                WHERE indexed_at < ? AND is_active = 1
                """,
                (datetime.now().isoformat(), cutoff_date)
            )

            return cursor.rowcount

    def _clean_orphaned_applications(self) -> int:
        """Remove learning_applications for deleted learnings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM learning_applications
                WHERE learning_id NOT IN (
                    SELECT id FROM learning_index
                )
                """
            )

            return cursor.rowcount

    def _optimize_database(self):
        """Run VACUUM to optimize database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
```

**CLI Command**:
```bash
# Manual maintenance
gao-dev learning maintenance

# Scheduled (cron)
# Add to user's crontab:
# 0 2 * * * cd /project && gao-dev learning maintenance
```

**Validation**: Add test for decay updates and archival

---

### C11: Context Similarity Logic Fix

**Problem**: Minor logic bug in tag overlap calculation

**Solution**: Handle asymmetric tag cases

**Fix: Improved Context Similarity**

```python
def _context_similarity(
    self,
    learning: Dict,
    scale_level: ScaleLevel,
    project_type: str,
    context: Dict
) -> float:
    """
    Calculate context similarity score (FIXED).

    Handles asymmetric cases where only one side has tags.
    """
    score = 0.0

    # Scale level match (30% weight)
    learning_scale = learning.get('metadata', {}).get('scale_level', 0)
    if learning_scale == scale_level.value:
        score += 0.3
    elif abs(learning_scale - scale_level.value) == 1:
        score += 0.15  # Adjacent levels

    # Project type match (20% weight)
    learning_type = learning.get('metadata', {}).get('project_type', '')
    if learning_type == project_type:
        score += 0.2

    # Tag overlap (30% weight) - FIXED
    learning_tags = set(learning.get('tags', []))
    context_tags = set(context.get('tags', []))

    if learning_tags or context_tags:  # Either has tags
        if learning_tags and context_tags:
            # Both have tags: Normal Jaccard similarity
            overlap = len(learning_tags & context_tags)
            union = len(learning_tags | context_tags)
            score += 0.3 * (overlap / union)
        else:
            # Asymmetric: Partial credit for having tags
            score += 0.1  # Small bonus, but not full 0.3

    # Category relevance (20% weight)
    learning_category = learning.get('category', '')
    if learning_category in ['quality', 'architectural', 'process']:
        score += 0.2

    return min(score, 1.0)
```

---

### C12: Multi-Project Test Infrastructure

**Problem**: No test infrastructure for multi-project learning loops

**Solution**: Design test isolation strategy

**Fix: Test Fixtures**

```python
# tests/integration/test_learning_loop_fixtures.py

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class MultiProjectTestFixture:
    """
    Test fixture for multi-project learning loop tests.

    Provides:
    - Isolated project directories
    - Separate .gao-dev databases
    - Time manipulation for decay testing
    - Learning application audit trail
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="gao_test_"))
        self.projects = {}
        self.current_time = datetime.now()

    def create_project(self, name: str) -> Path:
        """Create isolated project directory."""
        project_dir = self.temp_dir / name
        project_dir.mkdir(parents=True)

        # Initialize .gao-dev
        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create isolated database
        db_path = gao_dev_dir / "documents.db"
        # ... initialize schema ...

        self.projects[name] = {
            'path': project_dir,
            'db_path': db_path
        }

        return project_dir

    def advance_time(self, days: int):
        """Simulate time passing for decay testing."""
        self.current_time += timedelta(days=days)

        # Update LearningApplicationService to use mock time
        # (Requires dependency injection of time function)

    def verify_learning_used(
        self,
        project_name: str,
        learning_id: int
    ) -> bool:
        """
        Verify that a learning was actually used.

        Checks:
        1. Learning in Brian's context
        2. Workflow adjustment record
        3. Learning application record
        """
        db_path = self.projects[project_name]['db_path']

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM learning_applications WHERE learning_id = ?",
                (learning_id,)
            )
            count = cursor.fetchone()[0]

            return count > 0

    def cleanup(self):
        """Clean up test projects."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
```

**E2E Test Example**:
```python
def test_two_project_quality_learning_loop():
    """
    Test learning loop across two projects.

    Project 1: Quality issue → Retrospective → Learning indexed
    Project 2: Brian applies learning → Extra testing added → Success
    Result: Learning confidence increases
    """
    fixture = MultiProjectTestFixture()

    # Project 1: Create quality issue and learning
    project1 = fixture.create_project("auth-service")

    # ... run project, fail quality gate, hold retrospective ...
    learning_id = create_learning("Auth tests need edge cases", category="quality")

    # Simulate 30 days passing
    fixture.advance_time(days=30)

    # Project 2: Apply learning
    project2 = fixture.create_project("payment-service")

    # Run Brian workflow selection with learning
    workflows = brian.select_workflows_with_learning(
        "Add payment API",
        project2
    )

    # Verify learning was applied
    assert fixture.verify_learning_used(project2.name, learning_id)

    # Verify extra testing was added
    workflow_names = [w.workflow_name for w in workflows]
    assert "extra-integration-testing" in workflow_names

    # ... run project, quality gates pass ...

    # Record success
    learning_app.record_application(
        learning_id=learning_id,
        epic_num=1,
        outcome="success",
        context="Applied to payment API"
    )

    # Verify confidence increased
    stats = learning_app._calculate_updated_stats(learning_id)
    assert stats['confidence'] > 0.5

    fixture.cleanup()
```

---

## Architecture Updates

### Updated Component Diagrams

**CeremonyOrchestrator with Transaction Boundary**:
```
CeremonyOrchestrator
    │
    ├─→ hold_ceremony()
    │   └─→ with git_state_manager.transaction():
    │       ├─→ create_ceremony_record()
    │       ├─→ create_action_items()
    │       ├─→ index_learnings()
    │       ├─→ save_transcript()
    │       └─→ git_commit() [automatic]
    │
    ├─→ CeremonyFailureHandler
    │   ├─→ handle_failure(type, epic, error)
    │   ├─→ Circuit breaker (3 failures → disable)
    │   └─→ Policy: ABORT | RETRY | CONTINUE | SKIP
    │
    └─→ CeremonyTriggerEngine
        ├─→ Max limits (10 per epic)
        ├─→ Cooldown (24h planning, 12h standup)
        └─→ Timeout (10 minutes)
```

**LearningApplicationService with Additive Scoring**:
```
LearningApplicationService
    │
    ├─→ get_relevant_learnings()
    │   ├─→ Query candidates (limit 50)
    │   ├─→ For each: score = 0.3*base + 0.2*success + ...
    │   ├─→ Filter (score > 0.2)
    │   └─→ Return top 5
    │
    ├─→ record_application()
    │   ├─→ Insert learning_applications row
    │   └─→ Update stats (application_count++, recalc success_rate, confidence)
    │
    └─→ Learning decay: SMOOTH exponential (no cliffs)
```

---

## Story Changes

### Story Point Revisions

**Epic 28**: 30 → 35 points
- Story 28.4: 5 → 8 points (transaction handling, error recovery)
- **NEW Story 28.6**: 5 points (DocumentStructureManager)

**Epic 29**: 38 → 51 points
- Story 29.2: 8 → 12 points (scoring formula rework)
- Story 29.4: 8 → 12 points (dependency validation)
- Story 29.7: 3 → 8 points (multi-project test infrastructure)

**Total**: 68 → 86 points (realistic: 108 with complexity multipliers)

---

## Implementation Checklist

### Phase 1: Critical Fixes (Week 1)

**Day 1-2: Ceremony Safety**
- [ ] Implement C1: Ceremony infinite loop prevention
  - [ ] Max limits config
  - [ ] Cooldown logic
  - [ ] Cycle detection
  - [ ] Timeout handling
- [ ] Implement C9: Ceremony failure handling
  - [ ] Failure policy enum
  - [ ] CeremonyFailureHandler class
  - [ ] Circuit breaker
  - [ ] Integration with WorkflowCoordinator

**Day 3-4: Learning Stability**
- [ ] Implement C2: Additive scoring formula
  - [ ] Replace multiplicative with weighted sum
  - [ ] Smooth decay function
  - [ ] Improved confidence formula
  - [ ] Lower threshold to 0.2
- [ ] Implement C10: Learning maintenance
  - [ ] LearningMaintenanceService class
  - [ ] CLI command
  - [ ] Tests

**Day 5: Transactions & Dependencies**
- [ ] Implement C3: Transaction boundary
  - [ ] Update CeremonyOrchestrator with GitIntegratedStateManager
  - [ ] Retry logic
  - [ ] Integration tests
- [ ] Implement C7: Dependency validation
  - [ ] NetworkX dependency graph
  - [ ] Validation logic
  - [ ] Fallback strategies

### Phase 2: Missing Components (Week 1)

**Day 6: DocumentStructureManager**
- [ ] Implement C4: Story 28.6
  - [ ] DocumentStructureManager class
  - [ ] Template methods
  - [ ] Global doc updates
  - [ ] Tests

**Day 7: Migration & Limits**
- [ ] Implement C6: Migration rollback
  - [ ] Rollback script
  - [ ] Backup strategy
  - [ ] Verification
- [ ] Implement C8: Action item limits
  - [ ] Max limits (1 per epic)
  - [ ] Deferral logic
  - [ ] Config options

### Phase 3: Performance & Testing

**Ongoing**:
- [ ] C5: Update performance targets in docs
- [ ] C11: Context similarity fix
- [ ] C12: Multi-project test fixtures
- [ ] Update all documentation with fixes
- [ ] Add risk mitigation plans to PRD

---

## Success Criteria

**All critical fixes complete** when:
- [ ] 12 critical blockers (C1-C12) implemented
- [ ] All fixes have unit tests
- [ ] Integration tests pass with fixes
- [ ] Documentation updated
- [ ] Story point estimates revised
- [ ] Timeline updated to 8 weeks
- [ ] Risk mitigation plans documented

**Ready for implementation** when:
- [ ] All checklist items completed
- [ ] Code review of all fixes
- [ ] Feature flags configured
- [ ] Rollback plan tested
- [ ] Go/No-Go review passes

---

## Timeline

**Total Effort**: 1 week (40 hours)

**Breakdown**:
- Critical fixes (C1-C12): 32 hours
- Documentation updates: 4 hours
- Testing: 4 hours

**ROI**: Saves 3+ weeks of debugging and rework

---

**Status**: Ready for Implementation
**Next Steps**: Begin Phase 1 (Ceremony Safety) fixes
