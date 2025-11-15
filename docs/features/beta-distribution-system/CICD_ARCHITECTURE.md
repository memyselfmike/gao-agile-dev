2# CI/CD Architecture for Beta Distribution

**Version**: 1.0
**Status**: Planning
**Created**: 2025-01-13

---

## Overview

This document defines the complete CI/CD pipeline for GAO-Dev beta distribution, including automated versioning, changelog generation, build processes, and deployment to multiple channels.

### Goals

1. **Automated Versioning**: No manual version updates in pyproject.toml
2. **Automated Changelog**: Generated from conventional commits
3. **Automated Builds**: Triggered on push/merge to main
4. **Automated Testing**: Run full test suite before builds
5. **Multiple Deployment Targets**: Git tags, GitHub Releases, TestPyPI, PyPI
6. **Zero Manual Steps**: Push to main → tests → build → deploy → notify

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Developer Workflow                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    git commit -m "feat: add feature"
                    git push origin main
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions (CI/CD)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Lint &    │→ │   Test     │→ │   Build    │→ │  Deploy  │ │
│  │  Type Check│  │   Suite    │  │  Package   │  │  to Env  │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Calculate  │→ │  Generate  │→ │   Create   │               │
│  │  Version   │  │ Changelog  │  │  Git Tag   │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ GitHub       │  │  TestPyPI    │  │    PyPI      │
        │ Releases     │  │  (RC only)   │  │ (Production) │
        └──────────────┘  └──────────────┘  └──────────────┘
                    │             │             │
                    └─────────────┴─────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │  Beta Testers Update        │
                    │  pip install --upgrade ...  │
                    └─────────────────────────────┘
```

---

## Versioning Strategy

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

Examples:
- `1.0.0` - Production release
- `1.0.0-beta.1` - Beta release
- `1.0.0-rc.1` - Release candidate
- `1.0.0-dev.1+abc1234` - Development build

### Version Calculation

**Automated based on conventional commits**:

```yaml
Commit Type → Version Bump
──────────────────────────
feat:     → MINOR++  (0.1.0 → 0.2.0)
fix:      → PATCH++  (0.1.0 → 0.1.1)
perf:     → PATCH++  (0.1.0 → 0.1.1)

BREAKING: → MAJOR++  (0.1.0 → 1.0.0)
          (or body contains "BREAKING CHANGE:")

chore:    → No bump
docs:     → No bump
test:     → No bump
refactor: → PATCH++ (configurable)
```

### Beta Versioning

During beta phase (pre-1.0.0):

```
Commit                    → Version
────────────────────────────────────────
Initial                   → 0.1.0-beta.1
feat: add workflow        → 0.2.0-beta.1
fix: git operations       → 0.2.1-beta.1
feat: provider selection  → 0.3.0-beta.1
BREAKING: new config      → 1.0.0-beta.1  (RC phase)
```

### Version Storage

**Single Source of Truth**: Git tags

```python
# pyproject.toml (dynamic versioning)
[build-system]
requires = ["setuptools>=68.0", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
dynamic = ["version"]

[tool.setuptools_scm]
version_scheme = "post-release"
local_scheme = "node-and-date"
```

Git tags drive everything:
- Package version (via setuptools-scm)
- Changelog sections
- Release notes
- PyPI metadata

---

## Changelog Automation

### Conventional Commits

**Required format**:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Examples**:

```bash
# Feature (MINOR bump)
feat(orchestrator): add ceremony auto-triggering

# Bug fix (PATCH bump)
fix(git-manager): resolve Windows path handling

# Breaking change (MAJOR bump)
feat(config): restructure provider configuration

BREAKING CHANGE: provider_preferences.yaml format changed.
See migration guide for details.

# Non-versioned commits
chore(deps): update anthropic to 0.35.0
docs(readme): add installation instructions
test(cli): add project detection tests
```

### Changelog Generation

**Tool**: [git-cliff](https://github.com/orhun/git-cliff)

**Configuration** (`.cliff.toml`):

```toml
[changelog]
header = """
# Changelog

All notable changes to GAO-Dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

body = """
{% if version %}
## [{{ version }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}
## [Unreleased]
{% endif %}

{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | upper_first }}
{% for commit in commits %}
  - {{ commit.message | split(pat="\n") | first }}
    {%- if commit.breaking %} [**BREAKING**]{% endif %}
    {%- if commit.scope %} ({{ commit.scope }}){% endif %}
{% endfor %}
{% endfor %}

{% if github.contributors %}
### Contributors
{% for contributor in github.contributors %}
- @{{ contributor.username }}
{%- endfor %}
{% endif %}

"""

[git]
conventional_commits = true
filter_unconventional = true
commit_parsers = [
  { message = "^feat", group = "Features" },
  { message = "^fix", group = "Bug Fixes" },
  { message = "^perf", group = "Performance" },
  { message = "^refactor", group = "Refactoring" },
  { message = "^doc", group = "Documentation" },
  { message = "^test", skip = true },
  { message = "^chore", skip = true },
]

protect_breaking_commits = true
```

**Generated Output**:

```markdown
# Changelog

## [0.3.0-beta.1] - 2025-01-15

### Features
- Add ceremony auto-triggering (orchestrator)
- Support local Ollama models (provider)

### Bug Fixes
- Resolve Windows path handling (git-manager)
- Fix provider selection crash (cli)

### Performance
- Optimize workflow loading (orchestrator)

### Contributors
- @memyselfmike
- @contributor2

## [0.2.1-beta.1] - 2025-01-13

### Bug Fixes
- Fix git operations on project root detection (cli)
```

---

## Build Pipeline

### GitHub Actions Workflows

#### 1. **Continuous Integration** (`.github/workflows/ci.yml`)

Runs on: **Every push, every PR**

```yaml
name: CI - Test & Lint

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for setuptools-scm

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check .

      - name: Type check with mypy
        run: mypy gao_dev

      - name: Format check with black
        run: black --check .

      - name: Run tests
        run: pytest --cov=gao_dev --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

#### 2. **Beta Release** (`.github/workflows/beta-release.yml`)

Runs on: **Push to main branch** (automatic beta releases)

```yaml
name: Beta Release

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # For creating releases and tags
      id-token: write  # For trusted publishing (future)

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for version calculation

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build setuptools-scm git-cliff twine

      - name: Calculate next version
        id: version
        run: |
          # Get current version from latest tag
          CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")

          # Analyze commits since last tag
          COMMITS=$(git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%s")

          # Determine version bump
          if echo "$COMMITS" | grep -q "^feat\|^BREAKING"; then
            NEXT=$(python scripts/bump_version.py "$CURRENT" minor)
          elif echo "$COMMITS" | grep -q "^fix\|^perf"; then
            NEXT=$(python scripts/bump_version.py "$CURRENT" patch)
          else
            echo "No version bump needed"
            exit 0
          fi

          # Add beta suffix
          NEXT_BETA="${NEXT}-beta.1"

          echo "current=$CURRENT" >> $GITHUB_OUTPUT
          echo "next=$NEXT_BETA" >> $GITHUB_OUTPUT

      - name: Generate changelog
        run: |
          git-cliff --tag ${{ steps.version.outputs.next }} \
                    --output CHANGELOG.md

      - name: Build package
        run: |
          # setuptools-scm will use git tags
          python -m build

      - name: Create git tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -a v${{ steps.version.outputs.next }} \
                   -m "Release v${{ steps.version.outputs.next }}"
          git push origin v${{ steps.version.outputs.next }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ steps.version.outputs.next }}
          name: Release ${{ steps.version.outputs.next }}
          body_path: CHANGELOG.md
          files: |
            dist/*.whl
            dist/*.tar.gz
          prerelease: true  # Beta releases are pre-releases

      - name: Notify Discord
        uses: sarisia/actions-status-discord@v1
        with:
          webhook: ${{ secrets.DISCORD_WEBHOOK }}
          title: "Beta Release ${{ steps.version.outputs.next }}"
          description: |
            New beta version available!

            Install: `pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main`

            Changes: See release notes
          url: https://github.com/${{ github.repository }}/releases/tag/v${{ steps.version.outputs.next }}
```

#### 3. **Release Candidate** (`.github/workflows/rc-release.yml`)

Runs on: **Manual trigger** or **tag push matching `v*-rc.*`**

```yaml
name: Release Candidate

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'RC version (e.g., 1.0.0-rc.1)'
        required: true
  push:
    tags:
      - 'v*-rc.*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install build setuptools-scm twine

      - name: Build package
        run: python -m build

      - name: Publish to TestPyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_TOKEN }}
        run: |
          twine upload --repository testpypi dist/*

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          name: Release Candidate ${{ github.ref_name }}
          prerelease: true
          body: |
            ## Release Candidate

            This is a release candidate for production deployment.

            ### Installation (TestPyPI)
            ```bash
            pip install --index-url https://test.pypi.org/simple/ \
                        --extra-index-url https://pypi.org/simple/ \
                        gao-dev==${{ github.ref_name }}
            ```

            Please test thoroughly before production release.
```

#### 4. **Production Release** (`.github/workflows/production-release.yml`)

Runs on: **Manual trigger only** (with approval gates)

```yaml
name: Production Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Production version (e.g., 1.0.0)'
        required: true
      confirm:
        description: 'Type "RELEASE" to confirm'
        required: true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate confirmation
        run: |
          if [ "${{ github.event.inputs.confirm }}" != "RELEASE" ]; then
            echo "Confirmation failed. You must type 'RELEASE' to proceed."
            exit 1
          fi

  release:
    needs: validate
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    permissions:
      contents: write
      id-token: write

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install build setuptools-scm twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ github.event.inputs.version }}
          name: Release ${{ github.event.inputs.version }}
          prerelease: false
          generate_release_notes: true

      - name: Announce on Discord
        uses: sarisia/actions-status-discord@v1
        with:
          webhook: ${{ secrets.DISCORD_WEBHOOK }}
          title: "🎉 Production Release ${{ github.event.inputs.version }}"
          description: |
            GAO-Dev ${{ github.event.inputs.version }} is now available!

            Install: `pip install gao-dev`

            Release notes: https://github.com/${{ github.repository }}/releases/tag/v${{ github.event.inputs.version }}
```

---

## Build Scripts

### 1. **Version Bump Script** (`scripts/bump_version.py`)

```python
#!/usr/bin/env python3
"""
Semantic version bumping utility.

Usage:
    python scripts/bump_version.py 0.1.0 minor  # → 0.2.0
    python scripts/bump_version.py 0.1.0 patch  # → 0.1.1
    python scripts/bump_version.py 0.1.0 major  # → 1.0.0
"""

import sys
from typing import Tuple


def parse_version(version: str) -> Tuple[int, int, int, str]:
    """Parse semantic version string."""
    # Remove 'v' prefix if present
    version = version.lstrip('v')

    # Split prerelease suffix
    if '-' in version:
        base, prerelease = version.split('-', 1)
    else:
        base, prerelease = version, ''

    # Parse major.minor.patch
    major, minor, patch = map(int, base.split('.'))

    return major, minor, patch, prerelease


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to type."""
    major, minor, patch, _ = parse_version(version)

    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: bump_version.py <version> <major|minor|patch>")
        sys.exit(1)

    current_version = sys.argv[1]
    bump_type = sys.argv[2]

    next_version = bump_version(current_version, bump_type)
    print(next_version)
```

### 2. **Pre-Release Check Script** (`scripts/pre_release_check.sh`)

```bash
#!/bin/bash
# Pre-release validation checks

set -e

echo "🔍 Running pre-release checks..."

# Check 1: All tests pass
echo "✓ Running test suite..."
pytest --cov=gao_dev --cov-report=term-missing

# Check 2: No type errors
echo "✓ Type checking..."
mypy gao_dev

# Check 3: Code formatting
echo "✓ Checking code format..."
black --check .
ruff check .

# Check 4: No uncommitted changes
echo "✓ Checking git status..."
if [[ -n $(git status --porcelain) ]]; then
    echo "❌ Uncommitted changes detected!"
    git status --short
    exit 1
fi

# Check 5: On main branch
BRANCH=$(git branch --show-current)
if [[ "$BRANCH" != "main" ]]; then
    echo "❌ Not on main branch! Currently on: $BRANCH"
    exit 1
fi

# Check 6: Up to date with origin
echo "✓ Checking sync with origin..."
git fetch origin
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
if [[ "$LOCAL" != "$REMOTE" ]]; then
    echo "❌ Local branch is not up to date with origin!"
    exit 1
fi

echo "✅ All pre-release checks passed!"
```

### 3. **Build Script** (`scripts/build.sh`)

```bash
#!/bin/bash
# Build wheel and source distribution

set -e

echo "🏗️  Building GAO-Dev package..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info

# Install build dependencies
echo "Installing build dependencies..."
pip install --upgrade build setuptools-scm

# Build package
echo "Building package..."
python -m build

# List built artifacts
echo "✅ Build complete! Artifacts:"
ls -lh dist/

# Validate wheel
echo "Validating wheel..."
pip install --upgrade twine
twine check dist/*

echo "✅ Build validation passed!"
```

### 4. **Local Install Script** (`scripts/install_local.sh`)

```bash
#!/bin/bash
# Install GAO-Dev locally for testing

set -e

echo "📦 Installing GAO-Dev locally..."

# Build package
./scripts/build.sh

# Uninstall existing
echo "Uninstalling existing GAO-Dev..."
pip uninstall -y gao-dev || true

# Install from wheel
echo "Installing from wheel..."
WHEEL=$(ls dist/*.whl | head -1)
pip install "$WHEEL"

# Verify installation
echo "Verifying installation..."
gao-dev --version

echo "✅ Local installation complete!"
```

---

## Deployment Workflows

### Beta Deployment (Automatic on push to main)

```
Developer → git push origin main
    ↓
GitHub Actions triggers
    ↓
1. Run tests (all platforms)
2. Calculate next version from commits
3. Generate changelog
4. Build wheel
5. Create git tag
6. Create GitHub release
7. Notify Discord
    ↓
Beta Testers → pip install git+https://github.com/.../main
```

**Trigger**: Every push to `main`
**Frequency**: Daily or per-commit
**Approval**: None (automated)

### RC Deployment (Manual trigger)

```
Developer → Trigger workflow manually
    ↓
GitHub Actions triggers
    ↓
1. Run full test suite
2. Build package
3. Publish to TestPyPI
4. Create GitHub release (RC)
5. Notify testers
    ↓
Testers → pip install --index-url test.pypi.org... gao-dev==1.0.0-rc.1
```

**Trigger**: Manual workflow dispatch
**Frequency**: Weekly (RC phase)
**Approval**: None (but manual trigger)

### Production Deployment (Manual with approval)

```
Product Owner → Trigger workflow + type "RELEASE"
    ↓
GitHub requires environment approval
    ↓
GitHub Actions triggers
    ↓
1. Run comprehensive tests
2. Build package
3. Publish to PyPI
4. Create GitHub release (production)
5. Announce publicly
    ↓
Users → pip install gao-dev
```

**Trigger**: Manual workflow dispatch + confirmation
**Frequency**: Monthly (post-beta)
**Approval**: Required (GitHub environment protection)

---

## Repository Configuration

### Branch Protection Rules

**`main` branch**:
- ✅ Require pull request reviews (1 approval)
- ✅ Require status checks to pass (CI must pass)
- ✅ Require conversation resolution
- ✅ Require linear history
- ✅ Include administrators
- ❌ Allow force pushes (disabled)
- ❌ Allow deletions (disabled)

### Environment Protection Rules

**`production` environment**:
- ✅ Required reviewers (2 approvals)
- ✅ Wait timer (0 minutes)
- ✅ Deployment branches (main only)

### Secrets Required

```yaml
Secrets:
  ANTHROPIC_API_KEY          # For integration tests
  TEST_PYPI_TOKEN            # TestPyPI publishing
  PYPI_TOKEN                 # PyPI publishing
  DISCORD_WEBHOOK            # Deployment notifications
  CODECOV_TOKEN              # Code coverage reporting
```

---

## Testing Strategy

### Test Coverage Requirements

- **Unit Tests**: >90% coverage
- **Integration Tests**: Core workflows
- **E2E Tests**: Full user journeys
- **Platform Tests**: Windows, macOS, Linux
- **Python Versions**: 3.11, 3.12

### Automated Test Runs

**On every PR**:
- Lint (ruff, black)
- Type check (mypy)
- Unit tests (pytest)
- Integration tests (pytest)

**Before releases**:
- All above +
- E2E tests (sandbox projects)
- Performance tests (benchmarks)
- Security scan (bandit)

---

## Rollback Procedures

### Beta Release Rollback

```bash
# Revert to previous tag
git tag -d v0.3.0-beta.1
git push origin :refs/tags/v0.3.0-beta.1

# Delete GitHub release
gh release delete v0.3.0-beta.1

# Testers revert
pip install git+https://github.com/.../gao-agile-dev.git@v0.2.1-beta.1
```

### Production Release Rollback

```bash
# Cannot delete from PyPI!
# Must release a new version

# Option 1: Patch fix
git checkout v1.0.0
# Make fix
# Release v1.0.1

# Option 2: Yank release (hides from pip)
# (Manual process on pypi.org)
# Then release v1.0.1
```

**IMPORTANT**: PyPI versions are permanent. Yanking only hides from `pip install`, doesn't delete.

---

## Monitoring and Observability

### Metrics to Track

1. **Build Metrics**
   - Build success rate
   - Build duration
   - Test pass rate
   - Coverage percentage

2. **Deployment Metrics**
   - Time from commit to deployment
   - Number of beta installs (GitHub API)
   - Number of PyPI downloads

3. **Quality Metrics**
   - Number of issues opened post-release
   - Time to fix critical bugs
   - Rollback frequency

### Dashboard (GitHub Actions)

All metrics visible in:
- GitHub Actions tab (workflow runs)
- GitHub Insights (traffic, clones)
- PyPI Statistics (downloads)
- Codecov (coverage trends)

---

## Documentation Generation

### API Documentation (Future)

```yaml
# .github/workflows/docs.yml
name: Generate Docs

on:
  push:
    branches: [main]
    paths:
      - 'gao_dev/**/*.py'
      - 'docs/**/*.md'

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install mkdocs mkdocs-material mkdocstrings[python]

      - name: Build docs
        run: mkdocs build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

---

## Timeline and Migration

### Phase 1: Setup (Week 1)

- [ ] Add setuptools-scm to pyproject.toml
- [ ] Create `.cliff.toml` configuration
- [ ] Write build scripts (bump_version.py, build.sh, etc.)
- [ ] Create GitHub Actions workflows (ci.yml, beta-release.yml)
- [ ] Configure branch protection and secrets
- [ ] Test pipeline with dummy release

### Phase 2: Beta Automation (Week 2)

- [ ] Enable automatic beta releases on push to main
- [ ] Test full beta release workflow
- [ ] Set up Discord notifications
- [ ] Document release process for team

### Phase 3: RC Automation (Week 7)

- [ ] Create RC workflow
- [ ] Configure TestPyPI authentication
- [ ] Test RC deployment
- [ ] Document RC process

### Phase 4: Production Automation (Week 9)

- [ ] Create production workflow with approvals
- [ ] Configure PyPI authentication
- [ ] Create runbook for production releases
- [ ] Test production deployment to TestPyPI

---

## Appendix: File Structure

```
gao-agile-dev/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Continuous integration
│       ├── beta-release.yml          # Automatic beta releases
│       ├── rc-release.yml            # Release candidates
│       ├── production-release.yml    # Production releases
│       └── docs.yml                  # Documentation generation
│
├── scripts/
│   ├── bump_version.py               # Version calculation
│   ├── pre_release_check.sh          # Pre-release validation
│   ├── build.sh                      # Package building
│   └── install_local.sh              # Local testing install
│
├── .cliff.toml                       # Changelog configuration
├── CHANGELOG.md                      # Generated changelog
├── pyproject.toml                    # Package metadata (dynamic version)
└── README.md                         # Updated with CI badges
```

---

## Success Criteria

### Automation Metrics

- ✅ 0 manual steps for beta releases
- ✅ <5 minutes from commit to deployed beta
- ✅ 100% changelog coverage (all commits documented)
- ✅ 0 version conflicts (automated versioning)

### Quality Metrics

- ✅ >95% CI pass rate
- ✅ 0 releases with failing tests
- ✅ <10% rollback rate
- ✅ >90% test coverage maintained

### Developer Experience

- ✅ Push to main → auto-release (no manual steps)
- ✅ Clear changelog generation
- ✅ Fast feedback (<5 min builds)
- ✅ Easy local testing

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [git-cliff Documentation](https://git-cliff.org/)
- [setuptools-scm](https://github.com/pypa/setuptools-scm)
- [GitHub Actions](https://docs.github.com/en/actions)
