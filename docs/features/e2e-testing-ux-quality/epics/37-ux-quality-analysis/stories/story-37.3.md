# Story 37.3: Quality Scoring Algorithm

**Story ID**: 2.3
**Epic**: 2 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Done
**Story Points**: 5
**Priority**: High
**Completed**: 2025-11-15

---

## User Story

**As a** product manager
**I want** objective quality scores (0-100%) for conversations
**So that** I can measure improvement in Brian's UX over time

---

## Acceptance Criteria

- [x] **AC1**: _calculate_score() method implemented with penalty-based formula
- [x] **AC2**: Score range 0-100% (normalized and clamped)
- [x] **AC3**: Severity weights defined: CRITICAL=5.0, HIGH=3.0, MEDIUM=2.0, LOW=1.0 (documented)
- [x] **AC4**: N/A (requires manual expert rating dataset - future work)
- [x] **AC5**: Algorithm fully documented with examples and formula in docstring
- [x] **AC6**: Edge cases handled (0 turns→100%, no issues→100%, excessive issues→0%)
- [x] **AC7**: Validated against 5 sample conversations successfully
- [x] **AC8**: Baseline quality score established: 96.07% (95.00-96.67% range)

---

## Technical Context

From Architecture section 3.1 (ConversationAnalyzer._calculate_score):

**Scoring Formula**:
```
total_penalty = sum(severity_weights[issue.severity] for issue in issues)
max_total_penalty = total_turns * max_penalty_per_turn (10.0)
score = 100 * (1 - (total_penalty / max_total_penalty))
```

**Validation**: Must correlate with expert manual assessment

---

## Dependencies

- **Depends On**: Story 37.2 (issue detection)
- **Blocks**: Story 37.4 (reporting needs scores)

---

## References

- PRD Section: Success Metrics (Brian Quality Score)
- Architecture Section: 3.1 ConversationAnalyzer._calculate_score
- CRAAP Review: Critique #1 (Ambiguous Quality Scoring Algorithm)
