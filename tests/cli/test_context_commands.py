"""
Unit tests for context CLI commands.

Tests all 6 context commands:
1. show - Show context details
2. list - List recent contexts
3. history - Show context versions
4. lineage - Show document lineage
5. stats - Show cache/usage statistics
6. clear-cache - Clear context cache
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from gao_dev.cli.context_commands import (
    context,
    show_context,
    list_contexts,
    show_history,
    show_lineage,
    show_stats,
    clear_cache
)
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.core.context.context_lineage import ContextLineageTracker


@pytest.fixture
def runner():
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_context():
    """Create sample WorkflowContext for testing."""
    return WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=17,
        story_num=5,
        feature="context-system-integration",
        workflow_name="implement_story",
        current_phase="implementation",
        status="running",
        decisions={"use_rich": True, "support_json": True},
        artifacts=["gao_dev/cli/context_commands.py"],
        errors=[]
    )


@pytest.fixture
def mock_persistence(sample_context):
    """Mock ContextPersistence."""
    with patch("gao_dev.cli.context_commands.ContextPersistence") as mock:
        instance = mock.return_value
        instance.load_context.return_value = sample_context
        instance.search_contexts.return_value = [sample_context]
        instance.get_context_versions.return_value = [sample_context]
        yield instance


@pytest.fixture
def mock_cache():
    """Mock ContextCache."""
    with patch("gao_dev.cli.context_commands._get_global_cache") as mock:
        cache = mock.return_value
        cache.get_statistics.return_value = {
            "hits": 100,
            "misses": 25,
            "evictions": 5,
            "expirations": 10,
            "size": 50,
            "max_size": 100,
            "hit_rate": 0.8,
            "memory_usage": 1024000
        }
        yield cache


@pytest.fixture
def mock_tracker():
    """Mock ContextUsageTracker."""
    with patch("gao_dev.cli.context_commands._get_global_tracker") as mock:
        tracker = mock.return_value
        tracker.get_cache_hit_rate.return_value = {
            "total": 125,
            "hits": 100,
            "misses": 25,
            "hit_rate": 0.8
        }
        yield tracker


@pytest.fixture
def mock_lineage_tracker():
    """Mock ContextLineageTracker."""
    with patch("gao_dev.cli.context_commands.ContextLineageTracker") as mock:
        instance = mock.return_value
        instance.generate_lineage_report.return_value = "# Lineage Report\nTest content"
        yield instance


class TestShowContext:
    """Tests for 'gao-dev context show' command."""

    def test_show_context_success(self, runner, mock_persistence):
        """Test showing context details."""
        result = runner.invoke(show_context, ["test-workflow-id"])

        assert result.exit_code == 0
        assert "Workflow Context" in result.output
        assert "Context Details" in result.output
        mock_persistence.load_context.assert_called_once_with("test-workflow-id")

    def test_show_context_json_output(self, runner, mock_persistence, sample_context):
        """Test JSON output format."""
        result = runner.invoke(show_context, ["test-workflow-id", "--json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["workflow_id"] == sample_context.workflow_id
        assert output_data["epic_num"] == 17
        assert output_data["story_num"] == 5

    def test_show_context_not_found(self, runner, mock_persistence):
        """Test handling of non-existent context."""
        from gao_dev.core.context.exceptions import ContextNotFoundError
        mock_persistence.load_context.side_effect = ContextNotFoundError("Not found")

        result = runner.invoke(show_context, ["non-existent-id"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_show_context_displays_decisions(self, runner, mock_persistence):
        """Test that decisions are displayed."""
        result = runner.invoke(show_context, ["test-workflow-id"])

        assert result.exit_code == 0
        assert "Decisions" in result.output
        assert "use_rich" in result.output

    def test_show_context_displays_artifacts(self, runner, mock_persistence):
        """Test that artifacts are displayed."""
        result = runner.invoke(show_context, ["test-workflow-id"])

        assert result.exit_code == 0
        assert "Artifacts" in result.output
        assert "context_commands.py" in result.output


class TestListContexts:
    """Tests for 'gao-dev context list' command."""

    def test_list_contexts_default(self, runner, mock_persistence):
        """Test listing contexts with default options."""
        result = runner.invoke(list_contexts, [])

        assert result.exit_code == 0
        assert "Recent Workflow Contexts" in result.output
        mock_persistence.search_contexts.assert_called_once()

    def test_list_contexts_with_filters(self, runner, mock_persistence):
        """Test listing with filters."""
        result = runner.invoke(list_contexts, [
            "--epic", "17",
            "--feature", "context-system",
            "--status", "running"
        ])

        assert result.exit_code == 0
        call_args = mock_persistence.search_contexts.call_args
        filters = call_args.kwargs['filters']
        assert filters['epic_num'] == 17
        assert filters['feature'] == "context-system"
        assert filters['status'] == "running"

    def test_list_contexts_json_output(self, runner, mock_persistence, sample_context):
        """Test JSON output format."""
        result = runner.invoke(list_contexts, ["--json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert len(output_data) > 0
        assert output_data[0]["epic_num"] == 17

    def test_list_contexts_empty_results(self, runner, mock_persistence):
        """Test handling of empty results."""
        mock_persistence.search_contexts.return_value = []

        result = runner.invoke(list_contexts, [])

        assert result.exit_code == 0
        assert "No contexts found" in result.output

    def test_list_contexts_custom_limit(self, runner, mock_persistence):
        """Test custom limit parameter."""
        result = runner.invoke(list_contexts, ["--limit", "50"])

        assert result.exit_code == 0
        call_args = mock_persistence.search_contexts.call_args
        assert call_args.kwargs['limit'] == 50


class TestShowHistory:
    """Tests for 'gao-dev context history' command."""

    def test_show_history_success(self, runner, mock_persistence):
        """Test showing context history."""
        result = runner.invoke(show_history, ["17", "5"])

        assert result.exit_code == 0
        assert "Context History for Story 17.5" in result.output
        mock_persistence.get_context_versions.assert_called_once_with(
            epic_num=17, story_num=5
        )

    def test_show_history_json_output(self, runner, mock_persistence, sample_context):
        """Test JSON output format."""
        result = runner.invoke(show_history, ["17", "5", "--json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert len(output_data) > 0

    def test_show_history_no_results(self, runner, mock_persistence):
        """Test handling of no history."""
        mock_persistence.get_context_versions.return_value = []

        result = runner.invoke(show_history, ["17", "5"])

        assert result.exit_code == 0
        assert "No context history found" in result.output

    def test_show_history_displays_versions(self, runner, mock_persistence, sample_context):
        """Test that version history is displayed."""
        # Create multiple versions
        versions = []
        for i in range(3):
            ctx = WorkflowContext(
                workflow_id=str(uuid.uuid4()),
                epic_num=17,
                story_num=5,
                feature="context-system",
                workflow_name=f"workflow_{i}",
                current_phase="implementation",
                status="completed" if i < 2 else "running"
            )
            versions.append(ctx)

        mock_persistence.get_context_versions.return_value = versions

        result = runner.invoke(show_history, ["17", "5"])

        assert result.exit_code == 0
        # Check that table contains version count
        assert "Total versions: 3" in result.output
        # Check that all three versions appear in table (at least workflow IDs)
        assert result.output.count("...") >= 3  # Each workflow ID is truncated with "..."


class TestShowLineage:
    """Tests for 'gao-dev context lineage' command."""

    def test_show_lineage_success(self, runner, mock_lineage_tracker):
        """Test showing document lineage."""
        result = runner.invoke(show_lineage, ["17"])

        assert result.exit_code == 0
        assert "Document Lineage - Epic 17" in result.output
        mock_lineage_tracker.generate_lineage_report.assert_called_once_with(
            epic=17, output_format="markdown"
        )

    def test_show_lineage_json_output(self, runner, mock_lineage_tracker):
        """Test JSON output format."""
        mock_lineage_tracker.generate_lineage_report.return_value = json.dumps({
            "epic": 17,
            "lineage": []
        })

        result = runner.invoke(show_lineage, ["17", "--json"])

        assert result.exit_code == 0
        mock_lineage_tracker.generate_lineage_report.assert_called_once_with(
            epic=17, output_format="json"
        )

    def test_show_lineage_displays_report(self, runner, mock_lineage_tracker):
        """Test that lineage report is displayed."""
        result = runner.invoke(show_lineage, ["17"])

        assert result.exit_code == 0
        # Should contain the mock report content
        assert "Lineage Report" in result.output or "Document Lineage" in result.output


class TestShowStats:
    """Tests for 'gao-dev context stats' command."""

    def test_show_stats_default(self, runner, mock_cache, mock_tracker):
        """Test showing statistics with default options."""
        result = runner.invoke(show_stats, [])

        assert result.exit_code == 0
        assert "Context Cache & Usage Statistics" in result.output
        assert "Cache Statistics" in result.output
        assert "Usage Statistics" in result.output

    def test_show_stats_json_output(self, runner, mock_cache, mock_tracker):
        """Test JSON output format."""
        result = runner.invoke(show_stats, ["--json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert "cache" in output_data
        assert "usage" in output_data
        assert output_data["cache"]["hits"] == 100
        assert output_data["usage"]["total"] == 125

    def test_show_stats_with_workflow_filter(self, runner, mock_cache, mock_tracker):
        """Test statistics with workflow filter."""
        result = runner.invoke(show_stats, ["--workflow-id", "test-workflow"])

        assert result.exit_code == 0
        assert "Filters applied" in result.output
        mock_tracker.get_cache_hit_rate.assert_called_once_with(
            workflow_id="test-workflow",
            context_key=None
        )

    def test_show_stats_with_context_key_filter(self, runner, mock_cache, mock_tracker):
        """Test statistics with context key filter."""
        result = runner.invoke(show_stats, ["--context-key", "epic_definition"])

        assert result.exit_code == 0
        assert "Filters applied" in result.output
        mock_tracker.get_cache_hit_rate.assert_called_once_with(
            workflow_id=None,
            context_key="epic_definition"
        )

    def test_show_stats_displays_metrics(self, runner, mock_cache, mock_tracker):
        """Test that metrics are displayed correctly."""
        result = runner.invoke(show_stats, [])

        assert result.exit_code == 0
        # Cache metrics
        assert "50 / 100" in result.output  # size / max_size
        assert "100" in result.output  # hits
        assert "80.00%" in result.output  # hit rate
        # Usage metrics
        assert "125" in result.output  # total


class TestClearCache:
    """Tests for 'gao-dev context clear-cache' command."""

    def test_clear_cache_with_confirm_flag(self, runner, mock_cache):
        """Test clearing cache with --confirm flag."""
        result = runner.invoke(clear_cache, ["--confirm"])

        assert result.exit_code == 0
        assert "Cache Cleared Successfully" in result.output
        mock_cache.clear.assert_called_once()

    def test_clear_cache_with_interactive_confirm(self, runner, mock_cache):
        """Test clearing cache with interactive confirmation."""
        result = runner.invoke(clear_cache, input="y\n")

        assert result.exit_code == 0
        assert "Cache Cleared Successfully" in result.output
        mock_cache.clear.assert_called_once()

    def test_clear_cache_cancelled(self, runner, mock_cache):
        """Test cancelling cache clear."""
        result = runner.invoke(clear_cache, input="n\n")

        assert result.exit_code == 0
        assert "cancelled" in result.output
        mock_cache.clear.assert_not_called()

    def test_clear_cache_displays_stats(self, runner, mock_cache):
        """Test that before/after stats are displayed."""
        # Set up stats for before and after
        mock_cache.get_statistics.side_effect = [
            {
                "size": 50,
                "memory_usage": 1024000,
                "hits": 100,
                "misses": 25,
                "evictions": 5,
                "expirations": 10,
                "max_size": 100,
                "hit_rate": 0.8
            },
            {
                "size": 0,
                "memory_usage": 0,
                "hits": 100,
                "misses": 25,
                "evictions": 5,
                "expirations": 10,
                "max_size": 100,
                "hit_rate": 0.8
            }
        ]

        result = runner.invoke(clear_cache, ["--confirm"])

        assert result.exit_code == 0
        assert "50" in result.output  # entries removed
        assert "Cache Statistics" in result.output


class TestContextCommandGroup:
    """Tests for context command group."""

    def test_context_group_exists(self, runner):
        """Test that context command group exists."""
        result = runner.invoke(context, ["--help"])

        assert result.exit_code == 0
        assert "Context management commands" in result.output

    def test_context_group_lists_commands(self, runner):
        """Test that all subcommands are listed."""
        result = runner.invoke(context, ["--help"])

        assert result.exit_code == 0
        assert "show" in result.output
        assert "list" in result.output
        assert "history" in result.output
        assert "lineage" in result.output
        assert "stats" in result.output
        assert "clear-cache" in result.output


class TestErrorHandling:
    """Tests for error handling in context commands."""

    def test_show_context_handles_exception(self, runner, mock_persistence):
        """Test error handling in show command."""
        mock_persistence.load_context.side_effect = Exception("Database error")

        result = runner.invoke(show_context, ["test-id"])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_list_contexts_handles_exception(self, runner, mock_persistence):
        """Test error handling in list command."""
        mock_persistence.search_contexts.side_effect = Exception("Database error")

        result = runner.invoke(list_contexts, [])

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_clear_cache_handles_exception(self, runner, mock_cache):
        """Test error handling in clear-cache command."""
        mock_cache.clear.side_effect = Exception("Cache error")

        result = runner.invoke(clear_cache, ["--confirm"])

        assert result.exit_code == 1
        assert "Error" in result.output


# Integration tests (run with real database)

@pytest.mark.integration
class TestContextCommandsIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database for testing."""
        db_path = tmp_path / "test_gao_dev.db"
        return db_path

    @pytest.fixture
    def real_persistence(self, temp_db):
        """Real ContextPersistence instance."""
        return ContextPersistence(db_path=temp_db)

    @pytest.fixture
    def saved_context(self, real_persistence, sample_context):
        """Save a context to database."""
        real_persistence.save_context(sample_context)
        return sample_context

    def test_show_context_integration(self, runner, saved_context, temp_db):
        """Integration test for show command."""
        with patch("gao_dev.cli.context_commands.ContextPersistence") as mock:
            mock.return_value = ContextPersistence(db_path=temp_db)

            result = runner.invoke(show_context, [saved_context.workflow_id])

            assert result.exit_code == 0
            assert str(saved_context.epic_num) in result.output

    def test_list_contexts_integration(self, runner, saved_context, temp_db):
        """Integration test for list command."""
        with patch("gao_dev.cli.context_commands.ContextPersistence") as mock:
            mock.return_value = ContextPersistence(db_path=temp_db)

            result = runner.invoke(list_contexts, ["--epic", "17"])

            assert result.exit_code == 0
            assert "17.5" in result.output
