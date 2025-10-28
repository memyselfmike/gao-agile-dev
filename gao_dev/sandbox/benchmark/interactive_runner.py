"""Interactive benchmark runner for Claude Code sessions.

This module enables running benchmarks directly from Claude Code using the Task tool,
without requiring API keys. It's designed to be called by Claude within a Code session.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

from .config import WorkflowPhaseConfig
from .runner import BenchmarkResult, BenchmarkStatus
from ..benchmark_loader import BenchmarkConfig


logger = structlog.get_logger()


@dataclass
class PhaseExecutionPlan:
    """Plan for executing a single phase interactively."""

    phase_name: str
    agent_name: str
    task_prompt: str
    timeout_minutes: int
    project_path: Path


class InteractiveBenchmarkRunner:
    """
    Runs benchmarks interactively in Claude Code sessions.

    This runner is designed to be used by Claude (the assistant) in a Code session,
    using the Task tool to spawn agents without requiring API keys.

    Usage:
        # Called by Claude in a Code session
        runner = InteractiveBenchmarkRunner(config, project_path)
        plan = runner.create_execution_plan()
        # Claude then uses Task tool to execute each phase
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        project_path: Path,
    ):
        """
        Initialize interactive runner.

        Args:
            config: Benchmark configuration
            project_path: Path to sandbox project directory
        """
        self.config = config
        self.project_path = Path(project_path)
        self.logger = logger.bind(
            component="InteractiveBenchmarkRunner",
            project=str(project_path),
        )

    def create_execution_plan(self) -> List[PhaseExecutionPlan]:
        """
        Create execution plan for all phases.

        Returns:
            List of PhaseExecutionPlan objects for each phase
        """
        plans = []

        if not hasattr(self.config, "phases") or not self.config.phases:
            self.logger.warning("no_phases_in_config")
            return plans

        for i, phase_def in enumerate(self.config.phases, 1):
            phase_name = phase_def.get("name", f"Phase {i}")
            agent_name = phase_def.get("agent", "Amelia")
            duration_minutes = phase_def.get("expected_duration_minutes", 60)

            # Create task prompt
            task_prompt = self._create_task_prompt(phase_name, agent_name)

            plan = PhaseExecutionPlan(
                phase_name=phase_name,
                agent_name=agent_name,
                task_prompt=task_prompt,
                timeout_minutes=duration_minutes,
                project_path=self.project_path,
            )
            plans.append(plan)

        return plans

    def _create_task_prompt(self, phase_name: str, agent_name: str) -> str:
        """
        Create task prompt for an agent.

        Args:
            phase_name: Name of the phase
            agent_name: Name of the agent

        Returns:
            Complete task prompt
        """
        return f"""You are {agent_name}, a specialized GAO-Dev agent.

Your Phase: {phase_name}

Project Directory: {self.project_path}

Initial Benchmark Prompt:
{self.config.initial_prompt}

Instructions:
1. Work in the project directory: {self.project_path}
2. Execute the {phase_name} phase according to your role
3. Create all necessary files and artifacts
4. Follow GAO-Dev quality standards
5. Document your work as you go
6. Provide a summary when complete

Your Role:
- Execute {phase_name} autonomously
- Use your specialized expertise as {agent_name}
- Coordinate with the overall benchmark goal
- Produce production-quality output

Begin your work now.
"""

    def get_phase_summary(self) -> str:
        """
        Get summary of all phases for display.

        Returns:
            Formatted string showing all phases
        """
        if not hasattr(self.config, "phases") or not self.config.phases:
            return "No phases configured"

        lines = [f"\n{'='*80}"]
        lines.append(f"Benchmark: {self.config.name} v{self.config.version}")
        lines.append(f"Phases: {len(self.config.phases)}")
        lines.append(f"{'='*80}\n")

        for i, phase_def in enumerate(self.config.phases, 1):
            phase_name = phase_def.get("name", f"Phase {i}")
            agent_name = phase_def.get("agent", "Unknown")
            duration = phase_def.get("expected_duration_minutes", 0)

            lines.append(
                f"  {i}. {phase_name:<30} Agent: {agent_name:<10} (~{duration} min)"
            )

        lines.append(f"\n{'='*80}\n")
        return "\n".join(lines)


def load_benchmark_for_interactive_run(benchmark_path: Path) -> BenchmarkConfig:
    """
    Load benchmark configuration for interactive execution.

    Args:
        benchmark_path: Path to benchmark YAML file

    Returns:
        BenchmarkConfig ready for interactive execution
    """
    from ..benchmark_loader import load_benchmark

    return load_benchmark(benchmark_path)
