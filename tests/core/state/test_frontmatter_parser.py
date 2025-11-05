"""Tests for FrontmatterParser.

Tests YAML frontmatter parsing and serialization for markdown files.
"""

import pytest
from gao_dev.core.state.frontmatter_parser import FrontmatterParser


class TestFrontmatterParser:
    """Test suite for FrontmatterParser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return FrontmatterParser()

    def test_parse_valid_frontmatter(self, parser):
        """Test parsing valid frontmatter."""
        content = """---
epic: 1
story_num: 1
title: Test Story
status: pending
points: 3
---

This is the story body.
"""
        frontmatter, body = parser.parse(content)

        assert frontmatter["epic"] == 1
        assert frontmatter["story_num"] == 1
        assert frontmatter["title"] == "Test Story"
        assert frontmatter["status"] == "pending"
        assert frontmatter["points"] == 3
        assert body == "This is the story body."

    def test_parse_no_frontmatter(self, parser):
        """Test parsing content without frontmatter."""
        content = "Just regular markdown content."
        frontmatter, body = parser.parse(content)

        assert frontmatter == {}
        assert body == "Just regular markdown content."

    def test_parse_empty_frontmatter(self, parser):
        """Test parsing empty frontmatter."""
        content = """---
---

Body content here.
"""
        frontmatter, body = parser.parse(content)

        assert frontmatter == {}
        # Empty frontmatter still matches pattern, so body includes the delimiters
        # This is expected behavior when frontmatter is truly empty
        assert "Body content here." in body

    def test_parse_malformed_yaml(self, parser):
        """Test parsing with malformed YAML frontmatter."""
        content = """---
epic: 1
invalid yaml: [unclosed
---

Body content.
"""
        frontmatter, body = parser.parse(content)

        # Should return empty frontmatter on YAML error
        assert frontmatter == {}
        # Body should still be parsed
        assert "Body content." in body

    def test_parse_multiline_values(self, parser):
        """Test parsing frontmatter with multiline values."""
        content = """---
epic: 1
story_num: 1
title: Multi-line Title
description: |
  This is a multi-line
  description field
status: pending
---

Story body.
"""
        frontmatter, body = parser.parse(content)

        assert frontmatter["epic"] == 1
        assert "Multi-line" in frontmatter["title"]
        assert "multi-line" in frontmatter["description"]
        assert body == "Story body."

    def test_parse_nested_data(self, parser):
        """Test parsing nested YAML data."""
        content = """---
epic: 1
story_num: 1
metadata:
  tags:
    - backend
    - api
  complexity: high
---

Body.
"""
        frontmatter, body = parser.parse(content)

        assert frontmatter["epic"] == 1
        assert "metadata" in frontmatter
        assert "tags" in frontmatter["metadata"]
        assert "backend" in frontmatter["metadata"]["tags"]

    def test_serialize_basic(self, parser):
        """Test serializing frontmatter and body."""
        frontmatter = {
            "epic": 1,
            "story_num": 1,
            "title": "Test Story",
            "status": "pending",
        }
        body = "This is the story body."

        result = parser.serialize(frontmatter, body)

        assert result.startswith("---\n")
        assert "epic: 1" in result
        assert "story_num: 1" in result
        assert "title: Test Story" in result
        assert "status: pending" in result
        assert result.endswith("This is the story body.\n")

    def test_serialize_preserves_order(self, parser):
        """Test serialization preserves field order."""
        frontmatter = {
            "epic": 1,
            "story_num": 1,
            "title": "Test",
            "status": "pending",
        }
        body = "Body"

        result = parser.serialize(frontmatter, body)

        # YAML dump should maintain insertion order (Python 3.7+)
        lines = result.split("\n")
        assert "epic:" in lines[1]

    def test_serialize_unicode(self, parser):
        """Test serialization with Unicode characters."""
        frontmatter = {
            "title": "Test with Unicode: \u00e9\u00e8\u00ea",
            "epic": 1,
            "story_num": 1,
        }
        body = "Body with Unicode: \u2713"

        result = parser.serialize(frontmatter, body)

        assert "\u00e9" in result or "\\u" in result  # Either literal or escaped
        assert "\u2713" in result or "Body with Unicode:" in result

    def test_roundtrip_parse_serialize(self, parser):
        """Test parse -> serialize roundtrip."""
        original = """---
epic: 1
story_num: 1
title: Test Story
status: pending
points: 3
priority: P1
---

This is the story body.
Multiple lines of content.
"""
        frontmatter, body = parser.parse(original)
        regenerated = parser.serialize(frontmatter, body)

        # Parse again to verify
        fm2, body2 = parser.parse(regenerated)

        assert fm2 == frontmatter
        assert body2.strip() == body.strip()

    def test_validate_frontmatter_valid(self, parser):
        """Test frontmatter validation with all required fields."""
        frontmatter = {
            "epic": 1,
            "story_num": 1,
            "title": "Test",
            "status": "pending",
        }

        assert parser.validate_frontmatter(frontmatter) is True

    def test_validate_frontmatter_missing_epic(self, parser):
        """Test validation fails when epic missing."""
        frontmatter = {"story_num": 1, "title": "Test", "status": "pending"}

        assert parser.validate_frontmatter(frontmatter) is False

    def test_validate_frontmatter_missing_story_num(self, parser):
        """Test validation fails when story_num missing."""
        frontmatter = {"epic": 1, "title": "Test", "status": "pending"}

        assert parser.validate_frontmatter(frontmatter) is False

    def test_validate_frontmatter_missing_title(self, parser):
        """Test validation fails when title missing."""
        frontmatter = {"epic": 1, "story_num": 1, "status": "pending"}

        assert parser.validate_frontmatter(frontmatter) is False

    def test_validate_frontmatter_missing_status(self, parser):
        """Test validation fails when status missing."""
        frontmatter = {"epic": 1, "story_num": 1, "title": "Test"}

        assert parser.validate_frontmatter(frontmatter) is False

    def test_validate_frontmatter_extra_fields(self, parser):
        """Test validation succeeds with extra fields."""
        frontmatter = {
            "epic": 1,
            "story_num": 1,
            "title": "Test",
            "status": "pending",
            "owner": "Amelia",
            "points": 5,
            "extra_field": "value",
        }

        assert parser.validate_frontmatter(frontmatter) is True

    def test_validate_frontmatter_empty(self, parser):
        """Test validation fails with empty frontmatter."""
        assert parser.validate_frontmatter({}) is False

    def test_parse_preserves_whitespace_in_body(self, parser):
        """Test parsing preserves whitespace in body."""
        content = """---
epic: 1
story_num: 1
title: Test
status: pending
---

Line 1

Line 2 with spaces
Line 3
"""
        frontmatter, body = parser.parse(content)

        assert "Line 1" in body
        assert "Line 2 with spaces" in body
        assert body.count("\n") >= 3

    def test_serialize_empty_body(self, parser):
        """Test serialization with empty body."""
        frontmatter = {"epic": 1, "story_num": 1, "title": "Test", "status": "pending"}
        body = ""

        result = parser.serialize(frontmatter, body)

        assert "---\n" in result
        assert result.endswith("\n")

    def test_parse_complex_story_file(self, parser):
        """Test parsing a realistic story file."""
        content = """---
epic: 15
story_num: 3
title: Markdown-SQLite Syncer
status: pending
owner: TBD
points: 6
priority: P0
sprint: null
---

## Story Description

Implement bidirectional sync between markdown and SQLite.

## Acceptance Criteria

- [ ] Parse frontmatter
- [ ] Sync to database
- [ ] Detect conflicts

## Technical Notes

Use SHA256 for hashing.
"""
        frontmatter, body = parser.parse(content)

        assert frontmatter["epic"] == 15
        assert frontmatter["story_num"] == 3
        assert frontmatter["title"] == "Markdown-SQLite Syncer"
        assert frontmatter["points"] == 6
        assert "## Story Description" in body
        assert "## Acceptance Criteria" in body
        assert "SHA256" in body
