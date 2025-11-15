"""Output matcher for E2E test validation.

Story: 36.4 - Fixture System
Epic: 36 - Test Infrastructure

Validates subprocess output against expected patterns with ANSI stripping and diff generation.
"""

import re
import difflib
from typing import List, Dict, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class MatchResult:
    """
    Output pattern matching result.

    Attributes:
        success: True if all patterns matched
        matches: List of match details per pattern
        actual_output: Clean output (ANSI stripped)

    Example:
        >>> result = MatchResult(
        ...     success=True,
        ...     matches=[{"pattern": "hello", "matched": True, "match_text": "hello"}],
        ...     actual_output="hello world"
        ... )
    """

    success: bool
    matches: List[Dict[str, Any]]
    actual_output: str

    def get_failed_patterns(self) -> List[str]:
        """
        Get list of patterns that didn't match.

        Returns:
            List of failed pattern strings
        """
        return [m["pattern"] for m in self.matches if not m["matched"]]

    def get_matched_patterns(self) -> List[str]:
        """
        Get list of patterns that matched.

        Returns:
            List of matched pattern strings
        """
        return [m["pattern"] for m in self.matches if m["matched"]]


class OutputMatcher:
    """
    Match output against expected patterns with ANSI stripping.

    Provides pattern matching with regex support, ANSI code stripping,
    and helpful diff generation for failed matches.

    Example:
        >>> matcher = OutputMatcher()
        >>> result = matcher.match("\\x1b[32mHello\\x1b[0m", ["Hello"])
        >>> assert result.success
    """

    def __init__(self):
        """
        Initialize OutputMatcher.

        Compiles ANSI escape regex for efficient stripping.
        """
        # ANSI escape code pattern (matches all escape sequences)
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self.logger = logger.bind(component="output_matcher")

        self.logger.debug("output_matcher_initialized")

    def strip_ansi(self, text: str) -> str:
        """
        Remove ANSI escape codes from text.

        Strips all ANSI escape sequences including colors, cursor movement,
        and formatting codes.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Clean text without ANSI codes

        Example:
            >>> matcher = OutputMatcher()
            >>> clean = matcher.strip_ansi("\\x1b[32mGreen\\x1b[0m text")
            >>> assert clean == "Green text"
        """
        if not text:
            return text

        clean = self.ansi_escape.sub('', text)

        self.logger.debug(
            "ansi_stripped",
            original_length=len(text),
            clean_length=len(clean),
            ansi_codes_removed=len(text) - len(clean),
        )

        return clean

    def match(
        self,
        actual: str,
        expected_patterns: List[str],
        strict: bool = False,
    ) -> MatchResult:
        """
        Match actual output against expected patterns.

        Strips ANSI codes before matching. Each pattern is treated as a
        regex pattern with DOTALL and MULTILINE flags.

        Args:
            actual: Actual output from subprocess (may contain ANSI)
            expected_patterns: List of regex patterns to match
            strict: If True, all patterns must match in order (not implemented)

        Returns:
            MatchResult with success flag and match details

        Example:
            >>> matcher = OutputMatcher()
            >>> result = matcher.match(
            ...     "Scale Level: 4\\nType: greenfield",
            ...     [r"Scale Level.*4", r"greenfield"]
            ... )
            >>> assert result.success
        """
        if not expected_patterns:
            # No patterns to match - always succeeds
            return MatchResult(
                success=True,
                matches=[],
                actual_output=self.strip_ansi(actual),
            )

        # Strip ANSI codes for clean matching
        clean_actual = self.strip_ansi(actual)

        self.logger.debug(
            "matching_patterns",
            pattern_count=len(expected_patterns),
            output_length=len(clean_actual),
        )

        # Match each pattern
        matches = []
        for pattern in expected_patterns:
            try:
                match = re.search(pattern, clean_actual, re.DOTALL | re.MULTILINE)
                matched = match is not None

                match_detail = {
                    "pattern": pattern,
                    "matched": matched,
                    "match_text": match.group(0) if match else None,
                    "match_start": match.start() if match else None,
                    "match_end": match.end() if match else None,
                }
                matches.append(match_detail)

                if matched:
                    self.logger.debug(
                        "pattern_matched",
                        pattern=pattern,
                        match_text=match.group(0)[:100],
                    )
                else:
                    self.logger.warning(
                        "pattern_not_matched",
                        pattern=pattern,
                        output_preview=clean_actual[:200],
                    )

            except re.error as e:
                # Invalid regex pattern
                self.logger.error(
                    "invalid_regex_pattern",
                    pattern=pattern,
                    error=str(e),
                )
                matches.append({
                    "pattern": pattern,
                    "matched": False,
                    "match_text": None,
                    "error": str(e),
                })

        # Check if all matched
        all_matched = all(m["matched"] for m in matches)

        result = MatchResult(
            success=all_matched,
            matches=matches,
            actual_output=clean_actual,
        )

        self.logger.info(
            "match_complete",
            success=all_matched,
            matched_count=len([m for m in matches if m["matched"]]),
            total_patterns=len(expected_patterns),
        )

        return result

    def diff(self, actual: str, expected: str) -> str:
        """
        Generate diff between actual and expected output.

        Strips ANSI codes from actual output before comparison.
        Generates unified diff with 3 lines of context.

        Args:
            actual: Actual output (may contain ANSI codes)
            expected: Expected output (plain text)

        Returns:
            Unified diff string (empty if identical)

        Example:
            >>> matcher = OutputMatcher()
            >>> diff = matcher.diff("Hello World", "Hello Universe")
            >>> assert "- Hello Universe" in diff
            >>> assert "+ Hello World" in diff
        """
        clean_actual = self.strip_ansi(actual)

        self.logger.debug(
            "generating_diff",
            actual_length=len(clean_actual),
            expected_length=len(expected),
        )

        # Generate unified diff
        diff_lines = difflib.unified_diff(
            expected.splitlines(keepends=True),
            clean_actual.splitlines(keepends=True),
            fromfile="expected",
            tofile="actual",
            lineterm="",
            n=3,  # 3 lines of context
        )

        diff_text = ''.join(diff_lines)

        if diff_text:
            self.logger.info(
                "diff_generated",
                diff_lines=len(diff_text.splitlines()),
            )
        else:
            self.logger.debug("outputs_identical")

        return diff_text

    def assert_match(
        self,
        actual: str,
        expected_patterns: List[str],
        message: str = "",
    ) -> None:
        """
        Assert that actual output matches expected patterns.

        Convenience method that raises AssertionError with helpful message
        if patterns don't match.

        Args:
            actual: Actual output
            expected_patterns: Expected regex patterns
            message: Optional custom error message prefix

        Raises:
            AssertionError: If patterns don't match

        Example:
            >>> matcher = OutputMatcher()
            >>> matcher.assert_match("Hello World", ["Hello"])
        """
        result = self.match(actual, expected_patterns)

        if not result.success:
            failed = result.get_failed_patterns()
            error_msg = f"{message}\n" if message else ""
            error_msg += f"Failed to match {len(failed)} pattern(s):\n"

            for pattern in failed:
                error_msg += f"  - {pattern}\n"

            error_msg += f"\nActual output (first 500 chars):\n{result.actual_output[:500]}"

            self.logger.error(
                "assertion_failed",
                failed_patterns=failed,
                message=message,
            )

            raise AssertionError(error_msg)

        self.logger.debug("assertion_passed", pattern_count=len(expected_patterns))
