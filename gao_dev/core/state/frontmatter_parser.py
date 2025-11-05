"""Frontmatter parser for markdown files.

Provides parsing and serialization of YAML frontmatter in markdown files,
used for bidirectional sync between markdown and database.
"""

import re
from typing import Dict, Any, Tuple
import yaml


class FrontmatterParser:
    """Parse and serialize YAML frontmatter in markdown files.

    Handles extraction of YAML frontmatter from markdown files and
    regeneration of markdown with updated frontmatter while preserving
    the content body.

    Example:
        >>> parser = FrontmatterParser()
        >>> content = '''---
        ... title: My Story
        ... status: pending
        ... ---
        ...
        ... Story content here
        ... '''
        >>> frontmatter, body = parser.parse(content)
        >>> frontmatter['title']
        'My Story'
        >>> body
        'Story content here'
    """

    # Match frontmatter: --- ... --- with content after
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL
    )

    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse markdown content into frontmatter and body.

        Extracts YAML frontmatter from the beginning of a markdown file
        and returns both the parsed frontmatter dictionary and the remaining
        content body.

        Args:
            content: Markdown file content

        Returns:
            Tuple of (frontmatter dict, body string)
            - frontmatter: Dictionary of YAML frontmatter fields
            - body: Remaining markdown content after frontmatter

        Example:
            >>> parser = FrontmatterParser()
            >>> fm, body = parser.parse("---\\ntitle: Test\\n---\\n\\nContent")
            >>> fm
            {'title': 'Test'}
            >>> body
            'Content'
        """
        match = self.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter_str = match.group(1)
            body = match.group(2).strip()

            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                # Handle empty frontmatter
                if frontmatter is None:
                    frontmatter = {}
            except yaml.YAMLError:
                # Invalid YAML, return empty frontmatter
                frontmatter = {}

            return frontmatter, body
        else:
            # No frontmatter found, return empty dict and full content
            return {}, content.strip()

    def serialize(self, frontmatter: Dict[str, Any], body: str) -> str:
        """Serialize frontmatter and body into markdown content.

        Combines a frontmatter dictionary and content body into a properly
        formatted markdown file with YAML frontmatter.

        Args:
            frontmatter: Frontmatter dictionary
            body: Content body string

        Returns:
            Complete markdown content with frontmatter

        Example:
            >>> parser = FrontmatterParser()
            >>> content = parser.serialize({'title': 'Test'}, 'Content')
            >>> print(content)
            ---
            title: Test
            ---
            <BLANKLINE>
            Content
            <BLANKLINE>
        """
        # Serialize frontmatter to YAML
        frontmatter_str = yaml.dump(
            frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
        return f"---\n{frontmatter_str}---\n\n{body}\n"

    def validate_frontmatter(self, frontmatter: Dict[str, Any]) -> bool:
        """Validate frontmatter has required fields.

        Checks that all required fields are present in the frontmatter
        dictionary for a valid story file.

        Args:
            frontmatter: Frontmatter dictionary to validate

        Returns:
            True if valid (all required fields present), False otherwise

        Example:
            >>> parser = FrontmatterParser()
            >>> parser.validate_frontmatter({'epic': 1, 'story_num': 1, 'title': 'Test', 'status': 'pending'})
            True
            >>> parser.validate_frontmatter({'epic': 1})
            False
        """
        required_fields = ["epic", "story_num", "title", "status"]
        return all(field in frontmatter for field in required_fields)
