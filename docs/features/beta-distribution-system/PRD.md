# PRD: Beta Distribution and Update Management System

**Feature Name**: Beta Distribution and Update Management
**Version**: 1.0
**Status**: Planning
**Created**: 2025-01-13
**Owner**: GAO-Dev Core Team

---

## Executive Summary

GAO-Dev currently has a **critical architecture issue**: the system can operate on its own repository instead of user projects, causing git conflicts and consistency checker warnings. This occurs because:

1. Beta testers clone the GAO-Dev repo and run `pip install -e .` (editable mode)
2. They may run `gao-dev start` from within the GAO-Dev directory
3. Project detection falls back to the current directory if no markers are found
4. All git operations then affect GAO-Dev's repo instead of the user's project

**This PRD defines a comprehensive beta distribution system** that:
- Completely separates GAO-Dev tooling from user projects
- Enables rapid iteration with safe updates
- Protects beta tester installations from breaking changes
- Provides multiple distribution channels for different stages

---

## Problem Statement

### Current Issues

1. **Repo Confusion**
   - GAO-Dev repo and user project repos are conflated
   - Git operations can affect the wrong repository
   - Consistency checker operates on GAO-Dev's own files

2. **Update Complexity**
   - "Pull from repo and restart" works for developers
   - Breaks for beta testers who need clean separation
   - No versioning or rollback mechanism

3. **Installation Ambiguity**
   - No clear installation instructions for beta testers
   - Editable installs create directory confusion
   - Missing safety mechanisms to prevent misuse

4. **Breaking Changes Risk**
   - No strategy for database schema updates
   - No rollback mechanism if updates fail
   - User project state could be corrupted

### Impact

- **High severity**: Beta testers experience git conflicts
- **Data risk**: User project databases could be corrupted by incompatible updates
- **User confusion**: Unclear where GAO-Dev ends and their project begins
- **Testing limitations**: Can't test distribution mechanisms before launch

---

## Goals and Non-Goals

### Goals

1. **Complete Separation**
   - GAO-Dev tooling lives in Python site-packages
   - User projects are entirely separate directories
   - No possibility of repo confusion

2. **Safe Updates**
   - Database schema migrations handled automatically
   - Rollback mechanism for failed updates
   - Version compatibility checking

3. **Fast Iteration**
   - Beta testers can update with one command
   - Updates deploy within minutes of push
   - No manual file distribution needed

4. **Multiple Distribution Channels**
   - Development: Editable installs with safety checks
   - Beta: GitHub-based installs with rapid updates
   - Pre-production: TestPyPI for final validation
   - Production: PyPI for public release

5. **Comprehensive Safety**
   - Detect and prevent running from GAO-Dev source directory
   - Validate package integrity before updates
   - Backup user state before migrations
   - Graceful degradation on update failures

### Non-Goals

1. **Auto-update system**: Users must manually update (avoid unexpected changes)
2. **Multi-version support**: Only latest version supported in beta
3. **Backward compatibility**: Beta phase allows breaking changes with migrations
4. **Self-hosted infrastructure**: Use existing platforms (GitHub, PyPI)

---

## Distribution Approaches Analysis

### Approach 1: Manual Wheel Distribution

**Description**: Build `.whl` files and share manually (email, file share, etc.)

**Implementation**:
```bash
# Developer builds
python -m build
# Share: dist/gao_dev-1.0.0-py3-none-any.whl

# Tester installs
pip install gao_dev-1.0.0-py3-none-any.whl

# Tester updates
pip install --force-reinstall gao_dev-1.0.1-py3-none-any.whl
```

**Pros**:
- ✅ Complete control over distribution
- ✅ Works offline
- ✅ No external dependencies
- ✅ Clear versioning

**Cons**:
- ❌ Manual distribution process
- ❌ Testers must track files manually
- ❌ No automatic update notifications
- ❌ Version tracking burden on testers

**Risk Level**: Low
**Complexity**: Low
**Update Speed**: Slow (hours to days)
**Best For**: Initial beta with <5 testers

---

### Approach 2: Git Clone + Editable Install (Current Method)

**Description**: Testers clone repo and use `pip install -e .`

**Implementation**:
```bash
# Tester setup
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e .

# Updates
cd gao-agile-dev
git pull origin main
# Changes immediately active

# CRITICAL: Must change to project directory
cd ~/my-project
gao-dev start
```

**Pros**:
- ✅ Fast updates (git pull)
- ✅ Developer-friendly workflow
- ✅ Can test branches easily
- ✅ No build step needed

**Cons**:
- ❌ **HIGH RISK**: Repo confusion (current problem!)
- ❌ Requires git knowledge
- ❌ Testers have two directories to manage
- ❌ Can accidentally run from wrong directory
- ❌ Source code exposed (not "beta product" experience)

**Risk Level**: **HIGH** ⚠️
**Complexity**: Medium
**Update Speed**: Fast (seconds)
**Best For**: Internal developers only (NOT beta testers)

**RECOMMENDATION**: ⛔ **DO NOT USE for beta testing** without extensive safety mechanisms

---

### Approach 3: Git URL Install (Recommended for Beta)

**Description**: Install directly from GitHub URL without cloning

**Implementation**:
```bash
# Tester installs
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Or specific version
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@v1.0.0

# Updates
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Pros**:
- ✅ **Complete separation** (installs to site-packages)
- ✅ One-command install
- ✅ One-command updates
- ✅ No local repo for testers to manage
- ✅ Can pin to commits/tags/branches
- ✅ Supports pre-release tags (v1.0.0-beta.3)
- ✅ No repo confusion possible

**Cons**:
- ❌ Requires GitHub access (not offline)
- ❌ Slightly slower than editable (must download)
- ❌ Full reinstall on each update
- ❌ Requires internet for updates

**Risk Level**: **LOW** ✅
**Complexity**: Low
**Update Speed**: Fast (minutes)
**Best For**: Active beta testing (5-50 testers)

**RECOMMENDATION**: ✅ **RECOMMENDED for beta phase**

---

### Approach 4: GitHub Releases

**Description**: Create GitHub releases with attached `.whl` files

**Implementation**:
```bash
# Developer creates release
git tag v1.0.0
git push origin v1.0.0
python -m build
# Upload dist/*.whl to GitHub release UI

# Tester installs
pip install https://github.com/memyselfmike/gao-agile-dev/releases/download/v1.0.0/gao_dev-1.0.0-py3-none-any.whl

# Updates (manual process)
# Check releases page → Download new version → Install
```

**Pros**:
- ✅ Professional presentation
- ✅ Built-in changelog (release notes)
- ✅ Versioned artifacts
- ✅ Download statistics
- ✅ Clear version history

**Cons**:
- ❌ Manual release process
- ❌ Longer URLs for testers
- ❌ No auto-update mechanism
- ❌ Must manually check for updates

**Risk Level**: Low
**Complexity**: Medium
**Update Speed**: Medium (hours)
**Best For**: Stable beta releases, milestone testing

**RECOMMENDATION**: ✅ **GOOD for milestone releases** (v1.0.0-beta.1, v1.0.0-rc.1)

---

### Approach 5: TestPyPI (Pre-Production)

**Description**: Publish to TestPyPI (test.pypi.org) before production PyPI

**Implementation**:
```bash
# Developer publishes
python -m build
twine upload --repository testpypi dist/*

# Tester installs
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    gao-dev

# Updates
pip install --upgrade --index-url https://test.pypi.org/simple/ gao-dev
```

**Pros**:
- ✅ Mimics production exactly
- ✅ Standard pip workflow
- ✅ Easy updates (pip install --upgrade)
- ✅ Validates PyPI metadata
- ✅ Tests distribution infrastructure

**Cons**:
- ❌ Requires PyPI account setup
- ❌ Versioning is permanent (can't delete)
- ❌ Public (anyone can install)
- ❌ Additional configuration complexity

**Risk Level**: Low
**Complexity**: Medium-High
**Update Speed**: Fast (minutes after publish)
**Best For**: Final validation before production release

**RECOMMENDATION**: ✅ **GOOD for release candidates** (1-2 weeks before production)

---

### Approach 6: Production PyPI (Final Release)

**Description**: Publish to official PyPI (pypi.org)

**Implementation**:
```bash
# Developer publishes
python -m build
twine upload dist/*

# User installs
pip install gao-dev

# Updates
pip install --upgrade gao-dev
```

**Pros**:
- ✅ Industry standard
- ✅ Trusted by users
- ✅ Easy discovery
- ✅ Simple commands
- ✅ Permanent availability

**Cons**:
- ❌ **Permanent** (can't unpublish versions)
- ❌ Public commitment
- ❌ Version numbers can't be reused
- ❌ Must be production-ready

**Risk Level**: Medium (permanent publication)
**Complexity**: Medium
**Update Speed**: Fast (minutes)
**Best For**: Production release (post-beta)

**RECOMMENDATION**: ✅ **REQUIRED for production** (after beta validation)

---

## Recommended Phased Rollout

### Phase 1: Initial Beta (Weeks 1-2)

**Approach**: Approach 3 (Git URL Install)

```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Rationale**:
- Complete separation (no repo confusion)
- Fast iteration (push to GitHub → testers update immediately)
- Low ceremony (no release process)
- Easy to test different branches

**Team Size**: 3-10 testers
**Update Frequency**: Daily to weekly
**Support Level**: Direct communication (Slack/Discord)

---

### Phase 2: Expanded Beta (Weeks 3-6)

**Approach**: Approach 3 (Git URL) + Approach 4 (GitHub Releases for milestones)

```bash
# Daily builds
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Milestone releases
pip install https://github.com/.../releases/download/v1.0.0-beta.3/gao_dev-1.0.0b3-py3-none-any.whl
```

**Rationale**:
- Continue fast iteration with git URLs
- Stable milestones via GitHub releases
- Clear versioning for tracking issues
- Release notes for change documentation

**Team Size**: 10-30 testers
**Update Frequency**: Weekly releases, daily git updates
**Support Level**: Documentation + community support

---

### Phase 3: Release Candidate (Weeks 7-8)

**Approach**: Approach 5 (TestPyPI)

```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    gao-dev==1.0.0rc1
```

**Rationale**:
- Validate PyPI publication process
- Test production-like distribution
- Final metadata and description testing
- Practice for production release

**Team Size**: 30-50 testers (broader audience)
**Update Frequency**: Weekly RC releases
**Support Level**: Full documentation + FAQ

---

### Phase 4: Production Release

**Approach**: Approach 6 (PyPI)

```bash
pip install gao-dev
```

**Rationale**:
- Industry-standard distribution
- Maximum reach and discoverability
- Professional presentation
- Long-term support commitment

**Team Size**: Unlimited
**Update Frequency**: Semantic versioning (major.minor.patch)
**Support Level**: GitHub Issues, Stack Overflow, docs site

---

## Safety Mechanisms

### 1. Source Repository Detection

Prevent running GAO-Dev from its own source repository:

```python
# gao_dev/cli/project_detection.py

def _is_gaodev_source_repo(path: Path) -> bool:
    """
    Detect if current directory is GAO-Dev's source repository.

    Checks for distinctive source files that wouldn't exist in user projects.
    """
    gaodev_markers = [
        "gao_dev/orchestrator/orchestrator.py",
        "gao_dev/cli/commands.py",
        "docs/bmm-workflow-status.md",
        ".gaodev-source",  # Explicit marker file
    ]

    return any((path / marker).exists() for marker in gaodev_markers)

def detect_project_root(start_dir: Optional[Path] = None) -> Path:
    start_dir = start_dir or Path.cwd()

    # SAFETY CHECK: Prevent running from GAO-Dev source
    if _is_gaodev_source_repo(start_dir):
        raise GAODevSourceDirectoryError(
            "ERROR: Running GAO-Dev from its source repository!\n\n"
            "GAO-Dev must be installed via pip and run from your project directory.\n\n"
            "Installation:\n"
            "  pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main\n\n"
            "Usage:\n"
            "  cd /path/to/your/project\n"
            "  gao-dev start\n\n"
            "For development, use:\n"
            "  gao-dev start --project /path/to/your/project"
        )

    # ... rest of detection logic
```

**Test Cases**:
- ✅ Running from GAO-Dev source → Clear error
- ✅ Running from site-packages install → Works
- ✅ Running from user project → Works
- ✅ Running with `--project` flag → Works

---

### 2. Version Compatibility Checking

Ensure user project databases are compatible with GAO-Dev version:

```python
# gao_dev/core/version_manager.py

class VersionManager:
    """Manage version compatibility and migrations."""

    CURRENT_VERSION = "1.0.0"
    MIN_COMPATIBLE_VERSION = "0.9.0"

    def check_compatibility(self, project_path: Path) -> CompatibilityResult:
        """
        Check if project is compatible with current GAO-Dev version.

        Returns:
            CompatibilityResult with status: compatible, needs_migration, incompatible
        """
        gaodev_dir = project_path / ".gao-dev"
        version_file = gaodev_dir / "version.txt"

        if not version_file.exists():
            # New project
            return CompatibilityResult(
                status="compatible",
                action="initialize",
                message="New project - will initialize .gao-dev"
            )

        project_version = version_file.read_text().strip()

        if self._needs_migration(project_version):
            return CompatibilityResult(
                status="needs_migration",
                action="migrate",
                from_version=project_version,
                to_version=self.CURRENT_VERSION,
                migrations=self._get_required_migrations(project_version)
            )

        if not self._is_compatible(project_version):
            return CompatibilityResult(
                status="incompatible",
                action="error",
                message=(
                    f"Project created with GAO-Dev {project_version} "
                    f"which is incompatible with current version {self.CURRENT_VERSION}.\n\n"
                    f"Please update project or downgrade GAO-Dev."
                )
            )

        return CompatibilityResult(status="compatible", action="continue")
```

**Test Cases**:
- ✅ New project → Initialize
- ✅ Compatible version → Continue
- ✅ Needs migration → Run migrations
- ✅ Incompatible version → Error with instructions

---

### 3. Pre-Update Backup

Backup user state before applying updates:

```python
# gao_dev/core/backup_manager.py

class BackupManager:
    """Manage backups of user project state."""

    def create_backup(self, project_path: Path) -> Path:
        """
        Create backup of .gao-dev directory before updates.

        Returns:
            Path to backup directory
        """
        gaodev_dir = project_path / ".gao-dev"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = project_path / ".gao-dev-backups" / f"backup_{timestamp}"

        # Copy entire .gao-dev directory
        shutil.copytree(gaodev_dir, backup_dir)

        # Store metadata
        metadata = {
            "timestamp": timestamp,
            "gaodev_version": VersionManager.CURRENT_VERSION,
            "reason": "pre_update_backup",
            "files": [str(p.relative_to(backup_dir)) for p in backup_dir.rglob("*")]
        }
        (backup_dir / "backup_metadata.json").write_text(
            json.dumps(metadata, indent=2)
        )

        logger.info("backup_created", backup_path=str(backup_dir))
        return backup_dir

    def restore_backup(self, project_path: Path, backup_path: Path) -> None:
        """Restore from backup (rollback failed update)."""
        gaodev_dir = project_path / ".gao-dev"

        # Remove current state
        if gaodev_dir.exists():
            shutil.rmtree(gaodev_dir)

        # Restore from backup
        shutil.copytree(backup_path, gaodev_dir)

        logger.info("backup_restored", backup_path=str(backup_path))
```

**Test Cases**:
- ✅ Backup created before migration
- ✅ Restore on migration failure
- ✅ Old backups cleaned up (keep last 5)
- ✅ Backup metadata tracks version

---

### 4. Migration Transaction Safety

Ensure migrations are atomic (all-or-nothing):

```python
# gao_dev/lifecycle/migration_runner.py

class MigrationRunner:
    """Run database migrations with transaction safety."""

    def run_migrations(
        self,
        project_path: Path,
        from_version: str,
        to_version: str
    ) -> MigrationResult:
        """
        Run all required migrations with full rollback on error.

        Pattern:
        1. Create backup
        2. Begin transaction
        3. Run migrations in order
        4. Commit transaction
        5. On error: rollback transaction + restore backup
        """
        backup_manager = BackupManager()
        backup_path = backup_manager.create_backup(project_path)

        try:
            db_path = project_path / ".gao-dev" / "documents.db"
            conn = sqlite3.connect(str(db_path))

            # Get required migrations
            migrations = self._get_migrations(from_version, to_version)

            logger.info("running_migrations", count=len(migrations))

            for migration in migrations:
                logger.info("applying_migration", migration=migration.name)

                # Run migration
                migration.up(conn)

                # Record in schema_version table
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (migration.version, datetime.now().isoformat())
                )

            conn.commit()
            conn.close()

            # Update version file
            version_file = project_path / ".gao-dev" / "version.txt"
            version_file.write_text(to_version)

            logger.info("migrations_complete", from_version=from_version, to_version=to_version)

            return MigrationResult(
                success=True,
                from_version=from_version,
                to_version=to_version,
                migrations_applied=len(migrations)
            )

        except Exception as e:
            logger.error("migration_failed", error=str(e))

            # Rollback
            conn.rollback()
            conn.close()

            # Restore backup
            backup_manager.restore_backup(project_path, backup_path)

            return MigrationResult(
                success=False,
                error=str(e),
                backup_path=str(backup_path)
            )
```

**Test Cases**:
- ✅ All migrations succeed → State updated
- ✅ One migration fails → All rolled back
- ✅ Database corrupted during migration → Backup restored
- ✅ Version file updated only on success

---

### 5. Update Health Check

Validate installation after update:

```python
# gao_dev/cli/health_check.py

class HealthCheck:
    """Post-update health validation."""

    def run_post_update_check(self, project_path: Path) -> HealthCheckResult:
        """
        Comprehensive health check after update.

        Checks:
        1. All config files present
        2. Database schema valid
        3. Workflows loadable
        4. Agents configured
        5. Git operations functional
        """
        checks = []

        # Check 1: Config files
        config_check = self._check_config_files()
        checks.append(config_check)

        # Check 2: Database
        db_check = self._check_database(project_path)
        checks.append(db_check)

        # Check 3: Workflows
        workflow_check = self._check_workflows()
        checks.append(workflow_check)

        # Check 4: Agents
        agent_check = self._check_agents()
        checks.append(agent_check)

        # Check 5: Git
        git_check = self._check_git(project_path)
        checks.append(git_check)

        # Aggregate results
        all_passed = all(check.passed for check in checks)

        if not all_passed:
            failed_checks = [c for c in checks if not c.passed]
            logger.error(
                "health_check_failed",
                failed_count=len(failed_checks),
                failures=[c.name for c in failed_checks]
            )

        return HealthCheckResult(
            passed=all_passed,
            checks=checks,
            timestamp=datetime.now()
        )
```

**Test Cases**:
- ✅ All checks pass → Success message
- ✅ Config missing → Detailed error
- ✅ Database corrupt → Rollback offered
- ✅ Git broken → Instructions provided

---

## Package Configuration Updates

### Required Changes to pyproject.toml

```toml
[project]
name = "gao-dev"
version = "1.0.0-beta.1"  # Add beta suffix
# ... existing config ...

# Add classifiers for beta status
classifiers = [
    "Development Status :: 4 - Beta",  # Changed from 3 - Alpha
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[tool.setuptools.package-data]
gao_dev = [
    "workflows/**/*",
    "workflows/**/*.yaml",
    "workflows/**/*.yml",
    "config/**/*",                      # All config files
    "config/**/*.yaml",                 # YAML configs
    "config/**/*.yml",                  # YML configs
    "config/**/*.json",                 # JSON schemas
    "config/checklists/**/*.yaml",      # Checklists
    "config/domains/**/*.yaml",         # Domain configs
    "config/schemas/**/*.json",         # JSON schemas
    "config/templates/**/*",            # Templates
    "lifecycle/migrations/*.py",        # Database migrations
    "sandbox/reporting/templates/**/*", # Report templates
    "sandbox/reporting/assets/*",       # Report assets
    "py.typed",                         # Type hints marker
    ".gaodev-source",                   # Source marker (for detection)
]

# Add tool configurations
[tool.setuptools.exclude-package-data]
"*" = [
    "*.pyc",
    "*.pyo",
    "*~",
    "__pycache__",
    ".git*",
    "tests/*",
    "docs/*",
    "sandbox/projects/*",  # Don't include test projects
]
```

### Add Source Marker File

```bash
# Create .gaodev-source marker in repo root
echo "This is the GAO-Dev source repository. Do not run gao-dev from this directory." > .gaodev-source
```

This file will be:
- ✅ Included in packages (for detection)
- ✅ Used by project_detection to prevent source directory usage
- ✅ Documented in developer docs

---

## Testing Strategy

### Unit Tests

```python
# tests/cli/test_project_detection_safety.py

def test_detect_gaodev_source_repo():
    """Test detection of GAO-Dev source repository."""
    # Should detect source repo
    assert _is_gaodev_source_repo(Path("/path/to/gao-agile-dev"))

    # Should not detect user projects
    assert not _is_gaodev_source_repo(Path("/path/to/user-project"))

def test_prevent_running_from_source():
    """Test prevention of running from source directory."""
    with pytest.raises(GAODevSourceDirectoryError):
        detect_project_root(Path("/path/to/gao-agile-dev"))

def test_version_compatibility_check():
    """Test version compatibility detection."""
    vm = VersionManager()

    # Compatible version
    result = vm.check_compatibility("1.0.0", "1.0.1")
    assert result.status == "compatible"

    # Needs migration
    result = vm.check_compatibility("0.9.0", "1.0.0")
    assert result.status == "needs_migration"

    # Incompatible
    result = vm.check_compatibility("0.5.0", "1.0.0")
    assert result.status == "incompatible"

def test_backup_and_restore():
    """Test backup/restore mechanism."""
    backup_manager = BackupManager()

    # Create backup
    backup_path = backup_manager.create_backup(project_path)
    assert backup_path.exists()
    assert (backup_path / "backup_metadata.json").exists()

    # Modify original
    (project_path / ".gao-dev" / "test.txt").write_text("modified")

    # Restore
    backup_manager.restore_backup(project_path, backup_path)

    # Verify restoration
    assert not (project_path / ".gao-dev" / "test.txt").exists()
```

### Integration Tests

```python
# tests/integration/test_beta_distribution.py

def test_git_url_install_separation():
    """Test that git+URL installs provide complete separation."""
    # Install from git URL
    subprocess.run([
        "pip", "install",
        "git+https://github.com/memyselfmike/gao-agile-dev.git@main"
    ])

    # Create user project
    user_project = tmp_path / "my-project"
    user_project.mkdir()
    os.chdir(user_project)

    # Run gao-dev
    result = subprocess.run(["gao-dev", "start"], capture_output=True)

    # Verify:
    # 1. .gao-dev created in user project
    assert (user_project / ".gao-dev").exists()

    # 2. No GAO-Dev source files in user project
    assert not (user_project / "gao_dev").exists()

    # 3. Git operations affect user project
    assert (user_project / ".git").exists()

def test_update_preserves_user_state():
    """Test that updates don't affect user project state."""
    # Initial install
    subprocess.run(["pip", "install", "git+...@v1.0.0"])

    # Create user project with data
    user_project = tmp_path / "my-project"
    os.chdir(user_project)
    subprocess.run(["gao-dev", "init"])

    # Add user data
    (user_project / "docs" / "my-doc.md").write_text("User content")

    # Update GAO-Dev
    subprocess.run(["pip", "install", "--upgrade", "git+...@v1.0.1"])

    # Verify user data preserved
    assert (user_project / "docs" / "my-doc.md").read_text() == "User content"
    assert (user_project / ".gao-dev" / "documents.db").exists()

def test_migration_rollback_on_failure():
    """Test migration rollback on error."""
    # Create project with old version
    # Simulate migration failure
    # Verify rollback to backup
    pass
```

### Manual Testing Checklist

Beta testers will verify:

- [ ] Install from git URL works
- [ ] `gao-dev start` works from project directory
- [ ] Cannot run from GAO-Dev source (clear error)
- [ ] Update preserves project state
- [ ] Failed update rolls back gracefully
- [ ] Health check detects issues
- [ ] Documentation is clear and complete

---

## User Communication

### Installation Documentation

**Beta Tester Quick Start** (README.md):

```markdown
# GAO-Dev Beta Installation

## Requirements
- Python 3.11 or higher
- Git
- Internet connection

## Installation

```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

## Verification

```bash
gao-dev --version
# Should show: GAO-Dev 1.0.0-beta.1
```

## Usage

```bash
# Navigate to YOUR project (not GAO-Dev source!)
cd /path/to/your/project

# Start GAO-Dev
gao-dev start
```

## Updates

```bash
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

## Troubleshooting

### "Running from source repository" error

You're in the GAO-Dev source directory. Navigate to your project:
```bash
cd /path/to/your/actual/project
gao-dev start
```

### Update failed

Your project state has been automatically backed up. Contact support with:
```bash
gao-dev health-check --verbose
```

## Support

- GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues
- Discord: [link]
- Email: [email]
```

### Update Notifications

**Changelog Format** (CHANGELOG.md):

```markdown
# Changelog

## [1.0.0-beta.2] - 2025-01-15

### Added
- New workflow selection algorithm
- Enhanced error messages

### Changed
- Database schema migration (automatic)
- Config file structure (backwards compatible)

### Fixed
- Git operations on Windows
- Provider selection crash

### Migration Notes
This update includes automatic database migrations. Your project state will be backed up before migration.

### Breaking Changes
None

### Update Command
```bash
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

## [1.0.0-beta.1] - 2025-01-13

Initial beta release.
```

---

## Success Metrics

### Phase 1 (Initial Beta)

- ✅ 0 repo confusion incidents
- ✅ 100% successful installs (no errors)
- ✅ <5 minute average update time
- ✅ 0 data loss incidents

### Phase 2 (Expanded Beta)

- ✅ 50+ successful updates across testers
- ✅ 0 rollback failures
- ✅ >90% tester satisfaction
- ✅ <3 support tickets per update

### Phase 3 (Release Candidate)

- ✅ TestPyPI publication successful
- ✅ 100+ installs without issues
- ✅ Documentation completeness >95%
- ✅ 0 critical bugs

### Phase 4 (Production)

- ✅ PyPI publication successful
- ✅ 1000+ installs in first week
- ✅ <1% support ticket rate
- ✅ >4.5 star rating

---

## Timeline

| Phase | Duration | Start | End | Milestone |
|-------|----------|-------|-----|-----------|
| Phase 1 Setup | 1 week | Week 1 | Week 1 | Safety mechanisms implemented |
| Phase 1 Testing | 1 week | Week 2 | Week 2 | 5-10 testers validated |
| Phase 2 Expansion | 4 weeks | Week 3 | Week 6 | 30 testers, GitHub releases |
| Phase 3 RC | 2 weeks | Week 7 | Week 8 | TestPyPI validated |
| Phase 4 Production | Ongoing | Week 9+ | - | PyPI published |

---

## Risks and Mitigations

### Risk 1: Breaking Changes in Updates

**Risk**: Updates break existing projects

**Mitigation**:
- Automatic backups before updates
- Version compatibility checking
- Rollback mechanism
- Gradual rollout (git URL → GitHub releases → TestPyPI → PyPI)

### Risk 2: Database Corruption

**Risk**: Failed migrations corrupt user databases

**Mitigation**:
- Transaction-based migrations
- Automatic backups
- Validation after migration
- Health checks post-update

### Risk 3: Tester Confusion

**Risk**: Testers don't understand installation process

**Mitigation**:
- Clear documentation with examples
- Video tutorials
- Active support channel (Discord/Slack)
- Onboarding checklist

### Risk 4: Update Notification Failure

**Risk**: Testers miss important updates

**Mitigation**:
- CHANGELOG.md prominently displayed
- GitHub watch/notification encouragement
- Update checker in CLI (optional)
- Email notifications for critical updates

### Risk 5: Dependency Conflicts

**Risk**: GAO-Dev dependencies conflict with user projects

**Mitigation**:
- Conservative dependency versions
- Testing against popular frameworks
- Virtual environment recommendation
- Dependency conflict documentation

---

## Open Questions

1. **Update Frequency**: How often should beta updates ship?
   - **Proposal**: Daily builds on `main`, weekly stable releases

2. **Version Numbering**: How to number beta versions?
   - **Proposal**: Semantic versioning with beta suffix (1.0.0-beta.1, 1.0.0-beta.2, etc.)

3. **Backwards Compatibility**: When to allow breaking changes?
   - **Proposal**: Breaking changes only in major versions (1.x.x → 2.0.0)

4. **Rollback UI**: Should rollback be automatic or user-initiated?
   - **Proposal**: Automatic rollback on migration failure, manual rollback via CLI command

5. **Telemetry**: Should we collect anonymous usage data?
   - **Proposal**: Opt-in telemetry in beta, document what's collected

---

## Appendices

### Appendix A: Complete Installation Commands

```bash
# Phase 1: Beta (Git URL)
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Phase 2: Milestone (GitHub Release)
pip install https://github.com/memyselfmike/gao-agile-dev/releases/download/v1.0.0-beta.3/gao_dev-1.0.0b3-py3-none-any.whl

# Phase 3: RC (TestPyPI)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gao-dev==1.0.0rc1

# Phase 4: Production (PyPI)
pip install gao-dev
```

### Appendix B: Error Messages

All error messages follow this template:

```
[ERROR_CODE] Brief Description

Explanation of what went wrong.

Suggested Fix:
  command-to-run

Alternative Fix:
  alternative-command

Documentation: https://docs.gao-dev.com/errors/ERROR_CODE
Support: https://github.com/memyselfmike/gao-agile-dev/issues
```

Example:
```
[E001] Running from GAO-Dev Source Directory

GAO-Dev must be installed via pip and run from your project directory.

Suggested Fix:
  cd /path/to/your/project
  gao-dev start

Alternative Fix:
  gao-dev start --project /path/to/your/project

Documentation: https://docs.gao-dev.com/errors/E001
Support: https://github.com/memyselfmike/gao-agile-dev/issues/new
```

### Appendix C: Support Tier Matrix

| Phase | Response Time | Channels | SLA |
|-------|---------------|----------|-----|
| Phase 1 (Internal Beta) | <1 hour | Direct (Slack) | Best effort |
| Phase 2 (Expanded Beta) | <4 hours | Discord + GitHub | Best effort |
| Phase 3 (RC) | <24 hours | GitHub Issues | Best effort |
| Phase 4 (Production) | <48 hours | GitHub Issues | Community support |

---

## Conclusion

This PRD defines a comprehensive, multi-phased approach to beta distribution that:

1. **Eliminates repo confusion** through proper packaging and safety checks
2. **Enables rapid iteration** via GitHub-based distribution
3. **Protects user data** through backups, migrations, and rollbacks
4. **Scales from beta to production** with clear progression path
5. **Provides excellent UX** with clear docs and helpful errors

**Recommended Immediate Actions**:
1. Implement safety mechanisms (source repo detection)
2. Update `pyproject.toml` package-data
3. Create `.gaodev-source` marker file
4. Write beta tester documentation
5. Test Phase 1 approach with 3-5 internal testers

**Next Steps**: Create detailed technical architecture document and implementation plan.
