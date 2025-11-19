"""
Migration result models for config migration.

This module defines the data models for tracking migration results.

Epic 42: Integration Polish
Story 42.1: Existing Installation Migration (5 SP)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MigrationResult:
    """
    Result of a configuration migration operation.

    Tracks the outcome of migrating legacy GAO-Dev configurations
    to the new format.

    Attributes:
        migrated: Whether migration was performed
        reason: Explanation of why migration was/wasn't performed
        from_version: Version format migrated from (v1, epic35, or None)
        settings_migrated: List of settings that were migrated
        backup_path: Path to backup directory (if created)
        duration_ms: Time taken for migration in milliseconds
    """

    migrated: bool
    reason: Optional[str] = None
    from_version: Optional[str] = None
    settings_migrated: list[str] = field(default_factory=list)
    backup_path: Optional[Path] = None
    duration_ms: int = 0

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of migration result
        """
        return {
            "migrated": self.migrated,
            "reason": self.reason,
            "from_version": self.from_version,
            "settings_migrated": self.settings_migrated,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MigrationResult":
        """
        Create from dictionary.

        Args:
            data: Dictionary with migration result data

        Returns:
            MigrationResult instance
        """
        return cls(
            migrated=data.get("migrated", False),
            reason=data.get("reason"),
            from_version=data.get("from_version"),
            settings_migrated=data.get("settings_migrated", []),
            backup_path=Path(data["backup_path"]) if data.get("backup_path") else None,
            duration_ms=data.get("duration_ms", 0),
        )

    def summary(self) -> str:
        """
        Generate a human-readable summary of the migration.

        Returns:
            Summary string describing what was migrated
        """
        if not self.migrated:
            return f"Migration skipped: {self.reason}"

        settings_count = len(self.settings_migrated)
        settings_list = ", ".join(self.settings_migrated) if self.settings_migrated else "none"

        summary_parts = [
            f"Migrated from {self.from_version} format",
            f"Settings migrated ({settings_count}): {settings_list}",
            f"Duration: {self.duration_ms}ms",
        ]

        if self.backup_path:
            summary_parts.append(f"Backup created at: {self.backup_path}")

        return "\n".join(summary_parts)
