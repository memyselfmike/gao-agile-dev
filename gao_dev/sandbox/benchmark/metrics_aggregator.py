"""Metrics aggregation and reporting for benchmark runs."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from .models import AgentMetrics


logger = structlog.get_logger()


@dataclass
class StoryMetrics:
    """Metrics for a single story execution."""

    epic_name: str
    story_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_tokens: int
    total_cost_usd: float
    agents_used: List[str]
    status: str  # "completed", "failed", "skipped"


@dataclass
class BenchmarkMetricsReport:
    """Comprehensive metrics report for a benchmark run."""

    run_id: str
    benchmark_name: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    total_cost_usd: float
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    agent_count: int
    phase_count: int
    story_count: int
    success: bool
    agent_metrics: List[Dict[str, Any]]
    phase_summary: List[Dict[str, Any]]
    story_summary: List[Dict[str, Any]]


class MetricsAggregator:
    """
    Aggregates and reports metrics from benchmark runs.

    Tracks:
    - Agent execution metrics (time, tokens, cost)
    - Phase completion metrics
    - Overall benchmark performance
    - Detailed logs for debugging
    """

    def __init__(self, run_id: str, benchmark_name: str, output_dir: Path):
        """
        Initialize metrics aggregator.

        Args:
            run_id: Unique identifier for this benchmark run
            benchmark_name: Name of the benchmark
            output_dir: Directory to write metrics files
        """
        self.run_id = run_id
        self.benchmark_name = benchmark_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.start_time = datetime.now()
        self.agent_metrics: List[AgentMetrics] = []
        self.phase_results: List[Dict[str, Any]] = []
        self.story_metrics: List[StoryMetrics] = []
        self.log_entries: List[Dict[str, Any]] = []

        # Track current story for incremental metrics
        self.current_story: Optional[Dict[str, Any]] = None
        self.current_story_agents: List[AgentMetrics] = []

        self.logger = logger.bind(
            component="MetricsAggregator", run_id=run_id, benchmark=benchmark_name
        )

        # Create log file
        self.log_file = self.output_dir / f"{run_id}_verbose.log"
        self.metrics_file = self.output_dir / f"{run_id}_metrics.json"

        self.logger.info(
            "metrics_aggregator_initialized",
            log_file=str(self.log_file),
            metrics_file=str(self.metrics_file),
        )

    def log_event(
        self,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an event with timestamp.

        Args:
            event_type: Type of event (agent_start, agent_complete, phase_start, etc.)
            message: Human-readable message
            details: Additional details to log
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {},
        }

        self.log_entries.append(entry)

        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, indent=2) + "\n")

        self.logger.info(event_type, message=message, details=details)

    def record_phase_result(
        self,
        phase_name: str,
        agent_name: str,
        success: bool,
        duration_seconds: float,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Record phase execution result.

        Args:
            phase_name: Name of the phase
            agent_name: Name of the agent that executed it
            success: Whether the phase succeeded
            duration_seconds: How long it took
            details: Additional details
        """
        result = {
            "phase_name": phase_name,
            "agent_name": agent_name,
            "success": success,
            "duration_seconds": duration_seconds,
            "details": details or {},
        }

        self.phase_results.append(result)

        self.log_event(
            "phase_completed",
            f"Phase '{phase_name}' by {agent_name}: {'SUCCESS' if success else 'FAILED'}",
            result,
        )

    def record_story_start(
        self,
        epic_name: str,
        story_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record the start of a story execution.

        Args:
            epic_name: Name of the epic
            story_name: Name of the story
            metadata: Additional metadata
        """
        self.current_story = {
            "epic_name": epic_name,
            "story_name": story_name,
            "start_time": datetime.now(),
            "metadata": metadata or {},
        }
        self.current_story_agents = []

        self.log_event(
            "story_started",
            f"Story '{story_name}' in epic '{epic_name}' started",
            {"epic": epic_name, "story": story_name},
        )

    def record_story_complete(
        self,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record the completion of a story execution.

        Args:
            status: Status of story (completed, failed, skipped)
            metadata: Additional metadata
        """
        if not self.current_story:
            self.logger.warning("story_complete_called_without_start")
            return

        end_time = datetime.now()
        duration = (end_time - self.current_story["start_time"]).total_seconds()

        # Aggregate metrics from agents used in this story
        total_tokens = sum(m.total_tokens for m in self.current_story_agents)
        total_cost = sum(m.estimated_cost_usd for m in self.current_story_agents)
        agents_used = list(set(m.agent_name for m in self.current_story_agents))

        story_metric = StoryMetrics(
            epic_name=self.current_story["epic_name"],
            story_name=self.current_story["story_name"],
            start_time=self.current_story["start_time"].isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            agents_used=agents_used,
            status=status,
        )

        self.story_metrics.append(story_metric)

        self.log_event(
            "story_completed",
            f"Story '{story_metric.story_name}' {status}: {duration:.1f}s, ${total_cost:.4f}",
            {
                "epic": story_metric.epic_name,
                "story": story_metric.story_name,
                "status": status,
                "duration": duration,
                "tokens": total_tokens,
                "cost": total_cost,
                "agents": agents_used,
            },
        )

        # Reset current story tracking
        self.current_story = None
        self.current_story_agents = []

    def record_agent_metrics(self, metrics: AgentMetrics):
        """
        Record metrics from an agent execution.

        Now also tracks agents per story if a story is active.

        Args:
            metrics: AgentMetrics object from agent execution
        """
        self.agent_metrics.append(metrics)

        # Track for current story if active
        if self.current_story:
            self.current_story_agents.append(metrics)

        self.log_event(
            "agent_metrics_recorded",
            f"Agent {metrics.agent_name} completed in {metrics.duration_seconds:.2f}s",
            {
                "agent": metrics.agent_name,
                "duration": metrics.duration_seconds,
                "tokens": metrics.total_tokens,
                "cost": metrics.estimated_cost_usd,
            },
        )

    def get_story_progress(self) -> Dict[str, Any]:
        """
        Get current story progress metrics.

        Returns:
            Dict with current progress including story counts and status
        """
        completed = sum(
            1 for s in self.story_metrics if s.status == "completed"
        )
        failed = sum(1 for s in self.story_metrics if s.status == "failed")
        skipped = sum(1 for s in self.story_metrics if s.status == "skipped")
        total = len(self.story_metrics)

        return {
            "total_stories": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "in_progress": 1 if self.current_story else 0,
            "current_story": (
                self.current_story["story_name"] if self.current_story else None
            ),
        }

    def generate_report(self) -> BenchmarkMetricsReport:
        """
        Generate comprehensive metrics report.

        Returns:
            BenchmarkMetricsReport with all aggregated metrics
        """
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Aggregate metrics
        total_cost = sum(m.estimated_cost_usd for m in self.agent_metrics)
        total_tokens = sum(m.total_tokens for m in self.agent_metrics)
        total_input = sum(m.input_tokens for m in self.agent_metrics)
        total_output = sum(m.output_tokens for m in self.agent_metrics)

        # Check overall success
        all_phases_success = all(p["success"] for p in self.phase_results)

        report = BenchmarkMetricsReport(
            run_id=self.run_id,
            benchmark_name=self.benchmark_name,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration_seconds=total_duration,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            agent_count=len(self.agent_metrics),
            phase_count=len(self.phase_results),
            story_count=len(self.story_metrics),
            success=all_phases_success,
            agent_metrics=[asdict(m) for m in self.agent_metrics],
            phase_summary=self.phase_results,
            story_summary=[asdict(s) for s in self.story_metrics],
        )

        # Write to file
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2)

        self.log_event(
            "benchmark_complete",
            f"Benchmark completed in {total_duration:.2f}s, cost ${total_cost:.4f}",
            {
                "success": all_phases_success,
                "total_duration": total_duration,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
            },
        )

        self.logger.info(
            "metrics_report_generated",
            metrics_file=str(self.metrics_file),
            log_file=str(self.log_file),
        )

        return report

    def print_summary(self):
        """Print summary to console."""
        if not self.agent_metrics:
            print("\nNo metrics to report.")
            return

        total_cost = sum(m.estimated_cost_usd for m in self.agent_metrics)
        total_tokens = sum(m.total_tokens for m in self.agent_metrics)
        total_duration = sum(m.duration_seconds for m in self.agent_metrics)

        print("\n" + "=" * 80)
        print("BENCHMARK METRICS SUMMARY")
        print("=" * 80)
        print(f"Run ID: {self.run_id}")
        print(f"Benchmark: {self.benchmark_name}")
        print("")
        print(f"Total Duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Total Tokens: {total_tokens:,} ({total_tokens/1000:.1f}K)")
        print("")
        print("Agent Breakdown:")
        print(f"{'Agent':<15} {'Duration':<12} {'Tokens':<12} {'Cost':<10}")
        print("-" * 80)

        for m in self.agent_metrics:
            print(
                f"{m.agent_name:<15} "
                f"{m.duration_seconds:>7.1f}s ({m.duration_seconds/60:>4.1f}m)  "
                f"{m.total_tokens:>10,}  "
                f"${m.estimated_cost_usd:>8.4f}"
            )

        # Story-level metrics (if any)
        if self.story_metrics:
            print("")
            print(f"Story Breakdown ({len(self.story_metrics)} stories):")
            print(f"{'Epic/Story':<40} {'Status':<12} {'Duration':<10} {'Cost':<10}")
            print("-" * 80)

            for s in self.story_metrics:
                epic_story = f"{s.epic_name}/{s.story_name}"
                status_display = s.status.upper()
                duration_display = f"{s.duration_seconds:.1f}s"
                cost_display = f"${s.total_cost_usd:.4f}"

                print(
                    f"{epic_story:<40} "
                    f"{status_display:<12} "
                    f"{duration_display:<10} "
                    f"{cost_display:<10}"
                )

            # Story progress summary
            progress = self.get_story_progress()
            print("")
            print(f"Story Progress: {progress['completed']}/{progress['total_stories']} completed")
            if progress['failed'] > 0:
                print(f"  Failed: {progress['failed']}")
            if progress['skipped'] > 0:
                print(f"  Skipped: {progress['skipped']}")

        print("=" * 80)
        print(f"\nVerbose log: {self.log_file}")
        print(f"Metrics JSON: {self.metrics_file}")
        print("")
