# Story 42.4: Documentation and Docker Deployment Guide

## User Story

As a DevOps engineer deploying GAO-Dev in a Docker environment,
I want comprehensive documentation with Docker examples,
So that I can set up GAO-Dev for my team quickly and correctly.

## Acceptance Criteria

- [ ] AC1: Quick Start guide covers `gao-dev start` in <5 minutes reading time
- [ ] AC2: Docker Deployment Guide covers complete containerized setup
- [ ] AC3: Docker Compose example with environment variables and volumes
- [ ] AC4: Kubernetes deployment example (basic StatefulSet)
- [ ] AC5: Environment variable reference with all supported variables
- [ ] AC6: Troubleshooting guide covers top 10 common issues
- [ ] AC7: Migration guide for upgrading from previous versions
- [ ] AC8: All code examples are tested and working
- [ ] AC9: Screenshots/diagrams for wizard flows
- [ ] AC10: Documentation follows existing GAO-Dev style guide
- [ ] AC11: API reference for onboarding endpoints (OpenAPI)
- [ ] AC12: Changelog entry for this release

## Technical Notes

### Documentation Structure

```
docs/
  getting-started/
    installation.md           # pip install, prerequisites
    quick-start.md            # gao-dev start in 5 minutes
    docker-deployment.md      # Complete Docker guide

  guides/
    onboarding-wizard.md      # Wizard walkthrough with screenshots
    credential-management.md  # Security and storage options
    environment-variables.md  # Complete reference

  migration/
    upgrading-to-v2.md        # Version upgrade guide
    deprecated-commands.md    # Command migration reference

  troubleshooting/
    common-errors.md          # Error codes and fixes
    environment-issues.md     # Platform-specific issues
    faq.md                    # Frequently asked questions

  reference/
    api-onboarding.md         # OpenAPI reference
    configuration.md          # Config file reference
    cli-reference.md          # Command line reference
```

### Docker Deployment Guide Content

```markdown
# Docker Deployment Guide

## Quick Start

### Using Docker Run

docker run -it \
  -v $(pwd):/workspace \
  -v gao-dev-config:/root/.gao-dev \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -p 3000:3000 \
  gao-dev/gao-dev:latest \
  start

### Using Docker Compose

version: '3.8'

services:
  gao-dev:
    image: gao-dev/gao-dev:latest
    volumes:
      - ./project:/workspace
      - gao-dev-config:/root/.gao-dev
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AGENT_PROVIDER=claude-code
    ports:
      - "3000:3000"
    stdin_open: true
    tty: true

volumes:
  gao-dev-config:

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Anthropic API key | Required |
| AGENT_PROVIDER | AI provider selection | claude-code |
| GAO_DEV_HEADLESS | Skip interactive prompts | false |
| GAO_DEV_DOCKER | Force Docker mode | Auto-detected |

## Persistent Configuration

Mount /root/.gao-dev to persist:
- Global configuration
- Credential storage
- Onboarding state

## Kubernetes Deployment

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: gao-dev
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: gao-dev
        image: gao-dev/gao-dev:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: gao-dev-secrets
              key: anthropic-api-key
        volumeMounts:
        - name: config
          mountPath: /root/.gao-dev
  volumeClaimTemplates:
  - metadata:
      name: config
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

### Environment Variable Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | For Anthropic | API key | `sk-ant-...` |
| `OPENAI_API_KEY` | For OpenAI | API key | `sk-...` |
| `AGENT_PROVIDER` | No | Provider selection | `claude-code` |
| `GAO_DEV_HEADLESS` | No | Disable interactive | `1` |
| `GAO_DEV_GUI` | No | Force GUI mode | `1` |
| `GAO_DEV_DOCKER` | No | Force Docker detection | `1` |

### Changelog Entry

```markdown
## [2.0.0] - 2025-XX-XX

### Added
- Streamlined onboarding with unified `gao-dev start` command
- Web-based onboarding wizard for desktop environments
- TUI wizard for Docker, SSH, and WSL environments
- Environment auto-detection (Docker, SSH, WSL, Desktop, CI/CD)
- Credential management with environment-first storage
- Onboarding state persistence for recovery
- Docker deployment with first-class support

### Changed
- `gao-dev start` is now the single entry point
- Credentials stored via environment variables by default

### Deprecated
- `gao-dev init` - use `gao-dev start` instead
- `gao-dev web start` - use `gao-dev start` instead
```

## Test Scenarios

1. **Quick Start accuracy**: Given new user follows quick start, When completed, Then GAO-Dev is running in <5 minutes

2. **Docker run works**: Given Docker run command from docs, When executed, Then GAO-Dev starts with TUI wizard

3. **Docker Compose works**: Given Docker Compose from docs, When executed, Then GAO-Dev starts correctly

4. **Env var reference complete**: Given user needs env var, When checking reference, Then all variables documented

5. **Error code lookup**: Given error E001, When checking troubleshooting, Then fix instructions found

6. **Migration guide works**: Given user with v1.x, When following migration guide, Then upgrade succeeds

7. **Screenshots current**: Given wizard screenshots, When compared to app, Then match current UI

8. **API reference accurate**: Given OpenAPI spec, When compared to implementation, Then endpoints match

9. **Kubernetes example works**: Given K8s example, When applied, Then GAO-Dev runs in cluster

10. **Code examples tested**: Given any code example, When executed, Then produces expected result

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All code examples tested
- [ ] Screenshots captured from current version
- [ ] Documentation reviewed by technical writer
- [ ] Links verified working
- [ ] Spell-checked and grammar-checked
- [ ] Added to documentation site navigation
- [ ] Search indexing configured

## Story Points: 5

## Dependencies

- All Epic 40-41 stories (for accurate documentation)
- Story 42.3: Error Messages (for error code reference)

## Notes

- Use MkDocs for documentation site
- Consider video walkthrough for wizard
- Test documentation with someone unfamiliar with GAO-Dev
- Include troubleshooting for Docker Desktop on Windows/Mac
- Document Docker Desktop vs Docker Engine differences
- Add Helm chart example in future version
