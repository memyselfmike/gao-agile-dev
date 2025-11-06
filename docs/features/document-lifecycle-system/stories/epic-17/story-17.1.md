# Story 17.1: Document Loading Integration (Epic 12)

**Epic:** 17 - Context System Integration
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement actual document loading via DocumentLifecycleManager to make WorkflowContext functional. This replaces the stub `_load_document()` implementation with real integration to Epic 12's document management system, enabling WorkflowContext to access actual PRDs, architecture documents, epic definitions, and story content. The integration provides seamless document access for agents while maintaining proper caching and error handling for missing documents.

---

## Business Value

This story makes the Context Persistence Layer functional by connecting it to real documents:

- **Agent Enablement**: Agents can now access actual project documents through context API
- **Workflow Intelligence**: Workflows have access to complete project context (PRDs, architecture)
- **Autonomous Execution**: Agents can work independently with full context awareness
- **Error Resilience**: Graceful handling of missing documents prevents workflow failures
- **Cache Integration**: Loaded documents cached for performance (uses ContextCache)
- **Type Safety**: Proper mapping between doc types ensures correct document retrieval
- **Developer Experience**: Clear API for document access without file path management
- **Foundation for Agents**: Essential prerequisite for agent prompt integration (Story 17.4)
- **Testing Capability**: Integration tests can validate full document lifecycle
- **Production Ready**: Real document loading makes context system production-ready

---

## Acceptance Criteria

### Document Loading
- [ ] `context.get_prd()` returns actual PRD content from DocumentLifecycleManager
- [ ] `context.get_architecture()` returns actual architecture document
- [ ] `context.get_epic_definition()` returns actual epic definition
- [ ] `context.get_story_definition()` returns actual story content
- [ ] Document content returned as string (markdown format)
- [ ] Document metadata preserved (path, version, timestamps)

### Error Handling
- [ ] Document not found returns None gracefully (no exceptions)
- [ ] Missing document logged as warning (not error)
- [ ] Invalid document type handled gracefully
- [ ] File system errors caught and logged
- [ ] Error handling does not break workflow execution

### Integration
- [ ] Integration tests with DocumentLifecycleManager pass
- [ ] AgentContextAPI default loader uses DocumentLifecycleManager
- [ ] Examples in documentation work with real documents
- [ ] Document cache integration working (ContextCache)
- [ ] Multiple document loads use cache (second load faster)

### Type Mapping
- [ ] `doc_type="prd"` maps to DocumentType.PRD
- [ ] `doc_type="architecture"` maps to DocumentType.ARCHITECTURE
- [ ] `doc_type="epic"` maps to DocumentType.EPIC
- [ ] `doc_type="story"` maps to DocumentType.STORY
- [ ] Feature/epic/story identifiers used to construct paths

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/core/context/workflow_context.py`

Replace stub `_load_document()` method:

```python
from gao_dev.core.document_lifecycle_manager import DocumentLifecycleManager, DocumentType
from pathlib import Path

class WorkflowContext:
    def __init__(self, ...):
        # ... existing code ...
        self._doc_manager = DocumentLifecycleManager(project_root=Path.cwd())
        self._document_cache: Dict[str, str] = {}  # Cache loaded documents

    def _load_document(self, doc_type: str) -> Optional[str]:
        """
        Load document from DocumentLifecycleManager.

        Args:
            doc_type: Type of document (prd, architecture, epic, story)

        Returns:
            Document content as string, or None if not found
        """
        # Check cache first
        cache_key = f"{self.feature_name}:{doc_type}"
        if cache_key in self._document_cache:
            return self._document_cache[cache_key]

        try:
            # Map doc_type to DocumentType enum
            doc_type_map = {
                "prd": DocumentType.PRD,
                "architecture": DocumentType.ARCHITECTURE,
                "epic": DocumentType.EPIC,
                "story": DocumentType.STORY,
            }

            document_type = doc_type_map.get(doc_type)
            if not document_type:
                logger.warning(f"Unknown document type: {doc_type}")
                return None

            # Construct document path based on type
            if doc_type == "prd":
                doc_path = self._doc_manager.get_document_path(
                    document_type,
                    feature=self.feature_name
                )
            elif doc_type == "architecture":
                doc_path = self._doc_manager.get_document_path(
                    document_type,
                    feature=self.feature_name
                )
            elif doc_type == "epic":
                doc_path = self._doc_manager.get_document_path(
                    document_type,
                    feature=self.feature_name,
                    epic=self.epic_number
                )
            elif doc_type == "story":
                doc_path = self._doc_manager.get_document_path(
                    document_type,
                    feature=self.feature_name,
                    epic=self.epic_number,
                    story=self.story_number
                )

            # Load document content
            if doc_path and doc_path.exists():
                content = doc_path.read_text(encoding="utf-8")
                # Cache the content
                self._document_cache[cache_key] = content
                return content
            else:
                logger.warning(f"Document not found: {doc_type} at {doc_path}")
                return None

        except Exception as e:
            logger.warning(f"Error loading document {doc_type}: {e}")
            return None
```

**Files to Modify:**
- `gao_dev/core/context/workflow_context.py` - Replace `_load_document()` stub
- `gao_dev/core/context/agent_context_api.py` - Use DocumentLifecycleManager as default loader

**Files to Create:**
- `tests/core/context/test_document_loading_integration.py` - Integration tests

**Dependencies:**
- Epic 12 (DocumentLifecycleManager)
- Story 16.2 (WorkflowContext with stub loader)

---

## Testing Requirements

### Integration Tests

**Document Loading:**
- [ ] Test load PRD for existing feature
- [ ] Test load architecture for existing feature
- [ ] Test load epic definition for existing epic
- [ ] Test load story definition for existing story
- [ ] Test load returns None for non-existent document
- [ ] Test load returns None for invalid feature name

**Caching:**
- [ ] Test second load of same document uses cache
- [ ] Test cache hit faster than first load
- [ ] Test different documents cached separately
- [ ] Test cache persists across multiple calls

**Error Handling:**
- [ ] Test missing document returns None (no exception)
- [ ] Test invalid document type returns None
- [ ] Test file system error returns None
- [ ] Test malformed document path returns None

**AgentContextAPI Integration:**
- [ ] Test AgentContextAPI uses DocumentLifecycleManager
- [ ] Test agent can access PRD via context
- [ ] Test agent can access architecture via context
- [ ] Test agent can access epic definition via context

### Unit Tests
- [ ] Test document type mapping (prd -> DocumentType.PRD)
- [ ] Test cache key generation
- [ ] Test document path construction
- [ ] Test error logging for missing documents

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Update WorkflowContext docstring with document loading details
- [ ] Add examples of document access to README
- [ ] Document error handling behavior
- [ ] Add integration guide for DocumentLifecycleManager
- [ ] Update AgentContextAPI documentation with real examples
- [ ] Add troubleshooting guide for document loading issues
- [ ] Document caching behavior and performance

---

## Implementation Details

### Development Approach

**Phase 1: Core Integration**
1. Study DocumentLifecycleManager API
2. Replace stub `_load_document()` method
3. Implement document type mapping
4. Add basic error handling

**Phase 2: Caching**
1. Add document cache dict
2. Implement cache key generation
3. Add cache lookup before loading
4. Store loaded documents in cache

**Phase 3: Testing**
1. Write integration tests with real documents
2. Test error cases (missing documents)
3. Verify caching works correctly
4. Test AgentContextAPI integration

### Quality Gates
- [ ] All integration tests pass
- [ ] Document loading works with real documents
- [ ] Error handling tested (missing documents)
- [ ] Caching verified (second load faster)
- [ ] Documentation updated with examples
- [ ] No regression in existing context tests

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] `_load_document()` implemented with real DocumentLifecycleManager
- [ ] Document type mapping working (prd, architecture, epic, story)
- [ ] Error handling for missing documents (returns None)
- [ ] Document caching implemented and tested
- [ ] Integration tests pass (>80% coverage)
- [ ] AgentContextAPI uses DocumentLifecycleManager by default
- [ ] Documentation updated with real examples
- [ ] Code reviewed and approved
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.1 - Document Loading Integration

  - Integrate DocumentLifecycleManager for real document loading
  - Replace stub _load_document() with actual implementation
  - Map doc_type to DocumentType enum (prd, architecture, epic, story)
  - Add document caching for performance
  - Implement graceful error handling for missing documents
  - Add integration tests with DocumentLifecycleManager
  - Update AgentContextAPI to use DocumentLifecycleManager
  - Add documentation with real document examples

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
