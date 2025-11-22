# Epic 40: Startup & Detection

## Epic Description

This epic establishes the foundation for GAO-Dev's streamlined onboarding experience by implementing intelligent environment and context detection. The system will automatically detect whether users are running in Docker containers, SSH sessions, WSL, desktop GUI environments, or CI/CD pipelines, and adapt its behavior accordingly.

The epic also introduces the unified `gao-dev start` command that replaces the fragmented multi-command startup process, providing a single entry point for all users regardless of their environment or project state.

## Business Value

- **Reduced friction**: Users no longer need to know which command to run for their specific situation
- **Universal accessibility**: GAO-Dev works seamlessly in Docker, SSH, WSL, and desktop environments
- **Faster onboarding**: Automatic detection eliminates manual configuration steps
- **Better user experience**: Smart defaults based on detected context reduce decision fatigue

## Success Criteria

- [ ] Environment detection correctly identifies Docker, SSH, WSL, Desktop, and CI/CD environments with >99% accuracy
- [ ] Global state detection correctly identifies first-time vs returning users
- [ ] Project state detection correctly identifies empty, brownfield, and existing GAO-Dev projects
- [ ] `gao-dev start` works as unified entry point in all environments
- [ ] Detection completes in <100ms
- [ ] Deprecated commands show appropriate warnings and redirect to new flow
- [ ] All detection logic has comprehensive test coverage

## Stories

| Story | Title | Points | Description |
|-------|-------|--------|-------------|
| 40.1 | Environment Detection | 5 | Detect Docker/SSH/WSL/Desktop/CI environments |
| 40.2 | Global and Project State Detection | 5 | Detect user history and project context |
| 40.3 | StartupOrchestrator Implementation | 8 | Coordinate entire startup flow |
| 40.4 | Unified `gao-dev start` Command | 5 | Single entry point with auto-detection |
| 40.5 | Deprecated Command Handling | 3 | Deprecation warnings for legacy commands |

## Total Story Points: 26

## Dependencies

### External Dependencies
- Git installation (for git operations)
- Python 3.9+ runtime

### Internal Dependencies
- None (this is the foundation epic)

## Technical Notes

### Environment Detection Matrix

| Environment | Detection Method | Default Mode |
|-------------|------------------|--------------|
| Desktop GUI | `$DISPLAY` or Windows | Web wizard |
| SSH session | `$SSH_CLIENT` or `$SSH_TTY` | TUI wizard |
| Docker | `/.dockerenv` or `$GAO_DEV_DOCKER` | TUI wizard |
| WSL | `/proc/version` contains "Microsoft" | TUI wizard |
| CI/CD | `$CI` or `$GAO_DEV_HEADLESS` | Env vars only |

### Key Files to Create/Modify

- `gao_dev/cli/startup_orchestrator.py` (new)
- `gao_dev/core/environment_detector.py` (new)
- `gao_dev/core/state_detector.py` (new)
- `gao_dev/cli/commands.py` (modify start command)

## Definition of Done

- [ ] All stories completed and accepted
- [ ] Unit tests >80% coverage
- [ ] Integration tests for each environment type
- [ ] Cross-platform testing (Windows, macOS, Linux)
- [ ] Documentation updated
- [ ] Code reviewed and merged

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Environment detection false positives | Medium | Medium | Comprehensive test matrix across environments |
| Performance impact on startup | Low | Medium | Async detection, <100ms target with benchmarks |
| WSL detection edge cases | Medium | Low | Test across WSL1 and WSL2 versions |
