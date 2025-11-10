"""Intent parsing for conversational input."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import re


class IntentType(Enum):
    """Types of user intents."""

    FEATURE_REQUEST = "feature_request"
    CONFIRMATION = "confirmation"
    QUESTION = "question"
    HELP = "help"
    UNCLEAR = "unclear"


@dataclass
class Intent:
    """
    Parsed user intent.

    Attributes:
        type: Type of intent
        is_positive: For confirmations, whether yes or no
        entities: Extracted entities (epic numbers, story IDs, etc.)
    """

    type: IntentType
    is_positive: Optional[bool] = None
    entities: Dict[str, Any] = field(default_factory=dict)


class IntentParser:
    """
    Parse user input to detect intent.

    Uses simple pattern matching and keyword detection.
    Future: Could use NLP models for better accuracy.
    """

    def __init__(self) -> None:
        """Initialize parser with patterns."""
        self._confirmation_patterns = [
            r"\b(yes|yeah|yep|sure|ok|okay|proceed|go ahead)\b",
            r"\b(no|nope|nah|cancel|abort|stop)\b",
        ]

        self._feature_request_patterns = [
            r"\b(build|create|add|implement|make|develop)\b",
            r"\b(want|need|like)\s+(to\s+)?(build|create|add)",
            r"\b(fix|repair|debug)\b",
        ]

        self._question_patterns = [
            r"\b(what|how|why|when|where|who)\b",
            r"\b(status|progress|current)\b",
            r"\?$",
        ]

    def parse(self, user_input: str) -> Intent:
        """
        Parse user input to detect intent.

        Args:
            user_input: User's message

        Returns:
            Parsed Intent
        """
        user_lower = user_input.lower().strip()

        # Check for help
        if self._is_help_request(user_lower):
            return Intent(type=IntentType.HELP)

        # Check for confirmation
        confirmation = self._parse_confirmation(user_lower)
        if confirmation:
            return confirmation

        # Check for question
        if self._is_question(user_lower):
            return Intent(type=IntentType.QUESTION)

        # Check for feature request
        if self._is_feature_request(user_lower):
            return Intent(type=IntentType.FEATURE_REQUEST)

        # Default to unclear
        return Intent(type=IntentType.UNCLEAR)

    def _is_help_request(self, text: str) -> bool:
        """Check if input is help request."""
        return text in ["help", "?", "what can you do"]

    def _parse_confirmation(self, text: str) -> Optional[Intent]:
        """Parse confirmation (yes/no)."""
        # Check positive confirmation
        if re.search(self._confirmation_patterns[0], text, re.IGNORECASE):
            return Intent(type=IntentType.CONFIRMATION, is_positive=True)

        # Check negative confirmation
        if re.search(self._confirmation_patterns[1], text, re.IGNORECASE):
            return Intent(type=IntentType.CONFIRMATION, is_positive=False)

        return None

    def _is_question(self, text: str) -> bool:
        """Check if input is a question."""
        for pattern in self._question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_feature_request(self, text: str) -> bool:
        """Check if input is a feature request."""
        for pattern in self._feature_request_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
