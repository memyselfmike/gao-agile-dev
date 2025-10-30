"""Methodology-related exceptions.

Custom exception classes for methodology operations including registry
management, validation, and runtime errors.

Story 5.3: Exception classes for MethodologyRegistry.
"""


class MethodologyError(Exception):
    """Base exception for methodology-related errors.

    All methodology exceptions inherit from this class for easier
    exception handling and filtering.
    """

    pass


class MethodologyAlreadyRegisteredError(MethodologyError):
    """Raised when attempting to register a methodology with duplicate name.

    This error occurs when trying to register a methodology whose name
    already exists in the registry. Each methodology must have a unique name.

    Example:
        ```python
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(MyMethodology())
        registry.register_methodology(MyMethodology())  # Raises this error
        ```
    """

    pass


class MethodologyNotFoundError(MethodologyError):
    """Raised when requesting a methodology that isn't registered.

    This error occurs when attempting to retrieve a methodology by name
    that hasn't been registered yet.

    Example:
        ```python
        registry = MethodologyRegistry.get_instance()
        methodology = registry.get_methodology("unknown")  # Raises this error
        ```
    """

    pass


class InvalidMethodologyError(MethodologyError):
    """Raised when a methodology doesn't implement IMethodology interface.

    This error occurs when attempting to register an object that doesn't
    properly implement the IMethodology interface.

    Example:
        ```python
        registry = MethodologyRegistry.get_instance()

        class BadMethodology:
            pass

        registry.register_methodology(BadMethodology())  # Raises this error
        ```
    """

    pass
