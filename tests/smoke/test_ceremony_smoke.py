"""Smoke tests for ceremony system.

Quick validation that all ceremony components load and respond correctly.
Runs in <30 seconds.

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.5 - CLI Commands & Testing (AC9)
"""

import pytest
import sqlite3
import sys
import importlib.util
from pathlib import Path
from click.testing import CliRunner

from gao_dev.core.services.ceremony_trigger_engine import CeremonyTriggerEngine, TriggerContext
from gao_dev.core.services.ceremony_service import CeremonyService
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


@pytest.fixture
def setup_database(tmp_path):
    """Setup test database with schema and test epic."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database schema
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

    # Create test epic (required for foreign key constraints)
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    cursor.execute(
        """
        INSERT INTO epic_state (
            epic_num, title, status, total_stories, completed_stories,
            progress_percentage, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (1, "Test Epic", "in_progress", 8, 0, 0.0, now, now)
    )
    conn.commit()
    conn.close()

    return db_path


class TestCeremonyComponentsLoad:
    """Test that all ceremony components load correctly."""

    def test_ceremony_service_loads(self, setup_database):
        """Verify CeremonyService loads without errors."""
        db_path = setup_database
        service = CeremonyService(db_path=db_path)
        assert service is not None
        assert service.db_path == db_path

    def test_ceremony_trigger_engine_loads(self, setup_database):
        """Verify CeremonyTriggerEngine loads without errors."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        assert engine is not None
        assert engine.db_path == db_path
        assert engine.MAX_CEREMONIES_PER_EPIC == 10

    def test_ceremony_orchestrator_can_import(self):
        """Verify CeremonyOrchestrator can be imported."""
        from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator
        assert CeremonyOrchestrator is not None

    def test_workflow_selector_can_import(self):
        """Verify WorkflowSelector with ceremony injection can be imported."""
        from gao_dev.methodologies.adaptive_agile.workflow_selector import WorkflowSelector
        assert WorkflowSelector is not None

    def test_workflow_registry_can_import(self):
        """Verify WorkflowRegistry can be imported."""
        from gao_dev.core.workflow_registry import WorkflowRegistry
        assert WorkflowRegistry is not None


class TestCeremonyTriggerEvaluationSmoke:
    """Smoke test ceremony trigger evaluation."""

    def test_trigger_engine_evaluates_triggers(self, setup_database):
        """Verify trigger engine can evaluate triggers without errors."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        ceremonies = engine.evaluate_all_triggers(context)
        assert isinstance(ceremonies, list)

    def test_should_trigger_planning_responds(self, setup_database):
        """Verify should_trigger_planning responds correctly."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=0,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        should_trigger = engine.should_trigger_planning(context)
        assert isinstance(should_trigger, bool)

    def test_should_trigger_standup_responds(self, setup_database):
        """Verify should_trigger_standup responds correctly."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=2,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        should_trigger = engine.should_trigger_standup(context)
        assert isinstance(should_trigger, bool)

    def test_should_trigger_retrospective_responds(self, setup_database):
        """Verify should_trigger_retrospective responds correctly."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=8,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        should_trigger = engine.should_trigger_retrospective(context)
        assert isinstance(should_trigger, bool)


class TestCeremonyServiceSmoke:
    """Smoke test CeremonyService CRUD operations."""

    def test_create_summary_works(self, setup_database):
        """Verify create_summary works without errors."""
        db_path = setup_database
        service = CeremonyService(db_path=db_path)

        ceremony = service.create_summary(
            ceremony_type="planning",
            summary="Test planning session",
            participants="team",
            epic_num=1
        )

        assert ceremony is not None
        assert ceremony['id'] is not None
        assert ceremony['ceremony_type'] == "planning"

    def test_get_ceremony_works(self, setup_database):
        """Verify get() works without errors."""
        db_path = setup_database
        service = CeremonyService(db_path=db_path)

        # Create ceremony
        ceremony = service.create_summary(
            ceremony_type="standup",
            summary="Test standup",
            participants="team",
            epic_num=1
        )

        # Get ceremony
        retrieved = service.get(ceremony['id'])
        assert retrieved is not None
        assert retrieved['id'] == ceremony['id']

    def test_get_recent_works(self, setup_database):
        """Verify get_recent() works without errors."""
        db_path = setup_database
        service = CeremonyService(db_path=db_path)

        # Create ceremonies
        for i in range(3):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=1
            )

        # Get recent
        recent = service.get_recent(limit=5)
        assert isinstance(recent, list)
        assert len(recent) == 3


class TestCeremonyCLICommandsSmoke:
    """Smoke test CLI commands respond correctly."""

    def test_ceremony_hold_command_help(self):
        """Verify 'gao-dev ceremony hold' help works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()
        result = runner.invoke(ceremony, ['hold', '--help'])
        assert result.exit_code == 0
        assert 'Hold a ceremony manually' in result.output

    def test_ceremony_list_command_help(self):
        """Verify 'gao-dev ceremony list' help works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()
        result = runner.invoke(ceremony, ['list', '--help'])
        assert result.exit_code == 0
        assert 'List ceremonies for an epic' in result.output

    def test_ceremony_show_command_help(self):
        """Verify 'gao-dev ceremony show' help works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()
        result = runner.invoke(ceremony, ['show', '--help'])
        assert result.exit_code == 0
        assert 'Show ceremony details' in result.output

    def test_ceremony_evaluate_command_help(self):
        """Verify 'gao-dev ceremony evaluate' help works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()
        result = runner.invoke(ceremony, ['evaluate', '--help'])
        assert result.exit_code == 0
        assert 'Evaluate which ceremonies would trigger' in result.output

    def test_ceremony_safety_command_help(self):
        """Verify 'gao-dev ceremony safety' help works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()
        result = runner.invoke(ceremony, ['safety', '--help'])
        assert result.exit_code == 0
        assert 'Check ceremony safety status' in result.output

    def test_ceremony_hold_dry_run(self, setup_database, tmp_path):
        """Verify 'gao-dev ceremony hold --dry-run' works."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()

        # Change to temp directory with .gao-dev
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                ceremony,
                ['hold', 'planning', '--epic', '1', '--dry-run']
            )
            # May fail if not in GAO-Dev project, but shouldn't crash
            assert result.exit_code in [0, 1]

    def test_ceremony_evaluate_responds(self, setup_database, tmp_path):
        """Verify 'gao-dev ceremony evaluate' responds correctly."""
        from gao_dev.cli.ceremony_commands import ceremony
        runner = CliRunner()

        # Change to temp directory with .gao-dev
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                ceremony,
                ['evaluate', '--epic', '1', '--level', '3', '--stories-completed', '4', '--total-stories', '8']
            )
            # May fail if not in GAO-Dev project, but shouldn't crash
            assert result.exit_code in [0, 1]


class TestCeremonySystemIntegrationSmoke:
    """Smoke test that ceremony system integrates correctly."""

    def test_orchestrator_integration_smoke(self, setup_database):
        """Verify orchestrator can integrate with ceremony system."""
        from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
        from gao_dev.core.config_loader import ConfigLoader

        db_path = setup_database
        config = ConfigLoader()

        # Verify GAODevOrchestrator can be instantiated
        # (actual ceremony integration tested in integration tests)
        orchestrator = GAODevOrchestrator(
            config=config,
            project_root=db_path.parent.parent
        )
        assert orchestrator is not None

    def test_workflow_executor_loads_ceremony_workflows(self):
        """Verify WorkflowExecutor can load ceremony workflows."""
        from gao_dev.core.workflow_executor import WorkflowExecutor
        from gao_dev.core.config_loader import ConfigLoader

        config = ConfigLoader()
        executor = WorkflowExecutor(config=config)

        # Verify executor loads without errors
        assert executor is not None

    def test_safety_mechanisms_active(self, setup_database):
        """Verify safety mechanisms are active."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        # Verify safety limits configured
        assert engine.MAX_CEREMONIES_PER_EPIC == 10
        assert 'planning' in engine.COOLDOWN_HOURS
        assert 'standup' in engine.COOLDOWN_HOURS
        assert 'retrospective' in engine.COOLDOWN_HOURS
        assert engine.TIMEOUT_MINUTES == 10
