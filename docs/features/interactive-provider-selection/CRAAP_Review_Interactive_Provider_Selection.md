# CRAAP Review: Interactive Provider Selection

**Review Date**: 2025-01-12
**Reviewer**: Claude (Automated CRAAP Framework Analysis)
**Documents Reviewed**:
- `PRD.md` (650+ lines)
- `ARCHITECTURE.md` (1,250+ lines)
- `EPIC-35.md` (1,100+ lines)
- `README.md` (450+ lines)

**Total Documentation**: ~3,450 lines

---

## Executive Summary

The Interactive Provider Selection feature planning is **comprehensive and well-structured**, with detailed requirements, architecture, and implementation plan. However, the review identified **15 critical/moderate issues** that should be addressed before implementation begins, primarily around:

1. **Complexity concerns** - The solution may be overengineered for the problem
2. **Risk mitigation gaps** - Several edge cases and failure modes not addressed
3. **Testing estimates** - May be optimistic given the scope
4. **Platform-specific challenges** - Windows/macOS/Linux differences underspecified
5. **User experience trade-offs** - Forcing interaction on every first startup

**Overall Assessment**: ⚠️ **MODERATE CONCERNS** - Planning is solid but needs refinement before proceeding.

**Recommendation**: Address critical issues (Priority 1) before starting Story 35.1.

---

## CRAAP Analysis

### C - Critique and Refine

#### Identified Issues

**1. Testing Estimates May Be Optimistic** 🔴 CRITICAL
- **Issue**: Story 35.7 allocates 8 points for 120+ tests across unit, integration, E2E, and regression
- **Analysis**: Creating 120+ quality tests typically takes 15-20 hours minimum
- **Impact**: Could cause schedule slippage
- **Evidence**:
  - 60+ unit tests (3-5 min each = 3-5 hours)
  - 30+ integration tests (10-15 min each = 5-7 hours)
  - 10+ E2E tests (20-30 min each = 3-5 hours)
  - 20+ regression tests (5-10 min each = 2-3 hours)
  - Total: 13-20 hours just writing tests, not including debugging
- **Recommendation**:
  - Split Story 35.7 into two stories: "Core Testing" (8 pts) and "Regression & E2E" (5 pts)
  - Or increase Story 35.7 to 13 points

**2. Windows-Specific Challenges Underspecified** 🟡 MODERATE
- **Issue**: Architecture mentions cross-platform support but lacks Windows-specific details
- **Missing Details**:
  - Path separator handling (`\` vs `/`)
  - CLI detection differences (`where` vs `which`)
  - File permission model (Windows ACLs vs Unix permissions)
  - PowerShell vs CMD vs Git Bash terminal detection
  - Windows-specific Ollama installation paths
- **Impact**: Could cause Windows-specific bugs in production
- **Recommendation**: Add "Platform Compatibility Matrix" section to Architecture
- **Example Addition**:
  ```python
  # Windows-specific CLI detection
  def check_cli_windows(cli_name: str) -> bool:
      try:
          result = subprocess.run(
              ['where', cli_name],
              capture_output=True,
              timeout=2,
              shell=True  # Required on Windows
          )
          return result.returncode == 0
      except Exception:
          return False
  ```

**3. Ollama Model Detection Timeout Too Short** 🟡 MODERATE
- **Issue**: 3-second timeout for `ollama list` may be insufficient
- **Analysis**:
  - Large model collections (20+ models) can take 5-10 seconds to list
  - Slow disk (HDD, NAS) could exceed 3 seconds
  - First-time Ollama startup might initialize daemon
- **Impact**: False negatives, Ollama appears unavailable
- **Recommendation**: Increase timeout to 10 seconds with user feedback
- **Example**:
  ```python
  console.print("[dim]Detecting Ollama models (may take a moment)...[/dim]")
  models = await check_ollama_models(timeout=10)
  ```

**4. Preference File Corruption Recovery Incomplete** 🟡 MODERATE
- **Issue**: PreferenceManager handles corrupt files by returning `None`, but no recovery mechanism
- **Missing**:
  - Backup of previous working preferences
  - User notification that preferences were corrupt
  - Offer to restore from backup
  - Logging of corruption details for debugging
- **Impact**: User loses configuration, no way to recover
- **Recommendation**: Implement backup strategy
- **Example**:
  ```python
  def save_preferences(self, prefs: Dict) -> None:
      # Backup existing file first
      if self.preferences_file.exists():
          backup = self.preferences_file.with_suffix('.yaml.bak')
          shutil.copy(self.preferences_file, backup)

      # Atomic write
      temp_file = self.preferences_file.with_suffix('.yaml.tmp')
      temp_file.write_text(yaml.dump(prefs))
      temp_file.replace(self.preferences_file)  # Atomic on most systems
  ```

**5. API Key Validation Is Incomplete** 🟡 MODERATE
- **Issue**: ProviderValidator checks if `ANTHROPIC_API_KEY` is set, but not if it's valid
- **Analysis**: Invalid key only discovered when first API call fails
- **Missing**: Optional lightweight validation (e.g., check key format, or quick test API call)
- **Impact**: User proceeds with invalid key, fails later
- **Recommendation**: Add optional key validation
- **Example**:
  ```python
  async def validate_api_key(self, provider: str, key: str) -> bool:
      """Quick validation check (optional, can be slow)."""
      if not key.startswith('sk-ant-'):
          return False  # Obviously invalid format

      # Optional: test with simple API call
      # (Only if user opts in, as this adds latency)
      return True
  ```

**6. Model Selection UI Could Be Overwhelming** 🟢 MINOR
- **Issue**: If user has 50+ Ollama models, showing all in table could overwhelm
- **Missing**: Pagination, search, filtering
- **Impact**: Poor UX for power users with many models
- **Recommendation**:
  - Show first 10 models by default
  - Add "Show more" option or search
  - Group by model family (llama, mistral, etc.)

**7. Story 35.1 May Be Underestimated** 🟡 MODERATE
- **Issue**: 2 points for creating all stubs, data models, exceptions, test structure
- **Breakdown**:
  - 4 module stubs with class definitions
  - 5 exception classes
  - 3 data models with dataclasses
  - 4 test file stubs
  - Import validation (mypy)
  - Documentation
- **Analysis**: This is foundational work, likely 4-6 hours
- **Recommendation**: Keep at 2 points but be aware it's on the higher end

**8. No Explicit Rollback Plan** 🟡 MODERATE
- **Issue**: If Epic 35 causes production issues, rollback strategy unclear
- **Missing**:
  - Feature flag to disable provider selection
  - Rollback instructions for operations team
  - Monitoring/alerting for validation failures
- **Impact**: Difficult to revert if problems discovered
- **Recommendation**: Add feature flag
- **Example**:
  ```python
  # In defaults.yaml
  features:
    interactive_provider_selection: true  # Set to false to disable

  # In ChatREPL
  if config.features.interactive_provider_selection:
      provider_config = selector.select_provider()
  else:
      # Use defaults/env vars only
      provider_config = self._get_default_provider()
  ```

**9. Session State Initialization Order Unclear** 🟡 MODERATE
- **Issue**: ChatREPL has ChatSession for conversation state. Provider selection timing unclear.
- **Questions**:
  - Does provider selection happen before ChatSession creation?
  - Could provider selection interfere with session restoration?
  - What if user has a saved session but wants to change provider?
- **Impact**: Potential conflicts between session restoration and provider selection
- **Recommendation**: Clarify in architecture with sequence diagram

**10. No Mid-Session Provider Switching** 🟢 MINOR
- **Issue**: User must restart REPL to change providers
- **Missing**: Command like `/switch-provider` for mid-session changes
- **Impact**: Poor UX for experimentation
- **Recommendation**: Add to "Future Enhancements" section, consider for Epic 36

#### Recommendations

1. **Split Story 35.7** into two stories (testing + regression)
2. **Add Windows compatibility matrix** to Architecture
3. **Increase Ollama timeout** to 10 seconds with feedback
4. **Implement preference backup** strategy
5. **Add optional API key format validation**
6. **Add feature flag** for rollback capability
7. **Clarify session initialization** order in architecture
8. **Add model selection pagination** for large lists
9. **Document rollback plan** in separate ROLLBACK.md file
10. **Consider mid-session switching** as future enhancement

---

### R - Risk Potential and Unforeseen Issues

#### Identified Risks

**1. Prompt Toolkit Fails in Headless CI Environments** 🔴 CRITICAL
- **Risk**: Even with `AGENT_PROVIDER` env var, importing prompt_toolkit could fail in CI
- **Scenario**: Headless Docker container, no TTY, prompt_toolkit initialization fails
- **Impact**: CI/CD pipelines break
- **Likelihood**: Medium-High (common in containerized environments)
- **Mitigation**:
  ```python
  # Lazy import prompt_toolkit only when needed
  def prompt_provider(self):
      try:
          from prompt_toolkit import PromptSession
          # Use prompt_toolkit
      except ImportError:
          # Fallback to input()
          return input("Select provider: ")
  ```
- **Test**: Add CI test that runs in headless environment

**2. Race Condition with `.gao-dev/` Creation** 🟡 MODERATE
- **Risk**: Multiple processes creating `.gao-dev/` simultaneously
- **Scenario**: User runs multiple `gao-dev start` instances in same project
- **Impact**: File corruption, permission errors
- **Likelihood**: Low (unusual use case)
- **Mitigation**:
  ```python
  def ensure_gao_dev_dir(self) -> Path:
      gao_dev = self.project_root / ".gao-dev"
      try:
          gao_dev.mkdir(mode=0o700, exist_ok=True)  # exist_ok prevents race
      except FileExistsError:
          pass  # Another process created it, that's fine
      return gao_dev
  ```

**3. YAML Injection Vulnerability** 🔴 CRITICAL
- **Risk**: User-provided input saved to YAML could execute arbitrary code
- **Scenario**: User selects provider with malicious name containing YAML syntax
- **Impact**: Code execution, data exfiltration
- **Likelihood**: Low (requires malicious input)
- **Mitigation**:
  ```python
  def save_preferences(self, prefs: Dict) -> None:
      # Sanitize all string values
      sanitized = self._sanitize_dict(prefs)

      # Use safe_dump instead of dump
      yaml_str = yaml.safe_dump(sanitized, default_flow_style=False)
      self.preferences_file.write_text(yaml_str)

  def _sanitize_dict(self, data: Dict) -> Dict:
      """Remove any dangerous YAML syntax."""
      # Whitelist approach: only allow alphanumeric, dash, underscore
      # ... implementation ...
  ```
- **Test**: Add security tests with malicious input

**4. Rich Console Renders Incorrectly in Some Terminals** 🟡 MODERATE
- **Risk**: Rich formatted output broken in older terminals, Windows CMD, etc.
- **Scenario**: User has Windows CMD, Rich uses ANSI codes that aren't supported
- **Impact**: Garbled output, poor UX
- **Likelihood**: Medium (Windows CMD still common)
- **Mitigation**:
  ```python
  from rich.console import Console

  # Auto-detect terminal capabilities
  console = Console(
      force_terminal=None,  # Auto-detect
      force_interactive=None,  # Auto-detect
      legacy_windows=True  # Enable Windows compatibility mode
  )
  ```
- **Test**: Test on Windows CMD, PowerShell, Git Bash, WSL

**5. Provider Validation Hanging** 🟡 MODERATE
- **Risk**: Async validation hangs indefinitely if CLI stuck
- **Scenario**: OpenCode CLI prompts for input, `check_cli_available()` waits forever
- **Impact**: REPL startup hangs, user force-quits
- **Likelihood**: Low-Medium
- **Mitigation**:
  ```python
  async def check_cli_available(self, cli_name: str) -> bool:
      try:
          proc = await asyncio.wait_for(
              asyncio.create_subprocess_exec(
                  cli_name, '--version',
                  stdout=asyncio.subprocess.PIPE,
                  stderr=asyncio.subprocess.PIPE
              ),
              timeout=5.0  # Hard timeout
          )
          await proc.wait()
          return proc.returncode == 0
      except asyncio.TimeoutError:
          logger.warning(f"{cli_name} check timed out")
          return False
  ```

**6. Circular Dependency Risk** 🟡 MODERATE
- **Risk**: ProviderSelector → ProviderFactory → ProcessExecutor → ProviderSelector
- **Analysis**: Need to verify no circular imports
- **Mitigation**:
  - Use dependency injection
  - Lazy imports where possible
  - Run import checker: `python -c "import gao_dev.cli.provider_selector"`

**7. Memory Leak in Preference Loading** 🟢 MINOR
- **Risk**: Repeated load/save in long-running process leaks memory
- **Scenario**: REPL runs for hours, preference file modified externally, repeatedly reloaded
- **Likelihood**: Very Low
- **Mitigation**: Use weak references or explicit cleanup

**8. Preference File Lock Contention** 🟡 MODERATE
- **Risk**: Multiple GAO-Dev instances write to same preference file
- **Scenario**: User runs `gao-dev start` in multiple terminals
- **Impact**: Corrupted preferences, write conflicts
- **Mitigation**:
  ```python
  import fcntl  # Unix
  import msvcrt  # Windows

  def save_preferences(self, prefs: Dict) -> None:
      with open(self.preferences_file, 'w') as f:
          # Acquire exclusive lock
          if sys.platform == 'win32':
              msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
          else:
              fcntl.flock(f, fcntl.LOCK_EX)

          yaml.safe_dump(prefs, f)

          # Lock released automatically on close
  ```

**9. Model Name Mismatch** 🟡 MODERATE
- **Risk**: Ollama model names don't match canonical names in config
- **Scenario**: Ollama calls it `deepseek-coder-33b-instruct`, config expects `deepseek-r1`
- **Impact**: Validation passes but execution fails
- **Mitigation**: Model name translation layer or fuzzy matching

**10. Breaking Change to Startup Timing** 🟢 MINOR
- **Risk**: Users with scripts that depend on specific startup timing
- **Scenario**: Script expects REPL to start in <1s, now takes 3-5s due to prompts
- **Likelihood**: Low
- **Mitigation**: Document timing changes, provide bypass option

#### Mitigation Strategies

1. **Lazy import prompt_toolkit** - Only import when actually prompting
2. **Use `exist_ok=True`** - Prevent race conditions on directory creation
3. **Use `yaml.safe_dump()`** - Prevent YAML injection attacks
4. **Enable Rich Windows compatibility** - Handle diverse terminal environments
5. **Add timeouts to all async operations** - Prevent hanging
6. **Run circular dependency checker** - Validate import structure
7. **Add file locking** - Prevent concurrent write conflicts
8. **Add model name translation** - Handle name mismatches
9. **Add security tests** - Test with malicious input
10. **Document timing changes** - Set user expectations

---

### A - Analyse Flow / Dependencies

#### Dependency Issues

**1. Parallel Work Not Optimized** 🟡 MODERATE
- **Issue**: Stories 35.2, 35.3, 35.4 can be done in parallel, but not documented
- **Current Plan**: Stories appear sequential
- **Optimization**:
  ```
  Week 1, Day 1-2:
  - Story 35.1 (2 pts) - Day 1 morning
  - Story 35.2 (5 pts) - Day 1 afternoon + Day 2 morning (Developer A)
  - Story 35.3 (5 pts) - Day 1 afternoon + Day 2 morning (Developer B)
  - Story 35.4 (8 pts) - Day 1 afternoon + Day 2 (Developer C)

  Week 1, Day 3:
  - Story 35.5 (5 pts) - Needs 35.2, 35.3, 35.4 complete
  ```
- **Impact**: Could reduce timeline from 5 days to 3 days with 2-3 developers
- **Recommendation**: Add "Parallel Work Strategy" section to Epic

**2. ChatREPL Initialization Order Unclear** 🟡 MODERATE
- **Issue**: Provider selection in `__init__` but `select_provider()` might be async
- **Problem**: Python `__init__` is synchronous, can't `await`
- **Current Code**:
  ```python
  def __init__(self, project_root):
      provider_config = provider_selector.select_provider()  # Can't await!
  ```
- **Solution Options**:
  1. Make select_provider() synchronous (run async operations with `asyncio.run()`)
  2. Move provider selection to `start()` method (which is async)
  3. Create separate `async def create_repl()` factory method
- **Recommendation**: Use Option 1 (sync wrapper)
  ```python
  def select_provider(self) -> Dict:
      """Synchronous wrapper for async operations."""
      return asyncio.run(self._select_provider_async())
  ```

**3. ProcessExecutor Entry Points Not Considered** 🟡 MODERATE
- **Issue**: Story 35.6 only integrates with ChatREPL
- **Question**: What about other entry points that use ProcessExecutor?
  - `gao-dev create-prd`
  - `gao-dev create-architecture`
  - `gao-dev implement-story`
  - Benchmark runner
- **Impact**: Inconsistent provider selection across different commands
- **Recommendation**:
  - Add Story 35.6.1: "CLI Command Integration" (3 pts)
  - Update all CLI commands to use provider selection

**4. Tests Should Follow TDD Approach** 🟡 MODERATE
- **Issue**: Story 35.7 is last, but TDD recommends writing tests alongside code
- **Current**: All tests in Story 35.7 after implementation complete
- **Better Approach**: Each story includes its own tests
  - Story 35.2: PreferenceManager tests
  - Story 35.3: ProviderValidator tests
  - Story 35.4: InteractivePrompter tests
  - Story 35.5: ProviderSelector tests
  - Story 35.6: Integration tests
  - Story 35.7: Additional E2E and regression tests only
- **Recommendation**: Update epic to include tests in each story

**5. Documentation Timing Suboptimal** 🟢 MINOR
- **Issue**: Story 35.8 is last, but API docs should be written with code
- **Better**: Write API docs in each story, Story 35.8 just compiles/reviews
- **Recommendation**: Update epic to include docs in each story

#### Flow Improvements

1. **Add parallel work strategy** to epic breakdown
2. **Clarify async/sync** handling in ChatREPL integration
3. **Add CLI command integration** as Story 35.6.1
4. **Distribute tests** across implementation stories (TDD)
5. **Distribute documentation** across implementation stories
6. **Add integration checkpoint** after Story 35.5 (ensure everything works together)
7. **Add performance testing earlier** (Story 35.5.1: Performance validation)

---

### A - Alignment with Goal

#### Goal Analysis

**Primary Goal**: "Enable interactive provider selection at startup"

**Alignment Assessment**: ✅ **STRONG ALIGNMENT**

All requirements trace back to the core goal:
- Interactive prompts → Core goal
- Preference persistence → Improve UX (don't prompt every time)
- Validation → Ensure quality (don't let user proceed with broken config)
- OpenCode-specific prompts → Cover real use cases
- Model selection → Complete the configuration

#### Alignment Concerns

**1. Possible Scope Creep** 🟡 MODERATE
- **Concern**: Feature includes many "nice-to-haves" that aren't strictly necessary
- **Analysis**:
  - **Core MVP**: Prompt for provider, save choice ✅ ESSENTIAL
  - **Model selection**: Could default to recommended model ⚠️ NICE-TO-HAVE
  - **Preference persistence**: Could use env vars only ⚠️ NICE-TO-HAVE
  - **Validation**: Could validate lazily (on first use) ⚠️ NICE-TO-HAVE
  - **OpenCode-specific prompts**: Increases complexity ⚠️ NICE-TO-HAVE
- **Recommendation**: Consider phased approach
  - **Phase 1 (MVP)**: Basic provider prompt + save to file
  - **Phase 2**: Validation + model selection
  - **Phase 3**: Advanced features (OpenCode local/cloud, etc.)

**2. Success Criteria Partially Unmeasurable** 🟡 MODERATE
- **Measurable Criteria** ✅:
  - Interactive prompts appear: YES/NO
  - Saved preferences reused: YES/NO
  - All tests pass: YES/NO
  - Selection flow <30s: Measurable with timer
  - Works on all platforms: Testable
- **Vague Criteria** ⚠️:
  - "Clear error messages with actionable suggestions": Subjective
  - "Zero configuration for subsequent startups": What about env var users?
  - "User-friendly prompts": Who judges?
- **Recommendation**: Add user testing acceptance criteria
  - "3 out of 5 test users successfully configure provider in <2 minutes"
  - "0 critical usability issues found in testing"

**3. Missing Business Value Metric** 🟢 MINOR
- **Concern**: Success criteria focus on technical metrics, not business value
- **Missing**:
  - "Reduce support tickets related to provider configuration by 50%"
  - "Increase adoption of local models (Ollama) by X%"
  - "Reduce time-to-first-successful-run for new users"
- **Recommendation**: Add business metrics to PRD

**4. Overengineering Risk** 🟡 MODERATE
- **Concern**: 4 new classes, 120+ tests, 3,450 lines of docs for "prompt user for provider"
- **Analysis**:
  - **Simple solution**: 50 lines, ask user 3 questions, save to file
  - **Proposed solution**: 500+ lines, 4 classes, complex architecture
- **Question**: Is this proportional to the problem?
- **Counter-argument**: GAO-Dev is production software, needs quality
- **Recommendation**: Justify complexity in Architecture, or simplify

**5. Alternative Approach Not Fully Explored** 🟡 MODERATE
- **Concern**: Only one approach (interactive prompts) considered in detail
- **Alternative 1**: `gao-dev configure` standalone command (mentioned but not detailed)
- **Alternative 2**: Web UI for configuration (mentioned but dismissed)
- **Alternative 3**: Smart auto-detection (choose best available provider automatically)
- **Recommendation**: Add "Alternatives Considered" section to PRD with pros/cons

#### Recommendations

1. **Consider phased MVP** approach to reduce initial scope
2. **Add measurable usability criteria** (user testing)
3. **Add business value metrics** to success criteria
4. **Justify architectural complexity** or simplify
5. **Document alternative approaches** with rationale for choice
6. **Add "What We're NOT Doing"** section to bound scope

---

### P - Perspective (Critical Outsider View)

#### Challenging Assumptions

**Assumption 1: Users Want Interactive Prompts** 🔴 CRITICAL
- **Assumption**: "Users prefer interactive prompts over config files"
- **Challenge**: Power users often prefer declarative config (infrastructure as code)
- **Evidence**: DevOps community prefers YAML/JSON config over interactive wizards
- **Risk**: Forcing interaction annoys expert users
- **Alternative**: Make prompts opt-in, not default
- **Example**:
  ```bash
  # Default: use config file or env vars
  gao-dev start  # No prompts

  # Opt-in to interactive setup
  gao-dev start --interactive
  gao-dev configure  # Standalone setup command
  ```
- **Recommendation**: Flip the default (config first, prompts opt-in)

**Assumption 2: Per-Project Configuration is Correct** 🟡 MODERATE
- **Assumption**: "Users want different providers per project"
- **Challenge**: Most users probably want same provider everywhere
- **Evidence**: PRD mentions "global preferences" as future enhancement
- **Risk**: User repeats configuration for every project
- **Alternative**: Global defaults with per-project overrides
- **Recommendation**: Add global preferences in Epic 35, not later

**Assumption 3: First-Time Setup Should Happen in REPL** 🟡 MODERATE
- **Assumption**: "Best place for setup is during `gao-dev start`"
- **Challenge**: Setup wizard should be separate from main workflow
- **Evidence**: Most tools have `init` or `configure` command separate from `run`
- **Examples**:
  - `git init` vs `git commit`
  - `npm init` vs `npm start`
  - `docker init` vs `docker run`
- **Alternative**: `gao-dev init` does setup, `gao-dev start` uses config
- **Recommendation**: Consider separate setup command

**Assumption 4: Validation Should Happen at Startup** 🟡 MODERATE
- **Assumption**: "Validate provider before starting REPL"
- **Challenge**: Validation adds 1-3s latency to every startup
- **Alternative**: Lazy validation (validate on first API call)
- **Trade-off**: Faster startup vs earlier error detection
- **Recommendation**: Make validation optional (via config flag)

**Assumption 5: 39 Story Points is "1 Week"** 🟡 MODERATE
- **Assumption**: "39 story points = 40-50 hours = 1 week"
- **Challenge**: 1 week = 40 hours, but with meetings, emails, context switching, realistic implementation time is ~30 hours
- **Risk**: Timeline slippage
- **Recommendation**: Estimate 1.5-2 weeks for safer timeline

#### Alternative Approaches

**Alternative 1: Config File First (No Prompts by Default)** ⭐ RECOMMENDED
```yaml
# .gao-dev/config.yaml (auto-created with defaults)
provider:
  name: "claude-code"  # Default
  model: "sonnet-4.5"

# User edits file, no prompts needed
# Run: gao-dev start (uses config, no interaction)
```
**Pros**:
- Simpler implementation
- Version-controllable
- Faster startup (no prompts)
- Familiar to developers
- Easier to automate/test

**Cons**:
- Less discoverable for new users
- Need to document config format
- No validation until runtime

**Alternative 2: Smart Auto-Detection**
```python
# Automatically choose best available provider
def auto_select_provider():
    if check_cli('claude'):
        return {'provider': 'claude-code', 'model': 'sonnet-4.5'}
    elif check_cli('opencode') and check_cli('ollama'):
        return {'provider': 'opencode', 'model': 'deepseek-r1', 'local': True}
    elif check_cli('opencode'):
        return {'provider': 'opencode', 'model': 'sonnet-4.5', 'local': False}
    else:
        raise ProviderNotFoundError("No AI providers available")
```
**Pros**:
- Zero configuration (just works)
- Smart defaults
- Fast startup
- Great UX for beginners

**Cons**:
- Less control for users
- Might choose "wrong" provider
- Harder to debug

**Alternative 3: Web-Based Configuration UI**
```bash
gao-dev configure --web
# Opens browser with form:
# - Select provider (dropdown)
# - Select model (dropdown)
# - Test connection (button)
# - Save (button)
# Generates .gao-dev/config.yaml
```
**Pros**:
- Rich UI (dropdown, validation in real-time)
- Visual feedback
- Easier for non-technical users

**Cons**:
- Requires web server
- More complex implementation
- Doesn't work in headless environments

**Alternative 4: Standalone `gao-dev init` Command** ⭐ RECOMMENDED
```bash
# First time
gao-dev init
> Select provider: [1] Claude Code [2] OpenCode [3] Direct API
> 1
> Select model: [1] sonnet-4.5 [2] opus-4
> 1
> Save to: [1] This project [2] Global defaults
> 1
✓ Configuration saved to .gao-dev/config.yaml

# Subsequent starts
gao-dev start  # Just uses config, no prompts
```
**Pros**:
- Separation of concerns (setup vs run)
- Follows industry patterns (`init` vs `start`)
- Can skip `init` if using defaults
- Re-run `init` to reconfigure

**Cons**:
- Extra command to learn
- Two-step process

#### Stakeholder Perspectives

**From a NEW USER:**
- "I just want to try GAO-Dev, why do I need to configure so much?"
- "Can't it just work with sensible defaults?"
- "What's Claude Code vs OpenCode? I don't know!"

**From an EXPERT USER:**
- "Why is it prompting me? I already set `AGENT_PROVIDER`!"
- "This should be a YAML file I can version control."
- "Don't slow down my startup with validation!"

**From a DEVELOPER:**
- "This adds a lot of complexity to maintain."
- "What happens when we add provider #6, #7?"
- "The abstraction is nice, but is it worth it?"

**From a TESTER:**
- "Mocking user input is tedious and brittle."
- "How do I test the visual output?"
- "120 tests is a lot to maintain."

**From an OPERATOR (SRE/DevOps):**
- "This could break in production if prompts appear unexpectedly."
- "Need monitoring for validation failures."
- "What's the support burden?"

#### Recommendations

1. **Flip the default**: Config file first, prompts opt-in (`--interactive`)
2. **Add `gao-dev init`**: Separate setup from run
3. **Implement auto-detection**: Smart defaults, no config needed for common case
4. **Add global preferences**: Most users want same provider everywhere
5. **Make validation optional**: Fast startup by default, validate on demand
6. **Simplify the design**: Start with 1-2 classes, not 4
7. **Reduce test count**: Focus on critical paths, aim for 60-80 tests, not 120
8. **Add "What We're NOT Doing"**: Explicitly bound scope

---

## Priority Issues

### Critical (Must Fix Before Story 35.1)

1. **🔴 Testing estimates optimistic** - Split Story 35.7 or increase points to 13
2. **🔴 Prompt toolkit in CI/CD** - Add lazy import and fallback for headless environments
3. **🔴 YAML injection risk** - Use `yaml.safe_dump()` and sanitize input
4. **🔴 Flip the default** - Make interactive prompts opt-in, not mandatory

### Moderate (Should Fix Before Implementation)

5. **🟡 Windows compatibility** - Add platform-specific details to Architecture
6. **🟡 Ollama timeout** - Increase to 10 seconds with user feedback
7. **🟡 Preference backup** - Implement backup strategy for corruption recovery
8. **🟡 Rollback plan** - Add feature flag and rollback documentation
9. **🟡 Async/sync handling** - Clarify ChatREPL initialization with sync wrapper
10. **🟡 CLI command integration** - Add Story 35.6.1 for other entry points
11. **🟡 TDD approach** - Move tests into each story, not just 35.7
12. **🟡 Parallel work** - Document parallel work strategy for Stories 35.2-35.4
13. **🟡 Global preferences** - Add global config support in Epic 35, not later
14. **🟡 `gao-dev init`** - Consider separate setup command
15. **🟡 Timeline estimate** - Adjust to 1.5-2 weeks instead of 1 week

### Minor (Nice to Have)

16. **🟢 Model selection pagination** - Handle large model lists gracefully
17. **🟢 Mid-session provider switching** - Add to future enhancements
18. **🟢 Business metrics** - Add to success criteria
19. **🟢 API key validation** - Optional format check
20. **🟢 Simplify architecture** - Consider reducing from 4 classes to 2-3

---

## Action Items

### Before Starting Story 35.1

1. **[ ]** DECISION: Make prompts opt-in or keep as default? (Owner: Product Owner)
2. **[ ]** DECISION: Add `gao-dev init` or keep in `gao-dev start`? (Owner: Product Owner)
3. **[ ]** UPDATE: Story 35.7 - Split into two stories or increase to 13 points (Owner: Amelia)
4. **[ ]** UPDATE: Architecture - Add Windows compatibility matrix (Owner: Amelia)
5. **[ ]** UPDATE: Architecture - Add sync wrapper pattern for async operations (Owner: Amelia)
6. **[ ]** ADD: Story 35.6.1 - CLI Command Integration (3 pts) (Owner: Bob)
7. **[ ]** UPDATE: All stories - Include tests in each story (TDD approach) (Owner: Amelia)
8. **[ ]** ADD: Feature flag `features.interactive_provider_selection` (Owner: Amelia)
9. **[ ]** ADD: ROLLBACK.md document (Owner: Amelia)
10. **[ ]** UPDATE: Timeline estimate to 1.5-2 weeks (Owner: Bob)

### During Implementation

11. **[ ]** IMPLEMENT: Lazy import for prompt_toolkit (Owner: Amelia)
12. **[ ]** IMPLEMENT: `yaml.safe_dump()` and input sanitization (Owner: Amelia)
13. **[ ]** IMPLEMENT: Preference file backup strategy (Owner: Amelia)
14. **[ ]** IMPLEMENT: File locking for concurrent writes (Owner: Amelia)
15. **[ ]** IMPLEMENT: Increase Ollama timeout to 10s (Owner: Amelia)
16. **[ ]** TEST: Add CI test for headless environment (Owner: Amelia)
17. **[ ]** TEST: Add security tests for YAML injection (Owner: Amelia)
18. **[ ]** TEST: Test on Windows CMD, PowerShell, Git Bash (Owner: Amelia)

### Before Story 35.7 (Testing)

19. **[ ]** REVIEW: All async operations have timeouts (Owner: Amelia)
20. **[ ]** REVIEW: No circular dependencies (run import checker) (Owner: Amelia)
21. **[ ]** REVIEW: Rich console Windows compatibility enabled (Owner: Amelia)

### Before Story 35.8 (Documentation)

22. **[ ]** WRITE: "Alternatives Considered" section in PRD (Owner: Amelia)
23. **[ ]** WRITE: "What We're NOT Doing" scope boundary (Owner: Amelia)
24. **[ ]** UPDATE: Success criteria with measurable usability metrics (Owner: Product Owner)
25. **[ ]** ADD: Business value metrics to PRD (Owner: Product Owner)

---

## Conclusion

### Overall Assessment

The Interactive Provider Selection feature planning is **comprehensive and demonstrates strong technical thinking**, with detailed requirements, thoughtful architecture, and thorough test planning. The documentation quality is excellent (3,450 lines across 4 documents).

However, the review identified **significant concerns** that should be addressed:

**Major Concerns:**
1. **Complexity vs. Value** - The solution may be overengineered for the problem
2. **Default Behavior** - Forcing prompts on every first-time startup may annoy expert users
3. **Scope** - 39 story points for "prompt user for provider" seems high
4. **Risks** - Several edge cases (CI/CD, YAML injection, validation hanging) not fully addressed
5. **Timeline** - 1 week estimate may be optimistic

**Strengths:**
1. ✅ Excellent documentation quality
2. ✅ Thoughtful component design
3. ✅ Strong focus on testing
4. ✅ Good backward compatibility plan
5. ✅ Comprehensive error handling (once issues addressed)

### Health Score: 7/10

- **Requirements Clarity**: 9/10 ⭐
- **Architecture Quality**: 8/10 ⭐
- **Risk Mitigation**: 5/10 ⚠️
- **Scope Appropriateness**: 6/10 ⚠️
- **Timeline Realism**: 6/10 ⚠️

### Recommendation

**⚠️ PROCEED WITH CAUTION**

Address **Critical (Priority 1)** issues before starting implementation:
1. Decide on default behavior (prompts opt-in vs mandatory)
2. Fix testing estimates (split Story 35.7)
3. Add YAML injection protection
4. Add CI/CD compatibility (lazy imports)

Consider **Moderate (Priority 2)** issues before Story 35.5:
1. Windows compatibility details
2. Rollback plan
3. TDD approach (tests in each story)
4. Global preferences support

**Estimated Timeline Adjustment**: 1.5-2 weeks (not 1 week)

### Next Steps

1. **Product Decision Meeting** - Resolve critical design questions:
   - Prompts: opt-in or default?
   - Command: `gao-dev init` or `gao-dev start --interactive`?
   - Scope: Full feature or phased MVP?

2. **Architecture Refinement** - Address technical issues:
   - Add Windows compatibility matrix
   - Document async/sync handling
   - Add security considerations

3. **Epic Update** - Incorporate findings:
   - Update story points
   - Add Story 35.6.1 (CLI integration)
   - Distribute tests across stories
   - Adjust timeline

4. **Review Meeting** - Present CRAAP findings to team, get consensus

5. **GO/NO-GO Decision** - After addressing critical issues, decide whether to proceed

---

**Review Completed**: 2025-01-12
**Reviewer**: Claude (CRAAP Framework)
**Recommendation**: Address critical issues, then proceed with implementation
**Follow-up Review**: After critical issues resolved, before Story 35.1 begins
