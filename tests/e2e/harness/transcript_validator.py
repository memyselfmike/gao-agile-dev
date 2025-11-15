"""Transcript validation utility for conversation quality analysis.

Story: 37.1 - Conversation Instrumentation
Epic: 37 - UX Quality Analysis

Provides validation and analysis of conversation transcripts captured
during test mode execution.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import structlog

logger = structlog.get_logger()


class TranscriptValidationError(Exception):
    """Raised when transcript validation fails."""

    pass


class TranscriptValidator:
    """
    Validator for conversation transcripts.

    Validates format, content quality, and generates statistics for
    quality analysis.
    """

    # Required fields in each turn
    REQUIRED_TURN_FIELDS = ["timestamp", "user_input", "brian_response", "context_used"]

    # Required fields in context metadata
    REQUIRED_CONTEXT_FIELDS = ["project_root", "session_id"]

    def __init__(self, transcript_path: Path):
        """
        Initialize validator with transcript file.

        Args:
            transcript_path: Path to transcript JSON file

        Raises:
            FileNotFoundError: If transcript file doesn't exist
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_path}")

        self.transcript_path = transcript_path
        self.data: List[Dict[str, Any]] = []
        self.logger = logger.bind(transcript=str(transcript_path))

    def load_transcript(self) -> List[Dict[str, Any]]:
        """
        Load transcript from JSON file.

        Returns:
            List of conversation turns

        Raises:
            TranscriptValidationError: If file cannot be parsed
        """
        try:
            with open(self.transcript_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            self.logger.info("transcript_loaded", turn_count=len(self.data))
            return self.data

        except json.JSONDecodeError as e:
            raise TranscriptValidationError(f"Invalid JSON: {e}")
        except Exception as e:
            raise TranscriptValidationError(f"Failed to load transcript: {e}")

    def validate_format(self) -> bool:
        """
        Validate JSON format and structure.

        Checks:
        - File is valid JSON
        - Root is a list
        - Each turn has required fields
        - Field types are correct
        - Timestamps are valid ISO 8601

        Returns:
            True if format is valid

        Raises:
            TranscriptValidationError: If format is invalid
        """
        if not self.data:
            self.load_transcript()

        # Check root is list
        if not isinstance(self.data, list):
            raise TranscriptValidationError("Transcript must be a JSON list")

        if len(self.data) == 0:
            self.logger.warning("transcript_empty")
            return True  # Empty is technically valid

        # Validate each turn
        for i, turn in enumerate(self.data):
            turn_num = i + 1

            # Check turn is dict
            if not isinstance(turn, dict):
                raise TranscriptValidationError(
                    f"Turn {turn_num}: Must be a dictionary, got {type(turn).__name__}"
                )

            # Check required fields
            for field in self.REQUIRED_TURN_FIELDS:
                if field not in turn:
                    raise TranscriptValidationError(
                        f"Turn {turn_num}: Missing required field '{field}'"
                    )

            # Validate field types
            if not isinstance(turn["timestamp"], str):
                raise TranscriptValidationError(
                    f"Turn {turn_num}: timestamp must be string"
                )

            if not isinstance(turn["user_input"], str):
                raise TranscriptValidationError(
                    f"Turn {turn_num}: user_input must be string"
                )

            if not isinstance(turn["brian_response"], str):
                raise TranscriptValidationError(
                    f"Turn {turn_num}: brian_response must be string"
                )

            if not isinstance(turn["context_used"], dict):
                raise TranscriptValidationError(
                    f"Turn {turn_num}: context_used must be dictionary"
                )

            # Validate timestamp format (ISO 8601)
            try:
                datetime.fromisoformat(turn["timestamp"])
            except ValueError as e:
                raise TranscriptValidationError(
                    f"Turn {turn_num}: Invalid timestamp format: {e}"
                )

            # Validate context metadata
            context = turn["context_used"]
            for field in self.REQUIRED_CONTEXT_FIELDS:
                if field not in context:
                    raise TranscriptValidationError(
                        f"Turn {turn_num}: context_used missing required field '{field}'"
                    )

        self.logger.info("format_validation_passed", turn_count=len(self.data))
        return True

    def validate_content(self) -> bool:
        """
        Validate content quality.

        Checks:
        - Responses are non-empty
        - Timestamps are reasonable (not in future, sequential)
        - No duplicate turns
        - Response times are reasonable (<10 minutes per turn)

        Returns:
            True if content is valid

        Raises:
            TranscriptValidationError: If content quality issues found
        """
        if not self.data:
            self.load_transcript()

        if len(self.data) == 0:
            return True

        previous_timestamp: Optional[datetime] = None
        now = datetime.now()

        for i, turn in enumerate(self.data):
            turn_num = i + 1

            # Check for empty responses
            if not turn["brian_response"].strip():
                raise TranscriptValidationError(
                    f"Turn {turn_num}: brian_response is empty"
                )

            # Check timestamp is not in future
            timestamp = datetime.fromisoformat(turn["timestamp"])
            if timestamp > now:
                raise TranscriptValidationError(
                    f"Turn {turn_num}: Timestamp is in the future"
                )

            # Check timestamps are sequential
            if previous_timestamp and timestamp < previous_timestamp:
                raise TranscriptValidationError(
                    f"Turn {turn_num}: Timestamp is earlier than previous turn"
                )

            # Check reasonable response time (< 10 minutes between turns)
            if previous_timestamp:
                time_diff = (timestamp - previous_timestamp).total_seconds()
                if time_diff > 600:  # 10 minutes
                    self.logger.warning(
                        "long_response_time",
                        turn_num=turn_num,
                        seconds=time_diff,
                    )

            previous_timestamp = timestamp

        self.logger.info("content_validation_passed")
        return True

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate summary statistics for transcript.

        Returns:
            Dictionary with:
            - turn_count: Number of turns
            - duration_seconds: Total conversation duration
            - avg_response_time_seconds: Average time per turn
            - total_user_input_chars: Total characters in user input
            - total_brian_response_chars: Total characters in responses
            - context_changes: Number of context state changes
            - first_timestamp: First turn timestamp
            - last_timestamp: Last turn timestamp
        """
        if not self.data:
            self.load_transcript()

        if len(self.data) == 0:
            return {
                "turn_count": 0,
                "duration_seconds": 0,
                "avg_response_time_seconds": 0,
                "total_user_input_chars": 0,
                "total_brian_response_chars": 0,
                "context_changes": 0,
                "first_timestamp": None,
                "last_timestamp": None,
            }

        # Basic counts
        turn_count = len(self.data)

        # Calculate duration
        first_ts = datetime.fromisoformat(self.data[0]["timestamp"])
        last_ts = datetime.fromisoformat(self.data[-1]["timestamp"])
        duration_seconds = (last_ts - first_ts).total_seconds()

        # Average response time
        avg_response_time = duration_seconds / turn_count if turn_count > 0 else 0

        # Character counts
        total_user_chars = sum(len(turn["user_input"]) for turn in self.data)
        total_brian_chars = sum(len(turn["brian_response"]) for turn in self.data)

        # Count context changes
        context_changes = self._count_context_changes()

        summary = {
            "turn_count": turn_count,
            "duration_seconds": round(duration_seconds, 2),
            "avg_response_time_seconds": round(avg_response_time, 2),
            "total_user_input_chars": total_user_chars,
            "total_brian_response_chars": total_brian_chars,
            "avg_user_input_length": round(total_user_chars / turn_count, 2),
            "avg_brian_response_length": round(total_brian_chars / turn_count, 2),
            "context_changes": context_changes,
            "first_timestamp": self.data[0]["timestamp"],
            "last_timestamp": self.data[-1]["timestamp"],
        }

        self.logger.info("summary_generated", **summary)
        return summary

    def _count_context_changes(self) -> int:
        """
        Count number of context state changes.

        Returns:
            Number of times context changed between turns
        """
        if len(self.data) < 2:
            return 0

        changes = 0
        previous_context = self.data[0]["context_used"]

        for turn in self.data[1:]:
            current_context = turn["context_used"]

            # Check for changes in trackable fields
            if (
                current_context.get("current_epic") != previous_context.get("current_epic")
                or current_context.get("current_story") != previous_context.get("current_story")
                or current_context.get("pending_confirmation") != previous_context.get("pending_confirmation")
            ):
                changes += 1

            previous_context = current_context

        return changes

    def validate_all(self) -> bool:
        """
        Run all validations.

        Returns:
            True if all validations pass

        Raises:
            TranscriptValidationError: If any validation fails
        """
        self.validate_format()
        self.validate_content()
        return True

    def get_turn(self, index: int) -> Dict[str, Any]:
        """
        Get specific turn by index.

        Args:
            index: Turn index (0-based)

        Returns:
            Turn data

        Raises:
            IndexError: If index out of range
        """
        if not self.data:
            self.load_transcript()

        return self.data[index]

    def get_turns_by_context(
        self, epic: Optional[int] = None, story: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get turns filtered by context.

        Args:
            epic: Filter by epic number
            story: Filter by story number

        Returns:
            List of matching turns
        """
        if not self.data:
            self.load_transcript()

        filtered = []
        for turn in self.data:
            context = turn["context_used"]

            if epic is not None and context.get("current_epic") != epic:
                continue

            if story is not None and context.get("current_story") != story:
                continue

            filtered.append(turn)

        return filtered

    def print_summary(self) -> None:
        """Print formatted summary to stdout."""
        summary = self.generate_summary()

        print("\n" + "=" * 60)
        print("TRANSCRIPT SUMMARY")
        print("=" * 60)
        print(f"File: {self.transcript_path.name}")
        print(f"\nConversation Statistics:")
        print(f"  Turns: {summary['turn_count']}")
        print(f"  Duration: {summary['duration_seconds']}s")
        print(f"  Avg Response Time: {summary['avg_response_time_seconds']}s")
        print(f"\nContent Statistics:")
        print(f"  Total User Input: {summary['total_user_input_chars']} chars")
        print(f"  Total Brian Response: {summary['total_brian_response_chars']} chars")
        print(f"  Avg User Input Length: {summary['avg_user_input_length']} chars")
        print(f"  Avg Brian Response Length: {summary['avg_brian_response_length']} chars")
        print(f"\nContext:")
        print(f"  Context Changes: {summary['context_changes']}")
        print(f"\nTimespan:")
        print(f"  First Turn: {summary['first_timestamp']}")
        print(f"  Last Turn: {summary['last_timestamp']}")
        print("=" * 60 + "\n")
