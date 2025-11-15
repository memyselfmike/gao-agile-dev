# Story 38.4: Fixture Conversion Tool

**Story ID**: 3.4
**Epic**: 3 - Interactive Testing Tools
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 2
**Priority**: Low (Nice to Have)

---

## User Story

**As a** developer
**I want** to convert real user conversation transcripts into regression test fixtures
**So that** I can prevent regressions by capturing actual user interactions

---

## Acceptance Criteria

- [ ] **AC1**: CLI command `gao-dev convert-transcript` implemented
- [ ] **AC2**: Command reads transcript from `.gao-dev/test_transcripts/`
- [ ] **AC3**: Command generates YAML fixture in correct format
- [ ] **AC4**: Fixture includes user_input, brian_response, expect_output patterns
- [ ] **AC5**: Output patterns auto-generated from Brian responses (keyword extraction)
- [ ] **AC6**: Tool validates generated fixture with FixtureLoader
- [ ] **AC7**: Documentation includes usage examples
- [ ] **AC8**: 3+ real transcripts converted as examples

---

## Technical Context

Converts conversation transcripts captured in Story 2.1 into regression test fixtures (Story 1.4 format).

**Workflow**:
1. Run `gao-dev start --capture-mode`
2. Have conversation with Brian
3. Run `gao-dev convert-transcript session_TIMESTAMP.json`
4. Review and edit generated fixture
5. Add to test suite

---

## Dependencies

- **Depends On**: Story 2.1 (transcripts), Story 1.4 (fixture format)
- **Blocks**: None (optional tooling)

---

## References

- PRD Section: User Stories - Story 12
- CRAAP Review: Alignment #3 (Scope Creep - move to Phase 5 or make optional)
