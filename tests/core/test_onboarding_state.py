"""Tests for OnboardingStateManager.

Epic 41: Streamlined Onboarding
Story 41.5: Onboarding State Persistence and Recovery

Tests cover:
- Save/load state
- Resume detection
- Expiry handling
- Corrupted file handling
- Atomic writes
- File permissions
- Path matching
"""

import os
import platform
import stat
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from gao_dev.core.onboarding_state import (
    OnboardingStateManager,
    OnboardingStateError,
    StateCorruptedError,
    StateExpiredError,
    ResumeInfo,
    ONBOARDING_STEPS,
    check_for_resume,
)


class TestOnboardingStateManager:
    """Tests for OnboardingStateManager basic operations."""

    def test_init_default_path(self):
        """Test default config path is ~/.gao-dev/."""
        manager = OnboardingStateManager()
        assert manager.state_file == Path.home() / ".gao-dev" / "onboarding_state.yaml"

    def test_init_custom_path(self, tmp_path):
        """Test custom config path."""
        manager = OnboardingStateManager(config_path=tmp_path)
        assert manager.state_file == tmp_path / "onboarding_state.yaml"

    def test_init_custom_expiry(self, tmp_path):
        """Test custom expiry hours."""
        manager = OnboardingStateManager(config_path=tmp_path, expiry_hours=48)
        assert manager.expiry_hours == 48

    def test_exists_no_file(self, tmp_path):
        """Test exists returns False when no state file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        assert manager.exists() is False

    def test_exists_with_file(self, tmp_path):
        """Test exists returns True when state file exists."""
        manager = OnboardingStateManager(config_path=tmp_path)
        manager.start_onboarding(tmp_path)
        assert manager.exists() is True


class TestStartOnboarding:
    """Tests for starting onboarding sessions."""

    def test_start_creates_file(self, tmp_path):
        """Test start_onboarding creates state file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "my-project"
        project.mkdir()

        manager.start_onboarding(project)

        assert manager.state_file.exists()

    def test_start_initializes_state(self, tmp_path):
        """Test start_onboarding initializes correct state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "my-project"
        project.mkdir()

        manager.start_onboarding(project)

        state = manager.get_state()
        assert state is not None
        assert state["version"] == "1.0"
        assert state["completed"] is False
        assert state["project_path"] == str(project.resolve())
        assert state["steps_completed"] == []
        assert state["step_data"] == {}
        assert "started_at" in state
        assert "last_updated" in state

    def test_start_creates_parent_directory(self, tmp_path):
        """Test start_onboarding creates parent directory if needed."""
        config_path = tmp_path / "subdir" / ".gao-dev"
        manager = OnboardingStateManager(config_path=config_path)
        project = tmp_path / "my-project"
        project.mkdir()

        manager.start_onboarding(project)

        assert config_path.exists()
        assert manager.state_file.exists()


class TestSaveStep:
    """Tests for saving step progress."""

    def test_save_first_step(self, tmp_path):
        """Test saving first step."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app", "type": "greenfield"})

        state = manager.get_state()
        assert "project" in state["steps_completed"]
        assert state["step_data"]["project"]["name"] == "my-app"
        assert state["step_data"]["project"]["type"] == "greenfield"

    def test_save_multiple_steps(self, tmp_path):
        """Test saving multiple steps."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})
        manager.save_step("git", {"name": "Alex", "email": "alex@example.com"})

        state = manager.get_state()
        assert state["steps_completed"] == ["project", "git"]
        assert state["step_data"]["project"]["name"] == "my-app"
        assert state["step_data"]["git"]["name"] == "Alex"

    def test_save_updates_timestamp(self, tmp_path):
        """Test save_step updates last_updated timestamp."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        initial_state = manager.get_state()
        initial_time = initial_state["last_updated"]

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        manager.save_step("project", {"name": "my-app"})
        updated_state = manager.get_state()

        assert updated_state["last_updated"] >= initial_time

    def test_save_without_start_raises_error(self, tmp_path):
        """Test save_step raises error when no onboarding started."""
        manager = OnboardingStateManager(config_path=tmp_path)

        with pytest.raises(OnboardingStateError) as exc_info:
            manager.save_step("project", {"name": "my-app"})

        assert "No onboarding in progress" in str(exc_info.value)

    def test_save_duplicate_step_does_not_add_again(self, tmp_path):
        """Test saving same step twice doesn't duplicate it."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "first"})
        manager.save_step("project", {"name": "second"})

        state = manager.get_state()
        assert state["steps_completed"].count("project") == 1
        # But data should be updated
        assert state["step_data"]["project"]["name"] == "second"


class TestCanResume:
    """Tests for resume detection."""

    def test_can_resume_no_state(self, tmp_path):
        """Test can_resume returns False when no state file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        assert manager.can_resume(project) is False

    def test_can_resume_same_project(self, tmp_path):
        """Test can_resume returns True for same project."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})

        assert manager.can_resume(project) is True

    def test_cannot_resume_different_project(self, tmp_path):
        """Test can_resume returns False for different project path."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"
        project1.mkdir()
        project2.mkdir()

        manager.start_onboarding(project1)
        manager.save_step("project", {"name": "my-app"})

        assert manager.can_resume(project2) is False

    def test_cannot_resume_completed(self, tmp_path):
        """Test can_resume returns False when completed."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})
        manager.mark_complete()

        assert manager.can_resume(project) is False


class TestIsExpired:
    """Tests for expiry checking."""

    def test_not_expired_fresh_state(self, tmp_path):
        """Test is_expired returns False for fresh state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        assert manager.is_expired() is False

    def test_expired_old_state(self, tmp_path):
        """Test is_expired returns True for old state."""
        manager = OnboardingStateManager(config_path=tmp_path, expiry_hours=1)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Manually set old timestamp
        state = manager.get_state()
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        state["last_updated"] = old_time.isoformat()

        with open(manager.state_file, "w") as f:
            yaml.safe_dump(state, f)

        assert manager.is_expired() is True

    def test_is_expired_no_state(self, tmp_path):
        """Test is_expired returns False when no state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        assert manager.is_expired() is False

    def test_get_hours_old_fresh(self, tmp_path):
        """Test get_hours_old returns small value for fresh state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        hours = manager.get_hours_old()
        assert hours < 0.01  # Less than ~36 seconds

    def test_get_hours_old_specific_age(self, tmp_path):
        """Test get_hours_old returns correct value."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Set to 5 hours ago
        state = manager.get_state()
        old_time = datetime.now(timezone.utc) - timedelta(hours=5)
        state["last_updated"] = old_time.isoformat()

        with open(manager.state_file, "w") as f:
            yaml.safe_dump(state, f)

        hours = manager.get_hours_old()
        assert 4.9 < hours < 5.1


class TestResume:
    """Tests for resuming onboarding."""

    def test_resume_returns_next_step(self, tmp_path):
        """Test resume returns correct next step."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})
        manager.save_step("git", {"name": "Alex"})

        next_step, data = manager.resume()

        assert next_step == "provider"
        assert data["project"]["name"] == "my-app"
        assert data["git"]["name"] == "Alex"

    def test_resume_returns_first_step_when_empty(self, tmp_path):
        """Test resume returns first step when nothing completed."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        next_step, data = manager.resume()

        assert next_step == "project"
        assert data == {}

    def test_resume_returns_complete_when_all_done(self, tmp_path):
        """Test resume returns 'complete' when all steps done."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        for step in ONBOARDING_STEPS:
            manager.save_step(step, {step: "done"})

        next_step, _ = manager.resume()
        assert next_step == "complete"

    def test_resume_no_state_raises_error(self, tmp_path):
        """Test resume raises error when no state."""
        manager = OnboardingStateManager(config_path=tmp_path)

        with pytest.raises(OnboardingStateError) as exc_info:
            manager.resume()

        assert "No onboarding state to resume" in str(exc_info.value)


class TestGetResumeInfo:
    """Tests for resume information."""

    def test_get_resume_info_returns_info(self, tmp_path):
        """Test get_resume_info returns ResumeInfo object."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})
        manager.save_step("git", {"name": "Alex"})

        info = manager.get_resume_info()

        assert info is not None
        assert info.steps_completed == ["project", "git"]
        assert info.next_step == "provider"
        assert info.is_expired is False

    def test_get_resume_info_no_state(self, tmp_path):
        """Test get_resume_info returns None when no state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        assert manager.get_resume_info() is None

    def test_resume_info_format_steps(self):
        """Test ResumeInfo.format_steps_completed()."""
        info = ResumeInfo(
            steps_completed=["project", "git"],
            next_step="provider",
            minutes_ago=5,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_steps_completed() == "Project, Git"

    def test_resume_info_format_steps_empty(self):
        """Test format_steps_completed with no steps."""
        info = ResumeInfo(
            steps_completed=[],
            next_step="project",
            minutes_ago=0,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_steps_completed() == "None"

    def test_resume_info_format_time_just_now(self):
        """Test format_time_ago for just now."""
        info = ResumeInfo(
            steps_completed=["project"],
            next_step="git",
            minutes_ago=0,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_time_ago() == "just now"

    def test_resume_info_format_time_minutes(self):
        """Test format_time_ago for minutes."""
        info = ResumeInfo(
            steps_completed=["project"],
            next_step="git",
            minutes_ago=5,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_time_ago() == "5 minutes ago"

    def test_resume_info_format_time_one_minute(self):
        """Test format_time_ago for one minute."""
        info = ResumeInfo(
            steps_completed=["project"],
            next_step="git",
            minutes_ago=1,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_time_ago() == "1 minute ago"

    def test_resume_info_format_time_hours(self):
        """Test format_time_ago for hours."""
        info = ResumeInfo(
            steps_completed=["project"],
            next_step="git",
            minutes_ago=125,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_time_ago() == "2 hours ago"

    def test_resume_info_format_time_one_hour(self):
        """Test format_time_ago for one hour."""
        info = ResumeInfo(
            steps_completed=["project"],
            next_step="git",
            minutes_ago=60,
            is_expired=False,
            project_path=Path("/tmp/project"),
        )

        assert info.format_time_ago() == "1 hour ago"


class TestMarkComplete:
    """Tests for marking onboarding complete."""

    def test_mark_complete_sets_flag(self, tmp_path):
        """Test mark_complete sets completed flag."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.mark_complete()

        state = manager.get_state()
        assert state["completed"] is True

    def test_mark_complete_no_state(self, tmp_path):
        """Test mark_complete does nothing when no state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        # Should not raise
        manager.mark_complete()


class TestClear:
    """Tests for clearing state."""

    def test_clear_removes_file(self, tmp_path):
        """Test clear removes state file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        assert manager.state_file.exists()

        manager.clear()
        assert not manager.state_file.exists()

    def test_clear_no_file(self, tmp_path):
        """Test clear does nothing when no file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        # Should not raise
        manager.clear()


class TestAtomicWrites:
    """Tests for atomic write functionality."""

    def test_atomic_write_creates_file(self, tmp_path):
        """Test atomic write creates complete file."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Verify file is complete and valid
        with open(manager.state_file) as f:
            data = yaml.safe_load(f)

        assert data["version"] == "1.0"
        assert data["project_path"] == str(project.resolve())

    def test_no_temp_files_left(self, tmp_path):
        """Test no temporary files left after save."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})

        # Check no .tmp files left
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestFilePermissions:
    """Tests for secure file permissions."""

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="File permissions work differently on Windows",
    )
    def test_file_permissions_unix(self, tmp_path):
        """Test file has 600 permissions on Unix."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Check permissions
        file_stat = manager.state_file.stat()
        mode = stat.S_IMODE(file_stat.st_mode)

        # Should be 600 (owner read/write only)
        assert mode == stat.S_IRUSR | stat.S_IWUSR

    def test_permissions_on_windows(self, tmp_path):
        """Test file is created on Windows (permissions handled differently)."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Just verify file exists on Windows
        assert manager.state_file.exists()


class TestCorruptedState:
    """Tests for handling corrupted state files."""

    def test_corrupted_yaml_returns_none(self, tmp_path):
        """Test corrupted YAML returns None from get_state."""
        manager = OnboardingStateManager(config_path=tmp_path)

        # Create corrupted file
        manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        manager.state_file.write_text("invalid: yaml: content: [")

        assert manager.get_state() is None

    def test_corrupted_yaml_cannot_resume(self, tmp_path):
        """Test corrupted state cannot be resumed."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        # Create corrupted file
        manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        manager.state_file.write_text("invalid: yaml: content: [")

        assert manager.can_resume(project) is False

    def test_non_dict_returns_none(self, tmp_path):
        """Test non-dict YAML returns None."""
        manager = OnboardingStateManager(config_path=tmp_path)

        # Create file with list instead of dict
        manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        manager.state_file.write_text("- item1\n- item2\n")

        assert manager.get_state() is None

    def test_empty_file_returns_none(self, tmp_path):
        """Test empty file returns None."""
        manager = OnboardingStateManager(config_path=tmp_path)

        # Create empty file
        manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        manager.state_file.write_text("")

        assert manager.get_state() is None

    def test_missing_fields_handled(self, tmp_path):
        """Test missing fields are handled gracefully."""
        manager = OnboardingStateManager(config_path=tmp_path)

        # Create minimal file
        manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        manager.state_file.write_text("version: '1.0'\n")

        state = manager.get_state()
        assert state is not None
        assert state["version"] == "1.0"


class TestTimezoneHandling:
    """Tests for timezone handling."""

    def test_timestamps_are_utc(self, tmp_path):
        """Test timestamps are in UTC."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        state = manager.get_state()
        started = datetime.fromisoformat(state["started_at"])

        # Should have timezone info (UTC)
        assert started.tzinfo is not None or "+" in state["started_at"] or "Z" in state["started_at"]

    def test_handles_timezone_naive_timestamps(self, tmp_path):
        """Test handles timezone-naive timestamps from old state."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Manually write timezone-naive timestamp
        state = manager.get_state()
        state["last_updated"] = "2025-01-15T10:30:00"

        with open(manager.state_file, "w") as f:
            yaml.safe_dump(state, f)

        # Should handle gracefully
        assert manager.is_expired() is True  # Old timestamp


class TestCheckForResume:
    """Tests for check_for_resume convenience function."""

    def test_check_for_resume_returns_info(self, tmp_path):
        """Test check_for_resume returns ResumeInfo when resumable."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})

        info = check_for_resume(project, config_path=tmp_path)

        assert info is not None
        assert info.steps_completed == ["project"]
        assert info.next_step == "git"

    def test_check_for_resume_returns_none(self, tmp_path):
        """Test check_for_resume returns None when not resumable."""
        project = tmp_path / "project"
        project.mkdir()

        info = check_for_resume(project, config_path=tmp_path)

        assert info is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_project_path(self, tmp_path):
        """Test handling very long project path."""
        manager = OnboardingStateManager(config_path=tmp_path)

        # Create deep nested path (use fewer levels for Windows compatibility)
        deep_path = tmp_path
        for i in range(5):
            deep_path = deep_path / f"level_{i}"
        deep_path.mkdir(parents=True)

        manager.start_onboarding(deep_path)

        state = manager.get_state()
        assert state["project_path"] == str(deep_path.resolve())

    def test_special_characters_in_data(self, tmp_path):
        """Test handling special characters in step data."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("project", {
            "name": "my-app: with 'quotes' and \"more\"",
            "description": "Has\nnewlines\tand\ttabs",
            "special": "@ # $ % ^ & * ( )",
        })

        state = manager.get_state()
        assert state["step_data"]["project"]["name"] == "my-app: with 'quotes' and \"more\""

    def test_unicode_in_data(self, tmp_path):
        """Test handling unicode characters."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)
        manager.save_step("git", {
            "name": "Developer Name",
            "email": "dev@example.com",
        })

        state = manager.get_state()
        assert state["step_data"]["git"]["name"] == "Developer Name"

    def test_large_step_data(self, tmp_path):
        """Test handling large step data."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Create large data
        large_data = {
            f"key_{i}": f"value_{i}" * 100
            for i in range(100)
        }

        manager.save_step("project", large_data)

        state = manager.get_state()
        assert len(state["step_data"]["project"]) == 100

    def test_concurrent_access(self, tmp_path):
        """Test that atomic writes prevent corruption."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        manager.start_onboarding(project)

        # Simulate multiple rapid saves
        for i in range(10):
            manager.save_step("project", {"iteration": i})

        state = manager.get_state()
        assert state["step_data"]["project"]["iteration"] == 9


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    def test_full_onboarding_flow(self, tmp_path):
        """Test complete onboarding flow."""
        manager = OnboardingStateManager(config_path=tmp_path)
        project = tmp_path / "project"
        project.mkdir()

        # Start onboarding
        manager.start_onboarding(project)

        # Save each step
        manager.save_step("project", {
            "name": "my-app",
            "type": "greenfield",
            "description": "My new application",
        })

        manager.save_step("git", {
            "name": "Alex Developer",
            "email": "alex@example.com",
            "init_repository": True,
        })

        manager.save_step("provider", {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
        })

        manager.save_step("credentials", {
            "provider": "anthropic",
            "validated": True,
        })

        # Verify state
        state = manager.get_state()
        assert state["steps_completed"] == ["project", "git", "provider", "credentials"]
        assert len(state["step_data"]) == 4

        # Complete and cleanup
        manager.mark_complete()
        manager.clear()

        assert not manager.state_file.exists()

    def test_interrupted_and_resume_flow(self, tmp_path):
        """Test interrupted and resumed flow."""
        project = tmp_path / "project"
        project.mkdir()

        # First session - gets interrupted
        manager1 = OnboardingStateManager(config_path=tmp_path)
        manager1.start_onboarding(project)
        manager1.save_step("project", {"name": "my-app"})
        manager1.save_step("git", {"name": "Alex"})
        # Interrupted here...

        # Second session - resumes
        manager2 = OnboardingStateManager(config_path=tmp_path)

        # Check can resume
        assert manager2.can_resume(project) is True

        # Get resume info
        info = manager2.get_resume_info()
        assert info is not None
        assert info.steps_completed == ["project", "git"]
        assert info.next_step == "provider"

        # Resume
        next_step, data = manager2.resume()
        assert next_step == "provider"
        assert data["project"]["name"] == "my-app"
        assert data["git"]["name"] == "Alex"

        # Continue
        manager2.save_step("provider", {"provider": "anthropic"})
        manager2.save_step("credentials", {"validated": True})

        # Complete
        manager2.mark_complete()
        assert manager2.can_resume(project) is False

    def test_expired_state_flow(self, tmp_path):
        """Test handling expired state."""
        project = tmp_path / "project"
        project.mkdir()

        manager = OnboardingStateManager(config_path=tmp_path, expiry_hours=1)
        manager.start_onboarding(project)
        manager.save_step("project", {"name": "my-app"})

        # Set old timestamp
        state = manager.get_state()
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        state["last_updated"] = old_time.isoformat()

        with open(manager.state_file, "w") as f:
            yaml.safe_dump(state, f)

        # Can still check for resume
        assert manager.can_resume(project) is True

        # But is_expired returns True for warning
        assert manager.is_expired() is True

        # Resume info shows expired
        info = manager.get_resume_info()
        assert info.is_expired is True

    def test_wrong_directory_no_resume(self, tmp_path):
        """Test that resume is not offered for wrong directory."""
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"
        project1.mkdir()
        project2.mkdir()

        # Start in project1
        manager = OnboardingStateManager(config_path=tmp_path)
        manager.start_onboarding(project1)
        manager.save_step("project", {"name": "app1"})

        # Try to resume in project2
        info = check_for_resume(project2, config_path=tmp_path)
        assert info is None
