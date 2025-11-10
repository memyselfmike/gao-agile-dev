"""
Interactive Brian Chat - Demo Script

This script demonstrates typical usage patterns of the Interactive Brian Chat interface.
Shows different conversation types, init commands, and session state management.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.7 - Testing & Documentation

Usage:
    python examples/interactive_brian_demo.py

Requirements:
    - GAO-Dev installed (pip install -e .)
    - Anthropic API key configured (or local Ollama with deepseek-r1)
"""

import asyncio
import tempfile
from pathlib import Path
from typing import List
import structlog

from gao_dev.cli.chat_repl import ChatREPL
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

logger = structlog.get_logger()
console = Console()


class DemoScenario:
    """Represents a demo scenario with simulated inputs."""

    def __init__(self, name: str, description: str, inputs: List[str]):
        """
        Initialize demo scenario.

        Args:
            name: Scenario name
            description: Scenario description
            inputs: List of simulated user inputs
        """
        self.name = name
        self.description = description
        self.inputs = inputs


# =============================================================================
# DEMO SCENARIOS
# =============================================================================

SCENARIO_1_NEW_FEATURE = DemoScenario(
    name="New Feature Request",
    description="User requests a new feature, reviews analysis, and confirms execution",
    inputs=[
        "I want to add user authentication with JWT tokens",
        "yes",  # Confirm
        "exit"
    ]
)

SCENARIO_2_MULTI_TURN = DemoScenario(
    name="Multi-Turn Refinement",
    description="User refines request over multiple turns",
    inputs=[
        "I want to build a blog",
        "With Markdown support",
        "And syntax highlighting for code blocks",
        "yes",  # Confirm final plan
        "exit"
    ]
)

SCENARIO_3_BUG_FIX = DemoScenario(
    name="Bug Fix Request",
    description="User reports a bug and gets it fixed",
    inputs=[
        "Fix the bug where login form doesn't validate email format",
        "yes",  # Confirm fix
        "exit"
    ]
)

SCENARIO_4_GREENFIELD = DemoScenario(
    name="Greenfield Initialization",
    description="User initializes a new project from scratch",
    inputs=[
        "init",
        "I want to build a todo app with REST API",
        "yes",
        "exit"
    ]
)

SCENARIO_5_HELP_EXPLORATION = DemoScenario(
    name="Help and Exploration",
    description="New user explores capabilities",
    inputs=[
        "help",
        "What can you do?",
        "How do I create a PRD?",
        "exit"
    ]
)

SCENARIO_6_STATUS_CHECK = DemoScenario(
    name="Status Check and Next Steps",
    description="User checks project status and asks for recommendations",
    inputs=[
        "What's the status?",
        "What should I work on next?",
        "exit"
    ]
)

SCENARIO_7_CANCELLATION = DemoScenario(
    name="Cancellation Flow",
    description="User starts a request but then cancels",
    inputs=[
        "I want to build a complete e-commerce platform",
        "no",  # Decline after seeing scope
        "Actually, let's start with a simple product catalog",
        "yes",
        "exit"
    ]
)


# =============================================================================
# DEMO EXECUTION
# =============================================================================

async def run_scenario_demo(scenario: DemoScenario, project_root: Path) -> None:
    """
    Run a single demo scenario.

    Args:
        scenario: Demo scenario to run
        project_root: Project root path
    """
    console.print()
    console.print(
        Panel(
            f"[bold cyan]{scenario.name}[/bold cyan]\n\n{scenario.description}",
            title="Demo Scenario",
            border_style="cyan"
        )
    )
    console.print()

    # Show simulated inputs
    console.print("[dim]Simulated User Inputs:[/dim]")
    for i, user_input in enumerate(scenario.inputs, 1):
        console.print(f"  {i}. [yellow]{user_input}[/yellow]")
    console.print()

    # Note: In a real demo, you would actually run the REPL
    # For this demo script, we just show what would happen
    console.print("[dim]In a real session, this would:[/dim]")
    console.print("  1. Start ChatREPL")
    console.print("  2. Execute each input in sequence")
    console.print("  3. Show Brian's responses")
    console.print("  4. Exit gracefully")
    console.print()

    console.print("[green]Scenario demonstration complete![/green]")
    console.print()
    await asyncio.sleep(1)  # Pause between scenarios


async def demonstrate_session_state(project_root: Path) -> None:
    """
    Demonstrate session state persistence.

    Args:
        project_root: Project root path
    """
    console.print()
    console.print(
        Panel(
            "[bold magenta]Session State Demonstration[/bold magenta]\n\n"
            "Shows how conversation history is preserved across sessions",
            title="Session State",
            border_style="magenta"
        )
    )
    console.print()

    # Session 1
    console.print("[bold]Session 1:[/bold]")
    console.print("  User: I want to build a blog")
    console.print("  Brian: [Analyzes...]")
    console.print("  User: exit")
    console.print("  [Session saved to .gao-dev/last_session_history.json]")
    console.print()

    # Session 2
    console.print("[bold]Session 2 (later):[/bold]")
    console.print("  [REPL starts]")
    console.print("  Brian: Found previous session history from 2025-11-10")
    console.print("  [Context from Session 1 available]")
    console.print()

    console.print("[green]Session state demonstration complete![/green]")
    console.print()


async def demonstrate_error_recovery() -> None:
    """Demonstrate error handling and recovery."""
    console.print()
    console.print(
        Panel(
            "[bold red]Error Recovery Demonstration[/bold red]\n\n"
            "Shows how REPL handles errors gracefully",
            title="Error Handling",
            border_style="red"
        )
    )
    console.print()

    console.print("[bold]Scenario: Analysis Failure[/bold]")
    console.print("  User: Build something complex")
    console.print("  [Brian analysis fails - API error]")
    console.print("  Brian: I encountered an error analyzing your request: [error]")
    console.print("  Brian: Could you rephrase your request or provide more details?")
    console.print("  [REPL continues - no crash]")
    console.print()

    console.print("[bold]Scenario: Unclear Input[/bold]")
    console.print("  User: asdfqwer zxcv")
    console.print("  Brian: I'm not quite sure what you mean by 'asdfqwer zxcv...'")
    console.print("  Brian: Could you rephrase that? For example:")
    console.print("    - 'I want to build [feature]'")
    console.print("    - 'Help me fix [bug]'")
    console.print("  [REPL continues]")
    console.print()

    console.print("[green]Error recovery demonstration complete![/green]")
    console.print()


async def demonstrate_cancellation() -> None:
    """Demonstrate Ctrl+C cancellation."""
    console.print()
    console.print(
        Panel(
            "[bold yellow]Cancellation Demonstration[/bold yellow]\n\n"
            "Shows how Ctrl+C cancels operations without exiting REPL",
            title="Cancellation",
            border_style="yellow"
        )
    )
    console.print()

    console.print("[bold]Scenario: Cancel During Execution[/bold]")
    console.print("  User: Build a complete e-commerce platform")
    console.print("  Brian: [Starts executing 15 workflows...]")
    console.print("  Brian: [1/15] create_prd...")
    console.print("  [User presses Ctrl+C]")
    console.print()
    console.print("  [yellow]Operation cancelled by user[/yellow]")
    console.print()
    console.print("  You: [Can immediately try something else]")
    console.print("  [REPL continues - session preserved]")
    console.print()

    console.print("[green]Cancellation demonstration complete![/green]")
    console.print()


async def demonstrate_init_commands() -> None:
    """Demonstrate initialization commands."""
    console.print()
    console.print(
        Panel(
            "[bold blue]Initialization Commands Demonstration[/bold blue]\n\n"
            "Shows greenfield and brownfield project initialization",
            title="Init Commands",
            border_style="blue"
        )
    )
    console.print()

    # Greenfield
    console.print("[bold]Greenfield (New Project):[/bold]")
    console.print("  $ cd empty-directory")
    console.print("  $ gao-dev start")
    console.print()
    console.print("  Brian: No GAO-Dev project detected.")
    console.print("  Brian: Would you like to initialize? Type 'init' to get started.")
    console.print()
    console.print("  You: init")
    console.print()
    console.print("  Brian: Creating project structure...")
    console.print("  ✓ Project directories created")
    console.print("  ✓ Git repository initialized")
    console.print("  ✓ README.md created")
    console.print("  ✓ .gitignore created")
    console.print("  ✓ Initial commit created")
    console.print()

    # Brownfield
    console.print("[bold]Brownfield (Existing Project):[/bold]")
    console.print("  $ cd existing-flask-app")
    console.print("  $ gao-dev start")
    console.print()
    console.print("  You: init")
    console.print()
    console.print("  Brian: I see you have an existing project.")
    console.print("  Brian: Adding GAO-Dev tracking...")
    console.print("  ✓ Detected Python project with Flask")
    console.print("  ✓ Created .gao-dev/ directory")
    console.print("  ✓ Initialized document tracking")
    console.print("  ✓ Created initial README (preserved existing content)")
    console.print()

    console.print("[green]Initialization demonstration complete![/green]")
    console.print()


async def run_interactive_demo() -> None:
    """
    Run complete interactive demo showing all features.

    This is the main demo function that orchestrates all demonstrations.
    """
    console.print()
    console.print(
        Panel(
            Markdown("""
# Interactive Brian Chat - Complete Demo

This demo showcases all capabilities of the Interactive Brian Chat interface.

**What you'll see**:
- Common conversation patterns
- Multi-turn refinement
- Help system
- Initialization commands (greenfield & brownfield)
- Session state management
- Error handling and recovery
- Cancellation flows

**Note**: This is a simulated demo. In production, you would run:
```bash
gao-dev start
```
            """.strip()),
            title="[bold green]GAO-Dev Interactive Chat Demo[/bold green]",
            border_style="green"
        )
    )
    console.print()

    # Create temporary project for demos
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir) / "demo_project"
        project_root.mkdir()
        (project_root / ".gao-dev").mkdir()

        # Run all scenario demos
        scenarios = [
            SCENARIO_1_NEW_FEATURE,
            SCENARIO_2_MULTI_TURN,
            SCENARIO_3_BUG_FIX,
            SCENARIO_4_GREENFIELD,
            SCENARIO_5_HELP_EXPLORATION,
            SCENARIO_6_STATUS_CHECK,
            SCENARIO_7_CANCELLATION,
        ]

        console.print("[bold cyan]PART 1: Common Scenarios[/bold cyan]")
        console.print()

        for scenario in scenarios:
            await run_scenario_demo(scenario, project_root)

        # Demonstrate special features
        console.print("[bold cyan]PART 2: Special Features[/bold cyan]")
        console.print()

        await demonstrate_init_commands()
        await demonstrate_session_state(project_root)
        await demonstrate_error_recovery()
        await demonstrate_cancellation()

    # Summary
    console.print()
    console.print(
        Panel(
            Markdown("""
# Demo Complete!

You've seen all major features of the Interactive Brian Chat interface.

**To try it yourself**:
```bash
gao-dev start
```

**Quick Tips**:
- Just type naturally - Brian understands
- Use 'help' if you get stuck
- Type 'init' in empty directories to start new projects
- Press Ctrl+C to cancel operations (REPL continues)
- Session history is automatically saved

**Learn More**:
- User Guide: docs/features/interactive-brian-chat/USER_GUIDE.md
- Architecture: docs/features/interactive-brian-chat/ARCHITECTURE.md
- PRD: docs/features/interactive-brian-chat/PRD.md

Happy building! 🚀
            """.strip()),
            title="[bold green]Thanks for Watching![/bold green]",
            border_style="green"
        )
    )
    console.print()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main() -> None:
    """Main entry point for demo script."""
    try:
        await run_interactive_demo()
    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print()
        console.print(f"[red]Demo error: {e}[/red]")
        logger.exception("demo_error", error=str(e))


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
