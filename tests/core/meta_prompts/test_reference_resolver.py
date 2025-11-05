"""
Tests for ReferenceResolverRegistry and ReferenceResolver.
"""

import pytest
from datetime import timedelta
from gao_dev.core.meta_prompts import (
    ReferenceResolver,
    ReferenceResolverRegistry,
    InvalidReferenceError,
    ResolverNotFoundError,
    CircularReferenceError,
    MaxDepthExceededError,
)


class MockResolver(ReferenceResolver):
    """Mock resolver for testing."""

    def __init__(self, resolver_type: str = "mock"):
        self._type = resolver_type

    def resolve(self, reference: str, context: dict) -> str:
        """Return mock content."""
        return f"resolved:{reference}"

    def can_resolve(self, reference_type: str) -> bool:
        """Check if can resolve type."""
        return reference_type == self._type

    def get_type(self) -> str:
        """Get resolver type."""
        return self._type


class NestedResolver(ReferenceResolver):
    """Resolver that returns content with nested references."""

    def resolve(self, reference: str, context: dict) -> str:
        """Return content with nested reference."""
        if reference == "nested1":
            return "Content with @nested:nested2"
        elif reference == "nested2":
            return "Final content"
        return f"resolved:{reference}"

    def can_resolve(self, reference_type: str) -> bool:
        """Check if can resolve type."""
        return reference_type == "nested"

    def get_type(self) -> str:
        """Get resolver type."""
        return "nested"


class CircularResolver(ReferenceResolver):
    """Resolver that creates circular references."""

    def resolve(self, reference: str, context: dict) -> str:
        """Return content with circular reference."""
        if reference == "circular1":
            return "Content with @circular:circular2"
        elif reference == "circular2":
            return "Content with @circular:circular1"
        return f"resolved:{reference}"

    def can_resolve(self, reference_type: str) -> bool:
        """Check if can resolve type."""
        return reference_type == "circular"

    def get_type(self) -> str:
        """Get resolver type."""
        return "circular"


class TestReferenceResolver:
    """Test ReferenceResolver base class."""

    def test_get_type(self):
        """Test get_type returns correct type."""
        resolver = MockResolver("test")
        assert resolver.get_type() == "test"


class TestReferenceResolverRegistry:
    """Test ReferenceResolverRegistry functionality."""

    def test_register_resolver(self):
        """Test registering a resolver."""
        registry = ReferenceResolverRegistry()
        resolver = MockResolver()

        registry.register(resolver)

        assert "mock" in registry.list_resolvers()

    def test_parse_reference_valid(self):
        """Test parsing valid references."""
        registry = ReferenceResolverRegistry()

        ref_type, ref_value = registry.parse_reference("@doc:path/to/file.md")
        assert ref_type == "doc"
        assert ref_value == "path/to/file.md"

        ref_type, ref_value = registry.parse_reference(
            "@checklist:testing/unit-test-standards"
        )
        assert ref_type == "checklist"
        assert ref_value == "testing/unit-test-standards"

    def test_parse_reference_invalid_no_at(self):
        """Test parsing reference without @."""
        registry = ReferenceResolverRegistry()

        with pytest.raises(InvalidReferenceError) as exc_info:
            registry.parse_reference("doc:path/to/file.md")

        assert "must start with '@'" in str(exc_info.value)

    def test_parse_reference_invalid_syntax(self):
        """Test parsing reference with invalid syntax."""
        registry = ReferenceResolverRegistry()

        with pytest.raises(InvalidReferenceError) as exc_info:
            registry.parse_reference("@invalid")

        assert "Invalid reference syntax" in str(exc_info.value)

    def test_resolve_dispatches_to_correct_resolver(self):
        """Test resolve dispatches to correct resolver."""
        registry = ReferenceResolverRegistry()
        resolver1 = MockResolver("type1")
        resolver2 = MockResolver("type2")

        registry.register(resolver1)
        registry.register(resolver2)

        result = registry.resolve("@type1:value1", {})
        assert result == "resolved:value1"

        result = registry.resolve("@type2:value2", {})
        assert result == "resolved:value2"

    def test_resolve_resolver_not_found(self):
        """Test resolve raises error if resolver not found."""
        registry = ReferenceResolverRegistry()

        with pytest.raises(ResolverNotFoundError) as exc_info:
            registry.resolve("@unknown:value", {})

        assert "No resolver found for type: unknown" in str(exc_info.value)

    def test_nested_reference_resolution(self):
        """Test nested reference resolution."""
        registry = ReferenceResolverRegistry()
        registry.register(NestedResolver())
        registry.register(MockResolver())

        result = registry.resolve("@nested:nested1", {})

        # Should resolve nested reference
        assert "Final content" in result
        assert "@nested:nested2" not in result

    def test_circular_reference_detection(self):
        """Test circular reference detection."""
        registry = ReferenceResolverRegistry()
        registry.register(CircularResolver())

        with pytest.raises(CircularReferenceError) as exc_info:
            registry.resolve("@circular:circular1", {})

        assert "Circular reference detected" in str(exc_info.value)

    def test_max_depth_enforcement(self):
        """Test maximum nesting depth enforcement."""
        registry = ReferenceResolverRegistry(max_depth=2)

        class DeepResolver(ReferenceResolver):
            """Resolver with deep nesting."""

            def resolve(self, reference: str, context: dict) -> str:
                level = int(reference.replace("level", ""))
                if level < 10:
                    return f"@deep:level{level + 1}"
                return "done"

            def can_resolve(self, reference_type: str) -> bool:
                return reference_type == "deep"

            def get_type(self) -> str:
                return "deep"

        registry.register(DeepResolver())

        with pytest.raises(MaxDepthExceededError) as exc_info:
            registry.resolve("@deep:level1", {})

        assert "Maximum nesting depth" in str(exc_info.value)

    def test_cache_stores_resolved_references(self):
        """Test cache stores resolved references."""
        registry = ReferenceResolverRegistry()

        class CountingResolver(ReferenceResolver):
            """Resolver that counts calls."""

            def __init__(self):
                self.call_count = 0

            def resolve(self, reference: str, context: dict) -> str:
                self.call_count += 1
                return f"resolved:{reference}"

            def can_resolve(self, reference_type: str) -> bool:
                return reference_type == "count"

            def get_type(self) -> str:
                return "count"

        resolver = CountingResolver()
        registry.register(resolver)

        # First call should hit resolver
        result1 = registry.resolve("@count:test", {})
        assert resolver.call_count == 1

        # Second call should hit cache
        result2 = registry.resolve("@count:test", {})
        assert resolver.call_count == 1  # Still 1
        assert result1 == result2

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        registry = ReferenceResolverRegistry()
        resolver = MockResolver()
        registry.register(resolver)

        # Cache a reference
        registry.resolve("@mock:test", {})

        # Invalidate cache
        registry.invalidate_cache("@mock:test")

        # Stats should show miss on next access
        stats = registry.get_cache_stats()
        initial_misses = stats["misses"]

        registry.resolve("@mock:test", {})
        stats = registry.get_cache_stats()

        assert stats["misses"] > initial_misses

    def test_find_references(self):
        """Test finding references in content."""
        registry = ReferenceResolverRegistry()

        content = """
        This is content with @doc:file1.md and @checklist:test.
        Also has @query:some.query here.
        """

        references = registry._find_references(content)

        assert "@doc:file1.md" in references
        assert "@checklist:test." in references
        assert "@query:some.query" in references

    def test_cache_statistics(self):
        """Test cache statistics."""
        registry = ReferenceResolverRegistry()
        resolver = MockResolver()
        registry.register(resolver)

        # Generate some hits and misses
        registry.resolve("@mock:test1", {})  # Miss
        registry.resolve("@mock:test1", {})  # Hit
        registry.resolve("@mock:test2", {})  # Miss
        registry.resolve("@mock:test1", {})  # Hit

        stats = registry.get_cache_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 0.5

    def test_list_resolvers(self):
        """Test listing registered resolvers."""
        registry = ReferenceResolverRegistry()

        resolver1 = MockResolver("type1")
        resolver2 = MockResolver("type2")

        registry.register(resolver1)
        registry.register(resolver2)

        resolvers = registry.list_resolvers()

        assert "type1" in resolvers
        assert "type2" in resolvers
        assert len(resolvers) == 2
