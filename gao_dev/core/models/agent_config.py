"""
Agent configuration model for YAML-based agent definitions.

This module provides the AgentConfig data model used for loading agents
from YAML configuration files. It represents the declarative structure
of agent definitions following the BMAD agent schema pattern.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class AgentConfig:
    """
    Agent configuration loaded from YAML files.

    This dataclass represents a complete agent configuration including
    metadata, persona, tools, capabilities, and workflows. It serves
    as the primary data structure for declarative agent definitions.

    Attributes:
        name: Agent name (e.g., "Amelia")
        role: Agent role (e.g., "Software Developer")
        persona: Full persona text loaded from .md file
        tools: List of tool names available to agent
        capabilities: List of capability identifiers
        model: Claude model identifier
        workflows: List of workflow identifiers
        icon: Optional emoji icon for agent
        version: Configuration version (default: "1.0.0")
        metadata: Additional metadata from config section
        persona_file: Optional path to persona file (for reference)

    Example:
        ```python
        config = AgentConfig(
            name="Amelia",
            role="Software Developer",
            persona="You are Amelia...",
            tools=["Read", "Write", "Edit"],
            capabilities=["implementation", "code_review"],
            model="claude-sonnet-4-5-20250929",
            workflows=["dev-story"],
            icon="💻",
            version="1.0.0"
        )
        ```
    """

    name: str
    role: str
    persona: str
    tools: List[str]
    capabilities: List[str]
    model: str
    workflows: List[str] = field(default_factory=list)
    icon: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    persona_file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], persona: str) -> "AgentConfig":
        """
        Create AgentConfig from parsed YAML dictionary.

        Args:
            data: Dictionary containing agent configuration (the 'agent' section)
            persona: Persona text loaded from .md file

        Returns:
            AgentConfig: Populated agent configuration

        Raises:
            KeyError: If required fields are missing
            ValueError: If data is invalid

        Example:
            ```python
            yaml_data = {
                "metadata": {"name": "Amelia", "role": "Developer"},
                "tools": ["Read", "Write"],
                "capabilities": ["implementation"],
                "model": "claude-sonnet-4-5-20250929"
            }
            persona_text = "You are Amelia..."
            config = AgentConfig.from_dict(yaml_data, persona_text)
            ```
        """
        # Validate required fields
        if "metadata" not in data:
            raise ValueError("Agent config must have 'metadata' section")
        if "name" not in data["metadata"]:
            raise ValueError("Agent metadata must include 'name'")
        if "role" not in data["metadata"]:
            raise ValueError("Agent metadata must include 'role'")
        if "tools" not in data:
            raise ValueError("Agent config must have 'tools' list")

        return cls(
            name=data["metadata"]["name"],
            role=data["metadata"]["role"],
            persona=persona,
            tools=data["tools"],
            capabilities=data.get("capabilities", []),
            model=data.get("model", "claude-sonnet-4-5-20250929"),
            workflows=data.get("workflows", []),
            icon=data["metadata"].get("icon"),
            version=data["metadata"].get("version", "1.0.0"),
            metadata=data.get("config", {}),
            persona_file=data.get("persona_file")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert AgentConfig to dictionary.

        Returns a dictionary representation suitable for serialization
        or passing to agent constructors. Does not include persona text
        to avoid large payloads.

        Returns:
            Dict[str, Any]: Agent configuration as dictionary

        Example:
            ```python
            config = AgentConfig(name="Amelia", ...)
            config_dict = config.to_dict()
            # {
            #     "name": "Amelia",
            #     "role": "Software Developer",
            #     "tools": ["Read", "Write"],
            #     ...
            # }
            ```
        """
        return {
            "name": self.name,
            "role": self.role,
            "tools": self.tools,
            "capabilities": self.capabilities,
            "model": self.model,
            "workflows": self.workflows,
            "icon": self.icon,
            "version": self.version,
            "metadata": self.metadata,
            "persona_file": self.persona_file,
        }

    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Convert to YAML-serializable dictionary structure.

        Returns the full YAML structure including metadata section,
        suitable for writing back to YAML files.

        Returns:
            Dict[str, Any]: Complete YAML structure

        Example:
            ```python
            config = AgentConfig(name="Amelia", ...)
            yaml_dict = config.to_yaml_dict()
            # {
            #     "agent": {
            #         "metadata": {"name": "Amelia", "role": "Developer"},
            #         "tools": ["Read", "Write"],
            #         ...
            #     }
            # }
            ```
        """
        return {
            "agent": {
                "metadata": {
                    "name": self.name,
                    "role": self.role,
                    "icon": self.icon,
                    "version": self.version,
                },
                "persona_file": self.persona_file,
                "tools": self.tools,
                "capabilities": self.capabilities,
                "model": self.model,
                "workflows": self.workflows,
                "config": self.metadata,
            }
        }

    def __str__(self) -> str:
        """String representation."""
        return f"AgentConfig(name={self.name}, role={self.role}, tools={len(self.tools)})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"AgentConfig("
            f"name='{self.name}', "
            f"role='{self.role}', "
            f"tools={self.tools}, "
            f"capabilities={self.capabilities}, "
            f"model='{self.model}'"
            f")"
        )
