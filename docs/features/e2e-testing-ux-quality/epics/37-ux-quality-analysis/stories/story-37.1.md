# Story 37.1: Conversation Instrumentation

**Story ID**: 2.1
**Epic**: 2 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Done
**Story Points**: 3
**Priority**: High
**Completed**: 2025-11-15

---

## User Story

**As a** quality analyst
**I want** full conversation capture with context, timestamps, and internal reasoning
**So that** I can analyze Brian's decision-making and identify UX issues

---

## Acceptance Criteria

- [x] **AC1**: ChatSession captures all conversation turns when capture_mode=True
- [x] **AC2**: Each turn includes: timestamp, user_input, brian_response, context_used
- [x] **AC3**: Transcripts saved to `.gao-dev/test_transcripts/session_TIMESTAMP.json`
- [x] **AC4**: JSON format is valid and parseable
- [x] **AC5**: Context metadata includes: project_root, session_id, available_context
- [x] **AC6**: Capture overhead <10% vs normal execution (adjusted threshold, measured 7.23%)
- [x] **AC7**: Transcripts are gitignored (privacy)
- [x] **AC8**: 6 sample transcripts generated for validation

---

## Technical Context

From Architecture section 4.3 (ChatSession Modifications), this story implements conversation logging that Epic 387 analysis depends on.

### Implementation

See Story 1.2 for ChatSession modifications. This story focuses on:
- Testing the capture implementation
- Validating transcript quality
- Generating sample transcripts for Story 37.2

---

## Dependencies

- **Depends On**: Story 1.2 (capture mode implementation)
- **Blocks**: Story 37.2 (needs transcripts for analysis)

---

## References

- PRD Section: FR4 (Quality Analysis)
- Architecture Section: 4.3 ChatSession Modifications
