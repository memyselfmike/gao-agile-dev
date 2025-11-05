"""
Document reference resolver for @doc: references.

This resolver integrates with the Document Lifecycle System to inject document
content into prompts. It supports:
- Full document loading
- Markdown section extraction by heading
- YAML frontmatter field extraction
- Glob patterns for multiple documents
"""

import re
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import DocumentState

logger = structlog.get_logger(__name__)


class DocResolver(ReferenceResolver):
    """
    Resolver for @doc: references.

    This resolver loads document content from the Document Lifecycle System,
    supporting various extraction modes:

    Formats:
        @doc:path/to/file.md              - Full document content
        @doc:path/to/file.md#section      - Markdown section by heading
        @doc:path/to/file.md@yaml_key     - YAML frontmatter field
        @doc:glob:pattern/*.md            - Multiple documents matching glob

    Examples:
        >>> resolver = DocResolver(doc_manager, project_root)
        >>>
        >>> # Load full document
        >>> content = resolver.resolve("docs/PRD.md", {})
        >>>
        >>> # Extract section
        >>> criteria = resolver.resolve(
        ...     "stories/epic-3/story-3.1.md#acceptance-criteria",
        ...     {}
        ... )
        >>>
        >>> # Extract YAML field
        >>> status = resolver.resolve("stories/epic-3/story-3.1.md@status", {})
        >>>
        >>> # Load multiple documents
        >>> all_stories = resolver.resolve("glob:stories/epic-3/*.md", {})

    Args:
        doc_manager: Document lifecycle manager instance
        project_root: Project root directory for path resolution
        max_glob_files: Maximum files to load with glob patterns (default: 100)
        glob_delimiter: Delimiter between multiple documents (default: "\\n---\\n")
    """

    def __init__(
        self,
        doc_manager: DocumentLifecycleManager,
        project_root: Path,
        max_glob_files: int = 100,
        glob_delimiter: str = "\n---\n",
    ):
        """Initialize document resolver."""
        self.doc_manager = doc_manager
        self.project_root = Path(project_root)
        self.max_glob_files = max_glob_files
        self.glob_delimiter = glob_delimiter

    def can_resolve(self, reference_type: str) -> bool:
        """
        Check if this resolver can handle the reference type.

        Args:
            reference_type: Type of reference (e.g., "doc", "checklist")

        Returns:
            True if type is "doc"
        """
        return reference_type == "doc"

    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve @doc: reference to document content.

        Parses the reference format and delegates to appropriate handler:
        - glob:pattern -> _resolve_glob()
        - path#section -> _resolve_section()
        - path@yaml_key -> _resolve_yaml_field()
        - path -> _resolve_full()

        Args:
            reference: Reference value (e.g., "path/to/file.md#section")
            context: Context dict with variables for resolution

        Returns:
            Resolved document content as string

        Raises:
            ValueError: If reference format is invalid
        """
        logger.debug("resolving_doc_reference", reference=reference)

        # Parse reference format
        if reference.startswith("glob:"):
            return self._resolve_glob(reference[5:])
        elif "#" in reference:
            path, section = reference.split("#", 1)
            return self._resolve_section(path, section)
        elif "@" in reference:
            path, yaml_key = reference.split("@", 1)
            return self._resolve_yaml_field(path, yaml_key)
        else:
            return self._resolve_full(reference)

    def _resolve_full(self, path: str) -> str:
        """
        Load full document content.

        Resolves path relative to project root, loads document via
        DocumentLifecycleManager, and returns full content.

        Args:
            path: Document path (relative or absolute)

        Returns:
            Full document content, or empty string if not found
        """
        full_path = self._resolve_path(path)

        # Check if document is registered and active
        doc = self.doc_manager.registry.get_document_by_path(str(full_path))

        if not doc:
            logger.warning("document_not_registered", path=path)
            # Still try to read the file if it exists
            if full_path.exists():
                return self._read_file(full_path)
            return ""

        if doc.state != DocumentState.ACTIVE:
            logger.warning(
                "document_not_active",
                path=path,
                state=doc.state.value
            )
            # Still load content but log warning

        return self._read_file(full_path)

    def _resolve_section(self, path: str, section: str) -> str:
        """
        Extract markdown section by heading.

        Loads full document, then extracts the section under the specified
        heading. Heading matching is case-insensitive and normalizes whitespace.

        Args:
            path: Document path
            section: Heading name (e.g., "acceptance-criteria")

        Returns:
            Section content, or empty string if section not found

        Example:
            # Document content:
            # ## Acceptance Criteria
            # - Criterion 1
            # - Criterion 2
            # ## Next Section

            _resolve_section("doc.md", "acceptance-criteria")
            # Returns: "- Criterion 1\\n- Criterion 2"
        """
        content = self._resolve_full(path)
        if not content:
            return ""

        return self._extract_markdown_section(content, section)

    def _extract_markdown_section(self, content: str, heading: str) -> str:
        """
        Extract section from markdown by heading.

        Algorithm:
        1. Normalize heading to slug format (lowercase, hyphens)
        2. Scan lines looking for matching heading
        3. Collect lines until next heading of same/higher level
        4. Return collected content

        Supports heading levels 1-6 (# to ######).

        Args:
            content: Full markdown content
            heading: Heading slug (e.g., "acceptance-criteria")

        Returns:
            Section content with formatting preserved

        Example:
            # Main Heading
            Content here
            ## Subheading
            More content

            extract_section(content, "main-heading") -> "Content here"
            extract_section(content, "subheading") -> "More content"
        """
        lines = content.split('\n')
        heading_slug = self._normalize_heading(heading)

        in_section = False
        section_lines = []
        section_level = None

        for line in lines:
            # Check if this is a heading line
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                title_slug = self._normalize_heading(title)

                if title_slug == heading_slug:
                    # Found the section start
                    in_section = True
                    section_level = level
                elif in_section and level <= section_level:
                    # Reached next section at same or higher level - stop
                    break
            elif in_section:
                # Collect content lines
                section_lines.append(line)

        result = '\n'.join(section_lines).strip()

        if not result:
            logger.warning(
                "section_not_found",
                heading=heading,
                heading_slug=heading_slug
            )

        return result

    def _normalize_heading(self, heading: str) -> str:
        """
        Normalize heading to slug format.

        Converts heading to lowercase, replaces spaces/underscores with hyphens,
        removes special characters except hyphens.

        Args:
            heading: Original heading text

        Returns:
            Normalized slug

        Examples:
            "Acceptance Criteria" -> "acceptance-criteria"
            "User_Stories" -> "user-stories"
            "Feature #1" -> "feature-1"
        """
        # Convert to lowercase
        slug = heading.lower()

        # Replace spaces and underscores with hyphens
        slug = slug.replace(' ', '-').replace('_', '-')

        # Remove special characters except hyphens and alphanumeric
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        return slug

    def _resolve_yaml_field(self, path: str, yaml_key: str) -> str:
        """
        Extract YAML frontmatter field.

        Loads document, extracts YAML frontmatter, and navigates to the
        specified field using dot notation for nested keys.

        Args:
            path: Document path
            yaml_key: Field key, supports dot notation (e.g., "metadata.author")

        Returns:
            Field value as string, or empty string if not found

        Example:
            # Document with frontmatter:
            ---
            status: "in_progress"
            metadata:
              author: "john"
              version: 1.0
            tags: ["epic-3", "auth"]
            ---

            _resolve_yaml_field("doc.md", "status") -> "in_progress"
            _resolve_yaml_field("doc.md", "metadata.author") -> "john"
            _resolve_yaml_field("doc.md", "tags") -> "- epic-3\\n- auth"
        """
        content = self._resolve_full(path)
        if not content:
            return ""

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        if not frontmatter:
            logger.warning("no_frontmatter", path=path)
            return ""

        # Navigate nested keys
        keys = yaml_key.split('.')
        value = frontmatter

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    logger.warning(
                        "yaml_key_not_found",
                        path=path,
                        key=yaml_key,
                        missing_key=key
                    )
                    return ""
            else:
                logger.warning(
                    "yaml_key_not_dict",
                    path=path,
                    key=yaml_key,
                    current_key=key,
                    value_type=type(value).__name__
                )
                return ""

        # Convert to string
        if isinstance(value, (list, dict)):
            return yaml.dump(value, default_flow_style=False).strip()
        else:
            return str(value)

    def _extract_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract YAML frontmatter from markdown.

        Frontmatter must be at the start of the file, delimited by "---".

        Args:
            content: Full document content

        Returns:
            Dict of frontmatter data, or None if no frontmatter

        Example:
            ---
            key: value
            list: [1, 2, 3]
            ---
            Content here

            -> {"key": "value", "list": [1, 2, 3]}
        """
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            logger.error("invalid_yaml_frontmatter", error=str(e))
            return None

    def _resolve_glob(self, pattern: str) -> str:
        """
        Load multiple documents matching glob pattern.

        Expands glob pattern relative to project root, loads all matching
        files (up to max_glob_files), and concatenates with delimiter.

        Files are sorted alphabetically for consistent ordering.

        Args:
            pattern: Glob pattern (e.g., "stories/epic-3/*.md")

        Returns:
            Concatenated content of all matching files

        Example:
            # With files: story-1.md, story-2.md, story-3.md
            _resolve_glob("stories/*.md")
            # Returns:
            # # story-1.md
            #
            # [content of story-1]
            #
            # ---
            #
            # # story-2.md
            #
            # [content of story-2]
            # ...
        """
        # Resolve pattern relative to project root
        paths = sorted(self.project_root.glob(pattern))

        if not paths:
            logger.warning("glob_no_matches", pattern=pattern)
            return ""

        if len(paths) > self.max_glob_files:
            logger.warning(
                "glob_truncated",
                pattern=pattern,
                found=len(paths),
                max=self.max_glob_files
            )
            paths = paths[:self.max_glob_files]

        logger.info(
            "glob_resolved",
            pattern=pattern,
            file_count=len(paths)
        )

        contents = []
        for path in paths:
            try:
                content = self._read_file(path)
                # Add filename header for clarity
                contents.append(f"# {path.name}\n\n{content}")
            except Exception as e:
                logger.warning(
                    "glob_file_load_failed",
                    path=str(path),
                    error=str(e)
                )

        return self.glob_delimiter.join(contents)

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve path relative to project root.

        If path is absolute, returns as-is.
        If path is relative, resolves relative to project root.

        Args:
            path: File path (relative or absolute)

        Returns:
            Resolved absolute Path
        """
        path_obj = Path(path)

        if path_obj.is_absolute():
            return path_obj

        return (self.project_root / path_obj).resolve()

    def _read_file(self, path: Path) -> str:
        """
        Read file content with UTF-8 encoding.

        Args:
            path: File path to read

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file is not valid UTF-8
        """
        if not path.exists():
            logger.warning("file_not_found", path=str(path))
            return ""

        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            logger.error(
                "file_encoding_error",
                path=str(path),
                error=str(e)
            )
            return ""
        except Exception as e:
            logger.error(
                "file_read_error",
                path=str(path),
                error=str(e)
            )
            return ""
