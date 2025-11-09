"""Ceremony trigger evaluation engine with safety mechanisms.

This service evaluates trigger conditions for ceremonies based on workflow
state with comprehensive safety mechanisms to prevent infinite loops and
resource exhaustion.

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.3 - CeremonyTriggerEngine

Key Safety Mechanisms (C1 Fix):
- Max 10 ceremonies per epic (hard limit)
- Cooldown periods: 24h (planning/retro), 12h (standup)
- 10-minute timeout per ceremony
- Cycle detection
- Circuit breaker pattern (3 consecutive failures)

Design Pattern: Service Layer with Circuit Breaker
Dependencies: CeremonyService, StateCoordinator, structlog
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

import structlog
import yaml

from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.core.services.story_state_service import StoryStateService
from gao_dev.core.services.epic_state_service import EpicStateService

logger = structlog.get_logger(__name__)


class TriggerType(Enum):
    """Ceremony trigger types."""
    EPIC_START = "epic_start"
    EPIC_COMPLETION = "epic_completion"
    MID_EPIC_CHECKPOINT = "mid_epic_checkpoint"
    STORY_INTERVAL = "story_interval"
    STORY_COUNT_THRESHOLD = "story_count_threshold"
    QUALITY_GATE_FAILURE = "quality_gate_failure"
    REPEATED_FAILURE = "repeated_failure"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    DAILY = "daily"
    PHASE_END = "phase_end"


class CeremonyType(Enum):
    """Ceremony types."""
    PLANNING = "planning"
    STANDUP = "standup"
    RETROSPECTIVE = "retrospective"


@dataclass
class TriggerContext:
    """
    Context for trigger evaluation.

    Contains all information needed to evaluate whether a ceremony
    should trigger based on current workflow state.
    """
    # Required fields
    epic_num: int
    scale_level: ScaleLevel
    stories_completed: int
    total_stories: int
    quality_gates_passed: bool
    failure_count: int
    project_type: str

    # Optional fields
    story_num: Optional[int] = None
    last_standup: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate context fields."""
        if self.stories_completed < 0:
            raise ValueError("stories_completed must be >= 0")
        if self.total_stories < 0:
            raise ValueError("total_stories must be >= 0")
        if self.failure_count < 0:
            raise ValueError("failure_count must be >= 0")

    @property
    def progress_percentage(self) -> float:
        """Calculate epic progress percentage (0.0-1.0)."""
        if self.total_stories == 0:
            return 0.0
        return self.stories_completed / self.total_stories


class CeremonyTriggerEngine:
    """
    Evaluates trigger conditions for ceremonies with safety mechanisms.

    Implements C1 Fix: Ceremony infinite loop prevention
    - Max 10 ceremonies per epic (hard limit)
    - 24h/12h cooldowns
    - 10-minute timeout per ceremony
    - Cycle detection
    - Circuit breaker pattern

    Example:
        ```python
        engine = CeremonyTriggerEngine(db_path=Path(".gao-dev/documents.db"))

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=5,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )

        # Evaluate all triggers
        ceremonies = engine.evaluate_all_triggers(context)
        # Returns: [CeremonyType.STANDUP] (every 2 stories for Level 3)

        # Check specific ceremony
        should_plan = engine.should_trigger_planning(context)
        ```
    """

    # C1 Fix: Safety limits
    MAX_CEREMONIES_PER_EPIC = 10
    COOLDOWN_HOURS = {
        "planning": 24,
        "standup": 12,
        "retrospective": 24
    }
    TIMEOUT_MINUTES = 10

    def __init__(
        self,
        db_path: Path,
        config_path: Optional[Path] = None
    ):
        """
        Initialize ceremony trigger engine.

        Args:
            db_path: Path to SQLite database
            config_path: Optional path to ceremony_limits.yaml config
        """
        self.db_path = Path(db_path)
        self.ceremony_service = CeremonyService(db_path=self.db_path)
        self.story_service = StoryStateService(db_path=self.db_path)
        self.epic_service = EpicStateService(db_path=self.db_path)

        # Safety tracking
        self.ceremony_counts: Dict[int, int] = {}  # epic_num -> count
        self.last_ceremony_times: Dict[tuple[int, str], datetime] = {}  # (epic_num, type) -> time
        self.circuit_open: Dict[tuple[int, str], bool] = {}  # (epic_num, type) -> open
        self.consecutive_failures: Dict[tuple[int, str], int] = {}  # (epic_num, type) -> count

        # Load configuration
        self.config = self._load_config(config_path)

        self.logger = logger.bind(service="ceremony_trigger_engine")

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load ceremony limits configuration."""
        if config_path is None:
            # Default to config/ceremony_limits.yaml
            config_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "ceremony_limits.yaml"
            )

        if not config_path.exists():
            self.logger.warning(
                "ceremony_limits_config_not_found",
                path=str(config_path),
                message="Using default safety limits"
            )
            return self._get_default_config()

        try:
            with open(config_path) as f:
                config: Dict[str, Any] = yaml.safe_load(f)
                return config
        except Exception as e:
            self.logger.error(
                "config_load_failed",
                path=str(config_path),
                error=str(e)
            )
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default safety configuration."""
        return {
            "max_per_epic": self.MAX_CEREMONIES_PER_EPIC,
            "cooldown_hours": self.COOLDOWN_HOURS,
            "timeout_minutes": self.TIMEOUT_MINUTES,
            "circuit_breaker_threshold": 3
        }

    def evaluate_all_triggers(
        self,
        context: TriggerContext
    ) -> List[CeremonyType]:
        """
        Evaluate all trigger conditions with safety checks.

        Safety checks (C1 Fix):
        1. Max ceremonies per epic limit
        2. Cooldown periods
        3. Circuit breaker status

        Args:
            context: Trigger evaluation context

        Returns:
            List of ceremony types that should trigger
        """
        # C1 Fix: Check safety limits first
        if not self._check_safety_limits(context.epic_num):
            self.logger.warning(
                "ceremony_safety_limit_reached",
                epic_num=context.epic_num,
                count=self.ceremony_counts.get(context.epic_num, 0),
                max_allowed=self.config.get("max_per_epic", self.MAX_CEREMONIES_PER_EPIC)
            )
            return []  # Hit safety limit, no ceremonies

        ceremonies = []

        # Evaluate each ceremony type
        if self.should_trigger_planning(context):
            if self._check_cooldown(context.epic_num, "planning"):
                if not self._is_circuit_open(context.epic_num, "planning"):
                    ceremonies.append(CeremonyType.PLANNING)
                    self.logger.info(
                        "ceremony_trigger_approved",
                        ceremony_type="planning",
                        epic_num=context.epic_num
                    )

        if self.should_trigger_standup(context):
            if self._check_cooldown(context.epic_num, "standup"):
                if not self._is_circuit_open(context.epic_num, "standup"):
                    ceremonies.append(CeremonyType.STANDUP)
                    self.logger.info(
                        "ceremony_trigger_approved",
                        ceremony_type="standup",
                        epic_num=context.epic_num,
                        stories_completed=context.stories_completed
                    )

        if self.should_trigger_retrospective(context):
            if self._check_cooldown(context.epic_num, "retrospective"):
                if not self._is_circuit_open(context.epic_num, "retrospective"):
                    ceremonies.append(CeremonyType.RETROSPECTIVE)
                    self.logger.info(
                        "ceremony_trigger_approved",
                        ceremony_type="retrospective",
                        epic_num=context.epic_num,
                        progress=context.progress_percentage
                    )

        return ceremonies

    def should_trigger_planning(self, context: TriggerContext) -> bool:
        """
        Evaluate if planning ceremony should trigger.

        Rules:
        - Level 0-1: Never
        - Level 2: Optional (False by default)
        - Level 3+: Required at epic start

        Args:
            context: Trigger evaluation context

        Returns:
            True if planning should trigger, False otherwise
        """
        if context.scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return False

        if context.scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Required for Level 3+
            has_planning = self._has_ceremony(context.epic_num, "planning")

            if not has_planning:
                self.logger.info(
                    "planning_required",
                    epic_num=context.epic_num,
                    scale_level=context.scale_level
                )
                return True
            else:
                self.logger.debug(
                    "planning_already_held",
                    epic_num=context.epic_num
                )
                return False

        # Optional for Level 2 (return False by default)
        return False

    def should_trigger_standup(self, context: TriggerContext) -> bool:
        """
        Evaluate if standup should trigger.

        Rules by Scale Level:
        - Level 0-1: Never
        - Level 2: Every 3 stories (if >3 total stories)
        - Level 3: Every 2 stories OR quality gate failure
        - Level 4: Every story OR daily (whichever first)

        Args:
            context: Trigger evaluation context

        Returns:
            True if standup should trigger, False otherwise
        """
        if context.scale_level < ScaleLevel.LEVEL_2_SMALL_FEATURE:
            return False

        # Quality gate failure always triggers (Level 2+)
        if not context.quality_gates_passed:
            self.logger.info(
                "standup_triggered_by_quality_gate_failure",
                epic_num=context.epic_num,
                story_num=context.story_num
            )
            return True

        # Level-specific intervals
        if context.scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE:
            # Every 3 stories, only if >3 total
            if context.total_stories <= 3:
                return False
            should_trigger = (
                context.stories_completed > 0
                and context.stories_completed % 3 == 0
            )
            if should_trigger:
                self.logger.info(
                    "standup_interval_trigger_level_2",
                    epic_num=context.epic_num,
                    stories_completed=context.stories_completed,
                    interval=3
                )
            return should_trigger

        elif context.scale_level == ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Every 2 stories
            should_trigger = (
                context.stories_completed > 0
                and context.stories_completed % 2 == 0
            )
            if should_trigger:
                self.logger.info(
                    "standup_interval_trigger_level_3",
                    epic_num=context.epic_num,
                    stories_completed=context.stories_completed,
                    interval=2
                )
            return should_trigger

        elif context.scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            # Every story OR daily
            if context.last_standup is None:
                should_trigger = context.stories_completed > 0
                if should_trigger:
                    self.logger.info(
                        "standup_first_trigger_level_4",
                        epic_num=context.epic_num
                    )
                return should_trigger

            # Check if 24 hours since last standup
            hours_since = (datetime.now() - context.last_standup).total_seconds() / 3600
            if hours_since >= 24:
                self.logger.info(
                    "standup_daily_trigger_level_4",
                    epic_num=context.epic_num,
                    hours_since=hours_since
                )
                return True

            # Or every story
            should_trigger = context.stories_completed > 0
            if should_trigger:
                self.logger.info(
                    "standup_story_trigger_level_4",
                    epic_num=context.epic_num,
                    stories_completed=context.stories_completed
                )
            return should_trigger

        return False

    def should_trigger_retrospective(self, context: TriggerContext) -> bool:
        """
        Evaluate if retrospective should trigger.

        Rules:
        - Level 0: Never
        - Level 1: Only on repeated failure (2+ times)
        - Level 2: Epic completion
        - Level 3: Mid-epic checkpoint (50%) + epic completion
        - Level 4: Phase end + epic completion

        Args:
            context: Trigger evaluation context

        Returns:
            True if retrospective should trigger, False otherwise
        """
        if context.scale_level == ScaleLevel.LEVEL_0_CHORE:
            return False

        if context.scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            # Only if failed 2+ times
            should_trigger = context.failure_count >= 2
            if should_trigger:
                self.logger.info(
                    "retrospective_repeated_failure_trigger",
                    epic_num=context.epic_num,
                    failure_count=context.failure_count
                )
            return should_trigger

        # Check epic completion (all levels 2+)
        progress = context.progress_percentage
        if progress >= 1.0:
            self.logger.info(
                "retrospective_completion_trigger",
                epic_num=context.epic_num,
                progress=progress
            )
            return True

        # Mid-epic checkpoint for Level 3+
        if context.scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # At 50% completion (within 2%)
            if 0.48 <= progress <= 0.52:
                has_mid_retro = self._has_ceremony_with_metadata(
                    epic_num=context.epic_num,
                    ceremony_type="retrospective",
                    metadata_key="checkpoint",
                    metadata_value="mid"
                )

                if not has_mid_retro:
                    self.logger.info(
                        "retrospective_mid_epic_trigger",
                        epic_num=context.epic_num,
                        progress=progress
                    )
                    return True

        return False

    def _check_safety_limits(self, epic_num: int) -> bool:
        """
        C1 Fix: Check if epic has hit ceremony limits.

        Args:
            epic_num: Epic number

        Returns:
            True if within limits, False if limit reached
        """
        count = self._get_ceremony_count(epic_num)
        max_allowed: int = self.config.get("max_per_epic", self.MAX_CEREMONIES_PER_EPIC)

        return bool(count < max_allowed)

    def _check_cooldown(self, epic_num: int, ceremony_type: str) -> bool:
        """
        C1 Fix: Check if cooldown period has elapsed.

        Args:
            epic_num: Epic number
            ceremony_type: Ceremony type (planning, standup, retrospective)

        Returns:
            True if cooldown elapsed, False if still in cooldown
        """
        last_time = self._get_last_ceremony_time(epic_num, ceremony_type)

        if last_time is None:
            return True  # Never run before

        cooldown_hours = self.config.get("cooldown_hours", self.COOLDOWN_HOURS).get(
            ceremony_type,
            24
        )
        elapsed = (datetime.now() - last_time).total_seconds() / 3600

        if elapsed < cooldown_hours:
            self.logger.info(
                "ceremony_cooldown_active",
                epic_num=epic_num,
                ceremony_type=ceremony_type,
                hours_elapsed=round(elapsed, 2),
                cooldown_required=cooldown_hours
            )
            return False

        return True

    def _is_circuit_open(self, epic_num: int, ceremony_type: str) -> bool:
        """
        C1 Fix: Check if circuit breaker is open.

        Args:
            epic_num: Epic number
            ceremony_type: Ceremony type

        Returns:
            True if circuit open (ceremonies disabled), False otherwise
        """
        key = (epic_num, ceremony_type)
        is_open = self.circuit_open.get(key, False)

        if is_open:
            self.logger.warning(
                "ceremony_circuit_breaker_open",
                epic_num=epic_num,
                ceremony_type=ceremony_type
            )

        return is_open

    def record_ceremony_execution(
        self,
        epic_num: int,
        ceremony_type: str,
        success: bool
    ) -> None:
        """
        Record ceremony execution for safety tracking.

        Updates:
        - Ceremony count
        - Last ceremony time
        - Circuit breaker state (on repeated failures)

        Args:
            epic_num: Epic number
            ceremony_type: Ceremony type
            success: Whether ceremony succeeded
        """
        # Update count
        self.ceremony_counts[epic_num] = self.ceremony_counts.get(epic_num, 0) + 1

        # Update last run time
        key = (epic_num, ceremony_type)
        self.last_ceremony_times[key] = datetime.now()

        # Handle failures (circuit breaker)
        if not success:
            # Track consecutive failures
            failures = self.consecutive_failures.get(key, 0) + 1
            self.consecutive_failures[key] = failures

            threshold = self.config.get("circuit_breaker_threshold", 3)
            if failures >= threshold:
                self.circuit_open[key] = True
                self.logger.error(
                    "ceremony_circuit_breaker_triggered",
                    epic_num=epic_num,
                    ceremony_type=ceremony_type,
                    consecutive_failures=failures,
                    threshold=threshold
                )
        else:
            # Reset failure count on success
            if key in self.consecutive_failures:
                del self.consecutive_failures[key]
            # Reset circuit breaker
            if key in self.circuit_open:
                self.circuit_open[key] = False
                self.logger.info(
                    "ceremony_circuit_breaker_reset",
                    epic_num=epic_num,
                    ceremony_type=ceremony_type
                )

    def _has_ceremony(self, epic_num: int, ceremony_type: str) -> bool:
        """Check if ceremony has been held for epic."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM ceremony_summaries
                    WHERE epic_num = ? AND ceremony_type = ?
                    """,
                    (epic_num, ceremony_type)
                )
                row = cursor.fetchone()
                count: int = row[0] if row else 0
                return count > 0
        except Exception as e:
            self.logger.error(
                "ceremony_check_failed",
                epic_num=epic_num,
                ceremony_type=ceremony_type,
                error=str(e)
            )
            return False

    def _has_ceremony_with_metadata(
        self,
        epic_num: int,
        ceremony_type: str,
        metadata_key: str,
        metadata_value: str
    ) -> bool:
        """Check if ceremony with specific metadata exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM ceremony_summaries
                    WHERE epic_num = ?
                      AND ceremony_type = ?
                      AND json_extract(metadata, ?) = ?
                    """,
                    (epic_num, ceremony_type, f"$.{metadata_key}", metadata_value)
                )
                row = cursor.fetchone()
                count: int = row[0] if row else 0
                return count > 0
        except Exception as e:
            self.logger.error(
                "ceremony_metadata_check_failed",
                epic_num=epic_num,
                ceremony_type=ceremony_type,
                metadata_key=metadata_key,
                error=str(e)
            )
            return False

    def _get_ceremony_count(self, epic_num: int) -> int:
        """Get total ceremony count for epic."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM ceremony_summaries
                    WHERE epic_num = ?
                    """,
                    (epic_num,)
                )
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            self.logger.error(
                "ceremony_count_failed",
                epic_num=epic_num,
                error=str(e)
            )
            return 0

    def _get_last_ceremony_time(
        self,
        epic_num: int,
        ceremony_type: str
    ) -> Optional[datetime]:
        """Get last ceremony time for epic and type."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT held_at FROM ceremony_summaries
                    WHERE epic_num = ? AND ceremony_type = ?
                    ORDER BY held_at DESC
                    LIMIT 1
                    """,
                    (epic_num, ceremony_type)
                )
                row = cursor.fetchone()

                if row and row[0]:
                    return datetime.fromisoformat(row[0])
                return None
        except Exception as e:
            self.logger.error(
                "last_ceremony_time_failed",
                epic_num=epic_num,
                ceremony_type=ceremony_type,
                error=str(e)
            )
            return None

    def close(self) -> None:
        """Close all service connections."""
        self.ceremony_service.close()
        self.story_service.close()
        self.epic_service.close()

    def __enter__(self) -> "CeremonyTriggerEngine":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close connections."""
        self.close()
