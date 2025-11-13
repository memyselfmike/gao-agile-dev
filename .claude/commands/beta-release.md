# Trigger Beta Release

Trigger the GitHub Actions beta release workflow to create and publish a beta release.

## Prerequisites

1. Check that GitHub CLI is installed:
   ```bash
   gh --version
   ```
   If not installed, inform user to install from https://cli.github.com/

2. Check authentication:
   ```bash
   gh auth status
   ```
   If not authenticated, guide user: `gh auth login`

## Instructions

1. **Run pre-release checks first** (recommended):
   ```bash
   bash scripts/pre_release_check.sh
   ```

2. **Show what version will be created**:
   ```bash
   python scripts/bump_version.py
   ```

3. **Ask user for confirmation** before triggering

4. **Trigger the workflow**:
   ```bash
   gh workflow run beta-release.yml --ref main
   ```

5. **Monitor the workflow**:
   ```bash
   gh run watch
   ```
   Or view in browser:
   ```bash
   gh workflow view beta-release.yml --web
   ```

## What the Workflow Does

1. Calculates next semantic version from conventional commits
2. Increments beta suffix (v0.1.0-beta.1, v0.1.0-beta.2, etc.)
3. Creates git tag
4. Builds wheel with setuptools-scm
5. Generates changelog with git-cliff
6. Creates GitHub release with changelog
7. Uploads wheel artifact

## Notes

- Workflow runs on main branch only
- Requires manual trigger (not automatic)
- Creates beta tags (not stable releases)
- Safe to run multiple times (beta counter increments)
