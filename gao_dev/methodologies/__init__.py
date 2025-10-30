"""Development methodologies for GAO-Dev.

This package contains methodology implementations that define how
GAO-Dev analyzes complexity, selects workflows, and recommends agents.

Available Methodologies:
    - AdaptiveAgileMethodology: Scale-adaptive methodology (5 levels)
    - SimpleMethodology: Minimal 3-level methodology (Story 5.5)

Example:
    ```python
    from gao_dev.methodologies.adaptive_agile import AdaptiveAgileMethodology
    from gao_dev.methodologies.simple import SimpleMethodology
    from gao_dev.methodologies.registry import MethodologyRegistry

    # Get registry and methodology
    registry = MethodologyRegistry.get_instance()
    methodology = registry.get_methodology("adaptive-agile")

    # Use methodology
    assessment = await methodology.assess_complexity("Build a todo app")
    sequence = methodology.build_workflow_sequence(assessment)

    # Or use SimpleMethodology
    simple = registry.get_methodology("simple")
    assessment = await simple.assess_complexity("Fix a bug")
    ```
"""

from .adaptive_agile import AdaptiveAgileMethodology, ScaleLevel
from .simple import SimpleMethodology
from .exceptions import (
    InvalidMethodologyError,
    MethodologyAlreadyRegisteredError,
    MethodologyError,
    MethodologyNotFoundError,
)
from .registry import MethodologyRegistry

__all__ = [
    # Methodologies
    "AdaptiveAgileMethodology",
    "SimpleMethodology",
    "ScaleLevel",
    # Registry
    "MethodologyRegistry",
    # Exceptions
    "MethodologyError",
    "MethodologyAlreadyRegisteredError",
    "MethodologyNotFoundError",
    "InvalidMethodologyError",
]
