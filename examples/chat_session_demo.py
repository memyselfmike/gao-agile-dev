"""
Demo script for ChatSession - Story 30.5 Session State Management.

Demonstrates:
1. Multi-turn conversation with context
2. Bounded history (150 turns -> only 100 kept)
3. Memory monitoring and warnings
4. AI context management with token limits
5. Cancellation support
6. Session persistence (save/load)

Usage:
    python examples/chat_session_demo.py
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from gao_dev.orchestrator.chat_session import ChatSession, Turn


async def demo_multi_turn_conversation():
    """Demo 1: Multi-turn conversation with context."""
    print("=" * 60)
    print("DEMO 1: Multi-Turn Conversation with Context")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    async def mock_response_1(*args, **kwargs):
        yield "I can help you build a todo app with authentication."
        yield "Let me analyze your request..."

    async def mock_response_2(*args, **kwargs):
        yield "Building on your previous request..."
        yield "I'll add real-time notifications to the todo app."

    mock_brian.handle_input = mock_response_1

    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path.cwd()
    )

    # Turn 1: Initial request
    print("\nUser: Build a todo app with authentication")
    async for response in session.handle_input("Build a todo app with authentication"):
        print(f"Brian: {response}")

    # Turn 2: Follow-up request (uses context)
    print("\nUser: And add real-time notifications")
    mock_brian.handle_input = mock_response_2
    async for response in session.handle_input("And add real-time notifications"):
        print(f"Brian: {response}")

    # Show conversation history
    print("\n--- Conversation History ---")
    for i, turn in enumerate(session.history, 1):
        print(f"{i}. {turn.role.upper()}: {turn.content[:60]}...")

    print(f"\nTotal turns: {len(session.history)}")


async def demo_bounded_history():
    """Demo 2: Bounded history (150 turns -> 100 kept)."""
    print("\n" + "=" * 60)
    print("DEMO 2: Bounded History (150 turns -> 100 kept)")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path.cwd(),
        max_history=100  # Explicit for demo
    )

    # Add 150 turns
    print("\nAdding 150 conversation turns...")
    for i in range(150):
        session._add_turn("user", f"Message {i}")

    print(f"History after 150 turns: {len(session.history)} (should be 100)")

    # Check what was kept
    first_msg = session.history[0].content
    last_msg = session.history[-1].content

    print(f"First message kept: {first_msg}")
    print(f"Last message kept: {last_msg}")

    # Verify oldest removed
    all_contents = [t.content for t in session.history]
    print(f"\nMessage 0 in history: {'Message 0' in all_contents} (should be False)")
    print(f"Message 149 in history: {'Message 149' in all_contents} (should be True)")


def demo_memory_monitoring():
    """Demo 3: Memory monitoring and warnings."""
    print("\n" + "=" * 60)
    print("DEMO 3: Memory Monitoring and Warnings")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path.cwd()
    )

    # Check memory at different levels
    levels = [0, 25, 50, 80, 100]

    for level in levels:
        # Clear and add turns
        session.history.clear()
        for i in range(level):
            session._add_turn("user", f"Message {i}")

        stats = session.get_memory_usage()

        print(f"\nAt {level} turns:")
        print(f"  Turn count: {stats['turn_count']}")
        print(f"  Usage: {stats['usage_percent']:.1f}%")
        print(f"  Memory: {stats['memory_mb']:.2f} MB")
        print(f"  Near limit: {stats['near_limit']}")


def demo_ai_context_management():
    """Demo 4: AI context management with token limits."""
    print("\n" + "=" * 60)
    print("DEMO 4: AI Context Management (Token Limits)")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path.cwd()
    )

    # Add system message
    session._add_turn("system", "Session started")

    # Add 20 long messages (each ~1000 chars = 250 tokens)
    print("\nAdding 20 long messages (each ~250 tokens)...")
    for i in range(20):
        session._add_turn("user", "x" * 1000)

    # Get AI context with different token limits
    limits = [500, 1000, 2000, 4000]

    for limit in limits:
        context = session.get_context_for_ai(max_tokens=limit)
        system_count = sum(1 for t in context if t.role == "system")
        user_count = sum(1 for t in context if t.role == "user")

        print(f"\nToken limit: {limit}")
        print(f"  Total turns included: {len(context)}")
        print(f"  System messages: {system_count}")
        print(f"  User messages: {user_count}")


async def demo_cancellation_support():
    """Demo 5: Cancellation support."""
    print("\n" + "=" * 60)
    print("DEMO 5: Cancellation Support")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    async def slow_response(*args, **kwargs):
        yield "Starting operation..."
        await asyncio.sleep(0.5)
        yield "Working..."
        await asyncio.sleep(0.5)
        yield "Almost done..."

    mock_brian.handle_input = slow_response

    session = ChatSession(
        conversational_brian=mock_brian,
        command_router=mock_router,
        project_root=Path.cwd()
    )

    print("\nStarting operation...")

    # Start operation and cancel after 0.3 seconds
    async def run_with_cancel():
        try:
            responses = []
            async for response in session.handle_input("Long operation"):
                responses.append(response)
                print(f"  Received: {response}")

                # Simulate user pressing Ctrl+C after first response
                if len(responses) == 1:
                    print("\n[User presses Ctrl+C]")
                    session.cancel_event.set()

        except asyncio.CancelledError:
            print("\nOperation cancelled!")

    await run_with_cancel()

    # Check cancellation state
    print(f"\nCancellation state: {session.is_cancelled}")

    # Reset for next operation
    session.reset_cancellation()
    print(f"After reset: {session.is_cancelled}")


def demo_session_persistence():
    """Demo 6: Session persistence (save/load)."""
    print("\n" + "=" * 60)
    print("DEMO 6: Session Persistence (Save/Load)")
    print("=" * 60)

    # Setup mocks
    mock_brian = MagicMock()
    mock_router = MagicMock()

    # Create temp directory for demo
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        (project_root / ".gao-dev").mkdir()

        # Create session 1
        session1 = ChatSession(
            conversational_brian=mock_brian,
            command_router=mock_router,
            project_root=project_root
        )

        # Add conversation history
        print("\nSession 1: Adding conversation...")
        session1._add_turn("user", "Build a todo app")
        session1._add_turn("brian", "I can help with that")
        session1._add_turn("user", "Add authentication")
        session1._add_turn("brian", "Sure thing")
        session1.set_current_epic(5)

        print(f"  Turns: {len(session1.history)}")
        print(f"  Epic: {session1.context.current_epic}")

        # Save session
        save_path = session1.save_session()
        print(f"\nSession saved to: {save_path}")

        # Create session 2 and load
        session2 = ChatSession(
            conversational_brian=mock_brian,
            command_router=mock_router,
            project_root=project_root
        )

        print("\nSession 2: Loading previous session...")
        success = session2.load_session()

        print(f"  Load success: {success}")
        print(f"  Turns restored: {len(session2.history)}")
        print(f"  Epic restored: {session2.context.current_epic}")

        # Verify content
        print("\nRestored conversation:")
        for turn in session2.history:
            print(f"  {turn.role}: {turn.content}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("ChatSession Demo - Story 30.5")
    print("Session State Management")
    print("=" * 60)

    # Run all demos
    await demo_multi_turn_conversation()
    await demo_bounded_history()
    demo_memory_monitoring()
    demo_ai_context_management()
    await demo_cancellation_support()
    demo_session_persistence()

    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
