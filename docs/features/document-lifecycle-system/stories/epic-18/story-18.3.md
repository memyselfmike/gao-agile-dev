# Story 18.3: Document Lifecycle Integration

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 8
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Register all detected artifacts with DocumentLifecycleManager to enable proper document tracking, governance, and lifecycle management. This story takes the artifacts detected in Story 18.2 and automatically registers them with comprehensive metadata including document type, author, workflow context, and variables. The system infers document types from workflow names and file paths, determines authors from workflow agents, and handles registration failures gracefully to ensure workflow reliability.

---

## Business Value

This story completes the artifact tracking system:

- **Automatic Tracking**: All workflow artifacts automatically tracked in `.gao-dev/documents.db`
- **Document Governance**: All documents have owners, creation dates, and metadata
- **Lifecycle Management**: Documents enter proper lifecycle (draft → active → obsolete)
- **Audit Trail**: Complete record of what workflows created what documents
- **Search & Discovery**: Registered documents searchable via DocumentLifecycleManager
- **Relationship Tracking**: Link artifacts to epics, stories, and workflows
- **Compliance Ready**: Full metadata for regulatory compliance
- **Quality Gates**: Can validate expected artifacts were created
- **Context Integration**: Artifact metadata includes resolved workflow variables
- **Observability**: Comprehensive logging of all document registrations

---

## Acceptance Criteria

### Artifact Registration
- [ ] All detected artifacts registered with DocumentLifecycleManager
- [ ] `doc_lifecycle.register_document()` called for each artifact
- [ ] Registration includes path, doc_type, author, metadata
- [ ] Metadata includes workflow name, epic, story, phase
- [ ] Metadata includes resolved variables from workflow
- [ ] Metadata includes `created_by_workflow: true` flag
- [ ] Registration timestamp captured

### Document Type Inference
- [ ] Document types inferred correctly from workflow name (primary)
- [ ] Document types inferred correctly from file path (fallback)
- [ ] PRD workflow → "product-requirements" type
- [ ] Architecture workflow → "architecture" type
- [ ] Tech-spec workflow → "technical-specification" type
- [ ] Epic workflow → "epic" type
- [ ] Story workflow → "story" type
- [ ] Test workflow → "test-plan" type
- [ ] Default type "document" for unknown patterns

### Author Determination
- [ ] Author inferred from workflow agent
- [ ] John (PRD) → author: "john"
- [ ] Winston (Architecture) → author: "winston"
- [ ] Bob (Stories) → author: "bob"
- [ ] Amelia (Implementation) → author: "amelia"
- [ ] Murat (Testing) → author: "murat"
- [ ] Sally (UX) → author: "sally"
- [ ] Mary (Research) → author: "mary"

### Error Handling
- [ ] Registration failures logged as warnings (not errors)
- [ ] Registration failures don't break workflow execution
- [ ] Partial registration allowed (some artifacts succeed, some fail)
- [ ] Error messages include artifact path and error reason
- [ ] Continue processing remaining artifacts after failure

### Logging & Observability
- [ ] Logs show `artifact_registered` for each successful registration
- [ ] Logs include artifact path, doc_type, doc_id, author
- [ ] Logs show `artifact_registration_failed` for failures
- [ ] Logs include error context for debugging

### Testing
- [ ] Unit tests verify document type inference for all workflow types
- [ ] Unit tests verify author determination from agent names
- [ ] Unit tests verify metadata construction
- [ ] Integration test: PRD registered as "product-requirements"
- [ ] Integration test: Story registered as "story" with epic/story numbers
- [ ] Integration test: Artifacts appear in `.gao-dev/documents.db`
- [ ] Integration test: Query registered documents via DocumentLifecycleManager

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/orchestrator/orchestrator.py`

**Add artifact registration methods:**

```python
def _register_artifacts(
    self,
    artifacts: List[Path],
    workflow_info: "WorkflowInfo",
    epic: int,
    story: int,
    variables: Dict[str, Any]
) -> None:
    """
    Register detected artifacts with DocumentLifecycleManager.

    Args:
        artifacts: List of artifact paths (absolute)
        workflow_info: Workflow metadata
        epic: Epic number
        story: Story number
        variables: Resolved workflow variables
    """
    if not self.doc_lifecycle:
        logger.warning(
            "document_lifecycle_not_available",
            message="Cannot register artifacts - DocumentLifecycleManager not initialized"
        )
        return

    for artifact_path in artifacts:
        try:
            # Determine document type from workflow and path
            doc_type = self._infer_document_type(artifact_path, workflow_info)

            # Determine author from workflow agent
            author = self._get_agent_for_workflow(workflow_info).lower()

            # Build comprehensive metadata
            metadata = {
                "workflow": workflow_info.name,
                "epic": epic,
                "story": story,
                "phase": workflow_info.phase,
                "created_by_workflow": True,
                "variables": variables,
                "workflow_phase": workflow_info.phase,
            }

            # Register with document lifecycle manager
            doc = self.doc_lifecycle.register_document(
                path=artifact_path,
                doc_type=doc_type,
                author=author,
                metadata=metadata
            )

            logger.info(
                "artifact_registered",
                artifact=str(artifact_path.relative_to(self.project_root)),
                doc_type=doc_type,
                doc_id=doc.id,
                author=author,
                workflow=workflow_info.name
            )

        except Exception as e:
            # Log warning but don't fail workflow
            logger.warning(
                "artifact_registration_failed",
                artifact=str(artifact_path.relative_to(self.project_root)),
                error=str(e),
                error_type=type(e).__name__,
                message="Continuing without registration"
            )

def _infer_document_type(self, path: Path, workflow_info: "WorkflowInfo") -> str:
    """
    Infer document type from path and workflow.

    Args:
        path: Artifact path
        workflow_info: Workflow metadata

    Returns:
        Document type string (product-requirements, architecture, story, etc.)
    """
    path_lower = str(path).lower()
    workflow_lower = workflow_info.name.lower()

    # Strategy 1: Map based on workflow name (most reliable)
    workflow_type_mapping = {
        "prd": "product-requirements",
        "architecture": "architecture",
        "tech-spec": "technical-specification",
        "epic": "epic",
        "story": "story",
        "create-story": "story",
        "dev-story": "story",
        "test": "test-plan",
        "ux": "design",
        "design": "design",
    }

    for pattern, doc_type in workflow_type_mapping.items():
        if pattern in workflow_lower:
            return doc_type

    # Strategy 2: Map based on file path (fallback)
    path_type_mapping = {
        "prd": "product-requirements",
        "architecture": "architecture",
        "spec": "technical-specification",
        "epic": "epic",
        "story": "story",
        "test": "test-plan",
        "ux": "design",
        "design": "design",
    }

    for pattern, doc_type in path_type_mapping.items():
        if pattern in path_lower:
            return doc_type

    # Default: generic document type
    return "document"
```

**Integrate into `_execute_agent_task_static()`:**

```python
async def _execute_agent_task_static(
    self, workflow_info: "WorkflowInfo", epic: int = 1, story: int = 1
) -> AsyncGenerator[str, None]:
    # ... existing code from Story 18.1 and 18.2 ...

    # STEP 8: Detect artifacts created during execution
    artifacts = self._detect_artifacts(files_before, files_after)

    # STEP 9: Register artifacts with DocumentLifecycleManager
    if artifacts:
        self._register_artifacts(
            artifacts=artifacts,
            workflow_info=workflow_info,
            epic=epic,
            story=story,
            variables=variables  # From Story 18.1
        )
```

---

## Dependencies

- Story 18.2 (Artifact Detection System) - Must detect artifacts first
- Epic 12 (Document Lifecycle) - DocumentLifecycleManager must exist
- Story 18.1 (WorkflowExecutor Integration) - Need resolved variables

---

## Tasks

### Implementation Tasks
- [ ] Implement _register_artifacts() method
- [ ] Iterate through all detected artifacts
- [ ] Call _infer_document_type() for each artifact
- [ ] Call _get_agent_for_workflow() to determine author
- [ ] Build metadata dict with workflow context
- [ ] Call doc_lifecycle.register_document() for each artifact
- [ ] Handle registration exceptions gracefully
- [ ] Log successful registrations
- [ ] Log failed registrations
- [ ] Implement _infer_document_type() method
- [ ] Create workflow name to doc type mapping
- [ ] Create file path to doc type mapping
- [ ] Implement fallback logic (workflow → path → default)
- [ ] Integrate into _execute_agent_task_static()
- [ ] Call _register_artifacts() after artifact detection

### Testing Tasks
- [ ] Write unit test: test_infer_document_type_from_workflow_prd()
- [ ] Write unit test: test_infer_document_type_from_workflow_architecture()
- [ ] Write unit test: test_infer_document_type_from_workflow_story()
- [ ] Write unit test: test_infer_document_type_from_path()
- [ ] Write unit test: test_infer_document_type_default()
- [ ] Write unit test: test_get_agent_for_workflow_john()
- [ ] Write unit test: test_get_agent_for_workflow_winston()
- [ ] Write unit test: test_register_artifacts_success()
- [ ] Write unit test: test_register_artifacts_handles_failures()
- [ ] Write unit test: test_metadata_construction()
- [ ] Write integration test: test_prd_registered_correctly()
- [ ] Write integration test: test_story_registered_with_metadata()
- [ ] Write integration test: test_artifacts_in_database()
- [ ] Write integration test: test_query_registered_documents()

### Documentation Tasks
- [ ] Document document type inference rules
- [ ] Document author determination logic
- [ ] Document metadata structure
- [ ] Add examples of registered artifacts
- [ ] Document error handling behavior

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Code review approved
- [ ] Logging implemented and verified
- [ ] Documentation updated
- [ ] Manual testing with multiple workflows successful
- [ ] Artifacts verified in .gao-dev/documents.db
- [ ] Merged to feature branch

---

## Files to Modify

1. `gao_dev/orchestrator/orchestrator.py` (~80 LOC additions)
   - Add _register_artifacts() method (~40 LOC)
   - Add _infer_document_type() method (~30 LOC)
   - Integrate into _execute_agent_task_static() (~10 LOC)

2. `tests/orchestrator/test_document_registration.py` (new file, ~150 LOC)
   - Unit tests for document type inference
   - Unit tests for author determination
   - Unit tests for metadata construction
   - Unit tests for error handling

3. `tests/integration/test_artifact_lifecycle_integration.py` (new file, ~100 LOC)
   - Integration tests with DocumentLifecycleManager
   - Integration tests with database queries
   - Integration tests with multiple artifact types

---

## Success Metrics

- **Registration Rate**: >95% of artifacts successfully registered
- **Type Accuracy**: >90% of document types inferred correctly
- **Reliability**: 0 workflow failures due to registration errors
- **Performance**: Registration overhead <50ms per artifact
- **Test Coverage**: >80% coverage for registration code
- **Error Handling**: 100% of exceptions caught and logged

---

## Risk Assessment

**Risks:**
- DocumentLifecycleManager not available or not initialized
- Database write failures (disk full, permissions)
- Incorrect document type inference
- Performance impact from multiple registrations

**Mitigations:**
- Check if doc_lifecycle exists before registration
- Handle all exceptions gracefully (log, don't crash)
- Extensive unit tests for type inference rules
- Batch registration if performance becomes issue
- Add metrics to monitor registration performance

---

## Notes

- Registration must never fail the workflow - always catch exceptions
- Document type inference uses workflow name first (more reliable than path)
- Metadata should be comprehensive for audit trail
- Consider adding "registered_by: orchestrator" to metadata
- Future enhancement: batch registration for better performance
- Consider adding retry logic for transient database errors
- Document lifecycle state should be "draft" initially

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
