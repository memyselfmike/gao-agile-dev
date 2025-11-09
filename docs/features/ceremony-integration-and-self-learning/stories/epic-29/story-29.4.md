# Story 29.4: Workflow Adjustment Logic

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 12 story points (revised from 8 - C7 fix complexity)
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Story 29.2 (LearningApplicationService), Story 29.3 (Brian Context)

---

## User Story

**As a** workflow selector
**I want** to adjust workflows based on past learnings with cycle detection
**So that** past mistakes don't repeat and system improves continuously

---

## Acceptance Criteria

### AC1: WorkflowAdjuster Service Created

- [ ] Create `gao_dev/methodologies/adaptive_agile/workflow_adjuster.py` (~500 lines)
- [ ] Class `WorkflowAdjuster` with methods:
  - `adjust_workflows(workflows, learnings, scale_level) -> List[WorkflowStep]`
  - `_apply_quality_learnings(workflows, learnings) -> List[WorkflowStep]`
  - `_apply_process_learnings(workflows, learnings) -> List[WorkflowStep]`
  - `_apply_architectural_learnings(workflows, learnings) -> List[WorkflowStep]`
  - `_validate_adjustments(original, adjusted) -> bool`
  - `_detect_dependency_cycles(workflows) -> List[str]` (C7 fix)
  - `_enforce_adjustment_limits(workflows) -> List[WorkflowStep]` (C1 fix)
- [ ] Integration with WorkflowSelector
- [ ] Structured logging for all adjustments

### AC2: Dependency Cycle Detection (C7 Fix - CRITICAL)

- [ ] Install and use NetworkX for graph-based cycle detection
- [ ] Algorithm:
  ```python
  def _detect_dependency_cycles(self, workflows: List[WorkflowStep]) -> List[str]:
      """
      Detect circular dependencies in workflow steps using NetworkX.

      Args:
          workflows: List of workflow steps with depends_on

      Returns:
          List of cycle descriptions (empty if no cycles)

      Raises:
          WorkflowDependencyCycleError: If cycles detected
      """
      import networkx as nx

      # Build directed graph
      G = nx.DiGraph()
      for wf in workflows:
          G.add_node(wf.workflow_name)
          for dep in wf.depends_on:
              G.add_edge(wf.workflow_name, dep)

      # Find all cycles
      try:
          cycles = list(nx.simple_cycles(G))
          if cycles:
              cycle_descriptions = [" -> ".join(cycle + [cycle[0]]) for cycle in cycles]
              raise WorkflowDependencyCycleError(
                  f"Dependency cycles detected: {cycle_descriptions}"
              )
          return []
      except nx.NetworkXNoCycle:
          return []  # No cycles found
  ```
- [ ] Validate workflows before AND after adjustments
- [ ] Clear error messages identifying the cycle
- [ ] Unit tests for various cycle scenarios

### AC3: Adjustment Limits (C1 Fix)

- [ ] Maximum 3 workflows can be added per adjustment
- [ ] Maximum 3 adjustments per epic (prevents infinite loops)
- [ ] Track adjustments in database:
  ```sql
  CREATE TABLE workflow_adjustments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      epic_num INTEGER NOT NULL,
      learning_id INTEGER,
      adjustment_type TEXT,  -- 'add', 'modify', 'remove'
      workflow_name TEXT,
      reason TEXT,
      applied_at TEXT,
      FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num),
      FOREIGN KEY (learning_id) REFERENCES learning_index(id)
  );
  ```
- [ ] Raise `MaxAdjustmentsExceededError` if limits hit
- [ ] Log warning at 2 adjustments (approaching limit)

### AC4: Quality Learning Adjustments

- [ ] Identify quality learnings (category = "quality")
- [ ] Adjustments:
  ```python
  # If learning mentions "test coverage low"
  ’ Add workflow: "extended-testing" after implementation
  ’ Add workflow: "coverage-report" after testing

  # If learning mentions "code quality issues"
  ’ Add workflow: "code-review" after implementation
  ’ Add workflow: "static-analysis" after code review

  # If learning mentions "integration issues"
  ’ Add workflow: "integration-testing" after unit testing
  ’ Add workflow: "end-to-end-testing" after integration
  ```
- [ ] Workflows added with proper dependencies
- [ ] No duplicate workflows (check existing before adding)

### AC5: Process Learning Adjustments

- [ ] Identify process learnings (category = "process")
- [ ] Adjustments:
  ```python
  # If learning mentions "communication issues"
  ’ Increase standup frequency (interval: 2 ’ 1)
  ’ Add workflow: "ceremony-planning" at epic start

  # If learning mentions "scope creep"
  ’ Add workflow: "scope-review" mid-epic
  ’ Add workflow: "story-refinement" before implementation

  # If learning mentions "missed deadlines"
  ’ Add workflow: "time-estimation-review" at planning
  ’ Increase retrospective frequency (mid + final)
  ```
- [ ] Modify existing ceremony workflows (don't duplicate)

### AC6: Architectural Learning Adjustments

- [ ] Identify architectural learnings (category = "architectural")
- [ ] Adjustments:
  ```python
  # If learning mentions "architecture drift"
  ’ Add workflow: "architecture-review" after solutioning
  ’ Add workflow: "architecture-validation" mid-epic

  # If learning mentions "tech debt accumulation"
  ’ Add workflow: "tech-debt-assessment" at retrospective
  ’ Add workflow: "refactoring-review" after implementation

  # If learning mentions "security issues"
  ’ Add workflow: "security-review" after architecture
  ’ Add workflow: "security-testing" after implementation
  ```

### AC7: Adjustment Validation (C7 Fix)

- [ ] Validate adjusted workflows:
  - No dependency cycles (using NetworkX)
  - All dependencies exist
  - No duplicate workflow names
  - Required workflows not removed
  - Workflow depth <= 10 (prevents excessive nesting)
- [ ] Rollback to original workflows if validation fails
- [ ] Log validation errors with specific issues
- [ ] Return original + adjustment reason if can't adjust safely

### AC8: Integration with Brian Orchestrator

- [ ] Modify `BrianOrchestrator.select_workflows_with_learning()`:
  ```python
  def select_workflows_with_learning(self, user_prompt: str):
      # 1. Analyze complexity
      analysis = self._analyze_complexity(user_prompt)

      # 2. Build context with learnings (Story 29.3)
      context = self._build_context_with_learnings(...)
      learnings = self.learning_app.get_relevant_learnings(...)

      # 3. Select base workflows
      workflows = self.workflow_selector.select_workflows(
          scale_level=analysis.scale_level,
          context=context
      )

      # 4. Adjust workflows based on learnings (NEW)
      if learnings:
          try:
              workflows = self.workflow_adjuster.adjust_workflows(
                  workflows=workflows,
                  learnings=learnings,
                  scale_level=analysis.scale_level
              )
          except WorkflowDependencyCycleError as e:
              logger.error(f"Cycle detected, using original workflows: {e}")
              # Fallback to original workflows

      return workflows
  ```

### AC9: Adjustment Logging and Metrics

- [ ] Log all adjustments with structured logging:
  ```python
  logger.info(
      "workflow_adjusted",
      learning_id=learning.id,
      adjustment_type="add",
      workflow_name="extended-testing",
      reason="Low test coverage in past projects",
      scale_level=scale_level
  )
  ```
- [ ] Track metrics:
  - Number of adjustments per epic
  - Adjustment success rate
  - Most common adjustment types
  - Learnings that triggered adjustments

### AC10: Unit Tests

- [ ] Create `tests/methodologies/adaptive_agile/test_workflow_adjuster.py` (~400 lines)
- [ ] Tests:
  - Quality learning adjustments (add testing workflows)
  - Process learning adjustments (modify ceremonies)
  - Architectural learning adjustments (add review steps)
  - Cycle detection (various cycle scenarios)
  - Adjustment limits (max 3 workflows, max 3 adjustments)
  - Validation failures (missing dependencies, duplicates)
  - Fallback on validation failure
  - Integration with BrianOrchestrator
- [ ] Test coverage >95%

---

## Technical Details

### Files to Create/Modify

**1. WorkflowAdjuster Service** (new):
- `gao_dev/methodologies/adaptive_agile/workflow_adjuster.py` (~500 lines)

**2. Database Migration** (new):
- `migrations/migration_007_workflow_adjustments.py` (~150 lines)
- Create `workflow_adjustments` table

**3. BrianOrchestrator Integration** (modify):
- `gao_dev/orchestrator/brian_orchestrator.py` (+50 lines)

**4. Exception Classes** (new):
- `gao_dev/core/exceptions.py` (+30 lines)
  - `WorkflowDependencyCycleError`
  - `MaxAdjustmentsExceededError`

**5. Unit Tests** (new):
- `tests/methodologies/adaptive_agile/test_workflow_adjuster.py` (~400 lines)

### Dependency Cycle Detection Algorithm (C7 Fix)

```python
import networkx as nx
from typing import List
from gao_dev.core.exceptions import WorkflowDependencyCycleError

class WorkflowAdjuster:
    """
    Adjusts workflows based on past learnings with safety mechanisms.
    """

    MAX_WORKFLOWS_ADDED = 3  # C1 Fix
    MAX_ADJUSTMENTS_PER_EPIC = 3  # C1 Fix

    def _detect_dependency_cycles(
        self,
        workflows: List[WorkflowStep]
    ) -> List[str]:
        """
        Detect circular dependencies using NetworkX.

        Algorithm:
        1. Build directed graph (workflow -> dependencies)
        2. Use NetworkX simple_cycles() to find all cycles
        3. Raise error if cycles found with clear description

        Example cycle:
        workflow-a depends_on: [workflow-b]
        workflow-b depends_on: [workflow-c]
        workflow-c depends_on: [workflow-a]
        ’ Cycle: workflow-a -> workflow-b -> workflow-c -> workflow-a

        Returns:
            Empty list if no cycles

        Raises:
            WorkflowDependencyCycleError: If cycles detected
        """
        # Build directed graph
        G = nx.DiGraph()

        # Add all nodes first
        for wf in workflows:
            G.add_node(wf.workflow_name)

        # Add edges (workflow -> dependency)
        for wf in workflows:
            for dep in wf.depends_on:
                if dep not in G:
                    # Dependency references non-existent workflow
                    raise WorkflowDependencyCycleError(
                        f"Workflow '{wf.workflow_name}' depends on non-existent '{dep}'"
                    )
                G.add_edge(wf.workflow_name, dep)

        # Find all cycles
        try:
            cycles = list(nx.simple_cycles(G))
        except Exception as e:
            # NetworkX might raise for other graph issues
            raise WorkflowDependencyCycleError(f"Graph analysis error: {e}")

        if cycles:
            # Format cycles for error message
            cycle_descriptions = []
            for cycle in cycles:
                cycle_path = " -> ".join(cycle + [cycle[0]])
                cycle_descriptions.append(cycle_path)

            raise WorkflowDependencyCycleError(
                f"Dependency cycles detected:\n" +
                "\n".join(f"  - {desc}" for desc in cycle_descriptions)
            )

        return []

    def _validate_workflows(
        self,
        workflows: List[WorkflowStep],
        context: str = "adjusted"
    ) -> None:
        """
        Validate workflow list for common issues.

        Checks:
        1. No dependency cycles (C7 fix)
        2. All dependencies exist
        3. No duplicate workflow names
        4. Workflow depth <= 10 (prevents excessive nesting)

        Raises:
            WorkflowDependencyCycleError: If validation fails
        """
        # Check 1: Dependency cycles
        self._detect_dependency_cycles(workflows)

        # Check 2: All dependencies exist
        workflow_names = {wf.workflow_name for wf in workflows}
        for wf in workflows:
            for dep in wf.depends_on:
                if dep not in workflow_names:
                    raise WorkflowDependencyCycleError(
                        f"Workflow '{wf.workflow_name}' depends on non-existent '{dep}'"
                    )

        # Check 3: No duplicates
        if len(workflow_names) != len(workflows):
            duplicates = [name for name in workflow_names if
                          sum(1 for wf in workflows if wf.workflow_name == name) > 1]
            raise WorkflowDependencyCycleError(
                f"Duplicate workflow names: {duplicates}"
            )

        # Check 4: Workflow depth
        max_depth = self._calculate_max_depth(workflows)
        if max_depth > 10:
            raise WorkflowDependencyCycleError(
                f"Workflow depth {max_depth} exceeds limit of 10"
            )

    def _calculate_max_depth(
        self,
        workflows: List[WorkflowStep]
    ) -> int:
        """
        Calculate maximum dependency depth.

        Uses topological sort to find longest path.
        """
        G = nx.DiGraph()
        for wf in workflows:
            G.add_node(wf.workflow_name)
            for dep in wf.depends_on:
                G.add_edge(dep, wf.workflow_name)  # Reverse edge for topological

        try:
            # Longest path in DAG
            return nx.dag_longest_path_length(G)
        except nx.NetworkXError:
            # Not a DAG (has cycles) - handled by cycle detection
            return 0

    def adjust_workflows(
        self,
        workflows: List[WorkflowStep],
        learnings: List[ScoredLearning],
        scale_level: ScaleLevel
    ) -> List[WorkflowStep]:
        """
        Adjust workflows based on learnings with safety checks.

        Safety Mechanisms (C1, C7 fixes):
        - Max 3 workflows added per adjustment
        - Max 3 adjustments per epic
        - Dependency cycle detection
        - Validation before and after adjustments
        - Rollback on validation failure

        Args:
            workflows: Original workflow sequence
            learnings: Relevant learnings with scores
            scale_level: Current scale level

        Returns:
            Adjusted workflow sequence (or original if adjustment fails)
        """
        # Validate original workflows first
        try:
            self._validate_workflows(workflows, context="original")
        except WorkflowDependencyCycleError as e:
            logger.error(f"Original workflows invalid: {e}")
            raise  # Original workflows are broken - can't proceed

        # Check adjustment limits
        adjustment_count = self._get_adjustment_count_for_epic()
        if adjustment_count >= self.MAX_ADJUSTMENTS_PER_EPIC:
            logger.warning(
                f"Max adjustments ({self.MAX_ADJUSTMENTS_PER_EPIC}) reached for epic"
            )
            return workflows  # Return original

        # Track workflows added
        workflows_added = 0
        adjusted = workflows.copy()

        # Apply adjustments by category
        for learning in learnings:
            if workflows_added >= self.MAX_WORKFLOWS_ADDED:
                logger.warning(f"Max workflows added ({self.MAX_WORKFLOWS_ADDED})")
                break

            category = learning.learning.get("category")

            if category == "quality":
                added = self._apply_quality_learnings(adjusted, [learning])
                workflows_added += len(added)
            elif category == "process":
                added = self._apply_process_learnings(adjusted, [learning])
                workflows_added += len(added)
            elif category == "architectural":
                added = self._apply_architectural_learnings(adjusted, [learning])
                workflows_added += len(added)

        # Validate adjusted workflows
        try:
            self._validate_workflows(adjusted, context="adjusted")
        except WorkflowDependencyCycleError as e:
            logger.error(f"Adjusted workflows invalid: {e}, rolling back")
            return workflows  # Rollback to original

        # Record adjustments in database
        self._record_adjustments(workflows, adjusted, learnings)

        return adjusted
```

### Adjustment Examples

**Example 1: Quality Learning**
```python
# Learning: "Test coverage <80% caused production bugs"
# Category: quality
# Confidence: 0.85
# Success Rate: 0.9

# Original Workflows:
[
    WorkflowStep("create-prd", phase="planning"),
    WorkflowStep("create-stories", phase="planning"),
    WorkflowStep("implement-stories", phase="implementation"),
    WorkflowStep("test-feature", phase="testing")
]

# Adjusted Workflows (added 2 testing workflows):
[
    WorkflowStep("create-prd", phase="planning"),
    WorkflowStep("create-stories", phase="planning"),
    WorkflowStep("implement-stories", phase="implementation"),
    WorkflowStep("test-feature", phase="testing"),
    WorkflowStep("extended-testing", phase="testing", depends_on=["test-feature"]),  # ADDED
    WorkflowStep("coverage-report", phase="testing", depends_on=["extended-testing"])  # ADDED
]
```

**Example 2: Process Learning**
```python
# Learning: "Daily standups prevented blockers"
# Category: process
# Confidence: 0.75

# Original Workflows (Level 2 - standup every 3 stories):
[
    ...,
    WorkflowStep("ceremony-standup", interval=3),
    ...
]

# Adjusted Workflows (increased frequency):
[
    ...,
    WorkflowStep("ceremony-standup", interval=2),  # MODIFIED: 3 -> 2
    ...
]
```

**Example 3: Cycle Detection (C7 Fix)**
```python
# BAD: Learning adjustment creates cycle

# Original:
workflow_a depends_on: []
workflow_b depends_on: [workflow_a]

# Learning suggests: Add workflow_c before workflow_a
workflow_c depends_on: [workflow_b]  # Creates cycle!
workflow_a depends_on: [workflow_c]

# Cycle: workflow_a -> workflow_c -> workflow_b -> workflow_a

# System detects cycle and REJECTS adjustment:
WorkflowDependencyCycleError:
  "Dependency cycles detected:
   - workflow_a -> workflow_c -> workflow_b -> workflow_a"
```

---

## Testing Strategy

### Unit Tests

**Test 1: Quality Learning Adjustment**
```python
def test_quality_learning_adds_testing_workflows():
    """Test quality learning adds extended testing."""
    learning = create_learning(category="quality", content="Low test coverage")

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=[learning],
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE
    )

    # Should add extended-testing and coverage-report
    assert len(adjusted) == len(base_workflows) + 2
    assert any(wf.workflow_name == "extended-testing" for wf in adjusted)
```

**Test 2: Dependency Cycle Detection (C7 Fix)**
```python
def test_cycle_detection_rejects_invalid_adjustment():
    """Test cycle detection prevents invalid adjustments."""
    # Create workflows that would form a cycle
    workflows = [
        WorkflowStep("a", depends_on=["b"]),
        WorkflowStep("b", depends_on=["c"]),
        WorkflowStep("c", depends_on=["a"])  # Cycle!
    ]

    with pytest.raises(WorkflowDependencyCycleError) as exc_info:
        adjuster._detect_dependency_cycles(workflows)

    assert "a -> b -> c -> a" in str(exc_info.value)
```

**Test 3: Adjustment Limits (C1 Fix)**
```python
def test_max_workflows_added_enforced():
    """Test max 3 workflows can be added."""
    learnings = [create_learning() for _ in range(10)]

    adjusted = adjuster.adjust_workflows(
        workflows=base_workflows,
        learnings=learnings,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE
    )

    # Should add max 3 workflows
    workflows_added = len(adjusted) - len(base_workflows)
    assert workflows_added <= 3
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] WorkflowAdjuster service created
- [ ] Dependency cycle detection implemented (C7 fix)
- [ ] Adjustment limits enforced (C1 fix)
- [ ] Quality, process, architectural adjustments working
- [ ] Validation and rollback working
- [ ] Integration with BrianOrchestrator complete
- [ ] Unit tests passing (>95% coverage)
- [ ] NetworkX dependency added to requirements
- [ ] No linting errors (ruff)
- [ ] Type hints complete, mypy passes
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Story 29.2 (LearningApplicationService)
- Story 29.3 (Brian Context Augmentation)

**Downstream**:
- Story 29.5 (Action Item Integration)
- Story 29.7 (Testing & Validation)

**External**:
- NetworkX (add to requirements.txt)

---

## Notes

- **CRITICAL**: C7 fix (cycle detection) prevents system hangs
- **CRITICAL**: C1 fix (limits) prevents infinite adjustment loops
- NetworkX chosen for robust graph algorithms (battle-tested)
- Story complexity increased from 8 to 12 points due to C7 fix
- Fallback to original workflows on any validation failure
- This is the most complex story in Epic 29

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md` (Component 3: WorkflowSelector)
- Critical Fixes: `CRITICAL_FIXES.md` (C1, C7)
- Epic 29: `epics/epic-29-self-learning-feedback-loop.md`
