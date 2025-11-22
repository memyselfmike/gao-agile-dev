"""Data models for benchmark metrics.

This module defines strongly-typed data models for all metric categories:
- PerformanceMetrics: Time, tokens, API usage
- AutonomyMetrics: Manual interventions, success rates
- QualityMetrics: Tests, coverage, linting, security
- WorkflowMetrics: Stories, cycle time, phases
- BenchmarkMetrics: Composite model aggregating all metrics
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import json


@dataclass
class PerformanceMetrics:
    """
    Performance metrics tracking time, tokens, and API usage.

    Attributes:
        total_time_seconds: Total execution time in seconds
        phase_times: Time spent in each phase (dict of phase_name: seconds)
        token_usage_total: Total tokens used across all operations
        token_usage_by_agent: Tokens used by each agent (dict of agent_name: count)
        api_calls_count: Total number of API calls made
        api_calls_cost: Total cost in USD for all API calls
    """

    total_time_seconds: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    token_usage_total: int = 0
    token_usage_by_agent: Dict[str, int] = field(default_factory=dict)
    api_calls_count: int = 0
    api_calls_cost: float = 0.0

    def validate(self) -> bool:
        """
        Validate performance metrics.

        Returns:
            True if all metrics are valid, False otherwise
        """
        return (
            self.total_time_seconds >= 0
            and self.token_usage_total >= 0
            and self.api_calls_count >= 0
            and self.api_calls_cost >= 0
        )


@dataclass
class AutonomyMetrics:
    """
    Autonomy metrics tracking manual intervention and success rates.

    Attributes:
        manual_interventions_count: Number of times human intervention was needed
        manual_interventions_types: List of intervention type descriptions
        prompts_needed_initial: Number of initial prompts from user
        prompts_needed_followup: Number of follow-up/clarification prompts
        one_shot_success_rate: Percentage of tasks completed on first attempt (0.0-1.0)
        error_recovery_rate: Percentage of errors recovered autonomously (0.0-1.0)
        agent_handoffs_successful: Number of successful agent-to-agent handoffs
        agent_handoffs_failed: Number of failed agent-to-agent handoffs
    """

    manual_interventions_count: int = 0
    manual_interventions_types: List[str] = field(default_factory=list)
    prompts_needed_initial: int = 0
    prompts_needed_followup: int = 0
    one_shot_success_rate: float = 0.0  # 0.0 - 1.0
    error_recovery_rate: float = 0.0  # 0.0 - 1.0
    agent_handoffs_successful: int = 0
    agent_handoffs_failed: int = 0

    def validate(self) -> bool:
        """
        Validate autonomy metrics.

        Returns:
            True if all metrics are valid, False otherwise
        """
        return (
            self.manual_interventions_count >= 0
            and 0.0 <= self.one_shot_success_rate <= 1.0
            and 0.0 <= self.error_recovery_rate <= 1.0
            and self.agent_handoffs_successful >= 0
            and self.agent_handoffs_failed >= 0
        )


@dataclass
class QualityMetrics:
    """
    Quality metrics tracking tests, coverage, and code quality.

    Attributes:
        tests_written: Total number of tests written
        tests_passing: Number of tests that pass
        code_coverage_percentage: Code coverage percentage (0.0-100.0)
        linting_errors_count: Total number of linting errors
        linting_errors_by_severity: Linting errors grouped by severity
        type_errors_count: Total number of type checking errors
        security_vulnerabilities_count: Total number of security vulnerabilities
        security_vulnerabilities_by_severity: Vulnerabilities grouped by severity
        functional_completeness_percentage: Percentage of acceptance criteria met (0.0-100.0)
    """

    tests_written: int = 0
    tests_passing: int = 0
    code_coverage_percentage: float = 0.0  # 0.0 - 100.0
    linting_errors_count: int = 0
    linting_errors_by_severity: Dict[str, int] = field(default_factory=dict)
    type_errors_count: int = 0
    security_vulnerabilities_count: int = 0
    security_vulnerabilities_by_severity: Dict[str, int] = field(default_factory=dict)
    functional_completeness_percentage: float = 0.0  # 0.0 - 100.0

    def validate(self) -> bool:
        """
        Validate quality metrics.

        Returns:
            True if all metrics are valid, False otherwise
        """
        return (
            self.tests_written >= 0
            and self.tests_passing >= 0
            and self.tests_passing <= self.tests_written
            and 0.0 <= self.code_coverage_percentage <= 100.0
            and self.linting_errors_count >= 0
            and self.type_errors_count >= 0
            and self.security_vulnerabilities_count >= 0
            and 0.0 <= self.functional_completeness_percentage <= 100.0
        )


@dataclass
class WorkflowMetrics:
    """
    Workflow metrics tracking story progress and phase distribution.

    Attributes:
        stories_created: Total number of stories created
        stories_completed: Number of stories completed
        avg_cycle_time_seconds: Average time to complete a story in seconds
        phase_distribution: Time distribution across phases (dict of phase: percentage)
        rework_count: Number of times work had to be redone
    """

    stories_created: int = 0
    stories_completed: int = 0
    avg_cycle_time_seconds: float = 0.0
    phase_distribution: Dict[str, float] = field(default_factory=dict)
    rework_count: int = 0

    def validate(self) -> bool:
        """
        Validate workflow metrics.

        Returns:
            True if all metrics are valid, False otherwise
        """
        return (
            self.stories_created >= 0
            and self.stories_completed >= 0
            and self.stories_completed <= self.stories_created
            and self.avg_cycle_time_seconds >= 0
            and self.rework_count >= 0
        )


@dataclass
class BenchmarkMetrics:
    """
    Composite benchmark metrics aggregating all metric categories.

    This is the top-level model that contains all metrics for a benchmark run.

    Attributes:
        run_id: Unique identifier for this benchmark run
        timestamp: ISO format timestamp when run started
        project_name: Name of the project being benchmarked
        benchmark_name: Name of the benchmark configuration
        version: Schema version for metrics format
        performance: Performance metrics (time, tokens, API)
        autonomy: Autonomy metrics (interventions, success rates)
        quality: Quality metrics (tests, coverage, linting)
        workflow: Workflow metrics (stories, cycle time)
        metadata: Additional custom metadata
    """

    run_id: str
    timestamp: str  # ISO format
    project_name: str
    benchmark_name: str
    version: str = "1.0.0"

    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    autonomy: AutonomyMetrics = field(default_factory=AutonomyMetrics)
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    workflow: WorkflowMetrics = field(default_factory=WorkflowMetrics)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate all metrics.

        Returns:
            True if all nested metrics are valid, False otherwise
        """
        return (
            bool(self.run_id)
            and bool(self.timestamp)
            and bool(self.project_name)
            and bool(self.benchmark_name)
            and self.performance.validate()
            and self.autonomy.validate()
            and self.quality.validate()
            and self.workflow.validate()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of all metrics
        """
        return asdict(self)

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Convert to JSON string.

        Args:
            indent: Number of spaces for indentation (None for compact)

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkMetrics":
        """
        Create BenchmarkMetrics from dictionary.

        Args:
            data: Dictionary containing metrics data

        Returns:
            BenchmarkMetrics instance
        """
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            project_name=data["project_name"],
            benchmark_name=data["benchmark_name"],
            version=data.get("version", "1.0.0"),
            performance=PerformanceMetrics(**data.get("performance", {})),
            autonomy=AutonomyMetrics(**data.get("autonomy", {})),
            quality=QualityMetrics(**data.get("quality", {})),
            workflow=WorkflowMetrics(**data.get("workflow", {})),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BenchmarkMetrics":
        """
        Create BenchmarkMetrics from JSON string.

        Args:
            json_str: JSON string containing metrics data

        Returns:
            BenchmarkMetrics instance
        """
        return cls.from_dict(json.loads(json_str))
