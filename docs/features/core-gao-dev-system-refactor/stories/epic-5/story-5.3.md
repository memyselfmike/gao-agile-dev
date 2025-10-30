# Story 5.3: Implement Methodology Registry

**Epic**: Epic 5 - Methodology Abstraction
**Story Points**: 3
**Priority**: P2 (Medium)
**Status**: Ready

---

## User Story

**As a** core developer
**I want** a methodology registry that manages multiple methodologies
**So that** users can select and switch between methodologies (BMAD, Scrum, Kanban, custom)

---

## Description

Create `MethodologyRegistry` to register, discover, and retrieve methodologies. Enables GAO-Dev to support multiple methodologies simultaneously with runtime selection.

**Current State**: BMAD hardcoded everywhere, no registry system.

**Target State**: `MethodologyRegistry` in `gao_dev/methodologies/registry.py` managing methodology lifecycle.

---

## Acceptance Criteria

### MethodologyRegistry Implementation

- [ ] **Class created**: `gao_dev/methodologies/registry.py`
- [ ] **MethodologyRegistry class** with registration and lookup
- [ ] **Size**: < 200 lines
- [ ] **Thread-safe**: Concurrent access safe
- [ ] **Default methodology**: BMAD registered by default

### Core Methods

- [ ] **register_methodology(methodology: IMethodology) -> None**
  - Register methodology instance
  - Validate implements IMethodology
  - Prevent duplicate names
  - Raise MethodologyAlreadyRegisteredError if duplicate

- [ ] **get_methodology(name: str) -> IMethodology**
  - Retrieve methodology by name
  - Case-insensitive lookup
  - Raise MethodologyNotFoundError if not registered

- [ ] **list_methodologies() -> List[str]**
  - Return list of registered methodology names
  - Sorted alphabetically

- [ ] **has_methodology(name: str) -> bool**
  - Check if methodology registered
  - Case-insensitive check

- [ ] **get_default() -> IMethodology**
  - Return default methodology (BMAD)
  - Never raises (BMAD always registered)

- [ ] **set_default(name: str) -> None**
  - Set default methodology
  - Validate methodology exists

### Singleton Pattern

- [ ] **MethodologyRegistry is singleton**
  - Only one instance per process
  - Thread-safe instantiation
  - Global access via `MethodologyRegistry.get_instance()`

### Auto-Registration

- [ ] **Auto-register BMAD on first access**
  - BMAD registered automatically
  - Set as default
  - Other methodologies registered manually

### Exception Classes

- [ ] **MethodologyAlreadyRegisteredError** created
- [ ] **MethodologyNotFoundError** created
- [ ] **InvalidMethodologyError** created

### Testing

- [ ] Unit tests for MethodologyRegistry (85%+ coverage)
- [ ] Test registration and retrieval
- [ ] Test duplicate prevention
- [ ] Test default methodology
- [ ] Test thread safety
- [ ] All existing tests pass

---

## Technical Details

```python
import threading
from typing import Dict, List, Optional
import structlog
from gao_dev.core.interfaces.methodology import IMethodology

logger = structlog.get_logger(__name__)

class MethodologyRegistry:
    """Registry for development methodologies.

    Singleton registry that manages methodology instances.
    Provides registration, lookup, and default methodology management.

    Example:
        ```python
        registry = MethodologyRegistry.get_instance()

        # Register custom methodology
        registry.register_methodology(MyMethodology())

        # Get methodology
        bmad = registry.get_methodology("bmad")

        # List all
        methodologies = registry.list_methodologies()
        ```
    """

    _instance: Optional['MethodologyRegistry'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        self._methodologies: Dict[str, IMethodology] = {}
        self._default_name: str = "bmad"
        self._registry_lock = threading.Lock()
        self._auto_register_defaults()

    @classmethod
    def get_instance(cls) -> 'MethodologyRegistry':
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _auto_register_defaults(self) -> None:
        """Auto-register default methodologies."""
        from gao_dev.methodologies.bmad import BMADMethodology
        self.register_methodology(BMADMethodology())
        logger.info("default_methodology_registered", name="bmad")

    def register_methodology(self, methodology: IMethodology) -> None:
        """Register methodology."""
        name = methodology.name.lower()

        with self._registry_lock:
            if name in self._methodologies:
                raise MethodologyAlreadyRegisteredError(
                    f"Methodology '{name}' already registered"
                )

            if not isinstance(methodology, IMethodology):
                raise InvalidMethodologyError(
                    f"Methodology must implement IMethodology interface"
                )

            self._methodologies[name] = methodology
            logger.info(
                "methodology_registered",
                name=name,
                version=methodology.version
            )

    def get_methodology(self, name: str) -> IMethodology:
        """Get methodology by name."""
        name_lower = name.lower()

        with self._registry_lock:
            if name_lower not in self._methodologies:
                raise MethodologyNotFoundError(
                    f"Methodology '{name}' not registered. "
                    f"Available: {list(self._methodologies.keys())}"
                )
            return self._methodologies[name_lower]

    def list_methodologies(self) -> List[str]:
        """List registered methodologies."""
        with self._registry_lock:
            return sorted(self._methodologies.keys())

    def has_methodology(self, name: str) -> bool:
        """Check if methodology registered."""
        with self._registry_lock:
            return name.lower() in self._methodologies

    def get_default(self) -> IMethodology:
        """Get default methodology."""
        return self.get_methodology(self._default_name)

    def set_default(self, name: str) -> None:
        """Set default methodology."""
        # Validate exists
        self.get_methodology(name)

        with self._registry_lock:
            self._default_name = name.lower()
            logger.info("default_methodology_changed", name=name)
```

---

## Definition of Done

- [ ] MethodologyRegistry class implemented
- [ ] Singleton pattern working
- [ ] BMAD auto-registered
- [ ] All methods implemented
- [ ] Exception classes created
- [ ] 85%+ test coverage
- [ ] All existing tests pass
- [ ] Code review approved
- [ ] Committed to feature branch

---

## Files to Create

1. `gao_dev/methodologies/registry.py`
2. `gao_dev/methodologies/exceptions.py`
3. `tests/methodologies/test_registry.py`

---

## Related

- **Previous**: Story 5.2 - Extract BMAD Methodology
- **Next**: Story 5.4 - Decouple Core from BMAD
