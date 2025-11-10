# Story 31.6: Brian-Orchestrated Mary → John Handoff with Document Lifecycle

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.6
**Priority**: P0 (Critical - UX Completeness & Document Lifecycle Integration)
**Estimate**: 3 story points
**Duration**: 0.5-1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1, 31.2, 31.3, Epic 12-17 (Document Lifecycle), Epic 27 (Git-Integrated State Manager)

---

## Story Description

Implement Brian-orchestrated handoff from Mary's requirements analysis to John's PRD creation with full DocumentLifecycle integration. Mary's outputs must be properly registered as documents, tracked with state, linked to subsequent PRDs, and added to context that John receives.

**Current Problem**: Mary finishes analysis but:
- ❌ User has to manually invoke John
- ❌ Mary's documents not registered in DocumentLifecycle
- ❌ No document relationships tracked
- ❌ Context not enriched for John
- ❌ Direct agent-to-agent handoff (wrong!)

**Correct Architecture**: Brian orchestrates everything:
- ✅ Brian receives Mary's output
- ✅ Brian registers Mary's document in DocumentLifecycle
- ✅ Brian offers PRD creation to user
- ✅ Brian enriches context with Mary's documents
- ✅ Brian coordinates with John (not direct Mary→John)
- ✅ John receives enriched context (not just file path)
- ✅ PRD and Mary's doc are linked in documents.db

This completes the conversational loop with proper document tracking: Vague Idea → Mary (Requirements + Document Registration) → Brian (Orchestration) → John (PRD with Context) → Winston (Architecture) → etc.

---

## User Story

**As a** user who completed Mary's requirements analysis
**I want** Brian to orchestrate PRD creation with proper document tracking
**So that** all artifacts are tracked, related, and provide context for subsequent work

---

## Acceptance Criteria

### Core Orchestration
- [ ] Brian orchestrates handoff (no direct Mary→John communication)
- [ ] Brian offers: "Mary's completed requirements. Want me to create a PRD with John?"
- [ ] User can accept or decline offer
- [ ] If accepted, Brian coordinates with John (passing enriched context)
- [ ] If declined, Brian exits gracefully

### DocumentLifecycle Integration (NEW!)
- [ ] Mary's outputs registered in `documents.db` via DocumentLifecycle
- [ ] Document metadata: type, phase, author, state, file_path
- [ ] Document state: `draft` (during Mary session) → `active` (on completion)
- [ ] Mary's document linked to PRD via `related_documents` field
- [ ] Git commit includes Mary's document (atomic file+DB+git)

### Context Enrichment (NEW!)
- [ ] Brian creates enriched context with Mary's document
- [ ] Context includes: document content, metadata, structured summaries
- [ ] John receives context (not raw file path)
- [ ] John's prompt references Mary's requirements from context
- [ ] Context resolution handled by ContextEnricher

### Integration Points
- [ ] Works with vision elicitation outputs
- [ ] Works with brainstorming outputs
- [ ] Works with requirements analysis outputs
- [ ] Works with domain-specific requirements

### Testing
- [ ] 10+ tests (orchestration + document lifecycle + context enrichment)
- [ ] Integration test: Mary vision → register document → enrich context → John PRD
- [ ] Integration test: Document relationship (vision linked to PRD)
- [ ] Integration test: User declines (graceful exit)

---

## Architecture Overview (Corrected)

```
User: "I want to build something for teams"
  ↓
BrianOrchestrator.assess_vagueness() → 0.85 (very vague)
  ↓
Brian delegates to Mary
  ↓
MaryOrchestrator.elicit_vision()
  ├─ Multi-turn conversation (~15-20 turns)
  ├─ Generate VisionSummary
  ├─ Save to: .gao-dev/mary/vision-documents/vision-{timestamp}.md
  └─ Register in DocumentLifecycle ← NEW!
      ├─ Document type: "vision"
      ├─ Phase: "analysis"
      ├─ Author: "Mary"
      ├─ State: "active"
      ├─ Metadata: {workflow, session_id, ...}
      └─ Git commit (atomic file+DB+git via GitIntegratedStateManager)
  ↓
Return VisionSummary + document_id to Brian
  ↓
BrianOrchestrator receives VisionSummary
  ├─ Verify document registered (if not, register it)
  ├─ Offer to user: "Mary's captured your vision. Want me to create a PRD with John?"
  │
  ├─ User says "Yes"
  │   ├─ Brian creates enriched context ← NEW!
  │   │     ├─ Load document from DocumentLifecycle
  │   │     ├─ Parse vision canvas into structured data
  │   │     └─ Create context dict
  │   │
  │   ├─ Brian coordinates with John ← Brian orchestrates!
  │   │     └─ john.create_prd(context=enriched_context)
  │   │
  │   ├─ John creates PRD
  │   │     ├─ Uses enriched context
  │   │     └─ PRD includes vision canvas as input
  │   │
  │   └─ Brian links documents ← NEW!
  │         ├─ Update PRD document: related_documents = [vision_doc_id]
  │         └─ Update vision document: related_documents = [prd_doc_id]
  │
  └─ User says "No"
      └─ Brian: "No problem! You can create a PRD later."
```

**Key Architectural Points**:
1. **Brian orchestrates** - No direct agent-to-agent communication
2. **DocumentLifecycle tracks everything** - All artifacts registered
3. **Context is enriched** - Structured data passed, not raw files
4. **Documents are linked** - Relationships tracked in documents.db
5. **Atomic commits** - File + DB + Git via GitIntegratedStateManager (Epic 27)

---

## Files to Create/Modify

### Modified Files

**MaryOrchestrator** (`gao_dev/orchestrator/mary_orchestrator.py`, ~50 LOC):
```python
# Add DocumentLifecycleService
# Register all outputs after completion
# Return document_id with file_path
```

**BrianOrchestrator** (`gao_dev/orchestrator/brian_orchestrator.py`, ~80 LOC):
```python
# Detect Mary completion
# Enrich context from Mary's document
# Offer PRD creation
# Coordinate with John (pass context)
# Link documents after PRD creation
```

**John's PRD Workflow** (`gao_dev/workflows/2-plan/prd/workflow.yaml`, ~15 LOC):
```yaml
# Add context variables for Mary's requirements
```

**John's PRD Prompt** (`gao_dev/prompts/tasks/create_prd.yaml`, ~30 LOC):
```yaml
# Reference Mary's context
# Structure PRD around requirements when provided
```

### New Files

**ContextEnricher** (`gao_dev/core/context_enricher.py`, ~100 LOC):
```python
# Load documents from DocumentLifecycle
# Parse content (vision, brainstorm, requirements)
# Create structured context dict
```

**Tests** (`tests/orchestrator/test_mary_john_handoff.py`, ~180 LOC):
```python
# Test orchestration
# Test document registration
# Test context enrichment
# Test document linking
# Integration tests
```

---

## Technical Design Summary

See full implementation details in the complete story file for:
- Data model changes (VisionSummary with document_id)
- Mary's document registration code
- Brian's orchestration logic
- ContextEnricher implementation
- John's context-aware prompt
- Complete testing strategy

---

## Definition of Done

- [ ] Brian orchestrates handoff (no direct agent-to-agent)
- [ ] Mary's documents registered in DocumentLifecycle
- [ ] Context enriched with Mary's structured requirements
- [ ] John receives context (not raw file path)
- [ ] Documents linked via `related_documents`
- [ ] Git commits include document registration (atomic)
- [ ] 10+ unit tests passing
- [ ] 3 integration tests passing
- [ ] Code reviewed and approved
- [ ] User guide updated with document lifecycle flow

---

**Status**: Todo
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Corrected: Brian orchestration + DocumentLifecycle integration)
**Critical**: Proper orchestration pattern + document tracking
