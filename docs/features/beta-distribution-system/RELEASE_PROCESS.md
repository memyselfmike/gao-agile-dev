# GAO-Dev Release Process

**Version**: 1.0
**Last Updated**: 2025-01-13

---

## Overview

This document describes the automated release process for GAO-Dev beta testing through production deployment.

## Quick Reference

| Release Type | Trigger | Approval | Destination | Command |
|--------------|---------|----------|-------------|---------|
| **Beta** | Push to `main` | None (auto) | GitHub tags | `git push origin main` |
| **RC** | Manual workflow | None | TestPyPI | Via GitHub UI |
| **Production** | Manual workflow | Required | PyPI | Via GitHub UI |

---

## Beta Releases (Automated)

### Process

**Automatic on every push to `main` that includes `feat:`, `fix:`, or `perf:` commits**

```
Developer commits → Push to main → CI passes → Auto-release
```

### Steps (Automated by GitHub Actions)

1. **Commit with conventional format**
   ```bash
   git commit -m "feat(orchestrator): add ceremony auto-triggering"
   git push origin main
   ```

2. **GitHub Actions automatically:**
   - Runs full test suite
   - Calculates next version from commits
   - Builds package
   - Creates git tag (e.g., `v0.2.0-beta.1`)
   - Creates GitHub Release
   - Attaches wheel files

3. **Beta testers update:**
   ```bash
   pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
   ```

### Version Calculation

Automated based on commit types since last tag:

```
feat:     → minor bump (0.1.0 → 0.2.0)
fix:      → patch bump (0.1.0 → 0.1.1)
perf:     → patch bump
refactor: → patch bump

All beta releases get -beta.1 suffix
```

### Manual Beta Release

If you need to trigger a release manually:

1. Go to Actions tab on GitHub
2. Select "Beta Release" workflow
3. Click "Run workflow"
4. Select `main` branch
5. Click "Run workflow" button

---

## Release Candidate (RC) Process

### When to Create RC

- After beta testing phase (typically 6-8 weeks)
- Before production release
- To test PyPI publication process

### Steps

1. **Prepare for RC**
   ```bash
   # Ensure all tests pass
   ./scripts/pre_release_check.sh

   # Ensure on main branch
   git checkout main
   git pull origin main
   ```

2. **Trigger RC Workflow**
   - Go to GitHub Actions tab
   - Select "Release Candidate" workflow
   - Click "Run workflow"
   - Enter version (e.g., `1.0.0-rc.1`)
   - Click "Run workflow" button

3. **GitHub Actions automatically:**
   - Runs full test suite
   - Builds package
   - Publishes to TestPyPI
   - Creates GitHub Release (RC)

4. **Testers install from TestPyPI:**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
               --extra-index-url https://pypi.org/simple/ \
               gao-dev==1.0.0-rc.1
   ```

5. **Validation Period**
   - Test for 1-2 weeks
   - Fix any issues found
   - Create new RC if needed (rc.2, rc.3, etc.)

---

## Production Release Process

### Prerequisites

- ✅ RC tested for at least 1 week
- ✅ No critical bugs reported
- ✅ Documentation complete
- ✅ All tests passing
- ✅ Team approval obtained

### Steps

1. **Final Pre-Release Check**
   ```bash
   # Run comprehensive checks
   ./scripts/pre_release_check.sh

   # Verify on main branch
   git checkout main
   git pull origin main

   # Verify clean state
   git status
   ```

2. **Trigger Production Release**
   - Go to GitHub Actions tab
   - Select "Production Release" workflow
   - Click "Run workflow"
   - Enter version (e.g., `1.0.0`)
   - Type "RELEASE" in confirmation field
   - Click "Run workflow" button

3. **Approval Gate**
   - GitHub requires approval from configured reviewers
   - Reviewers verify:
     - Version number is correct
     - Release notes are complete
     - All checks passed
   - Approve deployment

4. **GitHub Actions automatically:**
   - Runs final test suite
   - Builds package
   - Publishes to PyPI (production)
   - Creates GitHub Release (production)
   - Announces release

5. **Users install from PyPI:**
   ```bash
   pip install gao-dev
   ```

6. **Post-Release**
   - Monitor PyPI downloads
   - Watch for issue reports
   - Prepare patch release if needed

---

## Conventional Commit Format

**All commits must follow this format for automated versioning:**

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `perf` | Performance improvement | PATCH |
| `refactor` | Code refactoring | PATCH |
| `docs` | Documentation only | None |
| `test` | Test changes only | None |
| `chore` | Build/tooling changes | None |

### Examples

```bash
# Feature (minor bump: 0.1.0 → 0.2.0)
git commit -m "feat(orchestrator): add ceremony auto-triggering"

# Bug fix (patch bump: 0.1.0 → 0.1.1)
git commit -m "fix(git-manager): resolve Windows path handling"

# Multiple lines
git commit -m "feat(provider): add Ollama support

Add support for local Ollama models including deepseek-r1,
llama2, and codellama.

Closes #123"

# Breaking change (major bump: 0.9.0 → 1.0.0)
git commit -m "feat(config): restructure provider configuration

BREAKING CHANGE: provider_preferences.yaml format changed.
See MIGRATION_GUIDE.md for upgrade instructions."

# No version bump
git commit -m "docs: update installation instructions"
git commit -m "test: add provider selection tests"
git commit -m "chore(deps): update anthropic to 0.35.0"
```

---

## Changelog Management

### Automated Generation

CHANGELOG.md is automatically generated from commit messages using git-cliff.

**Configuration**: `.cliff.toml`

### Manual Changelog Editing

If you need to manually edit the changelog:

1. Edit `CHANGELOG.md` directly
2. Commit with `docs:` prefix (won't trigger release)
3. Next release will preserve manual edits

### Changelog Structure

```markdown
# Changelog

## [0.3.0-beta.1] - 2025-01-15

### Features
- **orchestrator**: Add ceremony auto-triggering
- **provider**: Support local Ollama models

### Bug Fixes
- **git-manager**: Resolve Windows path handling

### Documentation
- Update installation instructions
```

---

## Rollback Procedures

### Rolling Back Beta Release

```bash
# 1. Delete the git tag
git tag -d v0.3.0-beta.1
git push origin :refs/tags/v0.3.0-beta.1

# 2. Delete GitHub release
gh release delete v0.3.0-beta.1 --yes

# 3. Testers revert to previous version
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@v0.2.1-beta.1
```

### Rolling Back RC Release

```bash
# 1. TestPyPI releases cannot be deleted
# 2. Must create new RC with fixes
# 3. Can "yank" release to hide it (manual on test.pypi.org)
```

### Rolling Back Production Release

**⚠️ PyPI releases are permanent and cannot be deleted!**

Options:
1. **Yank the release** (hides from `pip install`, doesn't delete)
   - Go to pypi.org
   - Find the release
   - Click "Yank release"
   - Must release fixed version

2. **Release patch fix immediately**
   ```bash
   # Fix the bug
   git commit -m "fix(critical): resolve production issue"
   git push origin main

   # Manually trigger production release with v1.0.1
   ```

---

## Troubleshooting

### Release Workflow Failed

1. **Check GitHub Actions logs**
   - Go to Actions tab
   - Click on failed workflow
   - Review logs for errors

2. **Common Issues**:
   - Tests failed → Fix tests, push to main
   - Build failed → Check pyproject.toml, dependencies
   - Version calculation failed → Check commit messages format
   - Tag already exists → Delete tag and retry

### No Release Triggered

**Possible causes**:

1. **No release-worthy commits**
   ```bash
   # Check commits since last tag
   git log $(git describe --tags --abbrev=0)..HEAD --oneline

   # If only docs/test/chore commits, no release triggered
   ```

2. **Commit format incorrect**
   ```bash
   # Wrong: Add new feature
   # Right: feat: add new feature
   ```

3. **Path exclusions**
   - Changes only to `docs/**` or `**.md` don't trigger releases
   - Check `.github/workflows/beta-release.yml` `paths-ignore`

### Version Conflict

If git tag already exists:

```bash
# Delete local tag
git tag -d v0.3.0-beta.1

# Delete remote tag
git push origin :refs/tags/v0.3.0-beta.1

# Retry release
```

### PyPI Upload Failed

1. **Check authentication**
   - Verify `PYPI_TOKEN` secret is set
   - Token must have upload permissions

2. **Version already exists**
   - PyPI doesn't allow version reuse
   - Must increment version number

---

## CI/CD Pipeline Status

### Monitoring

**GitHub Actions Dashboard**: https://github.com/memyselfmike/gao-agile-dev/actions

**Key Metrics**:
- ✅ CI pass rate (target: >95%)
- ⏱️ Build time (target: <5 minutes)
- 📦 Release frequency (beta: daily, production: monthly)

### Notifications

- GitHub Actions failures → Email to repo admin
- Successful releases → Discord webhook (if configured)

---

## Best Practices

### For Developers

1. **Always use conventional commits**
2. **Run pre-release checks locally before pushing**
   ```bash
   ./scripts/pre_release_check.sh
   ```
3. **Test builds locally**
   ```bash
   ./scripts/build.sh
   ./scripts/install_local.sh
   ```
4. **Keep commits focused** (one feature/fix per commit)
5. **Write clear commit messages** (they become changelog entries)

### For Releases

1. **Beta**: Push to main freely, releases are automatic
2. **RC**: Test thoroughly before production
3. **Production**: Get team approval, double-check everything

### Semantic Versioning

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features (backward compatible)
- **Patch** (1.0.0 → 1.0.1): Bug fixes

During beta (pre-1.0.0):
- Breaking changes can happen in minor versions
- All releases get `-beta.1` suffix

---

## Security

### Secrets Management

Required GitHub secrets:
- `ANTHROPIC_API_KEY` - For integration tests
- `TEST_PYPI_TOKEN` - TestPyPI publishing
- `PYPI_TOKEN` - PyPI publishing
- `DISCORD_WEBHOOK` - Release notifications (optional)

**Never commit**:
- API keys
- PyPI tokens
- Personal access tokens

### Token Permissions

- **PYPI_TOKEN**: Scoped to `gao-dev` project only
- **TEST_PYPI_TOKEN**: Scoped to `gao-dev` project only
- Use "trusted publishing" when available (future)

---

## Future Enhancements

### Planned

- [ ] Automated changelog in GitHub Release body
- [ ] Discord/Slack notifications for releases
- [ ] Automated security scanning (bandit, safety)
- [ ] Performance benchmarking on release
- [ ] Automated documentation deployment (MkDocs)
- [ ] Release notes generation from PRs

### Under Consideration

- [ ] Automated rollback on critical failures
- [ ] Canary releases (gradual rollout)
- [ ] A/B testing for new features
- [ ] Automated compatibility testing

---

## Questions?

- **GitHub Issues**: https://github.com/memyselfmike/gao-agile-dev/issues
- **Documentation**: `docs/features/beta-distribution-system/`
- **Architecture**: `CICD_ARCHITECTURE.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-01-13
