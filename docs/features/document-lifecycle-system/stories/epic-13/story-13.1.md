# Story 13.1: Reference Resolver Framework

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Create an extensible framework for resolving different reference types in prompts. This framework will serve as the foundation for all meta-prompt capabilities, enabling automatic context injection through @doc:, @checklist:, @query:, and @context: references.

---

## Business Value

This story provides the architectural foundation for automatic context injection:

- **Extensibility**: Plugin architecture allows adding new reference types
- **Performance**: Caching resolved references reduces repeated resolution overhead
- **Error Handling**: Graceful handling of missing/invalid references prevents workflow failures
- **Maintainability**: Clean separation between parsing and resolution logic
- **Future-proof**: Easy to add domain-specific reference types

---

## Acceptance Criteria

### Core Framework
- [ ] `ReferenceResolver` base class defined with abstract `resolve()` method
- [ ] `ReferenceResolverRegistry` manages all registered resolvers
- [ ] Plugin architecture for adding new resolvers (no code changes needed)
- [ ] `parse_reference()` extracts type and value from reference string
- [ ] `resolve_reference()` dispatches to correct resolver based on type
- [ ] Support for nested references (reference inside referenced file) up to 3 levels
- [ ] Cycle detection prevents infinite loops in nested references

### Error Handling
- [ ] Missing references handled gracefully (warning logged, empty string returned)
- [ ] Invalid reference syntax raises clear `InvalidReferenceError`
- [ ] Resolver not found raises `ResolverNotFoundError`
- [ ] Circular reference detection raises `CircularReferenceError`

### Caching
- [ ] Resolved references cached for performance
- [ ] Cache invalidation when source documents change
- [ ] Cache TTL configurable (default: 5 minutes)
- [ ] Cache statistics tracked (hits, misses, size)

### Testing
- [ ] Unit tests for framework (>80% coverage)
- [ ] Tests for all error conditions
- [ ] Tests for cache behavior
- [ ] Performance tests: Parse <1ms, resolve <50ms

---

## Technical Notes

### Architecture

```python
# gao_dev/core/meta_prompts/reference_resolver.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class ReferenceResolver(ABC):
    """Base class for reference resolvers."""

    @abstractmethod
    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve a reference to its content.

        Args:
            reference: The reference value (e.g., "path/to/file.md")
            context: Context dict with variables for resolution

        Returns:
            Resolved content as string

        Raises:
            ReferenceResolutionError: If resolution fails
        """
        pass

    @abstractmethod
    def can_resolve(self, reference_type: str) -> bool:
        """Check if this resolver can handle the reference type."""
        pass


class ReferenceResolverRegistry:
    """Registry of all reference resolvers."""

    def __init__(self):
        self._resolvers: Dict[str, ReferenceResolver] = {}
        self._cache: Dict[str, tuple[str, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)

    def register(self, resolver: ReferenceResolver):
        """Register a new resolver."""
        pass

    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve a reference using the appropriate resolver.

        Handles caching, error handling, and nested references.
        """
        pass

    def parse_reference(self, reference: str) -> tuple[str, str]:
        """
        Parse reference into (type, value).

        Examples:
            @doc:path/to/file.md -> ("doc", "path/to/file.md")
            @checklist:testing/unit-test-standards -> ("checklist", "testing/unit-test-standards")
        """
        pass
```

### Reference Syntax

All references follow the pattern: `@{type}:{value}`

Examples:
- `@doc:docs/PRD.md`
- `@checklist:testing/unit-test-standards`
- `@query:stories.where(epic=3, status='done')`
- `@context:epic_definition`
- `@config:current_epic` (existing from Epic 10)
- `@file:common/responsibilities/developer.md` (existing from Epic 10)

### Nested Reference Resolution

```python
# Example nested resolution:
# Template contains: @doc:templates/story-template.md
# story-template.md contains: @checklist:testing/unit-test-standards
# Result: Both references resolved recursively

def _resolve_nested(self, content: str, context: Dict, depth: int = 0) -> str:
    """Resolve nested references up to max depth."""
    if depth > 3:
        raise CircularReferenceError("Maximum nesting depth exceeded")

    # Find all references in content
    references = self._find_references(content)

    for ref in references:
        resolved = self.resolve(ref, context)
        content = content.replace(ref, resolved)

        # Recursively resolve any references in resolved content
        content = self._resolve_nested(content, context, depth + 1)

    return content
```

### Cache Implementation

```python
class ResolverCache:
    """LRU cache for resolved references."""

    def __init__(self, ttl: timedelta = timedelta(minutes=5), max_size: int = 100):
        self._cache: OrderedDict[str, tuple[str, datetime]] = OrderedDict()
        self._ttl = ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[str]:
        """Get cached value if valid."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                self._hits += 1
                # Move to end (LRU)
                self._cache.move_to_end(key)
                return value
            else:
                # Expired
                del self._cache[key]

        self._misses += 1
        return None

    def set(self, key: str, value: str):
        """Cache a value."""
        # Evict oldest if at max size
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = (value, datetime.now())
```

**Files to Create:**
- `gao_dev/core/meta_prompts/__init__.py`
- `gao_dev/core/meta_prompts/reference_resolver.py`
- `gao_dev/core/meta_prompts/resolver_registry.py`
- `gao_dev/core/meta_prompts/resolver_cache.py`
- `gao_dev/core/meta_prompts/exceptions.py`
- `tests/core/meta_prompts/test_reference_resolver.py`
- `tests/core/meta_prompts/test_resolver_cache.py`

**Dependencies:**
- Epic 12 (Story 12.4) - DocumentLifecycleManager for document loading

---

## Testing Requirements

### Unit Tests

**Framework Tests:**
- [ ] Test ReferenceResolverRegistry registration
- [ ] Test parse_reference() with various reference types
- [ ] Test resolve() dispatches to correct resolver
- [ ] Test nested reference resolution (1, 2, 3 levels)
- [ ] Test circular reference detection
- [ ] Test max depth enforcement

**Cache Tests:**
- [ ] Test cache hit returns cached value
- [ ] Test cache miss triggers resolution
- [ ] Test cache TTL expiration
- [ ] Test LRU eviction when max size reached
- [ ] Test cache statistics (hits, misses)
- [ ] Test cache invalidation

**Error Handling Tests:**
- [ ] Test missing reference returns empty string + warning
- [ ] Test invalid syntax raises InvalidReferenceError
- [ ] Test resolver not found raises ResolverNotFoundError
- [ ] Test circular reference raises CircularReferenceError

### Performance Tests
- [ ] Parse reference completes in <1ms
- [ ] Resolve cached reference completes in <1ms
- [ ] Resolve uncached reference completes in <50ms
- [ ] 100 nested resolutions complete in <1 second

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all classes and methods
- [ ] Architecture documentation explaining resolver pattern
- [ ] Examples of creating custom resolvers
- [ ] Reference syntax documentation
- [ ] Caching behavior documentation
- [ ] Error handling guide

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Performance benchmarks met
- [ ] Integration with PromptLoader verified
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.1 - Reference Resolver Framework

  - Create ReferenceResolver base class and registry
  - Implement plugin architecture for extensibility
  - Add caching with TTL and LRU eviction
  - Support nested references with cycle detection
  - Comprehensive error handling and logging
  - Add unit tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
