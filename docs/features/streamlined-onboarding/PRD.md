# Product Requirements Document: Streamlined Startup & Web-Based Onboarding

**Author**: John (Product Manager Agent)
**Date**: 2025-11-19
**Status**: Draft
**Version**: 1.0

---

## Executive Summary

### The Problem

GAO-Dev's current onboarding experience presents significant friction for new users and creates confusion for returning users. Beta testers consistently report that the multi-command startup process (`gao-dev start`, `gao-dev init`, `gao-dev web start`) is unintuitive and leads to failed first-time experiences. Users must manually configure git, set environment variables, and navigate feature flags before they can begin using the system.

### The Solution

This feature introduces a **single-command startup experience** that intelligently detects the user's context and provides a web-based onboarding wizard. When a user runs `gao-dev start` in any directory, GAO-Dev will:

1. Auto-detect whether this is a fresh install, new project, or existing project
2. Launch the web interface automatically
3. Present a guided onboarding wizard for first-time/new-project scenarios
4. Configure git, API providers, and system preferences through a friendly UI
5. Initialize all necessary infrastructure seamlessly

### Expected Impact

- **Reduce time-to-first-success** from ~15 minutes to under 3 minutes
- **Eliminate support requests** related to configuration issues
- **Increase user retention** by removing friction from the critical first-use experience
- **Standardize** the entry point, reducing cognitive load for documentation and support

---

## Problem Statement

### The Problem

New users attempting to use GAO-Dev face a fragmented and confusing onboarding experience that often leads to frustration and abandonment. The current system requires:

1. **Multiple commands with unclear purposes**: Users must understand the difference between `gao-dev start` (CLI REPL), `gao-dev init` (project initialization), and `gao-dev web start` (web interface)
2. **Manual prerequisite configuration**: Git must be initialized manually before GAO-Dev works
3. **Hidden feature gates**: Provider selection (Epic 35) is gated behind a feature flag that most users don't know exists
4. **Environment variable dependency**: Users must set `ANTHROPIC_API_KEY` or other provider keys without clear guidance
5. **Split interfaces**: CLI and web are separate experiences with no unified entry point
6. **Silent failures**: Database auto-healing and migration happen silently, leaving users confused when things don't work

### Current Situation

Users currently experience the following workflow:

1. Install GAO-Dev via pip
2. Create a project folder (or navigate to existing code)
3. Attempt to run `gao-dev start`
4. Encounter errors about missing git initialization
5. Initialize git manually
6. Try `gao-dev start` again
7. See provider selection (if feature flag enabled) or get cryptic errors about missing API keys
8. Set environment variables in their shell
9. Finally reach the CLI REPL
10. Discover the web interface exists separately

This 10-step process has an estimated **60% drop-off rate** before users complete their first meaningful interaction with GAO-Dev.

### The Solution

Implement a unified `gao-dev start` command that:

1. **Auto-detects context**: Fresh install vs new project vs existing project
2. **Launches web automatically**: Always opens the web interface
3. **Web-based onboarding wizard**: Guides users through:
   - Project naming
   - Git configuration (name, email, auto-init)
   - Provider selection with visual guidance
   - API key configuration with secure handling
   - Initial setup completion
4. **Seamless handoff**: After onboarding, user is ready to build immediately

---

## Goals & Success Criteria

### Goals

1. **Primary Goal**: Reduce time-to-first-success to under 3 minutes for new users
2. **Secondary Goal**: Eliminate configuration-related support requests
3. **Stretch Goal**: Achieve 90% onboarding completion rate (vs current ~40%)

### Success Criteria

- [ ] **Single command entry**: User can start GAO-Dev with only `gao-dev start` in any directory
- [ ] **Auto-detection works**: System correctly identifies fresh install, new project, brownfield project
- [ ] **Web launches automatically**: Browser opens without additional commands
- [ ] **Onboarding completes**: New users can go from `gao-dev start` to first conversation with Brian in <3 minutes
- [ ] **Git is configured**: Users without git user.name/email are prompted to configure
- [ ] **Provider works**: API key is validated and working before onboarding completes
- [ ] **No manual env vars**: Users are not required to set environment variables manually
- [ ] **Graceful fallback**: If web fails to launch, CLI continues to work with helpful messaging

### Key Performance Indicators (KPIs)

- **Onboarding completion rate**: >90% of new users complete onboarding wizard
- **Time to first message**: <3 minutes from `gao-dev start` to first Brian response
- **Configuration error rate**: <5% of users encounter configuration errors
- **Support ticket reduction**: 50% reduction in "how do I start" tickets
- **User satisfaction**: >4.5/5 rating on first-use experience surveys

---

## User Personas & Use Cases

### Primary Persona: Alex - New User

- **Background**: Software developer with 3+ years experience, comfortable with CLI but prefers visual interfaces for complex configuration
- **Goals**: Quickly evaluate GAO-Dev for their next project without reading extensive documentation
- **Pain Points**: Frustrated by tools that require extensive setup before seeing value
- **Needs**: Clear, guided setup that validates each step before proceeding

### Secondary Persona: Sam - Returning User

- **Background**: Used GAO-Dev on a previous project, starting a new one
- **Goals**: Start new project quickly, may want different provider settings
- **Pain Points**: Doesn't remember all the setup steps from last time
- **Needs**: Quick path for experienced users while still offering configuration options

### Tertiary Persona: Jordan - Enterprise Developer

- **Background**: Works in corporate environment with strict security policies
- **Goals**: Use GAO-Dev with company's approved AI provider and security constraints
- **Pain Points**: Can't store API keys in plaintext, needs enterprise SSO/proxy support
- **Needs**: Secure credential storage, environment variable support for CI/CD

### Use Cases

#### Use Case 1: First-Time Installation

- **Actor**: Alex (New User)
- **Goal**: Install GAO-Dev and create first project
- **Scenario**:
  1. Alex installs GAO-Dev: `pip install gao-dev`
  2. Creates project folder: `mkdir my-app && cd my-app`
  3. Runs: `gao-dev start`
  4. Browser opens with onboarding wizard
  5. Wizard detects: No git config, no .gao-dev, empty directory
  6. Wizard prompts for:
     - Project name (defaults to folder name)
     - Git user.name and user.email
     - Provider selection (Claude Code, OpenCode, Direct API)
     - API key entry (with validation)
  7. Wizard creates: .gao-dev/, initializes git, stores preferences
  8. Wizard shows: "Ready! Start building with Brian"
  9. Alex sees Brian chat interface, ready to describe their app
- **Success Criteria**: Complete flow in <3 minutes, all configuration valid

#### Use Case 2: New Project (Returning User)

- **Actor**: Sam (Returning User)
- **Goal**: Start new project with existing global configuration
- **Scenario**:
  1. Sam creates folder: `mkdir new-project && cd new-project`
  2. Runs: `gao-dev start`
  3. Browser opens
  4. Wizard detects: Global config exists, no .gao-dev, empty directory
  5. Wizard shows abbreviated flow:
     - "Welcome back! Create 'new-project'?" [Yes/Customize]
     - Uses existing git config and provider preferences
  6. Wizard creates: .gao-dev/, initializes git
  7. Sam immediately sees Brian chat
- **Success Criteria**: Complete flow in <30 seconds for returning users

#### Use Case 3: Existing Project (Brownfield)

- **Actor**: Any user
- **Goal**: Add GAO-Dev to existing codebase
- **Scenario**:
  1. User navigates to existing project with code
  2. Runs: `gao-dev start`
  3. Browser opens
  4. Wizard detects: Has package.json/requirements.txt/etc., no .gao-dev
  5. Wizard shows:
     - "I see an existing project. Let me help you add GAO-Dev."
     - Confirms project name
     - Asks about git (already initialized? use existing config?)
     - Selects provider (or uses global preference)
  6. Wizard creates: .gao-dev/, preserves existing code
  7. User sees Brian with context about existing project
- **Success Criteria**: Existing code untouched, .gao-dev properly initialized

#### Use Case 4: CI/CD Environment

- **Actor**: Jordan (Enterprise Developer)
- **Goal**: Run GAO-Dev in automated pipeline
- **Scenario**:
  1. CI script sets: `AGENT_PROVIDER=claude-code`, `ANTHROPIC_API_KEY=...`
  2. Runs: `gao-dev start --headless`
  3. GAO-Dev detects environment variables
  4. Skips onboarding wizard entirely
  5. Initializes with env var configuration
  6. Executes in CLI mode (no browser)
- **Success Criteria**: Zero interactive prompts in CI/CD mode

---

## Functional Requirements

### Startup Detection & Routing

#### FR-1: Unified Start Command
- **Description**: `gao-dev start` becomes the single entry point for all users
- **User Value**: One command to remember, eliminates confusion
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] `gao-dev start` works in any directory
  - [ ] Deprecation warnings shown for `gao-dev init` and `gao-dev web start`
  - [ ] Legacy commands continue to work but redirect to new flow

#### FR-2: Context Auto-Detection
- **Description**: Automatically detect user context on startup
- **User Value**: System adapts to user's situation without manual flags
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Detects fresh install (no global config)
  - [ ] Detects new project (empty dir or no .gao-dev)
  - [ ] Detects brownfield (existing code, no .gao-dev)
  - [ ] Detects existing GAO-Dev project (has .gao-dev)
  - [ ] Detection completes in <100ms

#### FR-3: Git Configuration Detection
- **Description**: Check if git is installed and configured
- **User Value**: Prevents cryptic git errors during operation
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Detects if git binary is available
  - [ ] Checks for git user.name and user.email (global and local)
  - [ ] Detects if current directory is a git repository
  - [ ] Graceful handling when git is not installed

### Web Interface Launch

#### FR-4: Auto-Launch Web Browser
- **Description**: Automatically open web interface on `gao-dev start`
- **User Value**: Immediate visual feedback, no additional commands
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Browser opens automatically after `gao-dev start`
  - [ ] Uses system default browser
  - [ ] Works on Windows, macOS, and Linux
  - [ ] Respects `--no-browser` flag for headless operation
  - [ ] Shows terminal message with URL if browser fails

#### FR-5: Port Conflict Resolution
- **Description**: Handle case where default port is in use
- **User Value**: Works even when other apps use common ports
- **Priority**: Should Have
- **Acceptance Criteria**:
  - [ ] Tries default port (3000) first
  - [ ] Auto-increments to find available port
  - [ ] Displays actual port in browser URL
  - [ ] Maximum 10 port attempts before error

### Onboarding Wizard

#### FR-6: Wizard Flow Controller
- **Description**: Multi-step wizard with progress indication
- **User Value**: Clear progress, ability to go back and review
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Shows step progress (e.g., "Step 2 of 4")
  - [ ] Allows back navigation
  - [ ] Validates each step before proceeding
  - [ ] Saves progress (can resume if browser closed)
  - [ ] Skips unnecessary steps based on detection

#### FR-7: Project Configuration Step
- **Description**: Configure project name and basic settings
- **User Value**: Personalized project setup
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Project name defaults to folder name
  - [ ] Validates project name (no special chars)
  - [ ] Shows detected project type (greenfield/brownfield)
  - [ ] Optional description field

#### FR-8: Git Configuration Step
- **Description**: Configure git user information
- **User Value**: Ensures git operations work correctly
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Pre-fills with global git config if available
  - [ ] Allows override for project-specific settings
  - [ ] Validates email format
  - [ ] Option to initialize git repository
  - [ ] Option to create initial commit

#### FR-9: Provider Selection Step
- **Description**: Visual provider selection with descriptions
- **User Value**: Clear understanding of provider options
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Shows all available providers with descriptions
  - [ ] Visual cards for each option (not just dropdown)
  - [ ] Indicates which providers require API keys
  - [ ] Shows model selection for each provider
  - [ ] Remembers preference for future projects

#### FR-10: API Key Configuration Step
- **Description**: Secure entry and validation of API keys
- **User Value**: Confident that credentials are correct
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Password-style input (hidden characters)
  - [ ] "Show" toggle for verification
  - [ ] Real-time validation with provider API
  - [ ] Clear error messages on validation failure
  - [ ] Option to use environment variable instead
  - [ ] Never stores key in plaintext in project files

#### FR-11: Completion & Handoff
- **Description**: Summary and transition to main interface
- **User Value**: Confirmation and clear next steps
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Summary of configuration
  - [ ] "Start Building" button
  - [ ] Quick tips for first-time users
  - [ ] Option to "Show this summary again"

### Credential Security

#### FR-12: Secure Credential Storage
- **Description**: Store API keys securely, never in plaintext
- **User Value**: Security-conscious users can trust GAO-Dev
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] Uses system keychain on macOS (Keychain)
  - [ ] Uses system keychain on Windows (Credential Manager)
  - [ ] Uses system keychain on Linux (Secret Service/libsecret)
  - [ ] Fallback to encrypted file if keychain unavailable
  - [ ] Never writes API key to git-tracked files
  - [ ] Option to use environment variable as source

#### FR-13: Environment Variable Support
- **Description**: Support environment variables for CI/CD
- **User Value**: Works in automated environments
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] `AGENT_PROVIDER` skips provider selection
  - [ ] `ANTHROPIC_API_KEY` (and similar) used if set
  - [ ] `GAO_DEV_HEADLESS=1` skips all prompts
  - [ ] Environment variables take precedence over stored config

### Graceful Degradation

#### FR-14: CLI Fallback
- **Description**: Continue working if web interface fails
- **User Value**: Never completely blocked from using GAO-Dev
- **Priority**: Must Have
- **Acceptance Criteria**:
  - [ ] If browser can't open, show URL in terminal
  - [ ] If web server fails, fall back to CLI REPL
  - [ ] Show clear message explaining fallback
  - [ ] Offer to try web again or continue with CLI

#### FR-15: Offline Support
- **Description**: Allow local provider selection when offline
- **User Value**: Can start setup without internet
- **Priority**: Could Have
- **Acceptance Criteria**:
  - [ ] Ollama (local) providers work offline
  - [ ] API key validation skipped if offline
  - [ ] Warning shown about unvalidated credentials
  - [ ] Full validation when connection restored

---

## Non-Functional Requirements

### Performance

- **Startup time**: `gao-dev start` to browser open <2 seconds
- **Wizard load**: Onboarding wizard interactive <500ms after browser open
- **Detection**: Context detection completes <100ms
- **Validation**: API key validation <3 seconds
- **Total onboarding**: First-time complete flow <3 minutes

### Security

- **API key storage**: Keys never stored in plaintext on disk
- **Key transmission**: Keys only sent over localhost (127.0.0.1)
- **Key display**: Keys masked by default in UI
- **No telemetry**: No user data or keys sent to external services during onboarding
- **File permissions**: Config files created with user-only permissions (600)

### Usability

- **Accessibility**: Wizard meets WCAG 2.1 AA standards
- **Keyboard navigation**: All wizard steps navigable by keyboard
- **Error messages**: Actionable with clear fix instructions
- **Progress persistence**: Can close browser and resume onboarding
- **Mobile responsive**: Wizard usable on tablet (not required for phone)

### Reliability

- **Idempotent**: Running `gao-dev start` multiple times is safe
- **Interruptible**: Ctrl+C during onboarding leaves system in valid state
- **Recovery**: Partial onboarding can be completed on next start
- **Backward compatible**: Existing projects continue to work

### Scalability

- **Global config**: Configuration stored globally applies to all projects
- **Project override**: Projects can override global settings
- **Multi-project**: Support user with many projects on same machine

---

## User Experience & Design

### Key User Flows

#### Flow 1: First-Time User (Complete Onboarding)

```
[Terminal]                     [Browser]
    |                              |
    | gao-dev start               |
    |----------------------------->|
    |                              |
    | Starting GAO-Dev...          |
    | Web interface: localhost:3000|
    |                              |
    |                    +---------v---------+
    |                    |  Onboarding       |
    |                    |  Welcome to       |
    |                    |  GAO-Dev!         |
    |                    |                   |
    |                    |  [Get Started]    |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Step 1: Project  |
    |                    |  Name: my-app     |
    |                    |  [x] Init git     |
    |                    |  [Continue]       |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Step 2: Git      |
    |                    |  Name: ________   |
    |                    |  Email: _______   |
    |                    |  [Continue]       |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Step 3: Provider |
    |                    |  [Claude Code]    |
    |                    |  [OpenCode]       |
    |                    |  [Direct API]     |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Step 4: API Key  |
    |                    |  Key: *********** |
    |                    |  [Validate]       |
    |                    |  "Key valid!"     |
    |                    |  [Complete Setup] |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Ready to Build!  |
    |                    |                   |
    |                    |  [Start with      |
    |                    |   Brian]          |
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Chat Interface   |
    |                    |  "Hi! I'm Brian.  |
    |                    |   What would you  |
    |                    |   like to build?" |
    |                    +-------------------+
```

#### Flow 2: Returning User (Quick Start)

```
[Terminal]                     [Browser]
    |                              |
    | gao-dev start               |
    |----------------------------->|
    |                              |
    |                    +---------v---------+
    |                    |  Welcome Back!    |
    |                    |                   |
    |                    |  Create project   |
    |                    |  "new-project"?   |
    |                    |                   |
    |                    |  Using: Claude    |
    |                    |                   |
    |                    |  [Yes] [Customize]|
    |                    +---------+---------+
    |                              |
    |                    +---------v---------+
    |                    |  Chat Interface   |
    |                    +-------------------+
```

#### Flow 3: Existing GAO-Dev Project

```
[Terminal]                     [Browser]
    |                              |
    | gao-dev start               |
    |----------------------------->|
    |                              |
    |                    +---------v---------+
    |                    |  Chat Interface   |
    |                    |  (no onboarding)  |
    |                    +-------------------+
```

### UI/UX Considerations

#### Design Principles

1. **Progressive disclosure**: Show only what's needed at each step
2. **Sensible defaults**: Pre-fill with best guesses, let user override
3. **Validation feedback**: Immediate, clear, actionable
4. **Escape hatches**: Always possible to go back or skip (with consequences)

#### Visual Design

- Use existing GAO-Dev web interface design system
- Card-based provider selection with icons
- Progress indicator (dots or steps)
- Success/error states with color coding
- Consistent button placement (primary action bottom-right)

#### Accessibility Requirements

- All form fields have labels
- Error messages associated with fields (aria-describedby)
- Focus management between steps
- Color not sole indicator of state
- Minimum touch target size (44x44px)

---

## Technical Considerations

### Architecture Overview

```
                    +-------------------+
                    |   gao-dev start   |
                    +--------+----------+
                             |
                    +--------v----------+
                    | StartupOrchestrator|
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v-------+ +----v----+ +-------v------+
     |ContextDetector | |GitHelper| |ProviderConfig|
     +----------------+ +---------+ +--------------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v----------+
                    |   WebServer       |
                    |   (FastAPI)       |
                    +--------+----------+
                             |
                    +--------v----------+
                    | OnboardingWizard  |
                    | (React Component) |
                    +-------------------+
```

### Integration Points

#### Existing Components to Modify

1. **ChatREPL** (`chat_repl.py`): Remove direct startup logic, delegate to StartupOrchestrator
2. **GreenfieldInitializer** (`greenfield_initializer.py`): Refactor to be called from onboarding
3. **BrownfieldInitializer** (`brownfield_initializer.py`): Refactor to be called from onboarding
4. **ProviderSelector** (`provider_selector.py`): Expose as web endpoint for wizard
5. **server.py**: Add onboarding API endpoints

#### New Components

1. **StartupOrchestrator**: Coordinates entire startup flow
2. **ContextDetector**: Determines user context (fresh/new/brownfield/existing)
3. **OnboardingAPI**: FastAPI endpoints for wizard
4. **CredentialManager**: Secure storage abstraction
5. **OnboardingWizard**: React component for web wizard

### Data Requirements

#### Global Configuration (New)

Location: `~/.gao-dev/config.yaml`

```yaml
version: "1.0"
user:
  git_name: "Alex Developer"
  git_email: "alex@example.com"
provider:
  default: "claude-code"
  model: "sonnet-4.5"
  api_key_source: "keychain"  # or "env:ANTHROPIC_API_KEY"
preferences:
  auto_open_browser: true
  telemetry_enabled: false
metadata:
  created_at: "2025-01-15T10:30:00Z"
  last_updated: "2025-01-15T10:30:00Z"
```

#### Onboarding State (New)

Location: `~/.gao-dev/onboarding.yaml`

```yaml
completed: false
current_step: 2
steps_completed:
  - project
started_at: "2025-01-15T10:30:00Z"
project_path: "/Users/alex/my-app"
```

#### Project Configuration (Enhanced)

Location: `<project>/.gao-dev/config.yaml`

```yaml
version: "1.0"
project:
  name: "my-app"
  created_at: "2025-01-15T10:30:00Z"
provider:
  override: null  # or specific provider config
  api_key_source: "global"  # or "keychain:project-name"
```

### Technical Constraints

1. **Python version**: 3.9+ (match existing requirement)
2. **Keychain libraries**:
   - macOS: `keyring` with native backend
   - Windows: `keyring` with Windows Credential Manager
   - Linux: `keyring` with SecretService
3. **Browser launch**: Use `webbrowser` module (standard library)
4. **Port selection**: Use `socket` to check availability
5. **Frontend**: React (existing web stack)

### Dependencies

#### New Python Dependencies

- `keyring>=24.0.0`: Secure credential storage
- No other new dependencies anticipated

#### Existing Dependencies (Leveraged)

- `fastapi`: Web server
- `uvicorn`: ASGI server
- `rich`: Terminal output
- `structlog`: Logging
- `pyyaml`: Configuration files

---

## Competitive Analysis

### Direct Competitors

| Tool | Onboarding Approach | Strengths | Weaknesses | Our Differentiation |
|------|---------------------|-----------|------------|---------------------|
| **Cursor** | First-run wizard in app | Integrated, no terminal needed | Requires app download, no CLI | Web-based, works everywhere |
| **GitHub Copilot** | VS Code extension flow | Familiar VS Code patterns | Requires VS Code | IDE-agnostic |
| **Codeium** | Account creation first | Simple, unified identity | Requires account | No account required for basic use |
| **Replit Agent** | Web-only, in-platform | Zero setup | No local development | Supports local files |

### Market Positioning

GAO-Dev differentiates by offering:

1. **Best of both worlds**: Web interface for visual tasks, CLI for power users
2. **No lock-in**: Works with multiple AI providers
3. **Transparent**: All code and config is local and visible
4. **Enterprise-ready**: Environment variable support, secure credential storage

---

## Scope & Prioritization

### In Scope

- Unified `gao-dev start` command
- Context auto-detection (4 scenarios)
- Web-based onboarding wizard (6 steps)
- Git configuration detection and setup
- Provider selection with visual UI
- Secure API key storage (system keychain)
- Environment variable support for CI/CD
- CLI fallback when web unavailable
- Global configuration system
- Project-level configuration overrides

### Out of Scope

- **SSO/OAuth integration**: Enterprise auth is future work
- **Team/organization features**: Multi-user is separate epic
- **API key sharing**: Each user manages own keys
- **Custom provider plugins**: Uses existing provider system
- **Offline mode for cloud providers**: Only Ollama works offline
- **Mobile wizard**: Desktop/tablet only
- **Guided tutorials**: Just onboarding, not product tours
- **Account creation**: No GAO-Dev accounts

### MVP vs. Future Phases

#### MVP (Phase 1) - This PRD

- Unified start command
- Context detection (4 scenarios)
- Basic onboarding wizard (4 steps)
- Git configuration
- Provider selection
- API key validation
- Basic credential storage (keyring)
- CLI fallback

#### Phase 2 - Enhanced Security

- Encrypted file fallback when keychain unavailable
- API key rotation reminders
- Credential health checks

#### Phase 3 - Advanced Features

- Project templates during onboarding
- Team configuration sharing
- Usage analytics (opt-in)

#### Future Considerations

- VSCode extension integration
- Enterprise SSO
- Self-hosted deployment wizard

---

## Dependencies & Risks

### Dependencies

#### Internal

- **Epic 35 (Provider Selection)**: Provides provider infrastructure - COMPLETE
- **Epic 30 (Interactive Brian Chat)**: Provides chat interface - COMPLETE
- **Epic 39 (Web Interface)**: Provides web server - COMPLETE
- **Frontend build system**: React components for wizard

#### External

- **System keychain availability**: Not all Linux systems have SecretService
- **Browser availability**: Some server environments have no browser
- **Git installation**: Git must be installed for full functionality

### Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| **Keychain not available** | Medium | Medium | Encrypted file fallback with user warning |
| **Browser fails to open** | Low | Medium | Clear terminal URL, CLI continues working |
| **Port always in use** | Low | Low | Auto-increment port, clear messaging |
| **API validation fails** | Medium | High | Detailed error messages with fix suggestions |
| **Git not installed** | Low | Medium | Clear installation instructions, optional git |
| **Users skip onboarding** | Medium | Medium | Minimal required steps, remember preferences |
| **Breaking change for existing users** | Medium | High | Backward compatibility mode, migration warnings |
| **Credential storage platform differences** | High | Medium | Abstract behind CredentialManager, test all platforms |

---

## Timeline & Milestones

### High-Level Timeline

#### Epic 1: Startup Orchestration (Foundation)
- Story 1.1: StartupOrchestrator implementation
- Story 1.2: ContextDetector implementation
- Story 1.3: Git configuration detection
- Story 1.4: Unified `gao-dev start` command
- Story 1.5: Deprecation warnings for legacy commands

#### Epic 2: Web Onboarding Backend
- Story 2.1: Onboarding API endpoints
- Story 2.2: Global configuration management
- Story 2.3: Onboarding state persistence
- Story 2.4: Provider selection endpoint
- Story 2.5: API key validation endpoint

#### Epic 3: Credential Security
- Story 3.1: CredentialManager abstraction
- Story 3.2: macOS Keychain integration
- Story 3.3: Windows Credential Manager integration
- Story 3.4: Linux SecretService integration
- Story 3.5: Encrypted file fallback

#### Epic 4: Web Onboarding Frontend
- Story 4.1: Wizard component architecture
- Story 4.2: Project configuration step
- Story 4.3: Git configuration step
- Story 4.4: Provider selection step
- Story 4.5: API key configuration step
- Story 4.6: Completion and handoff

#### Epic 5: Polish & Edge Cases
- Story 5.1: CLI fallback implementation
- Story 5.2: Environment variable bypass
- Story 5.3: Offline support (Ollama)
- Story 5.4: Error handling and messaging
- Story 5.5: Cross-platform testing

### Release Strategy

- **Alpha**: Internal testing with team
- **Beta**: Select beta testers with feedback loop
- **GA**: Full release with documentation update

### Definition of Done

- All acceptance criteria met
- Unit tests >80% coverage
- Integration tests for each flow
- Cross-platform testing (Windows, macOS, Linux)
- Documentation updated
- Migration guide for existing users

---

## Metrics & Analytics

### Analytics Requirements

Events to track (all client-side, opt-in):

- `onboarding_started`: User began onboarding
- `onboarding_step_completed`: Which step, how long
- `onboarding_completed`: Total time, steps skipped
- `onboarding_abandoned`: Which step, how long on step
- `provider_selected`: Which provider, model
- `api_key_validation`: Success/failure, provider
- `cli_fallback_triggered`: Reason for fallback

Conversion funnels:

1. `gao-dev start` -> Browser opens -> Wizard starts -> Complete
2. Per-step funnel within wizard

User behavior metrics:

- Time per step
- Back navigation frequency
- Validation error frequency
- Retry attempts

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Onboarding completion rate | >90% | Funnel analysis |
| Time to first message | <3 min | Event timestamps |
| API key validation success | >95% | Validation events |
| CLI fallback rate | <5% | Fallback events |
| User satisfaction | >4.5/5 | Post-onboarding survey |
| Support ticket reduction | -50% | Support system |

### Dashboards

- **Onboarding funnel**: Real-time conversion metrics
- **Error monitoring**: Validation failures, platform issues
- **Platform breakdown**: Success rates by OS

---

## Open Questions

1. **CLI deprecation timeline**: When do we fully remove `gao-dev init` and `gao-dev web start`?
   - Recommendation: 6 months deprecation warning, then remove in next major version

2. **Keychain fallback security**: Is encrypted file with user-provided password acceptable?
   - Recommendation: Yes, with clear warning about security implications

3. **Onboarding analytics**: Opt-in or opt-out?
   - Recommendation: Opt-in during onboarding, respect system privacy settings

4. **Multiple API key support**: Should we support multiple providers simultaneously?
   - Recommendation: Out of scope for MVP, store only active provider key

5. **Offline onboarding**: Can user complete onboarding without internet?
   - Recommendation: Yes for Ollama, defer API validation for cloud providers

6. **Existing project migration**: What happens to .gao-dev/ from before this feature?
   - Recommendation: Backward compatible, detect and skip onboarding

---

## Appendix

### References

- [Epic 35: Interactive Provider Selection](../interactive-provider-selection/PRD.md) - COMPLETE
- [Epic 30: Interactive Brian Chat](../interactive-brian-chat/PRD.md) - COMPLETE
- [Epic 39: Web Interface](../web-interface/PRD.md) - COMPLETE
- [Beta Testing Feedback Summary](../../../docs/beta-feedback-summary.md)
- [Cross-platform Keyring Documentation](https://keyring.readthedocs.io/)

### Glossary

- **Greenfield**: New project with no existing code
- **Brownfield**: Existing project adding GAO-Dev
- **Provider**: AI service (Claude Code, OpenCode, Direct API)
- **Keychain**: System secure credential storage
- **Headless**: Running without browser/GUI (CI/CD)

### Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-19 | John (PM Agent) | Initial draft |

---

## Design Decisions Summary

### Key Decisions Made

1. **Web-first approach**: Onboarding is web-based because visual provider selection and secure key entry are better experiences in a browser than CLI

2. **CLI not deprecated**: CLI remains fully functional with `gao-dev start --headless` for power users and CI/CD

3. **System keychain for secrets**: Using system keychain (not custom encryption) because it's the most secure option and users trust it for other credentials

4. **Global + project config**: Global config for user preferences, project config for overrides, enabling both consistency and flexibility

5. **Environment variables as override**: Env vars always take precedence, ensuring CI/CD works without interactive prompts

6. **Graceful degradation**: If any step fails, user can still use GAO-Dev (just with reduced functionality or manual config)

### Trade-offs Accepted

1. **Keychain dependency**: Adds complexity but significantly improves security
2. **Browser requirement**: Most users have browsers; headless mode covers exceptions
3. **Multi-step wizard**: More clicks but better understanding and validation
4. **Global config file**: Another file to manage but enables cross-project consistency
