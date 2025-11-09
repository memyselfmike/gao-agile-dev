"""Integration tests for ceremony orchestration.

Tests end-to-end ceremony orchestration including:
- Atomic transactions (C3 fix)
- Failure handling policies (C9 fix)
- Trigger evaluation
- Context flow

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.4 - Orchestrator Integration with Atomic Ceremonies
"""

import pytest
import sqlite3
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator, CeremonyExecutionError
from gao_dev.core.services.ceremony_trigger_engine import (
    CeremonyTriggerEngine,
    TriggerContext,
    CeremonyType
)
from gao_dev.core.services.ceremony_failure_handler import (
    CeremonyFailureHandler,
    CeremonyFailurePolicy
)
from gao_dev.core.services.git_integrated_state_manager import (
    GitIntegratedStateManager,
    WorkingTreeDirtyError
)
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel


def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent
        / "gao_dev"
        / "lifecycle"
        / "migrations"
        / "005_add_state_tables.py"
    )
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()


class TestCeremonyOrchestratorAtomicTransactions:
    """Test atomic transaction behavior (C3 Fix)."""

    def test_ceremony_commits_atomically_on_success(self, tmp_path):
        """Successful ceremony creates atomic commit with all artifacts."""
        # Setup
        from gao_dev.core.config_loader import ConfigLoader
        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema using Migration005
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT
            )
            """
        )
        conn.commit()
        Migration005.up(conn)
        conn.close()

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        git_state_manager = GitIntegratedStateManager(
            db_path=db_path,
            project_path=tmp_path,
            auto_commit=True
        )

        config = ConfigLoader(tmp_path)
        orchestrator = CeremonyOrchestrator(
            config=config,
            db_path=db_path,
            project_root=tmp_path,
            git_state_manager=git_state_manager
        )

        # Create epic in database (prerequisite)
        git_state_manager.coordinator.create_epic(
            epic_num=1,
            title="Test Epic",
            status="in_progress",
            total_stories=5
        )

        # Ensure working tree is clean before ceremony
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Setup epic"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        # Execute ceremony
        result = orchestrator.hold_standup(
            epic_num=1,
            participants=["Amelia", "Bob"]
        )

        # Verify results
        assert result is not None
        assert "ceremony_id" in result
        assert "transcript_path" in result
        assert "action_items" in result

        # Verify transcript file exists
        transcript_path = Path(result["transcript_path"])
        assert transcript_path.exists()
        assert transcript_path.read_text()

        # Verify git commit was created
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True
        )
        assert "ceremony" in git_log.stdout.lower()

        # Cleanup
        git_state_manager.close()
        orchestrator.close()

    def test_ceremony_rolls_back_on_failure(self, tmp_path):
        """Failed ceremony rolls back all changes (file + DB + git)."""
        # Setup
        from gao_dev.core.config_loader import ConfigLoader
        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema using Migration005
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT
            )
            """
        )
        conn.commit()
        Migration005.up(conn)
        conn.close()

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        git_state_manager = GitIntegratedStateManager(
            db_path=db_path,
            project_path=tmp_path,
            auto_commit=True
        )

        config = ConfigLoader(tmp_path)
        orchestrator = CeremonyOrchestrator(
            config=config,
            db_path=db_path,
            project_root=tmp_path,
            git_state_manager=git_state_manager
        )

        # Create epic in database
        git_state_manager.coordinator.create_epic(
            epic_num=1,
            title="Test Epic",
            status="in_progress",
            total_stories=5
        )

        # Inject failure by patching _execute_ceremony
        with patch.object(orchestrator, '_execute_ceremony', side_effect=Exception("Simulated failure")):
            # Execute ceremony (should fail and rollback)
            with pytest.raises(CeremonyExecutionError):
                orchestrator.hold_standup(
                    epic_num=1,
                    participants=["Amelia", "Bob"]
                )

        # Verify NO ceremony artifacts exist
        ceremonies_dir = tmp_path / ".gao-dev" / "ceremonies"
        if ceremonies_dir.exists():
            # Directory might exist, but should have no ceremony files
            ceremony_files = list(ceremonies_dir.glob("standup_epic1_*.txt"))
            assert len(ceremony_files) == 0, "Ceremony transcript should not exist after rollback"

        # Verify git log shows only initial commit (rollback worked)
        git_log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True
        )
        lines = [line for line in git_log.stdout.split("\n") if line.strip()]
        assert len(lines) == 1, "Should only have initial commit after rollback"
        assert "initial" in lines[0].lower()

        # Cleanup
        git_state_manager.close()
        orchestrator.close()


class TestCeremonyFailureHandling:
    """Test failure handling policies (C9 Fix)."""

    def test_abort_policy_for_planning_ceremony(self):
        """Planning ceremony failure returns ABORT policy."""
        handler = CeremonyFailureHandler()

        error = Exception("Planning failed")
        policy = handler.handle_failure(
            ceremony_type="planning",
            epic_num=1,
            error=error
        )

        assert policy == CeremonyFailurePolicy.ABORT

    def test_continue_policy_for_standup_ceremony(self):
        """Standup ceremony failure returns CONTINUE policy."""
        handler = CeremonyFailureHandler()

        error = Exception("Standup failed")
        policy = handler.handle_failure(
            ceremony_type="standup",
            epic_num=1,
            error=error
        )

        assert policy == CeremonyFailurePolicy.CONTINUE

    def test_retry_policy_for_retrospective_ceremony(self):
        """Retrospective ceremony failure returns RETRY policy."""
        handler = CeremonyFailureHandler()

        error = Exception("Retrospective failed")
        policy = handler.handle_failure(
            ceremony_type="retrospective",
            epic_num=1,
            error=error
        )

        assert policy == CeremonyFailurePolicy.RETRY

    def test_circuit_breaker_triggers_after_3_failures(self):
        """Circuit breaker opens after 3 consecutive failures."""
        handler = CeremonyFailureHandler()

        error = Exception("Failure")

        # First 3 failures return configured policy
        for i in range(3):
            policy = handler.handle_failure(
                ceremony_type="planning",
                epic_num=1,
                error=error
            )
            if i < 2:
                assert policy == CeremonyFailurePolicy.ABORT
            else:
                # 3rd failure triggers circuit breaker
                assert policy == CeremonyFailurePolicy.SKIP

        # 4th failure returns SKIP (circuit is open)
        policy = handler.handle_failure(
            ceremony_type="planning",
            epic_num=1,
            error=error
        )
        assert policy == CeremonyFailurePolicy.SKIP

    def test_reset_failures_closes_circuit_breaker(self):
        """Reset failures closes circuit breaker."""
        handler = CeremonyFailureHandler()

        error = Exception("Failure")

        # Trigger circuit breaker
        for _ in range(3):
            handler.handle_failure(
                ceremony_type="planning",
                epic_num=1,
                error=error
            )

        # Verify circuit is open
        assert handler.is_circuit_open("planning", 1)

        # Reset failures
        handler.reset_failures("planning", 1)

        # Verify circuit is closed
        assert not handler.is_circuit_open("planning", 1)

        # Verify failure count is reset
        assert handler.get_failure_count("planning", 1) == 0


class TestCeremonyTriggerEvaluation:
    """Test ceremony trigger evaluation."""

    def test_planning_triggers_at_epic_start_level_3(self, tmp_path):
        """Planning ceremony triggers at epic start for Level 3."""
        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=0,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )

        ceremonies = engine.evaluate_all_triggers(context)

        # Planning should trigger at start
        assert CeremonyType.PLANNING in ceremonies

        engine.close()

    def test_standup_triggers_every_2_stories_level_3(self, tmp_path):
        """Standup triggers every 2 stories for Level 3."""
        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=2,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )

        ceremonies = engine.evaluate_all_triggers(context)

        # Standup should trigger at 2 stories
        assert CeremonyType.STANDUP in ceremonies

        engine.close()

    def test_retrospective_triggers_at_epic_completion(self, tmp_path):
        """Retrospective triggers at epic completion."""
        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=10,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )

        ceremonies = engine.evaluate_all_triggers(context)

        # Retrospective should trigger at completion
        assert CeremonyType.RETROSPECTIVE in ceremonies

        engine.close()


class TestCeremonyContextFlow:
    """Test ceremony results flow into workflow context."""

    def test_ceremony_results_update_context(self, tmp_path):
        """Ceremony results are added to workflow context."""
        from gao_dev.core.services.workflow_coordinator import WorkflowCoordinator

        db_path = tmp_path / ".gao-dev" / "documents.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create minimal workflow coordinator
        coordinator = WorkflowCoordinator(
            workflow_registry=Mock(),
            agent_factory=Mock(),
            event_bus=Mock(),
            agent_executor=Mock(),
            project_root=tmp_path,
            db_path=db_path
        )

        # Create context
        context = {}

        # Create mock ceremony result
        ceremony_result = {
            'ceremony_type': 'standup',
            'ceremony_id': 1,
            'transcript_path': '/path/to/transcript.txt',
            'action_items': [
                {'title': 'Fix bug', 'assignee': 'Amelia'}
            ],
            'learnings': []
        }

        # Update context with ceremony
        coordinator._update_context_with_ceremony(context, ceremony_result)

        # Verify context updated
        assert 'ceremonies' in context
        assert len(context['ceremonies']) == 1
        assert context['ceremonies'][0]['type'] == 'standup'
        assert context['ceremonies'][0]['id'] == 1
        assert len(context['ceremonies'][0]['action_items']) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
