"""Artifact parser for extracting files from agent outputs."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict
import structlog

logger = structlog.get_logger()


@dataclass
class Artifact:
    """Represents a single file artifact extracted from agent output."""

    path: Path
    content: str
    language: Optional[str] = None
    source: str = "agent"  # "agent" or "inferred"

    def __post_init__(self):
        """Ensure path is a Path object."""
        if isinstance(self.path, str):
            self.path = Path(self.path)


class ArtifactParser:
    """
    Parses agent outputs to extract file artifacts.

    Handles various markdown formats:
    - **Save as**: docs/PRD.md
    - **File**: src/app.py
    - ```language # filename.ext
    """

    def __init__(self, project_root: Path):
        """
        Initialize artifact parser.

        Args:
            project_root: Root directory of the project (for path validation)
        """
        self.project_root = Path(project_root).resolve()
        self.logger = logger.bind(component="ArtifactParser")

        # Patterns for detecting file paths in markdown
        self.path_patterns = [
            r'\*\*Save as\*\*:\s*`?([^\s`\n]+)`?',  # **Save as**: docs/PRD.md
            r'\*\*File\*\*:\s*`?([^\s`\n]+)`?',      # **File**: src/app.py
            r'\*\*Path\*\*:\s*`?([^\s`\n]+)`?',      # **Path**: tests/test.py
            r'```[\w]*\s*#\s*([^\s\n]+)',            # ```python # src/app.py
        ]

    def parse_output(self, output: str, phase: str = "unknown") -> List[Artifact]:
        """
        Parse agent output and extract artifacts.

        Args:
            output: Raw agent output (markdown)
            phase: Phase name for context (e.g., "create-prd", "implement-story")

        Returns:
            List of extracted artifacts
        """
        artifacts = []

        self.logger.debug("parsing_agent_output", phase=phase, output_length=len(output))

        # Extract all code blocks with their potential paths
        code_blocks = self._extract_code_blocks(output)
        self.logger.debug("code_blocks_extracted", count=len(code_blocks))

        # Try to match code blocks with file paths
        for block in code_blocks:
            artifact = self._create_artifact_from_block(block, output, phase)
            if artifact:
                artifacts.append(artifact)

        # Also look for explicit file declarations without code blocks
        explicit_artifacts = self._extract_explicit_files(output, phase)
        artifacts.extend(explicit_artifacts)

        self.logger.info(
            "artifacts_parsed",
            phase=phase,
            artifact_count=len(artifacts),
            artifacts=[str(a.path) for a in artifacts],
        )

        return artifacts

    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extract all code blocks from markdown.

        Returns:
            List of dicts with 'language', 'content', 'raw' keys
        """
        code_blocks = []

        # Pattern for markdown code blocks: ```language\ncontent\n```
        pattern = r'```(\w*)\n(.*?)```'

        for match in re.finditer(pattern, text, re.DOTALL):
            language = match.group(1) or "text"
            content = match.group(2).strip()
            raw = match.group(0)

            code_blocks.append({
                "language": language,
                "content": content,
                "raw": raw,
                "start": match.start(),
                "end": match.end(),
            })

        return code_blocks

    def _create_artifact_from_block(
        self, block: Dict[str, str], full_output: str, phase: str
    ) -> Optional[Artifact]:
        """
        Create artifact from a code block by finding its associated path.

        Args:
            block: Code block dict from _extract_code_blocks
            full_output: Full output text for context searching
            phase: Phase name for inference

        Returns:
            Artifact if path found, None otherwise
        """
        # Look for path indicators near this code block
        # Search backward and forward from the block position
        search_start = max(0, block["start"] - 500)
        search_end = min(len(full_output), block["end"] + 200)
        context = full_output[search_start:search_end]

        # Try all path patterns
        for pattern in self.path_patterns:
            matches = re.finditer(pattern, context)
            for match in matches:
                path_str = match.group(1)

                # Validate and normalize path
                if self._is_valid_path(path_str):
                    path = Path(path_str)

                    return Artifact(
                        path=path,
                        content=block["content"],
                        language=block.get("language"),
                        source="agent",
                    )

        # If no path found, try to infer from phase
        inferred_path = self._infer_path_from_phase(phase, block["language"])
        if inferred_path:
            self.logger.debug(
                "inferred_path_from_phase",
                phase=phase,
                path=str(inferred_path),
            )
            return Artifact(
                path=inferred_path,
                content=block["content"],
                language=block.get("language"),
                source="inferred",
            )

        return None

    def _extract_explicit_files(self, text: str, phase: str) -> List[Artifact]:
        """
        Extract files that are explicitly mentioned without code blocks.

        For cases where agent says "create file X with content Y" in prose.
        """
        # This is a simplified implementation
        # Could be extended to handle more complex cases
        return []

    def _infer_path_from_phase(
        self, phase: str, language: Optional[str] = None
    ) -> Optional[Path]:
        """
        Infer file path based on phase name and language.

        Args:
            phase: Phase name (e.g., "create-prd", "create-architecture")
            language: Code block language (e.g., "python", "typescript")

        Returns:
            Inferred path or None
        """
        phase_lower = phase.lower()

        # Phase-specific defaults
        if "prd" in phase_lower or "product requirements" in phase_lower:
            return Path("docs/PRD.md")
        elif "architecture" in phase_lower:
            return Path("docs/ARCHITECTURE.md")
        elif "story" in phase_lower:
            # Would need story number from context
            return None
        elif "implementation" in phase_lower:
            # Too ambiguous without more context
            return None

        return None

    def _is_valid_path(self, path_str: str) -> bool:
        """
        Check if path string is valid and safe.

        Args:
            path_str: Path string to validate

        Returns:
            True if path is valid and safe
        """
        if not path_str:
            return False

        # Reject absolute paths from other drives/roots
        if path_str.startswith('/') or (len(path_str) > 1 and path_str[1] == ':'):
            return False

        # Reject obvious directory traversal
        if '..' in path_str:
            return False

        # Reject paths with suspicious characters
        if any(c in path_str for c in ['*', '?', '<', '>', '|', '\0']):
            return False

        return True

    def validate_path(self, path: Path) -> bool:
        """
        Validate that a path is safe and within project boundaries.

        Args:
            path: Path to validate

        Returns:
            True if path is safe to use
        """
        try:
            # Resolve the path relative to project root
            full_path = (self.project_root / path).resolve()

            # Ensure it's within project root (no directory traversal)
            full_path.relative_to(self.project_root)

            return True
        except (ValueError, OSError):
            return False

    def write_artifacts(self, artifacts: List[Artifact]) -> Dict[str, bool]:
        """
        Write artifacts to disk.

        Args:
            artifacts: List of artifacts to write

        Returns:
            Dict mapping file paths to success status
        """
        results = {}

        for artifact in artifacts:
            try:
                # Validate path
                if not self.validate_path(artifact.path):
                    self.logger.warning(
                        "invalid_artifact_path",
                        path=str(artifact.path),
                        reason="path outside project or invalid",
                    )
                    results[str(artifact.path)] = False
                    continue

                # Create full path
                full_path = self.project_root / artifact.path

                # Create parent directories
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                full_path.write_text(artifact.content, encoding="utf-8")

                self.logger.info(
                    "artifact_written",
                    path=str(artifact.path),
                    size=len(artifact.content),
                )

                results[str(artifact.path)] = True

            except Exception as e:
                self.logger.error(
                    "artifact_write_failed",
                    path=str(artifact.path),
                    error=str(e),
                )
                results[str(artifact.path)] = False

        return results
