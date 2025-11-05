"""Legal team plugin for GAO-Dev.

This plugin provides Laura (Legal Analyst) and contract review prompts
for legal analysis and compliance checking.
"""

from pathlib import Path
from typing import List

from gao_dev.plugins.agent_plugin import BaseAgentPlugin
from gao_dev.plugins.models import AgentMetadata
from gao_dev.core.interfaces.agent import IAgent
from gao_dev.core.models.agent_config import AgentConfig
from gao_dev.core.models.prompt_template import PromptTemplate
from gao_dev.agents.claude_agent import ClaudeAgent


class LegalTeamPlugin(BaseAgentPlugin):
    """Legal team plugin providing Laura (Legal Analyst).

    This plugin demonstrates how to:
    1. Register custom agents via agent definitions
    2. Provide custom prompt templates
    3. Extend GAO-Dev for domain-specific use cases
    """

    def get_agent_class(self) -> type[IAgent]:
        """Return ClaudeAgent as the implementation."""
        return ClaudeAgent

    def get_agent_name(self) -> str:
        """Return the agent name."""
        return "Laura"

    def get_agent_metadata(self) -> AgentMetadata:
        """Return agent metadata."""
        return AgentMetadata(
            name="Laura",
            role="Legal Analyst",
            description="Legal analyst specializing in contract review and compliance",
            capabilities=["contract_review", "risk_assessment", "compliance_checking"],
            tools=["Read", "Write", "Grep", "Glob", "WebFetch"]
        )

    def get_agent_definitions(self) -> List[AgentConfig]:
        """Load Laura agent definition from YAML."""
        plugin_dir = Path(__file__).parent
        laura_config_path = plugin_dir / "agents" / "laura.agent.yaml"

        if laura_config_path.exists():
            laura_config = AgentConfig.from_yaml(laura_config_path)
            return [laura_config]

        return []

    def get_prompt_templates(self) -> List[PromptTemplate]:
        """Load contract review prompt template from YAML."""
        plugin_dir = Path(__file__).parent
        contract_review_path = plugin_dir / "prompts" / "contract_review.yaml"

        if contract_review_path.exists():
            contract_review_template = PromptTemplate.from_yaml(contract_review_path)
            return [contract_review_template]

        return []
