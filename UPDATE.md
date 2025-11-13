# Updating GAO-Dev

This guide explains how to update your local GAO-Dev installation to the latest version from the repository.

## Quick Update (Recommended)

Use the automated update scripts for a seamless update experience:

**Windows (Command Prompt or PowerShell):**
```cmd
update.bat
```

**Windows (Git Bash/WSL) or Unix/Linux/Mac:**
```bash
./update.sh
```

**Important**: Use the appropriate script for your shell. Don't run `bash update.bat`!

The update script will:
1. Pull the latest changes from GitHub
2. Update all dependencies
3. Run database migrations
4. Verify the installation
5. Check for consistency issues

## Manual Update Process

If you prefer to update manually or the script doesn't work:

### Step 1: Pull Latest Changes

```bash
# Make sure you're on the main branch
git checkout main

# Pull latest changes
git pull origin main
```

### Step 2: Update Dependencies

**With uv (recommended):**
```bash
# Sync dependencies (fast!)
uv sync
```

**With pip:**
```bash
# Update dependencies
pip install -e ".[dev]" --upgrade
```

### Step 3: Run Database Migrations

```bash
# Check migration status
gao-dev db status

# Apply pending migrations
gao-dev db migrate

# Verify migrations applied successfully
gao-dev db status
```

### Step 4: Run Consistency Checks

```bash
# Check for file-database consistency issues
gao-dev migrate consistency-check

# If issues found, repair them
gao-dev migrate consistency-repair
```

### Step 5: Verify Installation

```bash
# Check version
gao-dev version

# Run health check
gao-dev health
```

## Version Pinning for Stability

If you want to stay on a specific version for stability:

### Using Git Tags

```bash
# List available versions
git tag

# Checkout a specific version
git checkout v1.2.0

# Install that version
uv sync
gao-dev db migrate
```

### Using Git Branches

```bash
# Stay on a release branch instead of main
git checkout release/v1.x
git pull origin release/v1.x
```

## Handling Breaking Changes

### Major Version Updates (e.g., v1.x to v2.x)

1. **Read the CHANGELOG.md** - Check for breaking changes
2. **Backup your projects** - Copy your `.gao-dev/` directories
3. **Run migrations carefully** - They may transform data structures
4. **Test in a sandbox first**:
   ```bash
   gao-dev sandbox init test-update
   cd sandbox/projects/test-update
   # Test your workflows here
   ```

### Migration Rollback

If something goes wrong with migrations:

```bash
# Rollback last migration
gao-dev db rollback

# Rollback last 3 migrations
gao-dev db rollback --count 3
```

## Update Frequency Recommendations

### For Beta Testers

- **Daily/Weekly**: If you're actively testing and providing feedback
  ```bash
  git pull && uv sync && gao-dev db migrate
  ```

- **Weekly/Bi-weekly**: For stable testing with less frequent updates
  ```bash
  # Use update script once a week
  ./update.sh
  ```

### For Production Use

- **Release Branches Only**: Stay on `release/v1.x` branches
- **Test Before Updating**: Always test in sandbox first
- **Read Release Notes**: Check CHANGELOG.md for breaking changes

## Checking for Updates

### Check if Updates Available

```bash
# Fetch latest changes (doesn't apply them)
git fetch origin

# Check if you're behind
git status
# Will show: "Your branch is behind 'origin/main' by N commits"

# See what changed
git log HEAD..origin/main --oneline
```

### Check Current Version

```bash
# Show version info
gao-dev version

# Show detailed system info
gao-dev health
```

## Troubleshooting Updates

### Issue: Dependency Conflicts

```bash
# Clear cache and reinstall
rm -rf .venv  # or rd /s /q .venv on Windows
uv sync
uv pip install -e .
```

### Issue: Migration Failures

```bash
# Check migration status
gao-dev db status

# Validate migrations
gao-dev db validate

# Check logs for errors
# Migrations log to: .gao-dev/logs/migrations.log
```

### Issue: File-Database Inconsistencies

```bash
# Check for issues
gao-dev migrate consistency-check

# Repair automatically
gao-dev migrate consistency-repair

# Manual repair if needed
# Backup first!
cp .gao-dev/documents.db .gao-dev/documents.db.backup
gao-dev migrate consistency-repair --force
```

### Issue: Merge Conflicts

```bash
# If you have local changes that conflict
git stash                # Save your changes
git pull                 # Pull updates
git stash pop           # Restore your changes
# Resolve conflicts manually, then:
git add .
git commit
```

### Issue: "Command not found" After Update

```bash
# Reinstall CLI
uv pip install -e .

# Or reactivate environment
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows
```

## Staying Informed

### Release Notifications

- **Watch the repo**: Click "Watch" on GitHub for notifications
- **Check CHANGELOG.md**: Read before updating
- **Join discussions**: GitHub Discussions for questions

### What Changed?

```bash
# See all changes since last update
git log --oneline --graph --decorate --all

# See specific file changes
git diff HEAD~10 HEAD -- README.md

# See changes in last N days
git log --since="7 days ago" --oneline
```

## Best Practices for Beta Testers

1. ✅ **Update regularly** - Stay current with fixes and features
2. ✅ **Read release notes** - Know what changed before updating
3. ✅ **Backup before updating** - Copy `.gao-dev/` directories
4. ✅ **Test after updating** - Run `gao-dev health` and basic commands
5. ✅ **Report issues** - Create GitHub issues for bugs you find
6. ✅ **Use feature branches** - If contributing code
7. ✅ **Join community** - GitHub Discussions for questions

## Automated Update Schedule

For beta testers who want automatic updates:

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Add daily update at 2 AM
0 2 * * * cd /path/to/gao-agile-dev && ./update.sh >> /tmp/gao-update.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start program
5. Program: `C:\path\to\gao-agile-dev\update.bat`

## Emergency Rollback

If an update breaks everything:

```bash
# Find working commit
git reflog

# Rollback to working version
git reset --hard abc123  # Replace with working commit

# Reinstall
uv sync
uv pip install -e .

# Restore database from backup
cp .gao-dev/documents.db.backup .gao-dev/documents.db
```

## Questions or Issues?

- **GitHub Issues**: https://github.com/memyselfmike/gao-agile-dev/issues
- **Documentation**: Check docs/INDEX.md for guides
- **Health Check**: Run `gao-dev health` to diagnose problems

---

**Last Updated**: 2025-01-13
**For GAO-Dev Version**: 1.0.0+
