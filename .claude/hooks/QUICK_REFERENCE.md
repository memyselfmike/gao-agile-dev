# Hooks Quick Reference

## What Are Hooks?

**Python scripts** configured in `.claude/settings.json` that inject reminders into Claude's context at key workflow points.

**Success Rate**: 84% (vs 20% with simple instructions)
**Platform**: Cross-platform (Windows, macOS, Linux)

---

## File Structure

```
.claude/
├── settings.json                  # Project settings + hooks (COMMITTED)
├── settings.local.json            # Personal overrides (NOT COMMITTED)
├── settings.local.json.example    # Template (committed)
└── hooks/
    ├── skill-evaluation.py        # UserPromptSubmit hook
    ├── documentation-check.py     # PostToolUse hook (Edit/Write)
    ├── pre-push-validation.py     # PreToolUse hook (git push)
    ├── README.md                  # Full documentation
    ├── QUICK_REFERENCE.md         # This file
    └── TROUBLESHOOTING.md         # Troubleshooting guide
```

---

## The 3 Active Hooks

### 1. Skill Evaluation Hook
**Event**: `UserPromptSubmit`
**Script**: `skill-evaluation.py`
**Does**: Forces YES/NO evaluation of all 7 skills before work starts

### 2. Documentation Check Hook
**Event**: `PostToolUse` (Edit|Write)
**Script**: `documentation-check.py`
**Does**: Checks if documentation needs updating after code changes

### 3. Pre-Push Validation Hook
**Event**: `PreToolUse` (Bash with "git push")
**Script**: `pre-push-validation.py`
**Does**: Requires 8-point validation checklist before pushing

---

## Hook Configuration (.claude/settings.json)

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/skill-evaluation.py",
        "timeout": 10
      }]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/documentation-check.py",
        "timeout": 10
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-push-validation.py",
        "timeout": 10
      }]
    }]
  }
}
```

---

## Expected Hook Output

### Skill Evaluation Hook
```
SKILL EVALUATION:
- story-writing: [YES/NO] - [reason]
- prd-creation: [YES/NO] - [reason]
- architecture-design: [YES/NO] - [reason]
- code-review: [YES/NO] - [reason]
- ui-testing: [YES/NO] - [reason]
- bug-verification: [YES/NO] - [reason]
- documentation: [YES/NO] - [reason]

→ Activating: [skills marked YES]
```

### Documentation Check Hook
```
DOCUMENTATION IMPACT EVALUATION:
- API endpoints: [YES/NO] - [explanation]
- User workflows: [YES/NO] - [explanation]
- Feature docs: [YES/NO] - [explanation]
- Development patterns: [YES/NO] - [explanation]
- Architecture: [YES/NO] - [explanation]
- Examples: [YES/NO] - [explanation]

→ Updating: [affected docs]
```

### Pre-Push Validation Hook
```
PRE-PUSH VALIDATION:
- Installation verification: [PASS/FAIL]
- Test suite: [PASS/FAIL] - [X/Y tests, Z% coverage]
- Type checking: [PASS/FAIL] - [X errors]
- Code formatting: [PASS/FAIL]
- Documentation sync: [PASS/FAIL]
- Workflow status: [PASS/FAIL]
- Commit message: [PASS/FAIL]
- Workflow issues: [PASS/FAIL]

OVERALL STATUS: [READY TO PUSH / NOT READY]
```

---

## Quick Commands

### View Hook Configuration
```bash
cat .claude/settings.json | jq '.hooks'
```

### Test Hook Manually
```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"test.py"}}' | .claude/hooks/documentation-check.sh
```

### Check Scripts Are Executable
```bash
ls -l .claude/hooks/*.sh
```

### Make Scripts Executable
```bash
chmod +x .claude/hooks/*.sh
```

### Disable Hook (Option 1: Comment in JSON)
```json
{
  "hooks": {
    // "UserPromptSubmit": [...]  // Disabled
  }
}
```

### Disable Hook (Option 2: Make Non-Executable)
```bash
chmod -x .claude/hooks/skill-evaluation.sh
```

### Re-Enable Hook
```bash
chmod +x .claude/hooks/skill-evaluation.sh
```

---

## Available Hook Events

| Event | When It Fires |
|-------|---------------|
| **UserPromptSubmit** | When user enters a prompt |
| **PreToolUse** | Before any tool executes |
| **PostToolUse** | After tool completes successfully |
| **PermissionRequest** | When permission dialog shown |
| **Stop** | When main agent completes |
| **SubagentStop** | When task agent finishes |
| **SessionStart** | When Claude Code starts |
| **SessionEnd** | When Claude Code closes |

---

## Hook Input/Output

### Input (JSON via stdin)
```json
{
  "session_id": "abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "/path/to/file.py" }
}
```

### Parse with jq
```bash
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
```

### Exit Codes
- **Exit 0**: Success - stdout injected as `<system-reminder>`
- **Exit 2**: Blocking error - stderr shown, tool blocked
- **Other**: Non-blocking error - logged in verbose mode

---

## Performance Impact

| Hook | Time Added | Value Gained |
|------|------------|--------------|
| Skill Evaluation | ~2-3 sec | 84% skill activation |
| Documentation Check | ~1-2 sec | Current docs |
| Pre-Push Validation | ~5-10 sec | No broken pushes |
| **Total** | **<5% dev time** | **Consistent quality** |

---

## Common Scenarios

### "Claude isn't using the right skills"
**Solution**: Check UserPromptSubmit hook is configured and script is executable

### "Documentation is out of date"
**Solution**: Check PostToolUse hook is configured for Edit|Write

### "Bad code got pushed"
**Solution**: Check PreToolUse hook is configured for Bash commands

### "Hook not triggering"
**Solutions**:
1. Check `.claude/settings.json` syntax (valid JSON?)
2. Verify script executable: `ls -l .claude/hooks/*.sh`
3. Restart Claude Code session
4. Enable debug: `claude --debug`

### "I want to skip a hook this once"
**Solutions**:
1. Comment out in `settings.json`
2. Make script non-executable temporarily
3. Use settings.local.json override

---

## The Forced Eval Pattern (Why It Works)

Based on Scott Spence's research:

| Approach | Success Rate |
|----------|--------------|
| **Forced Eval Hook** | **84%** ✅ |
| LLM Eval Alternative | 80% |
| Simple Instruction | 20% |
| No Hook | 50% |

**Why 84%?**
1. **EVALUATE** - Explicit YES/NO for each check
2. **ACTIVATE** - Mandatory tool/skill invocation
3. **IMPLEMENT** - Blocked until 1 & 2 complete
4. **Aggressive language** - MANDATORY, CRITICAL, MUST

---

## Debugging One-Liners

```bash
# Check hook configuration
cat .claude/settings.json | jq '.hooks'

# View hook script
cat .claude/hooks/skill-evaluation.sh

# Test hook manually
echo '{"tool_name":"Edit","tool_input":{"file_path":"gao_dev/test.py"}}' | .claude/hooks/documentation-check.sh

# Check scripts are executable
ls -l .claude/hooks/*.sh

# Make all scripts executable
chmod +x .claude/hooks/*.sh

# View hook output in conversation
# Look for <system-reminder> tags in Claude's responses

# Enable debug mode
claude --debug

# Validate settings.json syntax
cat .claude/settings.json | jq '.'
```

---

## Environment Variables in Hooks

- **`$CLAUDE_PROJECT_DIR`** - Project root path (use this for portable paths)
- **`$CLAUDE_ENV_FILE`** - Environment file path
- **`$CLAUDE_CODE_REMOTE`** - "true" for web, empty for CLI

---

## Security Best Practices

```bash
# Good - quote variables
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Good - validate inputs
if [[ "$FILE_PATH" =~ \.\. ]]; then
  echo "Path traversal detected" >&2
  exit 2
fi

# Good - use absolute paths
"$CLAUDE_PROJECT_DIR"/.claude/hooks/script.sh

# Bad - no quotes
FILE_PATH=$(echo $INPUT | jq -r .tool_input.file_path)

# Bad - no validation
# (directly use user input)

# Bad - relative paths
./hooks/script.sh
```

---

## Customizing Hooks

### Modify Hook Script
1. Edit `.claude/hooks/script.sh`
2. Change output text in `cat <<'EOF'` block
3. Save file
4. Restart Claude Code session

### Modify Hook Configuration
1. Edit `.claude/settings.json`
2. Change `matcher`, `timeout`, or event type
3. Validate JSON syntax: `cat .claude/settings.json | jq '.'`
4. Restart Claude Code session

---

## Files Reference

- **`.claude/settings.json`** - Hook configuration (COMMIT THIS)
- **`.claude/settings.local.json`** - Local overrides (DO NOT COMMIT)
- **`.claude/hooks/skill-evaluation.sh`** - UserPromptSubmit hook
- **`.claude/hooks/documentation-check.sh`** - PostToolUse hook
- **`.claude/hooks/pre-push-validation.sh`** - PreToolUse hook
- **`.claude/hooks/README.md`** - Full documentation
- **`.claude/hooks/QUICK_REFERENCE.md`** - This file

---

## Version

**v2.0** (2025-01-22) - Official Claude Code hooks system implementation

**Breaking change from v1.0**: Now using .sh scripts + settings.json (not .md files)

---

**Full docs**: `.claude/hooks/README.md`

**Official docs**: [code.claude.com/docs/en/hooks.md](https://code.claude.com/docs/en/hooks.md)
