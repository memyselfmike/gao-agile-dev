"""Data models for benchmark execution."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AgentMetrics:
    """Detailed metrics from agent execution."""

    agent_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    tool_calls: int
    model_used: str


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    metrics: Optional[AgentMetrics] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
