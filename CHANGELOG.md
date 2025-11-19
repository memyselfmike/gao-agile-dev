# Changelog

All notable changes to GAO-Dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **onboarding**: Quick Start guide with <5 minutes setup time
- **onboarding**: Docker deployment guide with Docker Compose and Kubernetes examples
- **onboarding**: Comprehensive environment variables reference
- **onboarding**: Credential management guide with security best practices
- **onboarding**: Troubleshooting guide covering top 10 common issues
- **onboarding**: Migration guide for upgrading to v2.0
- **onboarding**: API reference for onboarding REST endpoints
- **beta-distribution**: Add comprehensive beta distribution system with CI/CD pipeline
- **beta-distribution**: Add automated versioning, changelog generation, and release workflows
- **beta-distribution**: Add safety mechanisms for repo separation

### Documentation
- Add `docs/getting-started/quick-start.md` - 5-minute onboarding guide
- Add `docs/getting-started/docker-deployment.md` - Container deployment guide
- Add `docs/guides/environment-variables.md` - Complete env var reference
- Add `docs/guides/credential-management.md` - Secure credential storage
- Add `docs/troubleshooting/common-errors.md` - Error codes E001-E701
- Add `docs/migration/upgrading-to-v2.md` - v2.0 upgrade guide
- Add `docs/reference/api-onboarding.md` - REST API specification
- Add comprehensive PRD for beta distribution system
- Add CI/CD architecture documentation
- Add user guide for beta testers

### Changed
- Improved documentation organization with dedicated directories for getting-started, guides, troubleshooting, migration, and reference

### Deprecated
- `gao-dev run` command (use `gao-dev start` instead)
- `gao-dev execute-workflow` command (use `gao-dev run-workflow` instead)
- Global `.gao-dev/` directory (use project-scoped `.gao-dev/` instead)

---

<!-- Changelog will be automatically generated from this point forward -->
