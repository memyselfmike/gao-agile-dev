# Story 35.8: Documentation & Examples

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.8
**Story Points**: 3
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.7
**Priority**: P0
**Status**: Todo

---

## Description

Create comprehensive user and developer documentation including user guide, API reference, FAQ, testing guide, troubleshooting, and examples demonstrating all features and common use cases.

**Note**: This story compiles and reviews documentation. API docs and inline documentation should have been written alongside code in Stories 35.2-35.6 (as per CRAAP resolution for TDD approach).

This story focuses on:
- User-facing documentation (USER_GUIDE, FAQ, TROUBLESHOOTING)
- Developer-facing documentation (API_REFERENCE, TESTING, INTEGRATION_GUIDE)
- Examples and use cases
- README updates and changelog entries
- Screenshots/recordings for visual guidance

---

## Acceptance Criteria

- [ ] User documentation created in `docs/features/interactive-provider-selection/`:
  - [ ] **USER_GUIDE.md**: Step-by-step guide with screenshots
    - [ ] First-time setup walkthrough
    - [ ] Returning user flow
    - [ ] Changing providers
    - [ ] Using environment variables
    - [ ] Feature flag usage
  - [ ] **FAQ.md**: 15+ common questions answered
    - [ ] How do I skip prompts?
    - [ ] How do I change providers?
    - [ ] Why isn't Ollama detected?
    - [ ] What if validation fails?
    - [ ] How do I use in CI/CD?
    - [ ] ... and 10+ more
  - [ ] **TROUBLESHOOTING.md**: Common issues and solutions
    - [ ] CLI not found errors
    - [ ] Validation failures
    - [ ] Permission errors
    - [ ] Corrupted preferences
    - [ ] Headless environment issues
- [ ] Developer documentation created:
  - [ ] **API_REFERENCE.md**: All classes, methods, parameters
    - [ ] PreferenceManager API
    - [ ] ProviderValidator API
    - [ ] InteractivePrompter API
    - [ ] ProviderSelector API
    - [ ] Exception hierarchy
    - [ ] Data models
  - [ ] **TESTING.md**: How to run and add tests
    - [ ] Running unit tests
    - [ ] Running integration tests
    - [ ] Running E2E tests
    - [ ] Running headless tests
    - [ ] Adding new tests
    - [ ] Coverage requirements
  - [ ] **INTEGRATION_GUIDE.md**: How to integrate new provider types
    - [ ] Adding provider to ProviderFactory
    - [ ] Implementing validation
    - [ ] Adding prompts
    - [ ] Testing new provider
- [ ] Examples created in `docs/features/interactive-provider-selection/examples/`:
  - [ ] `first-time-setup.md` - Complete first-time flow
  - [ ] `change-provider.md` - How to change providers
  - [ ] `local-models.md` - Using Ollama local models
  - [ ] `ci-cd-usage.md` - Using in CI/CD pipelines
  - [ ] `advanced-usage.md` - Advanced configurations
- [ ] README.md updated:
  - [ ] Feature overview section added
  - [ ] Link to full documentation
  - [ ] Quick start example
  - [ ] Installation requirements
  - [ ] Feature flag documentation
- [ ] CLAUDE.md updated:
  - [ ] Epic 35 marked complete in status
  - [ ] Provider selection mentioned in workflow section
  - [ ] Quick reference entry added
  - [ ] Commands updated (if applicable)
- [ ] Changelog entry added:
  - [ ] `docs/CHANGELOG.md` updated with Epic 35
  - [ ] Version bump (if applicable)
  - [ ] Breaking changes documented (if any)
  - [ ] Migration guide (if needed)
- [ ] All documentation reviewed:
  - [ ] No typos or formatting issues
  - [ ] All links work (internal and external)
  - [ ] Code examples are correct and tested
  - [ ] Consistent terminology throughout
  - [ ] Proper Markdown formatting
- [ ] Screenshots/recordings created:
  - [ ] GIF showing first-time flow
  - [ ] GIF showing returning user flow
  - [ ] Screenshots of error messages with suggestions
  - [ ] Screenshots of Rich table formatting
  - [ ] Optional: Video walkthrough (5-10 minutes)

---

## Tasks

- [ ] Write USER_GUIDE.md
  - [ ] First-time setup section
  - [ ] Returning user section
  - [ ] Changing providers section
  - [ ] Environment variables section
  - [ ] Feature flag section
  - [ ] Add screenshots
- [ ] Write FAQ.md
  - [ ] Collect 15+ common questions
  - [ ] Write clear, concise answers
  - [ ] Link to relevant sections in other docs
- [ ] Write TROUBLESHOOTING.md
  - [ ] CLI not found errors
  - [ ] Validation failures
  - [ ] Permission errors
  - [ ] Corrupted preferences
  - [ ] Headless environment issues
  - [ ] Include error messages and solutions
- [ ] Write API_REFERENCE.md
  - [ ] Compile API docs from docstrings
  - [ ] Document all public methods
  - [ ] Include parameter descriptions
  - [ ] Include return types
  - [ ] Add usage examples
- [ ] Write TESTING.md
  - [ ] Running tests section
  - [ ] Adding tests section
  - [ ] Coverage section
  - [ ] CI/CD section
- [ ] Write INTEGRATION_GUIDE.md
  - [ ] Adding providers section
  - [ ] Implementing validation section
  - [ ] Testing section
  - [ ] Best practices
- [ ] Create examples
  - [ ] first-time-setup.md
  - [ ] change-provider.md
  - [ ] local-models.md
  - [ ] ci-cd-usage.md
  - [ ] advanced-usage.md
- [ ] Update README.md
  - [ ] Add feature overview
  - [ ] Add quick start
  - [ ] Add links to docs
  - [ ] Update installation section
- [ ] Update CLAUDE.md
  - [ ] Mark Epic 35 complete
  - [ ] Update workflow section
  - [ ] Add quick reference
- [ ] Create changelog entry
  - [ ] Add to docs/CHANGELOG.md
  - [ ] Document features added
  - [ ] Document any breaking changes
- [ ] Create screenshots/GIFs
  - [ ] First-time flow GIF
  - [ ] Returning user GIF
  - [ ] Error message screenshots
  - [ ] Rich table screenshots
- [ ] Review all documentation
  - [ ] Spell check
  - [ ] Link check
  - [ ] Code example validation
  - [ ] Consistency check
  - [ ] Peer review

---

## Documentation Structure

```
docs/features/interactive-provider-selection/
├── PRD.md                          (Already created - Story 35.1)
├── ARCHITECTURE.md                 (Already created - Story 35.1)
├── EPIC-35.md                      (Already created - Story 35.1)
├── CRAAP_Review_Interactive_Provider_Selection.md  (Already created)
├── USER_GUIDE.md                   (NEW - This story)
├── FAQ.md                          (NEW - This story)
├── API_REFERENCE.md                (NEW - This story)
├── TESTING.md                      (NEW - This story)
├── TROUBLESHOOTING.md              (NEW - This story)
├── INTEGRATION_GUIDE.md            (NEW - This story)
├── README.md                       (NEW - Feature overview)
└── examples/
    ├── first-time-setup.md         (NEW)
    ├── change-provider.md          (NEW)
    ├── local-models.md             (NEW)
    ├── ci-cd-usage.md              (NEW)
    └── advanced-usage.md           (NEW)
```

---

## User Guide Outline

### USER_GUIDE.md

```markdown
# Interactive Provider Selection - User Guide

## Overview
[What is interactive provider selection?]

## First-Time Setup
1. Run `gao-dev start`
2. See provider selection table
3. Choose provider (1/2/3)
4. Configure provider-specific settings
5. Validate configuration
6. Save preferences (optional)

[Screenshot: Provider selection table]

## Returning User
1. Run `gao-dev start`
2. See "Use saved provider?" prompt
3. Press Enter to use saved config
4. Or type 'c' to change

[Screenshot: Saved preferences prompt]

## Using Environment Variables
```bash
export AGENT_PROVIDER=claude-code
gao-dev start  # No prompts, uses env var
```

## Feature Flag
To disable interactive selection:
```yaml
# gao_dev/config/defaults.yaml
features:
  interactive_provider_selection: false
```

## Changing Providers
[Step-by-step guide]

## Local Models (Ollama)
[Guide to using Ollama]
```

---

## FAQ Outline

### FAQ.md

```markdown
# Interactive Provider Selection - FAQ

## General

### How do I skip the interactive prompts?
Set the `AGENT_PROVIDER` environment variable:
```bash
export AGENT_PROVIDER=claude-code
gao-dev start
```

### How do I change my provider after initial setup?
[Answer with steps]

### Where are preferences stored?
`.gao-dev/provider_preferences.yaml` in your project directory.

### Can I use the same provider across all projects?
Not yet. Global preferences are planned for a future release.

## Troubleshooting

### Why isn't Ollama detected?
[Answer with troubleshooting steps]

### What does "CLI not found" mean?
[Answer with installation instructions]

### How do I fix "Validation failed"?
[Answer with common causes and solutions]

## CI/CD

### How do I use this in CI/CD pipelines?
Set the `AGENT_PROVIDER` environment variable in your CI config:
```yaml
env:
  AGENT_PROVIDER: claude-code
```

### What if CI/CD fails with "No TTY available"?
The system should automatically fallback to basic input. Ensure `AGENT_PROVIDER` is set.

## Advanced

### Can I customize the validation logic?
[Answer about extending ProviderValidator]

### Can I add custom providers?
[Answer with link to INTEGRATION_GUIDE.md]

... [10+ more questions]
```

---

## Examples

### Example: first-time-setup.md

```markdown
# Example: First-Time Setup

This example shows the complete first-time setup flow.

## Scenario
You're setting up GAO-Dev for the first time and want to use OpenCode with a local Ollama model.

## Steps

1. Start GAO-Dev:
```bash
cd your-project
gao-dev start
```

2. See provider selection table:
```
Available AI Providers
┌────────┬─────────────────────┬──────────────────────────────────┐
│ Option │ Provider            │ Description                      │
├────────┼─────────────────────┼──────────────────────────────────┤
│ 1      │ claude-code         │ Claude Code CLI (Anthropic)      │
│ 2      │ opencode            │ OpenCode CLI (Multi-provider)    │
│ 3      │ direct-api-anthropic│ Direct Anthropic API             │
└────────┴─────────────────────┴──────────────────────────────────┘

Select provider [1/2/3] (1):
```

3. Type `2` and press Enter.

4. See OpenCode configuration:
```
Use local model via Ollama? [y/N]:
```

5. Type `y` and press Enter.

6. See model selection:
```
Available Models
┌────────┬────────────────┬──────┐
│ Option │ Model          │ Size │
├────────┼────────────────┼──────┤
│ 1      │ deepseek-r1    │ 7B   │
│ 2      │ llama2         │ 7B   │
│ 3      │ codellama      │ 13B  │
└────────┴────────────────┴──────┘

Select model [1/2/3] (1):
```

7. Press Enter (use default: deepseek-r1).

8. See validation:
```
✓ Configuration validated successfully

Save as default for future sessions? [Y/n]:
```

9. Press Enter (save preferences).

10. See success message and REPL starts:
```
✓ Preferences saved to .gao-dev/provider_preferences.yaml

Starting GAO-Dev with OpenCode + deepseek-r1...

[GAO-Dev REPL greeting]
```

## Result
- Provider configured: OpenCode with local Ollama (deepseek-r1)
- Preferences saved for future sessions
- REPL ready to use
```

---

## Definition of Done

- [ ] All documentation files created (USER_GUIDE, FAQ, API_REFERENCE, TESTING, TROUBLESHOOTING, INTEGRATION_GUIDE)
- [ ] All examples working and tested
- [ ] Screenshots/GIFs created and embedded
- [ ] README.md updated with feature overview
- [ ] CLAUDE.md updated (Epic 35 complete)
- [ ] CHANGELOG.md updated with Epic 35 entry
- [ ] Documentation reviewed and approved
- [ ] No broken links or formatting issues
- [ ] All code examples validated
- [ ] Spell check passed
- [ ] Peer review complete
- [ ] Commit message: `feat(epic-35): Story 35.8 - Documentation & Examples (3 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Documentation Timing (CRAAP Moderate - Issue #5)**:
- **Original**: All documentation in Story 35.8
- **Revised**: API docs written alongside code (Stories 35.2-35.6)
- **Story 35.8**: Compiles, reviews, and creates user-facing docs

### Documentation Quality Standards

**User Documentation**:
- Clear, non-technical language
- Step-by-step instructions
- Screenshots and examples
- Common use cases covered

**Developer Documentation**:
- Technical but clear
- Complete API reference
- Usage examples for all methods
- Best practices and patterns

### Screenshot Guidelines

**Tools**:
- Windows: Snipping Tool, ShareX
- macOS: Screenshot (Cmd+Shift+5)
- GIFs: ScreenToGif (Windows), Kap (macOS), Peek (Linux)

**Content**:
- Show full terminal window
- Include prompt and output
- Highlight important parts
- Keep file size reasonable (<2MB)

**Locations**:
- Store in `docs/features/interactive-provider-selection/images/`
- Reference in Markdown: `![Description](images/screenshot.png)`

### Example Code Validation

**All examples must**:
- Be tested manually
- Work on current version
- Include expected output
- Handle errors gracefully

**Validation Script** (Optional):
```bash
# Validate all example code blocks
python scripts/validate_docs_examples.py docs/features/interactive-provider-selection/
```

### Link Checking

**Internal Links**:
- All links to other docs files
- All links to code files
- All section anchors

**External Links**:
- Installation instructions (npm, Ollama)
- GitHub issues/PRs
- Related documentation

**Tool**:
```bash
# Use markdown-link-check
npm install -g markdown-link-check
markdown-link-check docs/features/interactive-provider-selection/**/*.md
```

### Changelog Entry Format

```markdown
## [v2.X.X] - 2025-01-XX

### Added
- **Interactive Provider Selection (Epic 35)**: Users can now interactively select AI providers at startup
  - Provider selection prompts with Rich formatting
  - Preference persistence to `.gao-dev/provider_preferences.yaml`
  - Cross-platform CLI detection (Windows, macOS, Linux)
  - Ollama local model support
  - Validation with actionable error messages
  - Feature flag for rollback: `features.interactive_provider_selection`
  - Security: YAML injection prevention with input sanitization
  - CI/CD compatible: Lazy imports, env var bypass, headless mode

### Changed
- ChatREPL now calls ProviderSelector before ProcessExecutor creation

### Security
- Added YAML injection prevention with `yaml.safe_dump()` and input sanitization
- Preferences file permissions set to 0600 (user-only)

### Documentation
- Added USER_GUIDE.md, FAQ.md, TROUBLESHOOTING.md
- Added API_REFERENCE.md, TESTING.md, INTEGRATION_GUIDE.md
- Added 5 examples (first-time setup, change provider, local models, CI/CD, advanced)
```

### Effort Estimation

**Breakdown** (3 story points = 3-4 hours):
- User docs (USER_GUIDE, FAQ, TROUBLESHOOTING): 1.5 hours
- Developer docs (API_REFERENCE, TESTING, INTEGRATION_GUIDE): 1 hour
- Examples: 30 minutes
- Screenshots/GIFs: 30 minutes
- README/CLAUDE/CHANGELOG updates: 30 minutes
- Review and polish: 30 minutes

**Total**: 4 hours (upper end of 3 story points)

---

**Story Status**: Todo
**Next Action**: Begin documentation after Story 35.7 completes
**Created**: 2025-01-12
**Last Updated**: 2025-01-12

---

## Completion

**When this story is complete, Epic 35 is 100% done.**

All acceptance criteria met:
- ✅ Interactive prompts work on first-time startup
- ✅ Saved preferences reused on subsequent startups
- ✅ All existing tests pass (no regressions)
- ✅ >90% test coverage for new code
- ✅ Works on Windows, macOS, Linux
- ✅ Selection flow completes in <30 seconds
- ✅ Clear error messages with actionable suggestions
- ✅ Secure against YAML injection attacks
- ✅ Works in headless CI/CD environments
- ✅ Feature flag available for rollback
- ✅ Comprehensive documentation complete

**Epic 35 Status**: Complete
**Next Epic**: To be determined by product roadmap
