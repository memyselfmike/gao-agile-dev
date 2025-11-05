# Story 13.4: Context Reference Resolver (@context:)

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 3
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement @context: reference resolver for injecting cached context into prompts. This enables agents to access frequently used context (epic definitions, architecture, coding standards) without repeatedly loading documents.

---

## Business Value

This story improves performance and consistency:

- **Performance**: Cached context loads in <1ms vs 50-100ms for document reads
- **Consistency**: Same context used across workflow steps
- **Convenience**: Simple API for common context needs
- **Tracking**: Audit trail of what context was used where

---

## Acceptance Criteria

### Context Loading
- [ ] `@context:key` loads from ContextCache
- [ ] Fallback to DocumentLifecycleManager if not cached
- [ ] Common context keys predefined: epic_definition, architecture, coding_standards, acceptance_criteria
- [ ] Custom context keys supported
- [ ] Missing context handled gracefully (warning + empty string)

### Cache Integration
- [ ] Integrates with ContextCache from Epic 16
- [ ] Lazy loading if not in cache
- [ ] Cache invalidation on document updates
- [ ] TTL respected (default: 5 minutes)

### Context Tracking
- [ ] Track which context was used in each prompt resolution
- [ ] Log context access for audit trail
- [ ] Record context version (document hash) at time of use
- [ ] Query: "What context was used for this workflow execution?"

### Performance
- [ ] Cache hit resolves in <1ms
- [ ] Cache miss (fallback to document load) resolves in <100ms
- [ ] Context tracking overhead <5ms

---

## Technical Notes

### Implementation

```python
# gao_dev/core/meta_prompts/resolvers/context_resolver.py

from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.lifecycle.document_lifecycle_manager import DocumentLifecycleManager

class ContextResolver(ReferenceResolver):
    """Resolver for @context: references."""

    # Predefined context keys with their document mappings
    CONTEXT_MAPPINGS = {
        'epic_definition': lambda ctx: f"docs/features/{ctx['feature']}/epics.md#epic-{ctx['epic']}",
        'architecture': lambda ctx: f"docs/features/{ctx['feature']}/ARCHITECTURE.md",
        'prd': lambda ctx: f"docs/features/{ctx['feature']}/PRD.md",
        'coding_standards': lambda ctx: "docs/CODING_STANDARDS.md",
        'acceptance_criteria': lambda ctx: f"docs/stories/epic-{ctx['epic']}/story-{ctx['story']}.md#acceptance-criteria",
        'story_definition': lambda ctx: f"docs/stories/epic-{ctx['epic']}/story-{ctx['story']}.md",
    }

    def __init__(
        self,
        context_cache: ContextCache,
        doc_manager: DocumentLifecycleManager,
        context_tracker: ContextUsageTracker
    ):
        self.cache = context_cache
        self.doc_manager = doc_manager
        self.tracker = context_tracker

    def can_resolve(self, reference_type: str) -> bool:
        return reference_type == "context"

    def resolve(self, reference: str, context: dict) -> str:
        """
        Resolve @context: reference.

        Examples:
            @context:epic_definition - Load epic definition
            @context:architecture - Load architecture doc
            @context:custom_key - Load custom context key
        """
        # Check cache first
        cached = self.cache.get(reference)
        if cached:
            logger.debug(f"Context cache hit: {reference}")
            self._track_usage(reference, cached, context, cache_hit=True)
            return cached

        # Cache miss - load from document
        logger.debug(f"Context cache miss: {reference}")
        content = self._load_context(reference, context)

        # Cache the result
        if content:
            self.cache.set(reference, content)

        self._track_usage(reference, content, context, cache_hit=False)
        return content

    def _load_context(self, key: str, context: dict) -> str:
        """Load context from document."""
        # Check if predefined context key
        if key in self.CONTEXT_MAPPINGS:
            doc_path_func = self.CONTEXT_MAPPINGS[key]
            try:
                doc_path = doc_path_func(context)
            except KeyError as e:
                logger.warning(f"Missing context variable for {key}: {e}")
                return ""

            # Load document
            doc = self.doc_manager.get_document_by_path(doc_path)
            if not doc:
                logger.warning(f"Document not found for context key {key}: {doc_path}")
                return ""

            return self._read_file(doc_path)

        # Custom context key - try to load from context dict
        elif key in context:
            return str(context[key])

        else:
            logger.warning(f"Unknown context key: {key}")
            return ""

    def _track_usage(
        self,
        context_key: str,
        content: str,
        context: dict,
        cache_hit: bool
    ) -> None:
        """Track context usage for audit trail."""
        self.tracker.record_usage(
            context_key=context_key,
            workflow_id=context.get('workflow_id'),
            epic=context.get('epic'),
            story=context.get('story'),
            content_hash=self._hash_content(content),
            cache_hit=cache_hit
        )

    def _hash_content(self, content: str) -> str:
        """Hash content for version tracking."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()[:16]
```

### Context Usage Tracker

```python
# gao_dev/core/context/context_usage_tracker.py

from datetime import datetime
from typing import Optional

class ContextUsageTracker:
    """Track context usage for audit trail."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def record_usage(
        self,
        context_key: str,
        workflow_id: Optional[str],
        epic: Optional[int],
        story: Optional[str],
        content_hash: str,
        cache_hit: bool
    ) -> None:
        """Record context usage in database."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO context_usage (
                    context_key, workflow_id, epic, story,
                    content_hash, cache_hit, accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                context_key, workflow_id, epic, story,
                content_hash, cache_hit, datetime.now().isoformat()
            ))

    def get_usage_history(self, workflow_id: str) -> List[Dict]:
        """Get context usage history for workflow."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM context_usage
                WHERE workflow_id = ?
                ORDER BY accessed_at DESC
            """, (workflow_id,))
            return [dict(row) for row in cursor.fetchall()]
```

### Context Reference Examples

```yaml
# Epic definition auto-injected
user_prompt: |
  Create stories for the following epic:

  @context:epic_definition

  Follow the architecture guidelines:
  @context:architecture

# Acceptance criteria for validation
user_prompt: |
  Validate the implementation against acceptance criteria:

  @context:acceptance_criteria

# Coding standards
user_prompt: |
  Ensure code follows our standards:

  @context:coding_standards
```

**Files to Create:**
- `gao_dev/core/meta_prompts/resolvers/context_resolver.py`
- `gao_dev/core/context/context_usage_tracker.py`
- `tests/core/meta_prompts/resolvers/test_context_resolver.py`
- `tests/core/context/test_context_usage_tracker.py`

**Dependencies:**
- Story 13.1 (Reference Resolver Framework)
- Epic 16, Story 16.1 (ContextCache)
- Epic 12, Story 12.4 (DocumentLifecycleManager)

---

## Testing Requirements

### Unit Tests

**Context Resolution:**
- [ ] Test predefined context keys (epic_definition, architecture, etc.)
- [ ] Test custom context keys from context dict
- [ ] Test cache hit returns cached value
- [ ] Test cache miss loads from document
- [ ] Test missing context key handled gracefully
- [ ] Test missing document handled gracefully

**Context Tracking:**
- [ ] Test usage recorded in tracker
- [ ] Test workflow_id, epic, story tracked
- [ ] Test content hash recorded
- [ ] Test cache hit/miss flag tracked
- [ ] Test usage history query

**Cache Integration:**
- [ ] Test cache TTL respected
- [ ] Test cache invalidation on document update
- [ ] Test cache eviction (LRU)

### Integration Tests
- [ ] Test with real ContextCache
- [ ] Test with real DocumentLifecycleManager
- [ ] Test end-to-end in prompt template
- [ ] Test context tracking in database

### Performance Tests
- [ ] Cache hit resolves in <1ms
- [ ] Cache miss resolves in <100ms
- [ ] Context tracking overhead <5ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Predefined context keys documented
- [ ] Custom context key usage documented
- [ ] Context tracking and audit trail documented
- [ ] Performance characteristics documented
- [ ] Examples for common use cases

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Cache integration working
- [ ] Context tracking verified
- [ ] Integrated with ReferenceResolverRegistry
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.4 - Context Reference Resolver

  - Implement ContextResolver for @context: references
  - Define predefined context keys (epic_definition, architecture, etc.)
  - Integrate with ContextCache for performance
  - Add ContextUsageTracker for audit trail
  - Track context version (hash) at time of use
  - Add comprehensive tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
