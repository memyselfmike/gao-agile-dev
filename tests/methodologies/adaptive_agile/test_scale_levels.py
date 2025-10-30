"""Tests for scale levels and mappings.

Story 5.2: Test ScaleLevel enum and mapping functions.
"""

import pytest

from gao_dev.core.models.methodology import ComplexityLevel
from gao_dev.methodologies.adaptive_agile.scale_levels import (
    ScaleLevel,
    map_scale_to_complexity,
    map_complexity_to_scale,
    estimate_stories_from_scale,
    estimate_epics_from_scale,
)


class TestScaleLevel:
    """Test ScaleLevel enum."""

    def test_all_levels_exist(self):
        """Test all 5 scale levels are defined."""
        assert ScaleLevel.LEVEL_0_CHORE == 0
        assert ScaleLevel.LEVEL_1_BUG_FIX == 1
        assert ScaleLevel.LEVEL_2_SMALL_FEATURE == 2
        assert ScaleLevel.LEVEL_3_MEDIUM_FEATURE == 3
        assert ScaleLevel.LEVEL_4_GREENFIELD == 4

    def test_scale_level_is_int_enum(self):
        """Test ScaleLevel values are integers."""
        for level in ScaleLevel:
            assert isinstance(level.value, int)
            assert 0 <= level.value <= 4


class TestMapScaleToComplexity:
    """Test mapping scale levels to complexity levels."""

    def test_level_0_maps_to_trivial(self):
        """Test level 0 maps to TRIVIAL."""
        result = map_scale_to_complexity(ScaleLevel.LEVEL_0_CHORE)
        assert result == ComplexityLevel.TRIVIAL

    def test_level_1_maps_to_small(self):
        """Test level 1 maps to SMALL."""
        result = map_scale_to_complexity(ScaleLevel.LEVEL_1_BUG_FIX)
        assert result == ComplexityLevel.SMALL

    def test_level_2_maps_to_medium(self):
        """Test level 2 maps to MEDIUM."""
        result = map_scale_to_complexity(ScaleLevel.LEVEL_2_SMALL_FEATURE)
        assert result == ComplexityLevel.MEDIUM

    def test_level_3_maps_to_large(self):
        """Test level 3 maps to LARGE."""
        result = map_scale_to_complexity(ScaleLevel.LEVEL_3_MEDIUM_FEATURE)
        assert result == ComplexityLevel.LARGE

    def test_level_4_maps_to_xlarge(self):
        """Test level 4 maps to XLARGE."""
        result = map_scale_to_complexity(ScaleLevel.LEVEL_4_GREENFIELD)
        assert result == ComplexityLevel.XLARGE


class TestMapComplexityToScale:
    """Test reverse mapping complexity to scale levels."""

    def test_trivial_maps_to_level_0(self):
        """Test TRIVIAL maps to level 0."""
        result = map_complexity_to_scale(ComplexityLevel.TRIVIAL)
        assert result == ScaleLevel.LEVEL_0_CHORE

    def test_small_maps_to_level_1(self):
        """Test SMALL maps to level 1."""
        result = map_complexity_to_scale(ComplexityLevel.SMALL)
        assert result == ScaleLevel.LEVEL_1_BUG_FIX

    def test_medium_maps_to_level_2(self):
        """Test MEDIUM maps to level 2."""
        result = map_complexity_to_scale(ComplexityLevel.MEDIUM)
        assert result == ScaleLevel.LEVEL_2_SMALL_FEATURE

    def test_large_maps_to_level_3(self):
        """Test LARGE maps to level 3."""
        result = map_complexity_to_scale(ComplexityLevel.LARGE)
        assert result == ScaleLevel.LEVEL_3_MEDIUM_FEATURE

    def test_xlarge_maps_to_level_4(self):
        """Test XLARGE maps to level 4."""
        result = map_complexity_to_scale(ComplexityLevel.XLARGE)
        assert result == ScaleLevel.LEVEL_4_GREENFIELD


class TestBidirectionalMapping:
    """Test mappings are bidirectional."""

    def test_scale_to_complexity_to_scale(self):
        """Test round-trip: scale -> complexity -> scale."""
        for scale_level in ScaleLevel:
            complexity = map_scale_to_complexity(scale_level)
            back_to_scale = map_complexity_to_scale(complexity)
            assert back_to_scale == scale_level

    def test_complexity_to_scale_to_complexity(self):
        """Test round-trip: complexity -> scale -> complexity."""
        for complexity in ComplexityLevel:
            scale = map_complexity_to_scale(complexity)
            back_to_complexity = map_scale_to_complexity(scale)
            assert back_to_complexity == complexity


class TestEstimateStoriesFromScale:
    """Test story estimation."""

    def test_level_0_estimates_0_stories(self):
        """Test level 0 estimates 0 stories."""
        assert estimate_stories_from_scale(ScaleLevel.LEVEL_0_CHORE) == 0

    def test_level_1_estimates_1_story(self):
        """Test level 1 estimates 1 story."""
        assert estimate_stories_from_scale(ScaleLevel.LEVEL_1_BUG_FIX) == 1

    def test_level_2_estimates_5_stories(self):
        """Test level 2 estimates 5 stories."""
        assert estimate_stories_from_scale(ScaleLevel.LEVEL_2_SMALL_FEATURE) == 5

    def test_level_3_estimates_16_stories(self):
        """Test level 3 estimates 16 stories."""
        assert estimate_stories_from_scale(ScaleLevel.LEVEL_3_MEDIUM_FEATURE) == 16

    def test_level_4_estimates_50_stories(self):
        """Test level 4 estimates 50 stories."""
        assert estimate_stories_from_scale(ScaleLevel.LEVEL_4_GREENFIELD) == 50


class TestEstimateEpicsFromScale:
    """Test epic estimation."""

    def test_level_0_estimates_0_epics(self):
        """Test level 0 estimates 0 epics."""
        assert estimate_epics_from_scale(ScaleLevel.LEVEL_0_CHORE) == 0

    def test_level_1_estimates_0_epics(self):
        """Test level 1 estimates 0 epics."""
        assert estimate_epics_from_scale(ScaleLevel.LEVEL_1_BUG_FIX) == 0

    def test_level_2_estimates_1_epic(self):
        """Test level 2 estimates 1 epic."""
        assert estimate_epics_from_scale(ScaleLevel.LEVEL_2_SMALL_FEATURE) == 1

    def test_level_3_estimates_3_epics(self):
        """Test level 3 estimates 3 epics."""
        assert estimate_epics_from_scale(ScaleLevel.LEVEL_3_MEDIUM_FEATURE) == 3

    def test_level_4_estimates_8_epics(self):
        """Test level 4 estimates 8 epics."""
        assert estimate_epics_from_scale(ScaleLevel.LEVEL_4_GREENFIELD) == 8
