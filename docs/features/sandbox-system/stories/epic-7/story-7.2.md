# Story 7.2: Implement Artifact Output Parser

**Epic**: Epic 7 - Autonomous Artifact Creation & Git Integration
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-28

---

## User Story

**As a** benchmark system
**I want** to parse agent outputs to extract artifacts and file paths
**So that** agent-generated content is properly saved to the correct files

---

## Context

After Story 7.1, GAODevOrchestrator generates agent outputs, but we need to:
1. Parse markdown responses to extract file content
2. Determine the correct file paths for artifacts
3. Handle multiple files in a single agent response
4. Validate that paths are safe (within project boundaries)

---

## Acceptance Criteria

### AC1: ArtifactParser Class Created
- [ ] New class `ArtifactParser` in `gao_dev/sandbox/artifact_parser.py`
- [ ] Methods: `parse_output()`, `extract_files()`, `validate_path()`
- [ ] Handles markdown code blocks with file paths
- [ ] Proper error handling for malformed outputs

### AC2: File Extraction
- [ ] Can extract code blocks from markdown
- [ ] Recognizes file path indicators ("Save as:", "File:", etc.)
- [ ] Handles multiple files in single response
- [ ] Preserves formatting and indentation
- [ ] Supports multiple languages (Python, TypeScript, JSON, YAML, MD)

### AC3: Path Validation
- [ ] Validates paths are within project root
- [ ] Prevents directory traversal attacks (../)
- [ ] Normalizes paths (handles \ and /)
- [ ] Creates parent directories if needed
- [ ] Rejects absolute paths outside project

### AC4: Content Extraction
- [ ] Extracts content from ```language blocks
- [ ] Handles inline code with `single backticks`
- [ ] Preserves whitespace and line breaks
- [ ] Handles special characters
- [ ] UTF-8 encoding support

### AC5: Integration with Orchestrator
- [ ] Orchestrator calls ArtifactParser after agent execution
- [ ] Parsed artifacts written to disk
- [ ] File write errors handled gracefully
- [ ] Logs all artifacts created

---

## Technical Details

### Example Agent Output

```markdown
# Product Requirements Document

## Overview
This is the PRD for the todo application...

## Features
- User authentication
- CRUD operations
- Categories and tags

**Save as**: docs/PRD.md

---

## Test Plan

The test plan includes...

**File**: docs/TEST_PLAN.md
```

### Parsing Logic

```python
class ArtifactParser:
    def parse_output(self, output: str, phase: str) -> List[Artifact]:
        """Parse agent output and extract artifacts."""
        artifacts = []

        # Look for file path indicators
        patterns = [
            r'\*\*Save as\*\*:\s*(.+)',
            r'\*\*File\*\*:\s*(.+)',
            r'```(\w+)\s*#\s*(.+\.[\w]+)',  # Code block with file comment
        ]

        # Extract code blocks
        code_blocks = self._extract_code_blocks(output)

        # Match paths to content
        for block in code_blocks:
            path = self._find_path_for_block(block, patterns)
            if path:
                artifacts.append(Artifact(path=path, content=block.content))

        return artifacts

    def validate_path(self, path: str, project_root: Path) -> bool:
        """Ensure path is safe and within project."""
        resolved = (project_root / path).resolve()
        return resolved.is_relative_to(project_root)
```

### File Path Inference

If no explicit path is given, infer from phase:

| Phase | Default Path Pattern |
|-------|---------------------|
| Product Requirements | `docs/PRD.md` |
| System Architecture | `docs/ARCHITECTURE.md` |
| Story Creation | `docs/stories/epic-{epic}/story-{story}.md` |
| Implementation | Depends on file type (src/, tests/) |

---

## Files to Create

**New**:
- `gao_dev/sandbox/artifact_parser.py` - Main parser class
- `gao_dev/sandbox/models.py` - Artifact dataclass
- `tests/sandbox/test_artifact_parser.py` - Parser tests

**Modify**:
- `gao_dev/orchestrator/orchestrator.py` - Call parser after agent execution
- `gao_dev/sandbox/benchmark/orchestrator.py` - Integrate parser

---

## Dependencies

**Requires**:
- Story 7.1 (GAODevOrchestrator integration) - must be complete
- Regex for markdown parsing
- pathlib for path operations

**Blocks**:
- Story 7.3 (Atomic Git Commits) - needs artifacts to commit
- Story 7.5 (Artifact Verification) - needs parser output

---

## Implementation Steps

1. **Create Artifact Dataclass**
   ```python
   @dataclass
   class Artifact:
       path: Path
       content: str
       language: str
       phase: str
   ```

2. **Implement Parser**
   - Extract code blocks with regex
   - Find file path indicators
   - Match content to paths
   - Validate paths

3. **Add Path Inference**
   - Default paths by phase
   - Smart inference from content
   - Fallback to standard locations

4. **Integrate with Orchestrator**
   - Call parser after agent execution
   - Write artifacts to disk
   - Log operations
   - Handle errors

5. **Write Tests**
   - Unit tests for parsing logic
   - Path validation tests
   - Integration tests with orchestrator

---

## Testing Approach

### Unit Tests

```python
def test_parse_simple_markdown():
    parser = ArtifactParser()
    output = """
    # PRD
    Content here
    **Save as**: docs/PRD.md
    """
    artifacts = parser.parse_output(output, "create-prd")
    assert len(artifacts) == 1
    assert artifacts[0].path == Path("docs/PRD.md")

def test_validate_path_safety():
    parser = ArtifactParser()
    project_root = Path("/sandbox/project-001")

    # Valid paths
    assert parser.validate_path("docs/PRD.md", project_root)
    assert parser.validate_path("src/app.py", project_root)

    # Invalid paths
    assert not parser.validate_path("../../../etc/passwd", project_root)
    assert not parser.validate_path("/etc/passwd", project_root)

def test_extract_multiple_files():
    parser = ArtifactParser()
    output = """
    **File**: src/app.py
    ```python
    def main():
        pass
    ```

    **File**: tests/test_app.py
    ```python
    def test_main():
        pass
    ```
    """
    artifacts = parser.parse_output(output, "implementation")
    assert len(artifacts) == 2
```

### Integration Tests
- Parse real agent outputs
- Write to disk
- Verify file contents
- Test error handling

---

## Edge Cases

1. **No File Path Specified**: Use default path based on phase
2. **Multiple Code Blocks, One Path**: Combine into single file
3. **Malformed Markdown**: Log warning, skip artifact
4. **Special Characters in Paths**: Sanitize and validate
5. **Very Large Files**: Stream write, handle memory efficiently

---

## Definition of Done

- [ ] ArtifactParser class implemented
- [ ] Can extract files from markdown
- [ ] Path validation working
- [ ] Integration with orchestrator complete
- [ ] All tests passing (>90% coverage)
- [ ] Edge cases handled
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Committed with atomic commit

---

## Notes

**Why This Matters**: Without artifact parsing, agents generate content but we don't know where to save it. This is the bridge between agent output and real files on disk.

**Design Philosophy**: Be permissive where possible, strict where necessary. Accept various markdown formats, but strictly validate paths for security.

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: After Story 7.1 complete
**Estimated Completion**: 2-3 hours

---

*This story enables GAO-Dev to transform agent thoughts into tangible artifacts.*
