# Story 26.6: Ceremony Artifact Integration

**Epic**: Epic 26 - Multi-Agent Ceremonies
**Story ID**: 26.6
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Integrate ceremony artifacts with document lifecycle: register transcripts, link action items to source ceremony, link learnings to source ceremony.

---

## Acceptance Criteria

- [ ] All ceremony outputs registered as documents (DocumentLifecycleManager)
- [ ] Transcript files tracked
- [ ] Action items link to source ceremony (source_doc_id)
- [ ] Learnings link to source ceremony (source_doc_id)
- [ ] Metadata includes ceremony type, date, participants
- [ ] 8 integration tests

---

## Files to Modify

- `gao_dev/orchestrator/ceremony_orchestrator.py` (+~40 LOC)
- `tests/integration/test_ceremony_artifact_integration.py` (new, ~120 LOC)

---

## Definition of Done

- [ ] 8 tests passing
- [ ] Artifacts integrated
- [ ] Git commit: "feat(epic-26): integrate ceremony artifacts with document lifecycle"

---

**Created**: 2025-11-09
