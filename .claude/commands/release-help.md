# Release Commands Quick Reference

Display a quick reference guide for all GAO-Dev release and build commands.

## Available Slash Commands

### Development & Testing

**`/build`** - Build the GAO-Dev wheel package locally
- Runs: `bash scripts/build.sh`
- Outputs wheel to `dist/` directory
- Validates with twine

**`/install-local`** - Install GAO-Dev locally in editable mode
- Runs: `bash scripts/install_local.sh`
- Installs with `pip install -e .`
- Useful for testing before release

**`/pre-release-check`** - Run comprehensive pre-release quality checks
- Runs: `bash scripts/pre_release_check.sh`
- Checks: tests, mypy, black, ruff, git status, build
- All must pass before release

### Version Management

**`/bump-version`** - Calculate next version from conventional commits
- Runs: `python scripts/bump_version.py`
- Auto-detects: BREAKING CHANGE (major), feat (minor), fix (patch)
- Shows what version would be created

**`/generate-changelog`** - Generate/update CHANGELOG.md
- Runs: `git cliff`
- Groups commits by type (Features, Fixes, etc.)
- Detects breaking changes

### Release Workflow

**`/beta-release`** - Trigger GitHub Actions beta release workflow
- Runs: `gh workflow run beta-release.yml --ref main`
- Creates beta tag (v0.1.0-beta.1, etc.)
- Builds, tags, and publishes to GitHub releases

## Typical Release Workflow

1. **`/pre-release-check`** - Ensure code quality
2. **`/bump-version`** - Check what version will be created
3. **`/generate-changelog`** - Preview changelog (optional)
4. **`/beta-release`** - Trigger release workflow

## Notes

- All commands use Epic 36 infrastructure
- Beta releases use semantic versioning
- Changelog auto-generated from conventional commits
- CI pipeline runs automatically on push
- Beta releases require manual trigger

For detailed help on any command, type the command (e.g., `/build`)
