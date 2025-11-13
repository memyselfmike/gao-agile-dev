# Beta Distribution and Update Management System

**Status**: Planning
**Version**: 1.0.0
**Created**: 2025-01-13

---

## Overview

This feature solves the **critical repo confusion problem** where GAO-Dev can operate on its own repository instead of user projects. It establishes a comprehensive distribution system for safe beta testing with rapid iteration capabilities.

### The Problem

Current workflow:
```bash
# Beta tester clones GAO-Dev repo
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e .

# May accidentally run from GAO-Dev directory
gao-dev start  # ⚠️ OPERATES ON GAO-DEV'S OWN REPO!
```

**Result**: Git conflicts, consistency checker warnings, database operations on wrong project.

### The Solution

Proper packaging and distribution:
```bash
# Beta tester installs from GitHub
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Runs from their project
cd ~/my-project
gao-dev start  # ✅ OPERATES ON USER'S PROJECT
```

**Result**: Complete separation, no repo confusion, safe updates.

---

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| **[PRD.md](./PRD.md)** | Complete requirements, approach analysis, phased rollout | Product team, developers |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | Technical implementation details | Developers |
| **[USER_GUIDE.md](./USER_GUIDE.md)** | Beta tester installation and usage | Beta testers |
| **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** | Common issues and solutions | Beta testers, support |
| **[FAQ.md](./FAQ.md)** | Frequently asked questions | All audiences |

---

## Key Components

### 1. Safety Mechanisms

- **Source Repository Detection**: Prevents running GAO-Dev from its own source directory
- **Version Compatibility Checking**: Ensures project databases match GAO-Dev version
- **Pre-Update Backups**: Automatic backups before any destructive operations
- **Migration Transaction Safety**: Atomic migrations with rollback on failure
- **Health Checks**: Post-update validation

### 2. Distribution Channels

| Phase | Method | Command | Best For |
|-------|--------|---------|----------|
| **Phase 1** | Git URL Install | `pip install git+...@main` | Active beta (fast iteration) |
| **Phase 2** | GitHub Releases | `pip install https://github.com/.../releases/...` | Stable milestones |
| **Phase 3** | TestPyPI | `pip install --index-url test.pypi.org...` | Pre-production validation |
| **Phase 4** | PyPI | `pip install gao-dev` | Production release |

### 3. Update Management

- **One-Command Updates**: `pip install --upgrade --force-reinstall git+...`
- **State Preservation**: User projects remain unchanged during updates
- **Automatic Migrations**: Database schema updates handled transparently
- **Rollback Support**: Failed updates restore from backup

---

## Architecture Highlights

```
GAO-Dev Installation (Site-Packages)
├── /usr/local/lib/python3.11/site-packages/gao_dev/
│   ├── cli/          ← GAO-Dev code
│   ├── orchestrator/
│   ├── workflows/
│   └── config/

User Project (Completely Separate)
├── ~/my-project/
│   ├── .gao-dev/     ← User's project state
│   │   ├── documents.db
│   │   ├── version.txt
│   │   └── context.json
│   ├── docs/         ← User's documentation
│   ├── src/          ← User's code
│   └── .git/         ← User's git repo
```

**Key Insight**: GAO-Dev lives in Python's site-packages, never in user projects.

---

## Implementation Roadmap

### Phase 1: Setup (Week 1)

**Goal**: Implement safety mechanisms

- [ ] Add source repository detection
- [ ] Update `pyproject.toml` package-data
- [ ] Create `.gaodev-source` marker file
- [ ] Implement version compatibility checking
- [ ] Add backup manager
- [ ] Write unit tests

**Deliverable**: GAO-Dev prevents running from source directory

---

### Phase 2: Beta Testing (Weeks 2-6)

**Goal**: Validate with real testers

- [ ] Write beta tester documentation
- [ ] Set up Discord/Slack support channel
- [ ] Recruit 5-10 initial testers
- [ ] Monitor for issues
- [ ] Implement migration system
- [ ] Test updates with testers

**Deliverable**: 10+ beta testers using successfully

---

### Phase 3: Pre-Production (Weeks 7-8)

**Goal**: Final validation before production

- [ ] Publish to TestPyPI
- [ ] Expand to 30-50 testers
- [ ] Validate PyPI metadata
- [ ] Complete documentation
- [ ] Performance testing
- [ ] Security audit

**Deliverable**: Release candidate ready for production

---

### Phase 4: Production (Week 9+)

**Goal**: Public release

- [ ] Publish to PyPI
- [ ] Announce release
- [ ] Monitor metrics
- [ ] Community support setup
- [ ] Regular update cadence

**Deliverable**: Production-ready GAO-Dev on PyPI

---

## Success Metrics

### Technical Metrics

- ✅ **0 repo confusion incidents** (critical)
- ✅ **100% successful installs** (no errors during installation)
- ✅ **<5 minute update time** (fast iteration)
- ✅ **0 data loss incidents** (user projects protected)
- ✅ **>99% migration success rate** (reliable updates)

### User Experience Metrics

- ✅ **>90% tester satisfaction** (based on surveys)
- ✅ **<3 support tickets per update** (clear documentation)
- ✅ **<1 hour support response** (Phase 1-2)
- ✅ **>95% documentation completeness** (comprehensive coverage)

### Business Metrics

- ✅ **50+ successful beta installations** (Phase 2)
- ✅ **100+ TestPyPI installs** (Phase 3)
- ✅ **1000+ PyPI installs in first week** (Phase 4)
- ✅ **<1% support ticket rate** (production)

---

## Risk Mitigation

### High Risk: Breaking Changes

**Mitigation**:
- Semantic versioning (breaking changes only in major versions)
- Automatic backups before migrations
- Comprehensive testing in TestPyPI phase
- Gradual rollout with monitoring

### Medium Risk: Dependency Conflicts

**Mitigation**:
- Conservative dependency versions
- Testing against popular frameworks
- Virtual environment recommendations
- Clear conflict resolution docs

### Low Risk: Update Notification

**Mitigation**:
- CHANGELOG.md with each release
- GitHub notifications for watchers
- Optional update checker in CLI
- Email list for critical updates

---

## Development Workflow

### For Developers (Internal)

```bash
# Clone repo
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev

# Editable install
pip install -e .

# IMPORTANT: Always run from project directory, not GAO-Dev directory
cd /path/to/test-project
gao-dev start

# Or use --project flag
cd gao-agile-dev
gao-dev start --project /path/to/test-project
```

### For Beta Testers

```bash
# Install
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main

# Use
cd ~/my-project
gao-dev start

# Update
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

### For Production Users

```bash
# Install
pip install gao-dev

# Use
cd ~/my-project
gao-dev start

# Update
pip install --upgrade gao-dev
```

---

## Communication Plan

### Beta Tester Onboarding

1. **Welcome Email**: Installation instructions + Discord invite
2. **Quick Start Guide**: USER_GUIDE.md with examples
3. **Video Tutorial**: 5-minute walkthrough (optional)
4. **Support Channel**: Discord for questions
5. **Feedback Survey**: Weekly check-ins

### Update Notifications

1. **CHANGELOG.md**: Detailed change log with each update
2. **GitHub Release Notes**: For milestone releases
3. **Discord Announcements**: Breaking changes and major features
4. **Email Notifications**: Critical updates only

### Issue Tracking

1. **GitHub Issues**: Public issue tracker
2. **Discord**: Quick questions and discussion
3. **Email**: Private/sensitive issues
4. **Status Page**: Uptime and known issues (future)

---

## Testing Strategy

### Automated Tests

```bash
# Unit tests
pytest tests/cli/test_project_detection.py
pytest tests/core/test_version_manager.py
pytest tests/core/test_backup_manager.py

# Integration tests
pytest tests/integration/test_beta_distribution.py

# End-to-end tests
pytest tests/e2e/test_full_lifecycle.py
```

### Manual Testing

Beta testers will validate:

- [ ] Installation from git URL works
- [ ] Cannot run from GAO-Dev source (clear error)
- [ ] `gao-dev start` works from project directory
- [ ] Updates preserve project state
- [ ] Migrations run successfully
- [ ] Failed updates rollback gracefully
- [ ] Health checks catch issues
- [ ] Documentation is clear

### Load Testing

- **100 concurrent installs**: Validate GitHub rate limits
- **1000 project migrations**: Test migration performance
- **50 rapid updates**: Test update stability

---

## Dependencies

### New Dependencies (None!)

All safety mechanisms use existing dependencies:
- `pathlib` (stdlib)
- `shutil` (stdlib)
- `sqlite3` (stdlib)
- `subprocess` (stdlib)
- `structlog` (existing)

### Updated `pyproject.toml`

```toml
[tool.setuptools.package-data]
gao_dev = [
    "workflows/**/*",
    "config/**/*",
    "config/**/*.yaml",
    "config/**/*.yml",
    "config/**/*.json",
    "config/checklists/**/*.yaml",
    "config/domains/**/*.yaml",
    "lifecycle/migrations/*.py",
    "sandbox/reporting/templates/**/*",
    "sandbox/reporting/assets/*",
    ".gaodev-source",  # NEW: Source marker
    "py.typed",
]
```

---

## FAQ Quick Answers

**Q: Will updates break my project?**
A: No. Automatic backups + rollback on failure + version compatibility checks.

**Q: How do I update GAO-Dev?**
A: `pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main`

**Q: What if I accidentally run from GAO-Dev source?**
A: Clear error message with instructions (E001 error code).

**Q: Can I use multiple versions?**
A: Beta phase supports only latest version. Production will support LTS.

**Q: How do I report issues?**
A: GitHub Issues or Discord (beta), GitHub Issues only (production).

See [FAQ.md](./FAQ.md) for complete list.

---

## Next Steps

1. **Review PRD**: Team review and approval
2. **Create Epics**: Break down into stories
3. **Implement Safety**: Phase 1 development
4. **Beta Testing**: Recruit initial testers
5. **Iterate**: Weekly updates based on feedback

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-13 | Initial document | GAO-Dev Team |

---

## Related Documents

- **CLAUDE.md**: Developer guide for GAO-Dev development
- **docs/bmm-workflow-status.md**: Current development status
- **docs/SETUP.md**: Development environment setup
- **README.md**: Main project README

---

## Feedback

Questions or suggestions? Open an issue or join our Discord!

- GitHub Issues: https://github.com/memyselfmike/gao-agile-dev/issues
- Discord: [coming soon]
- Email: [coming soon]
