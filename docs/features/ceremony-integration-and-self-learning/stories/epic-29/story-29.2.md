# Story 29.2: LearningApplicationService

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 12 story points (revised from 8 - C2 fix complexity)
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Story 29.1 (schema must be migrated first)

---

## User Story

**As a** Brian (workflow selector)
**I want** relevant learnings with confidence scores based on stable scoring algorithm
**So that** I can select workflows informed by past experience without score instability

---

## Acceptance Criteria

### AC1: LearningApplicationService Class Created
- [ ] Create `gao_dev/core/services/learning_application_service.py` (~400 lines)
- [ ] Class with methods:
  - `get_relevant_learnings(scale_level, project_type, context, limit=5) -> List[ScoredLearning]`
  - `record_application(learning_id, epic_num, story_num, outcome, context)`
  - `_calculate_relevance_score(learning, scale_level, project_type, context) -> float`
  - `_calculate_decay(indexed_at) -> float`
  - `_context_similarity(learning, scale_level, project_type, context) -> float`
  - `_calculate_updated_stats(learning_id) -> Dict[str, float]`
- [ ] Dependencies: `LearningIndexService`, database connection
- [ ] Structured logging with structlog

### AC2: Additive Scoring Formula (C2 Fix - CRITICAL)
- [ ] Weighted additive formula (NOT multiplicative):
  ```python
  score = 0.30 * base_relevance +
          0.20 * success_rate +
          0.20 * confidence_score +
          0.15 * decay_factor +
          0.15 * context_similarity
  ```
- [ ] Prevents single low factor from zeroing entire score
- [ ] Each factor normalized to [0.0, 1.0]
- [ ] Final score clamped to [0.0, 1.0]
- [ ] Tested with edge cases (one factor zero, all factors zero)

### AC3: Smooth Decay Function (C2 Fix)
- [ ] Exponential decay: `decay = 0.5 + 0.5 * exp(-days / 180)`
- [ ] No cliffs or sudden drops
- [ ] Results: 0d=1.0, 30d=0.92, 90d=0.81, 180d=0.68, 365d=0.56
- [ ] Never drops below 0.5 (retains historical value)

### AC4: Improved Confidence Formula (C2 Fix)
- [ ] Square root growth: `base_confidence = min(0.95, 0.5 + 0.45 * sqrt(successes / total))`
- [ ] Adjust for low success rate: `if success_rate < 0.5: confidence *= (success_rate * 2)`
- [ ] Confidence never decreases on success
- [ ] Plateaus at 0.95

### AC5: Context Similarity with Asymmetric Handling (C11 Fix)
- [ ] Scale level match (25%): exact/adjacent/near scoring
- [ ] Project type match (20%): exact match or general
- [ ] Tag overlap (30%): Jaccard similarity
- [ ] Handle asymmetric tags: both have tags vs only one has tags
- [ ] Category relevance (15%): quality/architectural highest
- [ ] Temporal context (10%): same phase bonus

### AC6: Get Relevant Learnings Method
- [ ] Query candidates (category match, active, limit 50)
- [ ] Score each using `_calculate_relevance_score()`
- [ ] Filter by threshold (>0.2, lowered from 0.3)
- [ ] Sort by score descending
- [ ] Return top N as `List[ScoredLearning]`
- [ ] Performance: <50ms for 50 candidates (C5 fix)

### AC7: Record Application Method
- [ ] Insert into `learning_applications` table
- [ ] Calculate updated stats
- [ ] Update `learning_index`: application_count++, success_rate, confidence_score
- [ ] Thread-safe (database transactions)
- [ ] Performance: <100ms

### AC8: Unit Tests
- [ ] `tests/core/services/test_learning_application_service.py` (~300 lines)
- [ ] Test scoring formula stability (C2 fix critical)
- [ ] Test decay function (smooth curve)
- [ ] Test confidence formula (monotonic growth)
- [ ] Test context similarity (asymmetric tags)
- [ ] Test get_relevant_learnings (top 5, threshold, performance)
- [ ] Test record_application (updates stats correctly)
- [ ] Coverage >95%

---

## Technical Details

See ARCHITECTURE.md Component 2 for complete specifications.

**Key Files**:
- `gao_dev/core/services/learning_application_service.py` (~400 lines)
- `tests/core/services/test_learning_application_service.py` (~300 lines)

**Critical C2 Fix**: Additive formula is mandatory to prevent score instability.

---

## Testing Strategy

- Unit tests for all scoring components
- Integration tests with real learnings database
- Performance benchmarks (<50ms scoring, <100ms recording)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] LearningApplicationService created
- [ ] C2, C5, C11 fixes implemented and validated
- [ ] Unit tests passing (>95% coverage)
- [ ] Performance targets met
- [ ] No linting errors, type hints complete
- [ ] Code reviewed and approved
- [ ] Committed with clear message
- [ ] Story marked complete in sprint-status.yaml

---

## Dependencies

**Upstream**: Story 29.1 (schema), Epic 24 (LearningIndexService)
**Downstream**: Stories 29.3, 29.4, 29.6

---

## Notes

- **CRITICAL**: C2 fix (additive formula) prevents score instability
- Threshold lowered to 0.2 to catch edge cases
- Story complexity increased from 8 to 12 points
- This is the heart of the self-learning system

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `ARCHITECTURE.md` (Component 2)
- Critical Fixes: `CRITICAL_FIXES.md` (C2, C5, C11)
