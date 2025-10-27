"""Agent definitions for GAO-Dev team members."""

from claude_agent_sdk import AgentDefinition
from pathlib import Path
from typing import Dict


def load_agent_persona(agent_name: str) -> str:
    """Load agent persona from embedded agents directory."""
    agents_path = Path(__file__).parent.parent / "agents"
    persona_file = agents_path / f"{agent_name}.md"

    if not persona_file.exists():
        raise FileNotFoundError(f"Agent persona not found: {agent_name}")

    return persona_file.read_text(encoding="utf-8")


# ============================================================================
# MARY - Business Analyst
# ============================================================================

mary_agent = AgentDefinition(
    description="Business Analyst who conducts analysis, research, and requirements gathering",
    prompt=load_agent_persona("mary"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Grep",
        "Glob",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__health_check",
        # Research tools
        "WebSearch",
        "WebFetch",
    ]
)


# ============================================================================
# JOHN - Product Manager
# ============================================================================

john_agent = AgentDefinition(
    description="Product Manager who creates PRDs, defines features, and prioritizes work",
    prompt=load_agent_persona("john"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Grep",
        "Glob",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__get_sprint_status",
        "mcp__gao_dev__health_check",
        # Research tools
        "WebSearch",
        "WebFetch",
    ]
)


# ============================================================================
# WINSTON - Technical Architect
# ============================================================================

winston_agent = AgentDefinition(
    description="Technical Architect who designs system architecture and technical specifications",
    prompt=load_agent_persona("winston"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Edit",
        "Grep",
        "Glob",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__health_check",
        # Research tools
        "WebSearch",
        "WebFetch",
    ]
)


# ============================================================================
# SALLY - UX Designer
# ============================================================================

sally_agent = AgentDefinition(
    description="UX Designer who creates user experiences, wireframes, and design documentation",
    prompt=load_agent_persona("sally"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Grep",
        "Glob",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__get_story_status",
        "mcp__gao_dev__health_check",
        # Research tools
        "WebSearch",
        "WebFetch",
    ]
)


# ============================================================================
# BOB - Scrum Master
# ============================================================================

bob_agent = AgentDefinition(
    description="Scrum Master who creates and manages user stories and coordinates the team",
    prompt=load_agent_persona("bob"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Grep",
        "Glob",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__get_story_status",
        "mcp__gao_dev__set_story_status",
        "mcp__gao_dev__ensure_story_directory",
        "mcp__gao_dev__get_sprint_status",
        "mcp__gao_dev__health_check",
        # Git operations
        "mcp__gao_dev__git_commit",
        # Task management
        "TodoWrite",
    ]
)


# ============================================================================
# AMELIA - Software Developer
# ============================================================================

amelia_agent = AgentDefinition(
    description="Software Developer who implements stories, writes code, and performs code reviews",
    prompt=load_agent_persona("amelia"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Edit",
        "MultiEdit",
        "Grep",
        "Glob",
        # Shell operations
        "Bash",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__get_story_status",
        "mcp__gao_dev__set_story_status",
        "mcp__gao_dev__health_check",
        # Git operations
        "mcp__gao_dev__git_create_branch",
        "mcp__gao_dev__git_commit",
        "mcp__gao_dev__git_merge_branch",
        # Task management
        "TodoWrite",
        # Research tools
        "WebSearch",
        "WebFetch",
    ]
)


# ============================================================================
# MURAT - Test Architect
# ============================================================================

murat_agent = AgentDefinition(
    description="Test Architect who creates test strategies, test plans, and ensures quality",
    prompt=load_agent_persona("murat"),
    model="sonnet",
    tools=[
        # File operations
        "Read",
        "Write",
        "Edit",
        "Grep",
        "Glob",
        # Shell operations (for running tests)
        "Bash",
        # GAO-Dev tools
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__get_workflow",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__get_story_status",
        "mcp__gao_dev__health_check",
        # Git operations
        "mcp__gao_dev__git_commit",
        # Task management
        "TodoWrite",
    ]
)


# ============================================================================
# AGENT REGISTRY
# ============================================================================

AGENT_DEFINITIONS: Dict[str, AgentDefinition] = {
    "mary": mary_agent,
    "john": john_agent,
    "winston": winston_agent,
    "sally": sally_agent,
    "bob": bob_agent,
    "amelia": amelia_agent,
    "murat": murat_agent,
}


# Helper function to get agent by role
def get_agent_by_role(role: str) -> AgentDefinition:
    """
    Get agent definition by role.

    Args:
        role: Agent role (business_analyst, product_manager, architect, etc.)

    Returns:
        AgentDefinition for the specified role
    """
    role_mapping = {
        "business_analyst": "mary",
        "product_manager": "john",
        "architect": "winston",
        "ux_designer": "sally",
        "scrum_master": "bob",
        "developer": "amelia",
        "test_architect": "murat",
    }

    agent_name = role_mapping.get(role.lower())
    if not agent_name:
        raise ValueError(f"Unknown role: {role}")

    return AGENT_DEFINITIONS[agent_name]
