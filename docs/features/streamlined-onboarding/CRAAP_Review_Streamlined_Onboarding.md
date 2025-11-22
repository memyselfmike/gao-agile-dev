# CRAAP Review: Streamlined Startup & Web-Based Onboarding

**Review Date**: 2025-11-19
**Documents Reviewed**:
- PRD.md (v1.0)

---

## Executive Summary

The PRD for Streamlined Onboarding is comprehensive and well-structured, addressing a genuine user pain point identified by beta testers. However, the review identified **4 critical issues**, **7 moderate concerns**, and **5 minor improvements** that should be addressed before implementation.

**Key Findings:**
- The web-first approach may exclude important user segments (SSH users, WSL users, headless servers)
- Credential storage strategy has platform-specific risks that need deeper analysis
- The 5-epic structure may be over-engineered for MVP; consider consolidation
- Missing architecture document creates ambiguity around implementation details
- Some success metrics are unmeasurable without additional infrastructure

Overall, the PRD provides a solid foundation but requires refinement in security architecture, fallback scenarios, and MVP scope definition before moving to story creation.

---

## CRAAP Analysis

### Critique and Refine

**Identified Issues:**

1. **Vague "encrypted file fallback" specification** (FR-12)
   - No details on encryption algorithm, key derivation, or where the encryption key is stored
   - "Encrypted file" is meaningless security if the decryption key is also on disk
   - User-provided password mentioned in trade-offs but not in requirements

2. **Inconsistent terminology for project detection**
   - Uses "fresh install", "new project", "brownfield", "existing project" inconsistently
   - FR-2 lists 4 scenarios but they overlap (fresh install IS a new project)
   - Need clear taxonomy: Global state (first-time/returning) x Project state (none/greenfield/brownfield/gao-dev)

3. **Ambiguous "deprecation warnings" scope** (FR-1)
   - Says legacy commands "redirect to new flow" but also "continue to work"
   - These are contradictory - does `gao-dev init` initialize or redirect?
   - Need clear behavior specification for each deprecated command

4. **Missing error recovery specifications**
   - FR-6 says "Saves progress (can resume if browser closed)" but no details on how
   - What happens if server crashes mid-onboarding?
   - What if user closes terminal (killing server) but browser stays open?

5. **Over-specified wizard steps**
   - PRD specifies 6 steps in FR-6 but only 4 steps in "MVP Scope"
   - Use Case 1 shows 4 steps, Use Case 2 shows 2 steps
   - Need consistent step count across document

6. **Redundant success criteria**
   - "Success Criteria" section duplicates "Key Performance Indicators"
   - Goals section overlaps with both
   - Consolidate into single measurable criteria list

**Recommendations:**

1. **Define encryption fallback architecture** - Specify algorithm (AES-256-GCM), key derivation (PBKDF2), and that user password is required for this fallback (not stored)

2. **Create detection matrix** - Define 2x4 matrix of Global Config (exists/not) x Directory State (empty/code-no-gaodev/code-with-gaodev/gaodev-only)

3. **Specify deprecated command behavior** - Table with columns: Command, Current Behavior, New Behavior, Deprecation Message

4. **Add onboarding recovery protocol** - Specify onboarding.yaml checkpoints and how each failure mode is handled

5. **Standardize on 4 wizard steps** - Project -> Git -> Provider -> API Key (merge completion into API Key step)

---

### Risk Potential and Unforeseen Issues

**Identified Risks:**

1. **CRITICAL: Keychain unavailable more common than expected**
   - Linux servers often lack SecretService (no GUI)
   - Docker containers have no keychain
   - WSL2 has complex keychain setup
   - Risk: Large portion of target users (developers on Linux/Docker) hit fallback path

2. **CRITICAL: Browser launch fails silently on SSH sessions**
   - `webbrowser.open()` may return True but browser never opens
   - SSH sessions have no display server
   - Remote development (VS Code Remote, GitHub Codespaces) is increasingly common

3. **HIGH: API key validation creates external dependency**
   - FR-10 requires "Real-time validation with provider API"
   - What if provider API is down? User blocked from onboarding
   - What if user is behind corporate proxy that blocks validation?

4. **HIGH: Port auto-increment creates UX confusion**
   - User bookmarks localhost:3000, but next time it's localhost:3001
   - Browser auto-complete fills wrong port
   - Risk: "GAO-Dev stopped working" support tickets

5. **MEDIUM: Git configuration race condition**
   - User sets git config in wizard while another process uses git
   - `git config --global` is not atomic
   - Could corrupt .gitconfig

6. **MEDIUM: Multi-project confusion with global config**
   - User has 3 projects, changes global provider preference
   - All projects now use new provider? Or only new ones?
   - Need clear precedence and user communication

7. **LOW: macOS Keychain permission prompts**
   - Each new terminal session may prompt "allow access to keychain"
   - Users may deny and break GAO-Dev

**Mitigation Strategies:**

1. **For keychain availability:**
   - Detect keychain availability BEFORE offering it as option
   - Make encrypted file the first-class option on Linux servers
   - Document environment-specific setup guides

2. **For SSH/headless sessions:**
   - Add `--no-browser` auto-detection (check `$DISPLAY`, `$SSH_CLIENT`)
   - Provide QR code in terminal with URL for phone/other device
   - Consider TUI wizard as alternative to web wizard

3. **For API validation:**
   - Allow "skip validation" with warning
   - Cache validation result for 24 hours
   - Provide manual validation command for later

4. **For port conflicts:**
   - Store last-used port in global config
   - Always try same port first
   - Show clear message: "Using port 3001 (3000 was busy)"

5. **For git race condition:**
   - Use file locking when writing git config
   - Or set project-local git config instead of global

---

### Analyse Flow / Dependencies

**Dependency Issues:**

1. **Circular dependency in startup flow**
   - StartupOrchestrator needs config to decide behavior
   - Config may not exist (first-time user)
   - Need explicit bootstrap mode vs normal mode

2. **Web server dependency on initialization**
   - Web server needs project_root to serve API
   - project_root may not be determined until user picks folder
   - How does server start before project context exists?

3. **Provider validation depends on credentials**
   - Can't validate provider until API key entered
   - Can't store API key until provider selected
   - Can't select provider until wizard loads
   - Long dependency chain for first-time users

4. **Frontend build dependency unclear**
   - OnboardingWizard is React component
   - Is it part of existing frontend build or separate?
   - How is it loaded if main app isn't initialized?

5. **Epic sequencing has hidden dependencies**
   - Epic 4 (Frontend) should start with Epic 2 (Backend) for API contracts
   - Epic 3 (Credentials) blocks Epic 4 Story 4.5 (API key step)
   - Need explicit parallelization strategy

**Flow Improvements:**

1. **Add explicit state machine for startup**
   ```
   INIT -> DETECT_CONTEXT -> DETERMINE_FLOW ->
     FLOW_ONBOARDING: LAUNCH_WEB -> WIZARD -> COMPLETE -> READY
     FLOW_RETURNING: LAUNCH_WEB -> QUICK_START -> READY
     FLOW_EXISTING: LAUNCH_WEB -> READY
     FLOW_HEADLESS: CLI_INIT -> READY
   ```

2. **Decouple web server from project context**
   - Server can start with "no project" mode
   - Serve onboarding wizard that CREATES project context
   - Then reload with project context

3. **Parallelize Epic 3 and Epic 4**
   - Credential storage (Epic 3) and UI components (Epic 4) are independent
   - Only Story 4.5 (API key step) depends on Epic 3
   - Can start Epic 4 early and integrate later

4. **Define API contract first**
   - Before Epic 2 and 4, create OpenAPI spec for onboarding endpoints
   - Allows frontend and backend to develop in parallel

---

### Alignment with Goal

**Alignment Concerns:**

1. **Goal dilution: "Global configuration system" scope creep**
   - Core goal: Reduce onboarding friction
   - Global config is infrastructure that enables the goal
   - But PRD spends significant space on global config details
   - Risk: Building infrastructure instead of solving user problem

2. **Misaligned metric: "90% onboarding completion"**
   - If users can skip onboarding (returning users, existing projects), completion rate is misleading
   - Better metric: "% of users who successfully send first message to Brian"
   - Measures actual goal: time-to-first-success

3. **Over-engineering: 5 epics for MVP**
   - MVP could be: detect context, launch web, 4-step wizard, basic storage
   - Credential security (Epic 3) could be Phase 2 (use env vars for MVP)
   - Polish (Epic 5) should be integrated, not separate epic

4. **Missing requirement: Existing user migration**
   - What about users who already have .gao-dev/ from before this feature?
   - Do they see onboarding? Do we migrate their config?
   - This is critical for beta testers (the original complainers!)

5. **Questionable requirement: Port auto-increment (FR-5)**
   - Does this serve the core goal? Or is it nice-to-have?
   - Simpler: just use port 3000, error if busy
   - User can specify `--port` if needed

**Recommendations:**

1. **Ruthlessly prioritize MVP scope:**
   - Must have: Context detection, web launch, wizard, basic storage (env vars)
   - Should have: Keychain storage, returning user fast-path
   - Could have: Port auto-increment, offline support, encrypted fallback

2. **Change primary metric to:**
   - "Time from `gao-dev start` to first Brian response" (P50, P95)
   - This directly measures stated goal

3. **Consolidate to 3 epics for MVP:**
   - Epic 1: Startup & Detection (current Epic 1)
   - Epic 2: Web Wizard (merge current Epics 2 & 4)
   - Epic 3: Integration & Polish (merge current Epics 3 & 5, defer advanced credential storage)

4. **Add explicit migration story:**
   - Story: "Existing projects are detected and skip onboarding"
   - Story: "Existing preferences from .gao-dev/ are respected"

---

### Perspective (Critical Outsider View)

**Challenging Assumptions:**

1. **"Web is better for onboarding than CLI"**
   - Assumption: Visual UI is always better
   - Challenge: Many developers prefer CLI. Cursor/Copilot compete on CLI experience
   - Alternative: Rich TUI wizard (like `npm init` or `gh auth login`)
   - Consider: Offer both, let user choose

2. **"Users want to configure in browser"**
   - Assumption: Opening browser is positive UX
   - Challenge: Context switch from terminal to browser is friction
   - Many power users have terminal workflows, browser interrupts
   - Alternative: `gao-dev start --wizard=tui` for terminal-native experience

3. **"System keychain is most secure"**
   - Assumption: Keychain > encrypted file > env var
   - Challenge: Env vars are actually very secure (per-process, not persisted)
   - Keychain can be accessed by any app with permission
   - Alternative: Recommend env vars as primary, keychain as convenience

4. **"Single entry point is simpler"**
   - Assumption: One command (`gao-dev start`) is easier than three
   - Challenge: Unix philosophy - do one thing well
   - Power users may want `gao-dev web` without initialization
   - Alternative: Keep separate commands but make `gao-dev start` the recommended one

5. **"Onboarding should be skippable for returning users"**
   - Assumption: Returning users don't want wizard
   - Challenge: Returning users might want to change settings
   - Current flow: Quick start with [Customize] button
   - Risk: [Customize] is undiscoverable; users can't find settings later

**Alternative Approaches Not Explored:**

1. **Configuration file generation approach**
   - Instead of wizard: `gao-dev init` generates commented .gao-dev/config.yaml
   - User edits file directly (familiar for developers)
   - `gao-dev start` uses config, prompts only for missing required values
   - Pro: Transparent, version-controllable, scriptable

2. **Provider-first approach**
   - Detect provider from existing env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY)
   - If found, skip provider selection entirely
   - Only prompt for what's truly missing
   - Pro: Zero prompts for users with env vars set

3. **Template-based initialization**
   - `gao-dev start --template=python-cli`
   - Templates include sensible defaults for project type
   - Wizard only asks for project-specific values
   - Pro: Even faster for common project types

4. **Progressive onboarding**
   - Don't front-load all configuration
   - Start with minimal setup (just project name)
   - Prompt for git config when first git operation needed
   - Prompt for API key when first AI call needed
   - Pro: Instant start, configure as needed

**Devil's Advocate Questions:**

1. "Why do we need a wizard at all?"
   - Could we just prompt in terminal for the 4 values we need?
   - Name: default to folder name, Email: read from git config
   - Provider: default to claude-code, API key: prompt or env var
   - Total prompts: 0-2 for most users

2. "Is web-based onboarding actually the bottleneck?"
   - Beta tester feedback: "clunky and confusing"
   - Is the confusion about WHAT to do or HOW to do it?
   - Would better error messages solve this without a wizard?

3. "Are we solving the wrong problem?"
   - Users complain about steps, but maybe the real problem is error messages
   - Current: "Error: git not configured"
   - Better: "Git user.name not set. Run: git config --global user.name 'Your Name'"
   - Maybe we don't need a wizard, just better errors

---

## Priority Issues

### Critical (Must Fix Before Implementation)

1. **Encrypted file fallback security is undefined** - Cannot implement without specification (Critique)

2. **SSH/headless environment detection missing** - Large user segment will have broken experience (Risk)

3. **Web server bootstrap without project context undefined** - Architectural blocker (Flow)

4. **Keychain unavailability underestimated** - Linux/Docker users are primary audience (Risk)

### Moderate (Should Fix Before Story Writing)

1. **Inconsistent terminology for project detection** - Will cause confusion in stories (Critique)

2. **Epic structure is over-engineered for MVP** - Consolidate to 3 epics (Alignment)

3. **API validation external dependency** - Need offline/skip path (Risk)

4. **Missing existing user migration requirement** - Beta testers are existing users! (Alignment)

5. **Deprecation behavior unspecified** - What do legacy commands actually do? (Critique)

6. **Success metric measures wrong thing** - Measure time-to-first-message, not completion rate (Alignment)

7. **No TUI alternative for terminal-native users** - Consider offering both (Perspective)

### Minor (Nice to Have)

1. **Port auto-increment is scope creep** - Simpler: fixed port with error (Alignment)

2. **Redundant success criteria sections** - Consolidate (Critique)

3. **QR code for remote URL** - Nice UX for SSH users (Risk mitigation)

4. **API contract specification** - Would enable parallel development (Flow)

5. **Progressive onboarding alternative** - Explore in Phase 2 (Perspective)

---

## Action Items

### Before Story Writing

1. [ ] **PM**: Define encrypted file fallback security architecture (algorithm, key derivation, user password requirement)
2. [ ] **PM**: Create 2x4 detection matrix for context detection scenarios
3. [ ] **PM**: Specify deprecated command behaviors in table format
4. [ ] **PM**: Add SSH/headless auto-detection requirement (check $DISPLAY, $SSH_CLIENT)
5. [ ] **PM**: Consolidate epic structure from 5 to 3 epics for MVP
6. [ ] **PM**: Add existing user migration requirements
7. [ ] **PM**: Change primary metric to "time-to-first-Brian-response"
8. [ ] **Architect**: Design web server bootstrap mode (no project context)
9. [ ] **Architect**: Define keychain availability detection and fallback strategy
10. [ ] **Architect**: Create startup state machine diagram

### During Architecture

11. [ ] **Architect**: Specify API validation offline/skip behavior
12. [ ] **Architect**: Design TUI wizard alternative (consider for MVP or Phase 2)
13. [ ] **Architect**: Create OpenAPI spec for onboarding endpoints

### During Implementation

14. [ ] **Dev**: Implement environment detection for SSH/WSL/Docker
15. [ ] **Dev**: Test keychain availability on Linux server, Docker, WSL2
16. [ ] **QA**: Create test matrix for all detection scenarios
17. [ ] **QA**: Test on SSH session, VS Code Remote, GitHub Codespaces

---

## Conclusion

The Streamlined Onboarding PRD addresses a genuine and important user pain point. The web-first wizard approach is reasonable but needs more thought around edge cases (SSH, Docker, WSL) and security (encrypted file fallback).

**Overall Health: 7/10** - Solid foundation but needs refinement.

**Key Recommendations:**

1. **Simplify MVP scope** - Consolidate to 3 epics, defer advanced credential storage
2. **Harden edge cases** - SSH detection, keychain fallback, API validation offline
3. **Create architecture document** - State machine, API contracts, security architecture
4. **Consider TUI alternative** - Terminal-native users may prefer it

**Next Steps:**

1. Address Critical and Moderate issues above
2. Create ARCHITECTURE.md with technical decisions
3. Refine epic/story structure with simplified scope
4. Begin story writing with clear acceptance criteria

The feature is valuable and achievable, but rushing to implementation without addressing these issues will create technical debt and user frustration.
