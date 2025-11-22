# Epic 41: Onboarding Wizards

## Epic Description

This epic implements both the TUI (Terminal User Interface) and Web-based onboarding wizards that guide users through GAO-Dev configuration. The TUI wizard is designed as the primary experience for Docker, SSH, WSL, and headless environments, while the Web wizard provides a visual experience for desktop GUI users.

Both wizards share the same core functionality: project configuration, git setup, provider selection, and credential management. The epic also implements the CredentialManager with environment-variable-first storage priority, ensuring credentials are handled securely across all deployment contexts.

## Business Value

- **Universal onboarding**: Every user gets a guided experience regardless of environment
- **Security-first credentials**: Environment variables as primary storage protects keys in containers
- **Recovery support**: Users can resume interrupted onboarding sessions
- **Validation confidence**: Real-time API key validation prevents configuration errors
- **Docker deployment**: First-class support for containerized deployments

## Success Criteria

- [ ] TUI wizard provides equivalent functionality to Web wizard
- [ ] Onboarding completes in <3 minutes for first-time users
- [ ] Credential storage prioritizes environment variables over keychain
- [ ] API key validation works with retry/skip options
- [ ] Interrupted onboarding can be resumed from last completed step
- [ ] All wizards accessible via keyboard navigation
- [ ] >90% onboarding completion rate

## Stories

| Story | Title | Points | Description |
|-------|-------|--------|-------------|
| 41.1 | TUI Wizard Implementation | 8 | Rich-based terminal wizard for Docker/SSH/WSL |
| 41.2 | Web Wizard Backend API | 5 | FastAPI endpoints for onboarding |
| 41.3 | Web Wizard Frontend Components | 8 | React wizard components with steps |
| 41.4 | CredentialManager Implementation | 8 | Environment-first credential storage |
| 41.5 | Onboarding State Persistence | 5 | Save/resume onboarding progress |
| 41.6 | API Key Validation | 5 | Validation with offline/skip support |

## Total Story Points: 39

## Dependencies

### External Dependencies
- `keyring` library for system keychain access
- `cryptography` library for encrypted file fallback
- React for frontend components

### Internal Dependencies
- Epic 40: Startup & Detection (environment detection, orchestrator)

## Technical Notes

### Credential Storage Priority

1. **Environment Variables** (PRIMARY) - Best for Docker/CI/CD
2. **Mounted Config File** - Persistent Docker volumes
3. **System Keychain** - Desktop convenience
4. **Encrypted File** - Last resort fallback

### TUI Wizard Stack

- Rich library for terminal UI
- Prompt.ask() for input
- Tables for provider selection
- Panels for step display
- Status spinners for validation

### Web Wizard Stack

- FastAPI backend endpoints
- React frontend components
- WebSocket for real-time validation
- Secure key transmission (localhost only)

### Bootstrap Mode

Web server starts without project context and serves only onboarding endpoints, then transitions to full mode after completion.

## Definition of Done

- [ ] All stories completed and accepted
- [ ] Unit tests >80% coverage
- [ ] Integration tests for both wizard types
- [ ] Accessibility review for web wizard (WCAG 2.1 AA)
- [ ] Security review for credential handling
- [ ] Cross-platform testing
- [ ] Documentation updated

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Keychain unavailable in container | High | Medium | Environment variables are primary, clear guidance for users |
| TUI rendering issues on different terminals | Medium | Medium | Test on common terminals (bash, zsh, PowerShell, cmd) |
| API key validation timeout | Medium | Low | Configurable timeout, skip option |
| State persistence conflicts | Low | Medium | Atomic file writes, version checking |
