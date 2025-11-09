# Epic 29: Self-Learning Feedback Loop

**Epic ID**: epic-29
**Feature**: Ceremony Integration & Self-Learning System
**Duration**: 4 weeks (51 story points) - REVISED from 2 weeks (38 points)
**Owner**: Amelia (Developer)
**Status**: Planning
**Dependencies**: Epic 28 (ceremony integration)

---

## Epic Goal

Enable GAO-Dev to learn from past work and improve workflow selection through a closed-loop feedback system where retrospective learnings influence future workflow decisions.

**Success Criteria**:
- [ ] >50% of learnings applied in subsequent projects
- [ ] >70% success rate for applied learnings
- [ ] Brian's context includes top 5 relevant learnings
- [ ] Workflows adjusted based on past quality/process issues
- [ ] Learning confidence correlates with actual outcomes
- [ ] 45+ tests passing

---

## Overview

**The Problem**: Learnings from retrospectives sit in database unused - no feedback loop

**The Solution**: Multi-phase learning system:
1. **Collection**: Extract learnings from retrospectives (existing - Epic 26)
2. **Scoring**: Calculate relevance based on context, recency, success rate
3. **Application**: Brian uses learnings to select/adjust workflows
4. **Feedback**: Track outcomes, update learning confidence

**Impact**: System improves with every project - true autonomous learning

---

## User Stories (7 stories, 51 points - REVISED from 38)

### Story 29.1: Learning Schema Enhancement
**Points**: 3
**Owner**: Amelia
**Status**: Pending

**Description**:
Enhance learning_index table schema to track application metrics and create learning_applications table for tracking outcomes.

**Acceptance Criteria**:
- [ ] Create Migration 006:
  ```sql
  ALTER TABLE learning_index ADD COLUMN application_count INTEGER DEFAULT 0;
  ALTER TABLE learning_index ADD COLUMN success_rate REAL DEFAULT 1.0;
  ALTER TABLE learning_index ADD COLUMN confidence_score REAL DEFAULT 0.5;

  CREATE TABLE learning_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_id INTEGER REFERENCES learning_index(id),
    epic_num INTEGER,
    story_num INTEGER,
    outcome TEXT CHECK(outcome IN ('success', 'failure', 'partial')),
    application_context TEXT,
    applied_at TEXT NOT NULL,
    metadata JSON
  );
  ```
- [ ] Add indexes for performance
- [ ] Migration script validates data integrity
- [ ] Update LearningIndexService to handle new fields
- [ ] 5 unit tests (migration, queries)

**Database Design**:
- `application_count`: Number of times learning applied
- `success_rate`: (successes + 0.5*partials) / count
- `confidence_score`: 0.5 + (0.4 * (1 - exp(-count/10))) - increases with applications
- `learning_applications`: Audit trail of each application

---

### Story 29.2: LearningApplicationService
**Points**: 12 (REVISED from 8 - Complex scoring algorithm + transaction safety)
**Owner**: Amelia
**Status**: Pending

**Description**:
Create LearningApplicationService to score learnings by relevance and track application outcomes.

**Acceptance Criteria**:
- [ ] Create `gao_dev/core/services/learning_application_service.py` (~400 LOC)
- [ ] Implement `ScoredLearning` dataclass
- [ ] Implement `LearningApplicationService` with methods:
  - `get_relevant_learnings(scale_level, project_type, context, limit=5)`
  - `record_application(learning_id, epic_num, outcome, context)`
  - `_calculate_relevance_score(learning, scale_level, project_type, context)`
  - `_calculate_decay(indexed_at)` - Recency decay
  - `_context_similarity(learning, context)` - Similarity scoring
  - `_calculate_updated_stats(learning_id)` - Update after application
- [ ] Relevance scoring formula:
  ```
  score = base_relevance
          * success_rate
          * confidence_score
          * decay_factor
          * context_similarity
  ```
- [ ] Decay formula:
  - 0-30 days: 1.0 (full strength)
  - 30-90 days: Linear decay to 0.8
  - 90-180 days: Linear decay to 0.6
  - 180+ days: 0.5 (minimum)
- [ ] Context similarity based on:
  - Scale level match (30% weight)
  - Project type match (20% weight)
  - Tag overlap (30% weight)
  - Category relevance (20% weight)
- [ ] 15 unit tests (scoring, decay, similarity, recording)

**Scoring Example**:
```python
learning = {
    'relevance_score': 0.8,  # Base
    'success_rate': 0.9,     # 90% past success
    'confidence_score': 0.7, # High confidence
    'indexed_at': '2025-10-01',  # 39 days old
    'category': 'quality',
    'tags': ['testing', 'api'],
    'metadata': {'scale_level': 2, 'project_type': 'feature'}
}

context = {
    'scale_level': ScaleLevel.LEVEL_2_SMALL_FEATURE,
    'project_type': 'feature',
    'tags': ['api', 'authentication']
}

# Calculation:
base = 0.8
success = 0.9
confidence = 0.7
decay = 0.95  # (1.0 - (39-30)/60*0.2) = 0.97
similarity = 0.65  # (scale:0.3 + type:0.2 + tags:0.15)

score = 0.8 * 0.9 * 0.7 * 0.97 * 0.65 = 0.317
# Above threshold (>0.3) → Include in results
```

---

### Story 29.3: Brian Context Augmentation
**Points**: 8
**Owner**: Amelia
**Status**: Pending

**Description**:
Enhance BrianOrchestrator to build enriched context with relevant learnings for workflow selection.

**Acceptance Criteria**:
- [ ] Modify `brian_orchestrator.py` with learning integration
- [ ] Add method `select_workflows_with_learning(user_prompt, project_root, context)`
- [ ] Add method `_build_context_with_learnings(prompt, learnings)`
- [ ] Context template includes:
  ```
  # Workflow Selection Analysis

  ## User Request
  {user_prompt}

  ## Project Analysis
  {project_analysis}

  ## Scale Level: {scale_level}
  {scale_description}

  ## RELEVANT LEARNINGS FROM PAST WORK

  ### Learning 1: {topic}
  **Category**: {category}
  **Source**: {source_type} (Epic {epic_num})
  **Success Rate**: {success_rate}% ({application_count} applications)
  **Learning**: {learning}
  **Context**: {context}
  **Recommendation**: {recommendation}

  [... top 5 learnings ...]

  ## Recommended Workflow Sequence
  {workflows}
  ```
- [ ] Integration with LearningApplicationService
- [ ] Generate learning recommendations based on category
- [ ] 10 unit tests (context building, template rendering)

**Integration Flow**:
```
User Prompt
    ↓
Brian.select_workflows_with_learning()
    ↓
1. Analyze complexity → Scale level
2. Get relevant learnings (top 5)
3. Build enriched context
4. Select base workflows
5. Apply learning adjustments (Story 29.4)
6. Return augmented sequence
```

---

### Story 29.4: Workflow Adjustment Logic
**Points**: 12 (REVISED from 8 - Complex adjustment rules + dependency validation)
**Owner**: Amelia
**Status**: Pending

**Description**:
Implement logic to adjust workflows based on learnings - add extra testing for quality learnings, more ceremonies for process learnings, etc.

**Acceptance Criteria**:
- [ ] Create `gao_dev/methodologies/adaptive_agile/workflow_adjuster.py` (~250 LOC)
- [ ] Implement `WorkflowAdjuster` class with method:
  - `apply_adjustments(workflows, learnings, scale_level)`
- [ ] Adjustment rules by learning category:
  - **Quality learnings** → Insert extra testing workflows
  - **Process learnings** → Increase ceremony frequency
  - **Architectural learnings** → Add architecture review step
  - **Performance learnings** → Add performance testing
- [ ] Integrate with BrianOrchestrator
- [ ] Adjustments preserve workflow dependencies
- [ ] Record which learnings influenced adjustments (metadata)
- [ ] 12 unit tests (each category, combinations)

**Adjustment Examples**:

**Quality Learning**:
```
Learning: "API tests missed edge cases in auth flow"
→ Adjustment: Insert "extra-integration-testing" after "test-feature"
```

**Process Learning**:
```
Learning: "Mid-epic standup caught blocker early"
→ Adjustment: Change standup interval from 3 to 2 stories
```

**Architectural Learning**:
```
Learning: "Missed database schema review led to migration issues"
→ Adjustment: Insert "architecture-review" after "create-architecture"
```

---

### Story 29.5: Action Item Integration
**Points**: 5
**Owner**: Amelia
**Status**: Pending

**Description**:
Integrate action items from ceremonies into next sprint planning and auto-convert high-priority items to stories.

**Acceptance Criteria**:
- [ ] Create `gao_dev/core/services/action_item_integration_service.py` (~200 LOC)
- [ ] Implement methods:
  - `get_pending_action_items_for_epic(epic_num)`
  - `inject_action_items_into_planning(epic_num, planning_context)`
  - `auto_create_stories_from_action_items(epic_num, high_priority_only=True)`
- [ ] Planning ceremony context includes pending action items
- [ ] High-priority action items auto-converted to stories
- [ ] Story creation includes reference to source action item
- [ ] Action items marked as "completed" when story completes
- [ ] Integration with CeremonyOrchestrator (planning ceremony)
- [ ] 8 unit tests

**Flow**:
```
Retrospective → Action Items Created
    ↓
Next Planning Ceremony
    ↓
inject_action_items_into_planning()
    ↓
Planning Context Includes Action Items
    ↓
High-Priority Items → auto_create_stories_from_action_items()
    ↓
New Stories Created
    ↓
Story Completion → Mark Action Item Complete
```

**Auto-Story Criteria**:
- Priority: HIGH
- Category: "process_improvement" or "quality_improvement"
- Not already a story
- Clear, actionable title

---

### Story 29.6: Learning Decay & Confidence
**Points**: 3
**Owner**: Amelia
**Status**: Pending

**Description**:
Implement recency decay, confidence score updates, and logic to supersede obsolete learnings.

**Acceptance Criteria**:
- [ ] Decay algorithm in LearningApplicationService (already in 29.2, validate)
- [ ] Confidence update formula:
  ```python
  confidence = 0.5 + (0.4 * (1 - exp(-application_count / 10)))
  if success_rate < 0.5:
      confidence *= success_rate * 2  # Reduce if poor success
  ```
- [ ] Add `superseded_by` field to learning_index table
- [ ] Add method `supersede_learning(learning_id, new_learning_id, reason)`
- [ ] Superseded learnings excluded from `get_relevant_learnings()`
- [ ] Manual CLI command to supersede: `gao-dev learning supersede <old-id> <new-id>`
- [ ] 5 unit tests

**Supersession Example**:
```
Old Learning (ID: 42):
"Use JWT tokens for authentication"

New Learning (ID: 58):
"Use OAuth 2.0 with JWT - better security and scalability"

Action: learning.supersede_learning(42, 58, "Upgraded to OAuth 2.0")
Result: Learning 42 excluded from future queries
```

---

### Story 29.7: Testing & Validation
**Points**: 8 (REVISED from 3 - Comprehensive test suite + E2E scenarios + benchmarks)
**Owner**: Amelia
**Status**: Pending

**Description**:
Comprehensive testing for entire self-learning loop including unit, integration, and E2E tests.

**Acceptance Criteria**:
- [ ] Unit tests: 45 tests across all services
  - LearningApplicationService: 15 tests
  - Brian augmentation: 10 tests
  - WorkflowAdjuster: 12 tests
  - Action item integration: 8 tests
- [ ] Integration tests: 10 tests
  - Full learning cycle (retro → scoring → application → feedback)
  - Workflow adjustment in context
  - Action items to stories flow
- [ ] E2E tests: 2 scenarios
  - **Scenario 1**: Two-project learning loop
    - Project 1: Quality issue → Retro → Learning indexed
    - Project 2: Brian applies learning → Extra testing added → Success
    - Result: Confidence increased
  - **Scenario 2**: Process improvement loop
    - Project 1: Blocker caught by standup → Learning
    - Project 2: Standup frequency increased → Blocker avoided
    - Result: Success rate high
- [ ] Performance benchmarks:
  - Learning relevance scoring: <50ms for 50 candidates
  - Context augmentation: <100ms
  - Workflow adjustment: <50ms
- [ ] All tests passing
- [ ] Coverage >80% for new code

---

## Epic Deliverables

### Code (1,250+ LOC)
1. `gao_dev/core/services/learning_application_service.py` - Learning scoring (~400 LOC)
2. `gao_dev/orchestrator/brian_orchestrator.py` - Enhanced (~150 LOC added)
3. `gao_dev/methodologies/adaptive_agile/workflow_adjuster.py` - Adjustments (~250 LOC)
4. `gao_dev/core/services/action_item_integration_service.py` - Action items (~200 LOC)
5. Database migration script (~100 LOC)
6. Utilities and helpers (~150 LOC)

### Tests (900+ LOC)
- Unit tests: 45 tests
- Integration tests: 10 tests
- E2E tests: 2 scenarios

### Documentation
- Epic document (this file)
- 7 story files
- API documentation for new services
- Migration guide

---

## Dependencies

**Required**:
- ✅ Epic 28: Ceremony integration (must complete first)
- ✅ Epic 26: CeremonyOrchestrator
- ✅ Epic 24: LearningIndexService, ActionItemService
- ✅ Epic 25: FastContextLoader

**Blocks**:
- No dependent epics (this is final epic of feature)

---

## Technical Risks

**Risk 1: Learning Relevance Scoring Inaccurate**
- Impact: High (bad workflow decisions)
- Mitigation: Simple initial algorithm, iterate based on feedback, manual review option

**Risk 2: Too Many Action Items**
- Impact: Medium (noise, overwhelm)
- Mitigation: Priority filtering, auto-complete low-priority after 30 days, consolidation

**Risk 3: Confidence Algorithm Unstable**
- Impact: Medium (misleading scores)
- Mitigation: Conservative formula, plateau at ~20 applications, success rate dampening

**Risk 4: Performance Degradation**
- Impact: Low (FastContextLoader optimized)
- Mitigation: Caching, limit to top 5, async loading

---

## Self-Learning Loop Architecture

```
┌──────────────────────────────────────────────────────────┐
│  PHASE 1: COLLECTION (During Retrospective)             │
└────────┬─────────────────────────────────────────────────┘
         │
    Retrospective → Learnings Indexed
         │
         │ (confidence: 0.5, application_count: 0)
         │
┌────────▼─────────────────────────────────────────────────┐
│  PHASE 2: APPLICATION (New Project Starts)              │
└────────┬─────────────────────────────────────────────────┘
         │
    Brian.select_workflows_with_learning()
         │
         ├─→ LearningApplicationService.get_relevant_learnings()
         │   (scores by relevance, returns top 5)
         │
         ├─→ Build enriched context (learnings + recommendations)
         │
         ├─→ Select base workflows
         │
         └─→ WorkflowAdjuster.apply_adjustments(workflows, learnings)
                 │
                 └─→ Quality learnings → Extra testing
                     Process learnings → More ceremonies
                     Architectural learnings → Review step
         │
         │
┌────────▼─────────────────────────────────────────────────┐
│  PHASE 3: FEEDBACK (After Epic Completion)              │
└────────┬─────────────────────────────────────────────────┘
         │
    Epic Completes → Evaluate Outcome
         │
         ├─→ Tests passed? Quality gates met?
         ├─→ Did learnings help?
         │
         └─→ LearningApplicationService.record_application()
                 │
                 ├─→ application_count++
                 ├─→ Recalculate success_rate
                 └─→ Update confidence_score
         │
         │ (Learning becomes stronger/weaker)
         │
         └──→ LOOP CONTINUES for next project
```

---

## Testing Strategy

### Unit Tests (45 tests)
- LearningApplicationService: 15 tests
  - Relevance scoring: 5 tests
  - Decay calculation: 3 tests
  - Similarity scoring: 4 tests
  - Application recording: 3 tests
- Brian augmentation: 10 tests
  - Context building: 5 tests
  - Learning recommendations: 5 tests
- WorkflowAdjuster: 12 tests
  - Quality adjustments: 4 tests
  - Process adjustments: 4 tests
  - Architectural adjustments: 4 tests
- Action item integration: 8 tests
  - Pending items: 2 tests
  - Planning injection: 3 tests
  - Auto-story creation: 3 tests

### Integration Tests (10 tests)
- Full learning cycle: 3 tests
- Workflow adjustment in workflow: 3 tests
- Action items → stories flow: 2 tests
- Confidence updates: 2 tests

### E2E Tests (2 scenarios)
- Two-project quality learning loop
- Two-project process improvement loop

---

## Acceptance Criteria (Epic-Level)

Epic 29 is **COMPLETE** when:

1. **Self-Learning Implemented**:
   - [ ] All 7 stories completed and tested
   - [ ] Learning scoring algorithm works
   - [ ] Brian uses learnings for workflow selection
   - [ ] Workflows adjusted based on learnings
   - [ ] 57+ tests passing (45 unit + 10 integration + 2 E2E)

2. **Validation**:
   - [ ] E2E test: Two-project learning loop succeeds
   - [ ] Learnings applied in >50% of applicable cases
   - [ ] Success rate >70% for applied learnings
   - [ ] No regression in existing functionality

3. **Performance**:
   - [ ] Learning scoring: <50ms
   - [ ] Context augmentation: <100ms
   - [ ] Workflow adjustment: <50ms

4. **Documentation**:
   - [ ] All story files created
   - [ ] API documentation complete
   - [ ] Migration guide written

---

## Success Metrics (Post-Deployment)

**Quantitative**:
- Learning application rate: % of learnings applied in subsequent projects
- Learning success rate: % of applied learnings that led to successful outcomes
- Confidence accuracy: Correlation between confidence score and actual success
- Workflow improvement: Reduction in quality gate failures over time

**Qualitative**:
- User feedback on workflow recommendations
- Learning relevance perceived quality
- Action item actionability
- System autonomy perceived improvement

---

## Next Steps

After Epic 29 completion → **Feature Complete**
- Full ceremony integration + self-learning operational
- System can run autonomously and improve over time
- Ready for production use and real-world validation

---

**Status**: Ready for Story Breakdown and Implementation
**Start Date**: TBD (after Epic 28 completion)
**Target Completion**: TBD + 2 weeks
