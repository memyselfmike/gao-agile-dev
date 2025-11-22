# Story 42.1: Existing Installation Migration

## User Story

As an existing GAO-Dev user upgrading to the new version,
I want my configuration to be automatically migrated,
So that I don't lose my settings or have to reconfigure everything.

## Acceptance Criteria

- [ ] AC1: Detects existing `.gao-dev/gao-dev.yaml` (legacy format) and migrates to new format
- [ ] AC2: Detects existing `.gao-dev/provider_preferences.yaml` (Epic 35) and migrates settings
- [ ] AC3: Creates global config at `~/.gao-dev/config.yaml` from first migrated project
- [ ] AC4: Preserves provider selection, model choice, and preferences
- [ ] AC5: Backs up original files before migration (`.bak` extension)
- [ ] AC6: Migration runs automatically on first startup after upgrade
- [ ] AC7: Shows migration summary with what was migrated and where
- [ ] AC8: Skips onboarding for migrated users (they're "returning users")
- [ ] AC9: Handles corrupted legacy files gracefully (log warning, continue with defaults)
- [ ] AC10: Migration is idempotent (safe to run multiple times)
- [ ] AC11: Credential sources are preserved (env var, keychain references)
- [ ] AC12: Migration completes in <2 seconds

## Technical Notes

### Implementation Details

Create `gao_dev/core/migration/config_migrator.py`:

```python
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import shutil
from datetime import datetime

class ConfigMigrator:
    """Migrate legacy GAO-Dev configurations to new format."""

    def detect_legacy_config(self, project_path: Path) -> Optional[str]:
        """Detect which legacy config format exists."""
        gao_dev_dir = project_path / '.gao-dev'

        if (gao_dev_dir / 'gao-dev.yaml').exists():
            return 'v1'  # Original format
        elif (gao_dev_dir / 'provider_preferences.yaml').exists():
            return 'epic35'  # Epic 35 format
        return None

    def migrate(self, project_path: Path) -> MigrationResult:
        """Perform migration with backup and validation."""
        version = self.detect_legacy_config(project_path)
        if not version:
            return MigrationResult(migrated=False, reason="No legacy config found")

        # Backup original files
        self._backup_files(project_path)

        # Load and convert
        if version == 'v1':
            legacy_config = self._load_v1_config(project_path)
        else:
            legacy_config = self._load_epic35_config(project_path)

        new_config = self._convert_to_new_format(legacy_config)

        # Write new config
        self._write_new_config(project_path, new_config)

        # Create global config if first migration
        self._ensure_global_config(new_config)

        return MigrationResult(
            migrated=True,
            from_version=version,
            settings_migrated=list(new_config.keys()),
            backup_path=project_path / '.gao-dev' / 'backup'
        )
```

### Legacy Format: v1 (`gao-dev.yaml`)

```yaml
project_name: my-app
provider: anthropic
model: claude-3-sonnet
api_key_source: environment
features:
  interactive_provider_selection: true
```

### Legacy Format: Epic 35 (`provider_preferences.yaml`)

```yaml
provider: claude-code
model: sonnet-4.5
saved_at: "2025-01-15T10:30:00Z"
```

### New Format (`config.yaml`)

```yaml
version: "1.0"
project:
  name: my-app
  type: brownfield
  created_at: "2025-01-15T10:30:00Z"
provider:
  default: claude-code
  model: sonnet-4.5
credentials:
  storage: environment
```

### Backup Strategy

```
.gao-dev/
  backup/
    2025-01-15T10-30-00/
      gao-dev.yaml
      provider_preferences.yaml
```

## Test Scenarios

1. **v1 migration**: Given `.gao-dev/gao-dev.yaml` exists, When migration runs, Then new `config.yaml` created with migrated settings

2. **Epic 35 migration**: Given `provider_preferences.yaml` exists, When migration runs, Then provider and model migrated

3. **Backup created**: Given legacy config exists, When migration runs, Then original files backed up with timestamp

4. **Global config creation**: Given first migration, When migration runs, Then `~/.gao-dev/config.yaml` created

5. **Corrupted file handling**: Given invalid YAML in legacy file, When migration runs, Then logs warning and uses defaults

6. **Idempotent migration**: Given migration already complete, When migration runs again, Then no changes made

7. **Credential preservation**: Given `api_key_source: environment`, When migrated, Then `credentials.storage: environment`

8. **Migration summary**: Given successful migration, When complete, Then summary shows what was migrated

9. **Performance**: Given any legacy config, When migration runs, Then completes in <2 seconds

10. **Skip onboarding**: Given successful migration, When startup continues, Then onboarding wizard skipped

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests with real legacy configs
- [ ] Tested with configs from different GAO-Dev versions
- [ ] Code reviewed
- [ ] Migration documentation updated
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 40.2: Global and Project State Detection
- Story 41.5: Onboarding State Persistence

## Notes

- Collect sample legacy configs from beta users for testing
- Consider migration dry-run option for cautious users
- Log all migration actions for troubleshooting
- Handle both Unix and Windows path separators in legacy configs
- Preserve comments in YAML where possible (use ruamel.yaml)
- Consider adding `migrated_from` metadata for debugging
