# GAO-Dev Claude Code Hooks System

This directory contains Claude Code hooks that enforce best practices and ensure quality standards throughout the development workflow.

## Overview

Hooks are automated checks configured in `.claude/settings.json` that trigger at specific points in the development workflow. They execute shell scripts that inject reminders into Claude's context, ensuring consistent adherence to GAO-Dev standards.

## Hook Architecture

### Configuration Files

Claude Code settings follow a hierarchical structure similar to `.env` files:

**`.claude/settings.json`** (project-level, **committed to git**):
```json
{
  "hooks": {
    "UserPromptSubmit": [...],
    "PostToolUse": [...],
    "PreToolUse": [...]
  },
  "permissions": {
    "allow": [/* shared team permissions */]
  }
}
```
- Shared hooks configuration
- Project-level permissions
- Team standards
- **Committed to version control**

**`.claude/settings.local.json`** (local, **NOT committed**):
```json
{
  "permissions": {
    "allow": [/* personal overrides */]
  }
}
```
- User-specific permission overrides
- Local preferences
- **In `.gitignore`** - never committed
- Overrides settings from `settings.json`

**`.claude/settings.local.json.example`** (template, committed):
- Example template showing what can be customized
- Reference for new developers
- Copy to `settings.local.json` to customize

### Hook Scripts

Hooks reference executable Python scripts in `.claude/hooks/`:

```
.claude/hooks/
├── skill-evaluation.py            # UserPromptSubmit hook
├── documentation-check.py         # PostToolUse hook (Edit/Write)
├── pre-push-validation.py         # PreToolUse hook (git push)
├── README.md                      # This file
├── QUICK_REFERENCE.md             # One-page guide
└── TROUBLESHOOTING.md             # Troubleshooting guide
```

## Active Hooks

### 1. Skill Evaluation Hook (`skill-evaluation.py`)

**Event**: `UserPromptSubmit`
**Triggers**: Every time user submits a prompt
**Timeout**: 10 seconds

**Purpose**: Forces evaluation and activation of appropriate skills before work begins

**Configuration**:
```json
{
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/skill-evaluation.py",
          "timeout": 10
        }
      ]
    }
  ]
}
```

**Output**: Injects a system reminder requiring:
1. YES/NO evaluation of all 7 skills with reasoning
2. Activation of all "YES" skills using `Skill()` tool
3. Only then proceeding with implementation

**Success Rate**: 84% (forced eval pattern)

---

### 2. Documentation Check Hook (`documentation-check.py`)

**Event**: `PostToolUse`
**Triggers**: After Edit or Write operations on implementation files
**Timeout**: 10 seconds

**Purpose**: Ensures documentation stays synchronized with code changes

**Configuration**:
```json
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/documentation-check.py",
          "timeout": 10
        }
      ]
    }
  ]
}
```

**Triggers Only For**:
- Files matching: `*.py`, `*.ts`, `*.tsx`, `*.js`, `*.jsx`, `*.yaml`, `*.json`
- In directories: `gao_dev/`, `src/`

**Output**: Injects a reminder to evaluate impact on 6 documentation categories and activate documentation skill if needed

---

### 3. Pre-Push Validation Hook (`pre-push-validation.py`)

**Event**: `PreToolUse`
**Triggers**: Before any `git push` command
**Timeout**: 10 seconds

**Purpose**: Ensures comprehensive validation before code reaches remote repository

**Configuration**:
```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-push-validation.py",
          "timeout": 10
        }
      ]
    }
  ]
}
```

**Validates**:
1. Installation verification (all [PASS])
2. Test suite (≥80% coverage, 0 failures)
3. Type checking (0 errors)
4. Code formatting (Black compliance)
5. Documentation sync
6. Workflow status accuracy
7. Commit message format
8. Workflow issues

**Output**: Requires explicit validation checklist output before allowing push

---

## How Hooks Work

### 1. Configuration

Hooks are defined in `.claude/settings.json`:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

**Key Elements**:
- **EventName**: When hook triggers (UserPromptSubmit, PreToolUse, PostToolUse, etc.)
- **matcher**: Regex pattern for which tools trigger the hook ("Edit|Write", "Bash", "" for all)
- **type**: "command" (execute script) or "prompt" (query Claude Haiku)
- **command**: Shell script path (use `$CLAUDE_PROJECT_DIR` for portability)
- **timeout**: Max execution time in seconds

### 2. Execution

When a hook triggers:
1. Claude Code executes the shell script
2. Script receives JSON input via stdin (session info, tool parameters, etc.)
3. Script outputs text to stdout
4. Claude Code injects output as `<system-reminder>` into Claude's context
5. Claude must respond to the reminder before proceeding

### 3. Exit Codes

- **Exit 0**: Success - stdout injected as context
- **Exit 2**: Blocking error - stderr shown, tool call blocked
- **Other**: Non-blocking error - logged in verbose mode

### 4. Environment Variables

Available in hook scripts:
- **`$CLAUDE_PROJECT_DIR`**: Project root path
- **`$CLAUDE_ENV_FILE`**: Environment file path (SessionStart only)
- **`$CLAUDE_CODE_REMOTE`**: "true" for web, empty for CLI

## The Forced Evaluation Pattern (84% Success Rate)

Based on [Scott Spence's research](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably):

| Approach | Success Rate |
|----------|--------------|
| **Forced Eval Hook** | **84%** |
| LLM Eval Alternative | 80% |
| Simple Instruction | 20% |
| No Hook | 50% |

### Why It Works

The pattern creates a **commitment mechanism**:

1. **EVALUATE**: Claude must explicitly state YES/NO for each check with reasoning
2. **ACTIVATE**: Claude must invoke required tools/skills immediately
3. **IMPLEMENT**: Work can only proceed after steps 1 & 2

**Critical Success Factors**:
- Aggressive language (MANDATORY, CRITICAL, MUST)
- Explicit output format requirements
- Blocking implementation until evaluation complete
- <system-reminder> tags with high priority

## Configuration Management

### Disable Hook Temporarily

**Option 1**: Comment out in settings.json
```json
{
  "hooks": {
    // "UserPromptSubmit": [...]  // Disabled
  }
}
```

**Option 2**: Make script non-executable (Unix/Linux/macOS only)
```bash
chmod -x .claude/hooks/skill-evaluation.py
```

### Re-Enable Hook

**Option 1**: Uncomment in settings.json
**Option 2**: Make script executable (Unix/Linux/macOS only)
```bash
chmod +x .claude/hooks/skill-evaluation.py
```

### Modify Hook Behavior

Edit the Python script in `.claude/hooks/`:
1. Change the output text in the `print()` statement
2. Adjust evaluation criteria or filtering logic
3. Modify aggressiveness of language
4. Save the file
5. Hook changes take effect immediately in next Claude Code session

## Available Hook Events

From official Claude Code documentation:

| Event | When It Fires |
|-------|---------------|
| **PreToolUse** | Before any tool executes |
| **PostToolUse** | After tool completes successfully |
| **PermissionRequest** | When permission dialog shown |
| **UserPromptSubmit** | When user enters a prompt |
| **Stop** | When main agent completes |
| **SubagentStop** | When task agent finishes |
| **SessionStart** | When Claude Code starts |
| **SessionEnd** | When Claude Code closes |
| **Notification** | When notifications sent |

## Hook Input Format

Hooks receive JSON via stdin:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/conversation.jsonl",
  "cwd": "/current/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "..."
  }
}
```

**Access with jq**:
```bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
```

## Performance Impact

Hooks add minimal overhead:

| Hook | Time Added | Value Gained |
|------|------------|--------------|
| Skill Evaluation | ~2-3 sec | 84% skill activation rate |
| Documentation Check | ~1-2 sec | Current documentation |
| Pre-Push Validation | ~5-10 sec (reminder only) | No broken pushes |
| **Total** | **<5% dev time** | **Consistent quality** |

## Debugging Hooks

### Check Hook Configuration
```bash
cat .claude/settings.json | jq '.hooks'
```

### Test Hook Script Manually
```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"test.py"}}' | python .claude/hooks/documentation-check.py
```

### View Hook Output
Claude Code injects hook output as `<system-reminder>` tags in the conversation. Look for these in Claude's responses.

### Enable Debug Mode
```bash
claude --debug
```

Shows:
```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Found 1 hook commands to execute
[DEBUG] Hook command completed with status 0
```

## Best Practices

### For Hook Scripts

1. **Use Python for cross-platform compatibility** (Windows, macOS, Linux)
2. **Always exit with proper codes** (`sys.exit(0)` = success, `sys.exit(2)` = block)
3. **Parse JSON input safely** with try/except for robustness
4. **Use `$CLAUDE_PROJECT_DIR`** in settings.json for portable paths
5. **Keep timeout reasonable** (10-30 seconds)
6. **Output clear, actionable reminders**
7. **Use aggressive language** (MANDATORY, CRITICAL)
8. **Test thoroughly** using manual input before deployment

### For Hook Configuration

1. **Use `.claude/settings.json`** for team hooks (committed to git)
2. **Use `.claude/settings.local.json`** for personal overrides (NOT committed)
3. **Document all hooks** in README
4. **Version control settings.json** (commit to git)
5. **Never commit settings.local.json** (add to .gitignore)
6. **Provide settings.local.json.example** as a template for new developers

## Troubleshooting

### Hook Not Triggering

**Problem**: Hook doesn't seem to activate

**Solutions**:
- Check `.claude/settings.json` syntax (valid JSON?)
- Verify script is executable and Python is available: `python --version`
- Check matcher pattern matches tool name
- Test script manually: `echo '{}' | python .claude/hooks/script.py`
- Restart Claude Code session
- Enable debug mode (if available)

### Hook Output Not Showing

**Problem**: Script runs but output not visible

**Solutions**:
- Check exit code is 0
- Verify output goes to stdout (not stderr)
- Look for `<system-reminder>` tags in conversation
- Check timeout is sufficient

### Hook Blocking Tool Use

**Problem**: Hook prevents tool from executing

**Solutions**:
- Check if script exits with code 2 (blocking)
- Review script logic for errors
- Check timeout isn't exceeded
- Test script manually with sample input

## Security Considerations

### Input Validation

Always validate and sanitize inputs from hook JSON:

```python
# Good - validates before use
import json, sys, os

input_data = json.load(sys.stdin)
file_path = input_data.get("tool_input", {}).get("file_path", "")

if ".." in file_path or os.path.isabs(file_path):
    print("Path traversal detected", file=sys.stderr)
    sys.exit(2)
```

### Avoid Sensitive Files

Never hook operations on:
- `.env` files
- `.git/` directory
- Private keys
- Credentials

### Use Absolute Paths

Always reference `$CLAUDE_PROJECT_DIR` in settings.json:

```json
// Good - uses environment variable
{
  "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/script.py"
}

// Bad - relative paths unreliable
{
  "command": "python ./hooks/script.py"
}
```

## Integration with GAO-Dev

The hooks system integrates with:

### Skills
- Activates skills (story-writing, prd-creation, architecture-design, code-review, ui-testing, bug-verification, documentation)
- Uses `Skill()` tool in activation step

### Development Workflow
- Enforces TodoWrite usage
- Ensures test-first development
- Validates commit messages
- Maintains documentation

### Quality Standards
- 80%+ test coverage
- Type safety (no `any`)
- Code formatting (Black)
- Error handling

## Version History

### v3.0 (2025-01-22)
- **BREAKING CHANGE**: Converted hooks to Python for cross-platform compatibility
- Python scripts (`.py`) replace bash scripts (`.sh`) for Windows support
- Improved error handling with try/except for JSON parsing
- Cross-platform testing verified
- Cleaned up unnecessary archive and helper files

### v2.0 (2025-01-22)
- **BREAKING CHANGE**: Converted to official Claude Code hooks system
- Hooks now configured in `.claude/settings.json`
- Shell scripts (.sh) instead of markdown (.md)
- Proper event system (UserPromptSubmit, PreToolUse, PostToolUse)
- JSON input via stdin
- Exit code-based flow control
- Archived old markdown hooks

### v1.0 (2025-01-22)
- Initial implementation (incorrect - used markdown files)
- 3 core hooks (user-prompt-submit, post-edit, pre-push)
- Forced eval pattern implementation

## References

- **Official Claude Code Hooks Documentation**: [code.claude.com/docs/en/hooks.md](https://code.claude.com/docs/en/hooks.md)
- **Forced Eval Hook Pattern**: [Scott Spence's Research](https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably)
- **GAO-Dev Standards**: `CLAUDE.md`
- **Skills System**: `.claude/AGENTS_AND_SKILLS_README.md`

---

**Remember**: Hooks are your quality safety net. They ensure best practices are followed consistently, using the official Claude Code hooks system with 84% effectiveness.
