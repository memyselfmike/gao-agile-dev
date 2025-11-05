# Story 13.2: Document Reference Resolver (@doc:)

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement @doc: reference resolver for injecting document content into prompts. This resolver will support full document loading, markdown section extraction, YAML field extraction, and glob patterns for multiple documents.

---

## Business Value

This story enables powerful automatic context injection:

- **Automatic Context**: No manual copy-paste of document content into prompts
- **Section Extraction**: Pull only relevant sections (e.g., acceptance criteria from stories)
- **YAML Parsing**: Extract specific fields from frontmatter
- **Batch Loading**: Load multiple related documents with glob patterns
- **Always Current**: References always load latest version

---

## Acceptance Criteria

### Basic Document Loading
- [ ] `@doc:path/to/file.md` loads full document content
- [ ] Relative paths resolved from project root
- [ ] Absolute paths supported
- [ ] Missing documents handled gracefully (warning + empty string)
- [ ] Document loaded via DocumentLifecycleManager
- [ ] Loads only active documents by default

### Section Extraction
- [ ] `@doc:path/to/file.md#section` extracts markdown section by heading
- [ ] Supports nested headings (e.g., `#heading-1.subheading`)
- [ ] Section extraction preserves formatting
- [ ] Missing sections handled gracefully
- [ ] Supports heading levels 1-6

### YAML Field Extraction
- [ ] `@doc:path/to/file.md@yaml_key` extracts YAML frontmatter field
- [ ] Supports nested keys (e.g., `@metadata.author`)
- [ ] Handles arrays and objects in YAML
- [ ] Missing keys handled gracefully
- [ ] Validates YAML syntax before extraction

### Glob Patterns
- [ ] `@doc:glob:pattern/*.md` loads multiple documents
- [ ] Results separated by configurable delimiter (default: `\n---\n`)
- [ ] Max limit enforced (default: 100 files)
- [ ] Files sorted alphabetically
- [ ] Large result sets truncated with warning

### Performance
- [ ] Document loading <50ms per file
- [ ] Section extraction <10ms
- [ ] YAML parsing <10ms
- [ ] Caching reduces repeated loads to <1ms

---

## Technical Notes

### Implementation

```python
# gao_dev/core/meta_prompts/resolvers/doc_resolver.py

import re
from pathlib import Path
from typing import Optional
import yaml
from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver
from gao_dev.lifecycle.document_lifecycle_manager import DocumentLifecycleManager

class DocResolver(ReferenceResolver):
    """Resolver for @doc: references."""

    def __init__(self, doc_manager: DocumentLifecycleManager, project_root: Path):
        self.doc_manager = doc_manager
        self.project_root = project_root

    def can_resolve(self, reference_type: str) -> bool:
        return reference_type == "doc"

    def resolve(self, reference: str, context: dict) -> str:
        """
        Resolve @doc: reference.

        Formats:
            @doc:path/to/file.md - Full document
            @doc:path/to/file.md#section - Markdown section
            @doc:path/to/file.md@yaml_key - YAML field
            @doc:glob:pattern/*.md - Multiple documents
        """
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
        """Load full document content."""
        full_path = self.project_root / path
        doc = self.doc_manager.get_document_by_path(str(full_path))

        if not doc:
            logger.warning(f"Document not found: {path}")
            return ""

        return self._read_file(full_path)

    def _resolve_section(self, path: str, section: str) -> str:
        """Extract markdown section by heading."""
        content = self._resolve_full(path)
        if not content:
            return ""

        # Find section by heading
        return self._extract_markdown_section(content, section)

    def _extract_markdown_section(self, content: str, heading: str) -> str:
        """
        Extract section from markdown by heading.

        Example:
            # Main Heading
            Content here
            ## Subheading
            More content

            extract_section(content, "main-heading") -> returns "Content here"
            extract_section(content, "subheading") -> returns "More content"
        """
        lines = content.split('\n')
        heading_slug = heading.lower().replace(' ', '-')

        in_section = False
        section_lines = []
        section_level = None

        for line in lines:
            # Check if this is a heading line
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                title_slug = title.lower().replace(' ', '-')

                if title_slug == heading_slug:
                    # Found the section start
                    in_section = True
                    section_level = level
                elif in_section and level <= section_level:
                    # Reached next section at same or higher level
                    break
            elif in_section:
                section_lines.append(line)

        return '\n'.join(section_lines).strip()

    def _resolve_yaml_field(self, path: str, yaml_key: str) -> str:
        """Extract YAML frontmatter field."""
        content = self._resolve_full(path)
        if not content:
            return ""

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        if not frontmatter:
            return ""

        # Navigate nested keys
        keys = yaml_key.split('.')
        value = frontmatter

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                logger.warning(f"Cannot access key '{key}' in non-dict value")
                return ""

        # Convert to string
        if isinstance(value, (list, dict)):
            return yaml.dump(value)
        else:
            return str(value)

    def _extract_frontmatter(self, content: str) -> Optional[dict]:
        """Extract YAML frontmatter from markdown."""
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML frontmatter: {e}")
            return None

    def _resolve_glob(self, pattern: str, max_files: int = 100) -> str:
        """Load multiple documents matching glob pattern."""
        paths = sorted(self.project_root.glob(pattern))

        if len(paths) > max_files:
            logger.warning(f"Glob pattern matched {len(paths)} files, truncating to {max_files}")
            paths = paths[:max_files]

        contents = []
        for path in paths:
            try:
                content = self._read_file(path)
                contents.append(f"# {path.name}\n\n{content}")
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")

        return "\n\n---\n\n".join(contents)
```

### Reference Examples

```yaml
# Full document
user_prompt: |
  Review the PRD:
  @doc:docs/PRD.md

# Section extraction
user_prompt: |
  Implement the following acceptance criteria:
  @doc:stories/epic-3/story-3.1.md#acceptance-criteria

# YAML field extraction
user_prompt: |
  Current story status: @doc:stories/epic-3/story-3.1.md@status
  Story owner: @doc:stories/epic-3/story-3.1.md@owner

# Glob pattern
user_prompt: |
  Review all completed stories:
  @doc:glob:stories/epic-3/*.md
```

**Files to Create:**
- `gao_dev/core/meta_prompts/resolvers/__init__.py`
- `gao_dev/core/meta_prompts/resolvers/doc_resolver.py`
- `tests/core/meta_prompts/resolvers/test_doc_resolver.py`

**Dependencies:**
- Story 13.1 (Reference Resolver Framework)
- Epic 12, Story 12.4 (DocumentLifecycleManager)

---

## Testing Requirements

### Unit Tests

**Full Document Loading:**
- [ ] Test loading existing document
- [ ] Test loading missing document (returns empty)
- [ ] Test relative path resolution
- [ ] Test absolute path support
- [ ] Test document state filtering (active only)

**Section Extraction:**
- [ ] Test extracting top-level heading
- [ ] Test extracting nested heading
- [ ] Test missing section returns empty
- [ ] Test section with formatting preserved
- [ ] Test multiple sections with same name

**YAML Field Extraction:**
- [ ] Test extracting simple field
- [ ] Test extracting nested field (dot notation)
- [ ] Test extracting array field
- [ ] Test extracting object field
- [ ] Test missing field returns empty
- [ ] Test invalid YAML handled gracefully

**Glob Patterns:**
- [ ] Test glob matching multiple files
- [ ] Test glob with max limit
- [ ] Test glob with no matches
- [ ] Test glob sorting (alphabetical)
- [ ] Test glob with mixed file types

### Integration Tests
- [ ] Test with real document files
- [ ] Test with DocumentLifecycleManager
- [ ] Test with cached documents
- [ ] Test end-to-end resolution in prompt

### Performance Tests
- [ ] Single document load <50ms
- [ ] Section extraction <10ms
- [ ] YAML parsing <10ms
- [ ] Glob with 100 files <1 second
- [ ] Cached document access <1ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] Reference syntax documentation with examples
- [ ] Section extraction algorithm documentation
- [ ] YAML field navigation documentation
- [ ] Glob pattern usage guide
- [ ] Performance characteristics documented

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Performance benchmarks met
- [ ] Integrated with ReferenceResolverRegistry
- [ ] Example prompts using @doc: references tested
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.2 - Document Reference Resolver

  - Implement DocResolver for @doc: references
  - Support full document loading
  - Add markdown section extraction by heading
  - Add YAML frontmatter field extraction
  - Support glob patterns for multiple documents
  - Comprehensive error handling and logging
  - Add unit and integration tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
