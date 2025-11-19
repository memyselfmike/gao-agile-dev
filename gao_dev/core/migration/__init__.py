"""
Configuration migration module for GAO-Dev.

This module provides tools for migrating legacy GAO-Dev configurations
to the new unified format.

Epic 42: Integration Polish
Story 42.1: Existing Installation Migration (5 SP)

Components:
- ConfigMigrator: Main migration orchestrator
- MigrationResult: Result tracking model

Example:
    ```python
    from gao_dev.core.migration import ConfigMigrator, MigrationResult

    migrator = ConfigMigrator()

    # Check for legacy config
    if migrator.detect_legacy_config(project_path):
        result = migrator.migrate(project_path)
        print(migrator.get_migration_summary(result))
    ```
"""

from gao_dev.core.migration.config_migrator import ConfigMigrator
from gao_dev.core.migration.models import MigrationResult

__all__ = ["ConfigMigrator", "MigrationResult"]
