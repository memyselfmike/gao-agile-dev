# Release Management Skill

Use this skill when managing GAO-Dev releases, checking release status, creating new releases, or helping beta testers get updates.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Check latest releases | `gh release list --limit=5` |
| Check workflow status | `gh run list --workflow=beta-release.yml --limit=5` |
| Check current version | `git describe --tags --abbrev=0` |
| Trigger manual release | `gh workflow run beta-release.yml --ref main` |
| View release | `gh release view <tag>` |

---

## Release System Architecture

### Version Management
- **setuptools-scm**: Derives version from git tags automatically
- **No manual version editing** - just create tags
- **Semantic versioning**: MAJOR.MINOR.PATCH-beta.N

### Auto-Release Triggers
Beta releases auto-trigger on push to `main` when commits contain:
- `feat:` - New feature (minor bump)
- `fix:` - Bug fix (patch bump)
- `perf:` - Performance improvement (patch bump)
- `refactor:` - Code refactoring (patch bump)

**NO release triggered by**: `docs:`, `test:`, `chore:`

### Version Calculation
```
feat:     0.1.0 -> 0.2.0-beta.1
fix:      0.1.0 -> 0.1.1-beta.1
Multiple beta releases: -beta.1 -> -beta.2 -> -beta.3
```

---

## Common Tasks

### 1. Check Release Status

**After fixing a bug or adding a feature:**

```bash
# Check if workflow triggered
gh run list --workflow=beta-release.yml --limit=3

# See what release was created
gh release list --limit=3

# Get current version
git describe --tags --abbrev=0
```

### 2. Help Beta Testers Update

**Tell testers to run:**

```bash
# Install specific version
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@<TAG>

# Install latest from main
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Example with specific tag
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

### 3. Manual Release Trigger

If auto-release didn't trigger or you need to force a release:

```bash
# Trigger manually
gh workflow run beta-release.yml --ref main

# Monitor the workflow
gh run watch
```

### 4. Check Commits Since Last Release

```bash
# See commits that will be in next release
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Check for release-worthy commits
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%s" | grep -E "^(feat|fix|perf|refactor)"
```

### 5. Pre-Release Checklist

Before any release, verify:

```bash
# Run tests
pytest tests/ -v

# Check for uncommitted changes
git status

# Verify on main branch
git branch --show-current

# Pull latest
git pull origin main
```

---

## Troubleshooting

### No Release Created

**Possible causes:**

1. **Commit message format wrong**
   - Wrong: `Add new feature`
   - Right: `feat: add new feature`

2. **Only docs/test/chore commits**
   ```bash
   # Check what types of commits
   git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%s"
   ```

3. **Workflow failed**
   ```bash
   gh run list --workflow=beta-release.yml --limit=1
   gh run view <RUN_ID> --log
   ```

### Version Conflict

If tag already exists:

```bash
# Delete local tag
git tag -d <TAG>

# Delete remote tag
git push origin :refs/tags/<TAG>

# Delete GitHub release
gh release delete <TAG> --yes

# Re-run workflow
gh workflow run beta-release.yml --ref main
```

### Tester Can't Install

1. **Check tag exists:**
   ```bash
   git tag -l "*beta*" | tail -5
   ```

2. **Verify GitHub release:**
   ```bash
   gh release view <TAG>
   ```

3. **Alternative install methods:**
   ```bash
   # From main branch
   pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

   # From specific commit
   pip install git+https://github.com/memyselfmike/gao-agile-dev.git@<COMMIT_SHA>
   ```

---

## Available Slash Commands

The following commands are available for release management:

| Command | Purpose |
|---------|---------|
| `/beta-release` | Trigger beta release workflow |
| `/pre-release-check` | Run pre-release validation |
| `/bump-version` | Show what version will be created |
| `/generate-changelog` | Generate changelog from commits |
| `/release-help` | Show release help |
| `/build` | Build the package locally |
| `/install-local` | Install package locally for testing |

---

## Commit Message Format

**Always use conventional commits for proper versioning:**

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature (MINOR bump)
- `fix` - Bug fix (PATCH bump)
- `perf` - Performance improvement (PATCH bump)
- `refactor` - Code refactoring (PATCH bump)
- `docs` - Documentation only (no release)
- `test` - Test changes (no release)
- `chore` - Build/tooling (no release)

**Examples:**

```bash
# Feature
git commit -m "feat(orchestrator): add ceremony auto-triggering"

# Bug fix
git commit -m "fix(cli): pass config_loader as keyword argument"

# Breaking change (MAJOR bump)
git commit -m "feat(config): restructure configuration

BREAKING CHANGE: config format changed"
```

---

## Release Lifecycle

### Beta Testing Phase (Current)
1. Push to main with `feat:` or `fix:` commit
2. GitHub Actions auto-creates release
3. Testers install from GitHub
4. Collect feedback, fix issues
5. Repeat

### Release Candidate (Future)
1. After sufficient beta testing
2. Manual trigger of RC workflow
3. Publish to TestPyPI
4. Extended testing period

### Production Release (Future)
1. After RC validation
2. Manual trigger with approval
3. Publish to PyPI
4. Public availability

---

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package configuration, setuptools-scm |
| `.github/workflows/beta-release.yml` | Beta release workflow |
| `scripts/bump_version.py` | Version calculation script |
| `scripts/pre_release_check.sh` | Pre-release validation |
| `CHANGELOG.md` | Generated changelog |
| `docs/features/beta-distribution-system/RELEASE_PROCESS.md` | Full documentation |

---

## Communication Templates

### Announcing a Fix

```markdown
**GAO-Dev v0.2.1-beta.1 Released**

Fixed: [Brief description of fix]

Update with:
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

### Requesting Feedback

```markdown
Please test the new release and report any issues:
- GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues
- Include: Python version, OS, error message, steps to reproduce
```

---

## Best Practices

1. **Always use conventional commits** - They drive automatic versioning
2. **Check workflow status after push** - Verify release was created
3. **Communicate with testers** - Tell them when to update
4. **Run pre-release checks** - Before any manual releases
5. **Keep commits focused** - One fix per commit for clean changelogs
6. **Tag semantically** - Major for breaking, minor for features, patch for fixes

---

## References

- Full Documentation: `docs/features/beta-distribution-system/`
- Release Process: `docs/features/beta-distribution-system/RELEASE_PROCESS.md`
- CI/CD Architecture: `docs/features/beta-distribution-system/CICD_ARCHITECTURE.md`
- GitHub Releases: https://github.com/memyselfmike/gao-agile-dev/releases
