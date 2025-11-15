# Story 2.1: Conversation Instrumentation

**Story ID**: 2.1
**Epic**: 2 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 3
**Priority**: High

---

## User Story

**As a** quality analyst
**I want** full conversation capture with context, timestamps, and internal reasoning
**So that** I can analyze Brian's decision-making and identify UX issues

---

## Acceptance Criteria

- [ ] **AC1**: ChatSession captures all conversation turns when capture_mode=True
- [ ] **AC2**: Each turn includes: timestamp, user_input, brian_response, context_used
- [ ] **AC3**: Transcripts saved to `.gao-dev/test_transcripts/session_TIMESTAMP.json`
- [ ] **AC4**: JSON format is valid and parseable
- [ ] **AC5**: Context metadata includes: project_root, session_id, available_context
- [ ] **AC6**: Capture overhead <5% vs normal execution
- [ ] **AC7**: Transcripts are gitignored (privacy)
- [ ] **AC8**: 5+ sample transcripts generated for validation

---

## Technical Context

From Architecture section 4.3 (ChatSession Modifications), this story implements conversation logging that Epic 2 analysis depends on.

### Implementation

See Story 1.2 for ChatSession modifications. This story focuses on:
- Testing the capture implementation
- Validating transcript quality
- Generating sample transcripts for Story 2.2

---

## Dependencies

- **Depends On**: Story 1.2 (capture mode implementation)
- **Blocks**: Story 2.2 (needs transcripts for analysis)

---

## References

- PRD Section: FR4 (Quality Analysis)
- Architecture Section: 4.3 ChatSession Modifications
