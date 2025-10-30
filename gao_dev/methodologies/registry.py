"""Methodology registry for managing development methodologies.

Singleton registry that manages methodology instances, providing registration,
lookup, and default methodology management.

Story 5.3: MethodologyRegistry implementation.
"""

import threading
from typing import Dict, List, Optional

import structlog

from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.methodologies.exceptions import (
    InvalidMethodologyError,
    MethodologyAlreadyRegisteredError,
    MethodologyNotFoundError,
)

logger = structlog.get_logger(__name__)


class MethodologyRegistry:
    """Registry for development methodologies.

    Singleton registry that manages methodology instances with thread-safe
    registration, lookup, and default methodology management. Automatically
    registers AdaptiveAgileMethodology as the default methodology.

    Thread Safety:
        All registry operations are thread-safe using locks to prevent
        race conditions during concurrent access.

    Singleton Pattern:
        Only one registry instance exists per process. Use get_instance()
        to access the registry instead of creating instances directly.

    Example:
        ```python
        # Get registry instance
        registry = MethodologyRegistry.get_instance()

        # Register custom methodology
        registry.register_methodology(MyMethodology())

        # Get methodology by name
        adaptive_agile = registry.get_methodology("adaptive-agile")

        # List all registered methodologies
        methodologies = registry.list_methodologies()

        # Check if methodology exists
        if registry.has_methodology("custom-agile"):
            methodology = registry.get_methodology("custom-agile")

        # Get/set default methodology
        default = registry.get_default()
        registry.set_default("my-methodology")
        ```

    Attributes:
        _methodologies: Dictionary mapping methodology names to instances
        _default_name: Name of the default methodology
        _registry_lock: Thread lock for registry operations
    """

    _instance: Optional["MethodologyRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Private constructor. Use get_instance() instead.

        Initializes the registry and auto-registers default methodologies.
        """
        self._methodologies: Dict[str, IMethodology] = {}
        self._default_name: str = "adaptive-agile"
        self._registry_lock = threading.Lock()
        self._auto_register_defaults()

    @classmethod
    def get_instance(cls) -> "MethodologyRegistry":
        """Get singleton registry instance.

        Returns the single registry instance, creating it if it doesn't exist.
        Thread-safe using double-checked locking pattern.

        Returns:
            MethodologyRegistry: The singleton registry instance

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            assert registry is MethodologyRegistry.get_instance()  # Same instance
            ```
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing only).

        WARNING: This method is intended for testing purposes only.
        Do not use in production code.
        """
        with cls._lock:
            cls._instance = None

    def _auto_register_defaults(self) -> None:
        """Auto-register default methodologies.

        Registers AdaptiveAgileMethodology as the default methodology.
        Called automatically during registry initialization.
        """
        from gao_dev.methodologies.adaptive_agile import AdaptiveAgileMethodology

        self.register_methodology(AdaptiveAgileMethodology())
        logger.info("default_methodology_registered", name="adaptive-agile")

    def register_methodology(self, methodology: IMethodology) -> None:
        """Register a methodology in the registry.

        Args:
            methodology: Methodology instance implementing IMethodology

        Raises:
            MethodologyAlreadyRegisteredError: If methodology name already registered
            InvalidMethodologyError: If methodology doesn't implement IMethodology

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()

            class MyMethodology(IMethodology):
                @property
                def name(self) -> str:
                    return "my-methodology"
                # ... implement other methods

            registry.register_methodology(MyMethodology())
            ```
        """
        # Validate methodology implements IMethodology
        if not isinstance(methodology, IMethodology):
            raise InvalidMethodologyError(
                f"Methodology must implement IMethodology interface, "
                f"got {type(methodology).__name__}"
            )

        name = methodology.name.lower()

        with self._registry_lock:
            if name in self._methodologies:
                raise MethodologyAlreadyRegisteredError(
                    f"Methodology '{name}' already registered"
                )

            self._methodologies[name] = methodology
            logger.info(
                "methodology_registered",
                name=name,
                version=methodology.version,
                description=methodology.description,
            )

    def get_methodology(self, name: str) -> IMethodology:
        """Get methodology by name.

        Args:
            name: Methodology name (case-insensitive)

        Returns:
            IMethodology: The requested methodology instance

        Raises:
            MethodologyNotFoundError: If methodology not registered

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            methodology = registry.get_methodology("adaptive-agile")
            ```
        """
        name_lower = name.lower()

        with self._registry_lock:
            if name_lower not in self._methodologies:
                available = list(self._methodologies.keys())
                raise MethodologyNotFoundError(
                    f"Methodology '{name}' not registered. "
                    f"Available methodologies: {available}"
                )
            return self._methodologies[name_lower]

    def list_methodologies(self) -> List[str]:
        """List all registered methodology names.

        Returns:
            List[str]: Sorted list of methodology names

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            methodologies = registry.list_methodologies()
            print(methodologies)  # ['adaptive-agile', 'custom-methodology']
            ```
        """
        with self._registry_lock:
            return sorted(self._methodologies.keys())

    def has_methodology(self, name: str) -> bool:
        """Check if methodology is registered.

        Args:
            name: Methodology name (case-insensitive)

        Returns:
            bool: True if methodology registered, False otherwise

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            if registry.has_methodology("adaptive-agile"):
                methodology = registry.get_methodology("adaptive-agile")
            ```
        """
        with self._registry_lock:
            return name.lower() in self._methodologies

    def get_default(self) -> IMethodology:
        """Get default methodology.

        Returns the currently configured default methodology.
        Guaranteed to never raise (default methodology always registered).

        Returns:
            IMethodology: The default methodology instance

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            default = registry.get_default()
            print(default.name)  # 'adaptive-agile'
            ```
        """
        return self.get_methodology(self._default_name)

    def set_default(self, name: str) -> None:
        """Set default methodology.

        Args:
            name: Methodology name to set as default

        Raises:
            MethodologyNotFoundError: If methodology not registered

        Example:
            ```python
            registry = MethodologyRegistry.get_instance()
            registry.register_methodology(MyMethodology())
            registry.set_default("my-methodology")
            ```
        """
        # Validate methodology exists (raises if not found)
        self.get_methodology(name)

        with self._registry_lock:
            self._default_name = name.lower()
            logger.info("default_methodology_changed", name=name.lower())
