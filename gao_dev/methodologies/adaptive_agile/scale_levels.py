"""Scale levels for Adaptive Agile Methodology.

Defines the 5 scale levels (0-4) and mappings to generic complexity levels.

Story 5.2: Extracted from brian_orchestrator.py
"""

from enum import IntEnum

from gao_dev.core.models.methodology import ComplexityLevel


class ScaleLevel(IntEnum):
    """Adaptive Agile scale levels (0-4).

    Scale-adaptive approach with 5 granular levels for different project sizes.

    Levels:
        LEVEL_0_CHORE: Minutes - Simple task, typo fix, config change
        LEVEL_1_BUG_FIX: Hours - Single file bug fix, quick change
        LEVEL_2_SMALL_FEATURE: Days - 3-8 stories, simple feature
        LEVEL_3_MEDIUM_FEATURE: Weeks - 12-20 stories, complex feature
        LEVEL_4_GREENFIELD: Months - 40+ stories, full application

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import ScaleLevel

        # Determine scale level
        if story_count <= 3:
            level = ScaleLevel.LEVEL_1_BUG_FIX
        elif story_count <= 8:
            level = ScaleLevel.LEVEL_2_SMALL_FEATURE
        ```
    """

    LEVEL_0_CHORE = 0
    LEVEL_1_BUG_FIX = 1
    LEVEL_2_SMALL_FEATURE = 2
    LEVEL_3_MEDIUM_FEATURE = 3
    LEVEL_4_GREENFIELD = 4


def map_scale_to_complexity(scale_level: ScaleLevel) -> ComplexityLevel:
    """Map Adaptive Agile scale level to generic complexity level.

    Converts methodology-specific scale levels to the generic ComplexityLevel
    enum used by the IMethodology interface.

    Args:
        scale_level: Adaptive Agile scale level (0-4)

    Returns:
        Generic ComplexityLevel enum value

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import (
            ScaleLevel,
            map_scale_to_complexity
        )

        scale = ScaleLevel.LEVEL_2_SMALL_FEATURE
        complexity = map_scale_to_complexity(scale)
        # Returns: ComplexityLevel.MEDIUM
        ```
    """
    mapping = {
        ScaleLevel.LEVEL_0_CHORE: ComplexityLevel.TRIVIAL,
        ScaleLevel.LEVEL_1_BUG_FIX: ComplexityLevel.SMALL,
        ScaleLevel.LEVEL_2_SMALL_FEATURE: ComplexityLevel.MEDIUM,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE: ComplexityLevel.LARGE,
        ScaleLevel.LEVEL_4_GREENFIELD: ComplexityLevel.XLARGE,
    }
    return mapping[scale_level]


def map_complexity_to_scale(complexity_level: ComplexityLevel) -> ScaleLevel:
    """Map generic complexity level to Adaptive Agile scale level.

    Reverse mapping from generic ComplexityLevel to scale levels.
    Useful when working with generic assessment results.

    Args:
        complexity_level: Generic ComplexityLevel

    Returns:
        Adaptive Agile ScaleLevel

    Example:
        ```python
        from gao_dev.core.models.methodology import ComplexityLevel
        from gao_dev.methodologies.adaptive_agile import map_complexity_to_scale

        complexity = ComplexityLevel.LARGE
        scale = map_complexity_to_scale(complexity)
        # Returns: ScaleLevel.LEVEL_3_MEDIUM_FEATURE
        ```
    """
    mapping = {
        ComplexityLevel.TRIVIAL: ScaleLevel.LEVEL_0_CHORE,
        ComplexityLevel.SMALL: ScaleLevel.LEVEL_1_BUG_FIX,
        ComplexityLevel.MEDIUM: ScaleLevel.LEVEL_2_SMALL_FEATURE,
        ComplexityLevel.LARGE: ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        ComplexityLevel.XLARGE: ScaleLevel.LEVEL_4_GREENFIELD,
    }
    return mapping[complexity_level]


def estimate_stories_from_scale(scale_level: ScaleLevel) -> int:
    """Estimate story count based on scale level.

    Returns typical story count for each scale level.

    Args:
        scale_level: Adaptive Agile scale level

    Returns:
        Estimated number of user stories
    """
    estimates = {
        ScaleLevel.LEVEL_0_CHORE: 0,
        ScaleLevel.LEVEL_1_BUG_FIX: 1,
        ScaleLevel.LEVEL_2_SMALL_FEATURE: 5,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE: 16,
        ScaleLevel.LEVEL_4_GREENFIELD: 50,
    }
    return estimates[scale_level]


def estimate_epics_from_scale(scale_level: ScaleLevel) -> int:
    """Estimate epic count based on scale level.

    Returns typical epic count for each scale level.

    Args:
        scale_level: Adaptive Agile scale level

    Returns:
        Estimated number of epics
    """
    estimates = {
        ScaleLevel.LEVEL_0_CHORE: 0,
        ScaleLevel.LEVEL_1_BUG_FIX: 0,
        ScaleLevel.LEVEL_2_SMALL_FEATURE: 1,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE: 3,
        ScaleLevel.LEVEL_4_GREENFIELD: 8,
    }
    return estimates[scale_level]
