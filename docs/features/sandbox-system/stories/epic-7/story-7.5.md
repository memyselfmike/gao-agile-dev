# Story 7.5: Add Artifact Verification

**Epic**: Epic 7 - Autonomous Artifact Creation & Git Integration
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 3 story points
**Owner**: Murat (QA), Amelia (Developer)
**Created**: 2025-10-28

---

## User Story

**As a** benchmark system
**I want** to verify that expected artifacts were created and are valid
**So that** I can detect missing or malformed outputs from autonomous execution

---

## Context

After artifacts are created and committed, we need to verify:
1. Expected files actually exist
2. Files have valid content (not empty, proper format)
3. Git commits were created as expected
4. No critical artifacts are missing

---

## Acceptance Criteria

### AC1: File Existence Checks
- [ ] Verifies expected artifacts exist
- [ ] Checks file permissions
- [ ] Validates file is not empty
- [ ] Reports missing files as warnings

### AC2: Content Validation
- [ ] Minimum length checks (not just whitespace)
- [ ] Syntax validation for code files (Python, TypeScript)
- [ ] Markdown structure validation
- [ ] JSON/YAML parsing validation

### AC3: Git Verification
- [ ] Verifies commits were created
- [ ] Checks commit messages follow convention
- [ ] Validates files are in git history
- [ ] Ensures no uncommitted changes

### AC4: Quality Checks
- [ ] Code files have valid syntax
- [ ] No obvious errors (syntax errors, import errors)
- [ ] Markdown files have proper structure
- [ ] Config files are valid

### AC5: Reporting
- [ ] Lists all verified artifacts
- [ ] Reports missing artifacts
- [ ] Reports validation failures
- [ ] Includes in benchmark report

---

## Technical Details

### ArtifactVerifier Class

```python
class ArtifactVerifier:
    """Verify artifacts were created correctly."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def verify_phase_artifacts(
        self,
        phase: str,
        expected_artifacts: List[str]
    ) -> VerificationResult:
        """Verify artifacts for a phase."""

        results = []
        for artifact_path in expected_artifacts:
            result = self._verify_artifact(artifact_path)
            results.append(result)

        return VerificationResult(
            phase=phase,
            expected_count=len(expected_artifacts),
            found_count=len([r for r in results if r.exists]),
            valid_count=len([r for r in results if r.valid]),
            results=results
        )

    def _verify_artifact(self, path: str) -> ArtifactCheck:
        """Verify single artifact."""
        full_path = self.project_root / path

        check = ArtifactCheck(path=path)

        # File exists?
        check.exists = full_path.exists()
        if not check.exists:
            check.error = "File does not exist"
            return check

        # Not empty?
        check.size = full_path.stat().st_size
        if check.size == 0:
            check.error = "File is empty"
            return check

        # Valid content?
        try:
            content = full_path.read_text()
            check.valid = self._validate_content(path, content)
        except Exception as e:
            check.error = f"Failed to read: {e}"
            return check

        return check

    def _validate_content(self, path: str, content: str) -> bool:
        """Validate content based on file type."""
        suffix = Path(path).suffix

        if suffix == ".py":
            return self._validate_python(content)
        elif suffix in [".ts", ".tsx", ".js", ".jsx"]:
            return self._validate_javascript(content)
        elif suffix == ".md":
            return self._validate_markdown(content)
        elif suffix in [".json", ".yaml", ".yml"]:
            return self._validate_config(content, suffix)

        # Default: non-empty
        return len(content.strip()) > 0
```

### Expected Artifacts by Phase

```python
EXPECTED_ARTIFACTS = {
    "create-prd": [
        "docs/PRD.md"
    ],
    "create-architecture": [
        "docs/ARCHITECTURE.md"
    ],
    "create-story": [
        "docs/stories/epic-1/story-1.1.md",
        # ... more stories
    ],
    "implement-story": [
        "src/**/*.py",  # Glob patterns supported
        "tests/**/*.py",
        "package.json",
        "README.md"
    ]
}
```

---

## Files to Create

**New**:
- `gao_dev/sandbox/artifact_verifier.py` - Main verifier
- `gao_dev/sandbox/models.py` - Add verification models
- `tests/sandbox/test_artifact_verifier.py` - Tests

**Modify**:
- `gao_dev/sandbox/benchmark/orchestrator.py` - Call verifier after phase
- `gao_dev/sandbox/benchmark/config.py` - Add expected_artifacts field

---

## Dependencies

**Requires**:
- Story 7.1-7.3 (Orchestrator, Parser, Commits) - complete
- AST parser for Python validation
- JSON/YAML parsers

**Blocks**:
- None (informational only, doesn't block other stories)

---

## Implementation Steps

1. **Create ArtifactVerifier**
   - File existence checks
   - Content validation
   - Type-specific validation

2. **Add Syntax Validators**
   - Python: `ast.parse()`
   - JavaScript/TypeScript: Basic syntax checks
   - Markdown: Structure validation
   - JSON/YAML: Parse validation

3. **Define Expected Artifacts**
   - Per-phase expectations
   - Support glob patterns
   - Configurable via benchmark config

4. **Integrate with BenchmarkRunner**
   - Run verifier after each phase
   - Log results
   - Include in report
   - Non-blocking warnings

5. **Write Tests**
   - Test each validator
   - Test with valid files
   - Test with invalid files
   - Test reporting

---

## Definition of Done

- [ ] ArtifactVerifier implemented
- [ ] File existence checks working
- [ ] Content validation working
- [ ] Git verification working
- [ ] Integration complete
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Committed with atomic commit

---

**Created by**: Bob (Scrum Master)
**Estimated Completion**: 2-3 hours
