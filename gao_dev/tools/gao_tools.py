"""GAO-Dev custom tools for Claude Agent SDK."""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any
from pathlib import Path
import json

# Import core services
from ..core import (
    ConfigLoader,
    WorkflowRegistry,
    WorkflowExecutor,
    StateManager,
    GitManager,
    HealthCheck,
)


# Module-level initialization
# These will be initialized when tools are actually called
_config = None
_registry = None
_executor = None
_state_manager = None
_git_manager = None
_health_checker = None


def _get_config() -> ConfigLoader:
    """Get or create config loader."""
    global _config
    if _config is None:
        _config = ConfigLoader(Path.cwd())
    return _config


def _get_registry() -> WorkflowRegistry:
    """Get or create workflow registry."""
    global _registry
    if _registry is None:
        _registry = WorkflowRegistry(_get_config())
        _registry.index_workflows()
    return _registry


def _get_executor() -> WorkflowExecutor:
    """Get or create workflow executor."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor(_get_config())
    return _executor


def _get_state_manager() -> StateManager:
    """Get or create state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(_get_config())
    return _state_manager


def _get_git_manager() -> GitManager:
    """Get or create git manager."""
    global _git_manager
    if _git_manager is None:
        _git_manager = GitManager(_get_config())
    return _git_manager


def _get_health_checker() -> HealthCheck:
    """Get or create health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthCheck(_get_config())
    return _health_checker


# ============================================================================
# WORKFLOW TOOLS
# ============================================================================

@tool(
    "list_workflows",
    "List available GAO-Dev workflows, optionally filtered by phase",
    {"phase": int}
)
async def list_workflows(args: dict[str, Any]) -> dict[str, Any]:
    """List available workflows."""
    registry = _get_registry()
    phase = args.get("phase")

    workflows = registry.list_workflows(phase=phase)

    workflow_list = []
    for workflow in workflows:
        workflow_list.append({
            "name": workflow.name,
            "description": workflow.description,
            "phase": workflow.phase,
            "author": workflow.author,
            "autonomous": workflow.autonomous
        })

    result_text = f"Found {len(workflows)} workflows"
    if phase is not None:
        result_text += f" in phase {phase}"
    result_text += ":\n\n"

    for wf in workflow_list:
        result_text += f"• {wf['name']} (Phase {wf['phase']})\n"
        result_text += f"  {wf['description']}\n"
        if wf['author']:
            result_text += f"  Author: {wf['author']}\n"
        result_text += "\n"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


@tool(
    "get_workflow",
    "Get detailed information about a specific workflow",
    {"workflow_name": str}
)
async def get_workflow(args: dict[str, Any]) -> dict[str, Any]:
    """Get workflow details."""
    registry = _get_registry()
    workflow_name = args["workflow_name"]

    workflow = registry.get_workflow(workflow_name)

    if not workflow:
        return {
            "content": [{
                "type": "text",
                "text": f"Workflow '{workflow_name}' not found."
            }]
        }

    result_text = f"Workflow: {workflow.name}\n\n"
    result_text += f"Description: {workflow.description}\n"
    result_text += f"Phase: {workflow.phase}\n"
    result_text += f"Author: {workflow.author or 'Not specified'}\n"
    result_text += f"Autonomous: {workflow.autonomous}\n"
    result_text += f"Interactive: {workflow.interactive}\n"

    if workflow.variables:
        result_text += "\nVariables:\n"
        for var_name, var_config in workflow.variables.items():
            required = " (required)" if var_config.get("required") else ""
            result_text += f"  • {var_name}{required}: {var_config.get('description', 'No description')}\n"

    if workflow.required_tools:
        result_text += f"\nRequired tools: {', '.join(workflow.required_tools)}\n"

    if workflow.output_file:
        result_text += f"\nOutput file: {workflow.output_file}\n"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


@tool(
    "execute_workflow",
    "Execute a GAO-Dev workflow with parameters",
    {"workflow_name": str, "params": dict}
)
async def execute_workflow(args: dict[str, Any]) -> dict[str, Any]:
    """Execute a workflow."""
    registry = _get_registry()
    executor = _get_executor()

    workflow_name = args["workflow_name"]
    params = args.get("params", {})

    workflow = registry.get_workflow(workflow_name)
    if not workflow:
        return {
            "content": [{
                "type": "text",
                "text": f"Workflow '{workflow_name}' not found."
            }]
        }

    try:
        result = executor.execute(workflow, params)

        result_text = f"Workflow '{workflow_name}' executed successfully.\n\n"

        if result.get("instructions"):
            result_text += "Instructions:\n"
            result_text += result["instructions"] + "\n\n"

        if result.get("template"):
            result_text += "Template:\n"
            result_text += result["template"][:500]  # Truncate if too long
            if len(result["template"]) > 500:
                result_text += "\n... (truncated)"
            result_text += "\n\n"

        if result.get("output_file"):
            result_text += f"Output file: {result['output_file']}\n\n"

        if result.get("required_tools"):
            result_text += f"Required tools: {', '.join(result['required_tools'])}\n"

        return {
            "content": [{
                "type": "text",
                "text": result_text
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error executing workflow: {str(e)}"
            }]
        }


# ============================================================================
# STORY MANAGEMENT TOOLS
# ============================================================================

@tool(
    "get_story_status",
    "Get the current status of a user story",
    {"epic": int, "story": int}
)
async def get_story_status(args: dict[str, Any]) -> dict[str, Any]:
    """Get story status."""
    state_manager = _get_state_manager()

    epic = args["epic"]
    story = args["story"]

    status = state_manager.get_story_status(epic, story)

    if status:
        return {
            "content": [{
                "type": "text",
                "text": f"Story {epic}.{story} status: {status}"
            }]
        }
    else:
        return {
            "content": [{
                "type": "text",
                "text": f"Story {epic}.{story} not found."
            }]
        }


@tool(
    "set_story_status",
    "Update the status of a user story",
    {"epic": int, "story": int, "status": str}
)
async def set_story_status(args: dict[str, Any]) -> dict[str, Any]:
    """Set story status."""
    state_manager = _get_state_manager()

    epic = args["epic"]
    story = args["story"]
    status = args["status"]

    success = state_manager.set_story_status(epic, story, status)

    if success:
        return {
            "content": [{
                "type": "text",
                "text": f"Story {epic}.{story} status updated to: {status}"
            }]
        }
    else:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to update Story {epic}.{story}. Story may not exist."
            }]
        }


@tool(
    "ensure_story_directory",
    "Ensure the story directory exists for an epic",
    {"epic": int}
)
async def ensure_story_directory(args: dict[str, Any]) -> dict[str, Any]:
    """Ensure story directory exists."""
    state_manager = _get_state_manager()

    epic = args["epic"]
    epic_dir = state_manager.ensure_story_directory(epic)

    return {
        "content": [{
            "type": "text",
            "text": f"Story directory ensured: {epic_dir}"
        }]
    }


@tool(
    "get_sprint_status",
    "Get overall sprint status with all stories",
    {}
)
async def get_sprint_status(args: dict[str, Any]) -> dict[str, Any]:
    """Get sprint status."""
    state_manager = _get_state_manager()

    status = state_manager.get_sprint_status()

    result_text = f"Sprint Status:\n"
    result_text += f"Total stories: {status['total']}\n\n"

    if status['stories']:
        result_text += "Stories:\n"
        for story in status['stories']:
            result_text += f"  • Story {story['epic']}.{story['story']}: {story['status']}\n"
    else:
        result_text += "No stories found.\n"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


# ============================================================================
# GIT TOOLS
# ============================================================================

@tool(
    "git_create_branch",
    "Create a new git branch",
    {"branch_name": str}
)
async def git_create_branch(args: dict[str, Any]) -> dict[str, Any]:
    """Create git branch."""
    git_manager = _get_git_manager()

    branch_name = args["branch_name"]
    success = git_manager.git_branch(branch_name, create=True)

    if success:
        return {
            "content": [{
                "type": "text",
                "text": f"Branch '{branch_name}' created successfully."
            }]
        }
    else:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to create branch '{branch_name}'."
            }]
        }


@tool(
    "git_commit",
    "Create a git commit with files and message",
    {"files": list, "message": str}
)
async def git_commit(args: dict[str, Any]) -> dict[str, Any]:
    """Create git commit."""
    git_manager = _get_git_manager()

    files = args["files"]
    message = args["message"]

    # Add files
    add_success = git_manager.git_add(files)
    if not add_success:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to stage files: {', '.join(files)}"
            }]
        }

    # Commit
    commit_success = git_manager.git_commit(message)
    if commit_success:
        return {
            "content": [{
                "type": "text",
                "text": f"Committed {len(files)} file(s) with message: {message}"
            }]
        }
    else:
        return {
            "content": [{
                "type": "text",
                "text": "Failed to create commit."
            }]
        }


@tool(
    "git_merge_branch",
    "Merge a branch into the current branch",
    {"branch_name": str}
)
async def git_merge_branch(args: dict[str, Any]) -> dict[str, Any]:
    """Merge git branch."""
    git_manager = _get_git_manager()

    branch_name = args["branch_name"]
    success = git_manager.git_merge(branch_name)

    if success:
        return {
            "content": [{
                "type": "text",
                "text": f"Branch '{branch_name}' merged successfully."
            }]
        }
    else:
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to merge branch '{branch_name}'."
            }]
        }


# ============================================================================
# HEALTH CHECK TOOLS
# ============================================================================

@tool(
    "health_check",
    "Run system health check",
    {}
)
async def health_check(args: dict[str, Any]) -> dict[str, Any]:
    """Run health check."""
    health_checker = _get_health_checker()

    result = health_checker.run_all_checks()

    result_text = f"Health Check Results\n"
    result_text += f"Status: {result.status.value.upper()}\n"
    result_text += f"Summary: {result.summary}\n\n"

    for check in result.checks:
        status_icon = "[OK]" if check.status.value == "healthy" else "[WARN]" if check.status.value == "warning" else "[FAIL]"
        result_text += f"{status_icon} {check.name}: {check.message}\n"
        if check.remediation:
            result_text += f"  Remediation: {check.remediation}\n"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


# ============================================================================
# CREATE MCP SERVER
# ============================================================================

gao_dev_server = create_sdk_mcp_server(
    name="gao_dev",
    version="1.0.0",
    tools=[
        list_workflows,
        get_workflow,
        execute_workflow,
        get_story_status,
        set_story_status,
        ensure_story_directory,
        get_sprint_status,
        git_create_branch,
        git_commit,
        git_merge_branch,
        health_check,
    ]
)
