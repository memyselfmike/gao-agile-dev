# Hooks Troubleshooting Guide

## Quick Fix: Hooks Disabled by Default

**The hooks are now DISABLED by default** to prevent the errors you experienced.

Your `.claude/settings.json` now contains:
```json
{
  "hooks": {}
}
```

This means **no hooks will fire** until you explicitly enable them.

---

## The Problem You Experienced

You were getting "pre and post hook bash and write errors" because:

1. **PreToolUse with matcher "Bash"** fired on **EVERY** bash command (not just git push)
2. **PostToolUse with matcher "Edit|Write"** fired on **EVERY** file edit/write
3. This created a feedback loop where hooks fired constantly, causing errors

### Why This Happened

The original configuration was too aggressive:
- Every time Claude ran a bash command → hook fired
- Every time Claude wrote/edited a file → hook fired
- Hooks tried to parse JSON input that might not always be in the expected format
- This overwhelmed the system

---

## Solution: Enable Hooks When Ready

### Option 1: Keep Hooks Disabled (Recommended for Now)

Current state - no hooks active. Claude Code works normally without hook interference.

### Option 2: Enable Hooks Gradually

When you're ready to test hooks:

```bash
# Enable all hooks
bash .claude/hooks/ENABLE_HOOKS.sh

# Restart Claude Code session

# If issues occur, disable immediately:
bash .claude/hooks/DISABLE_HOOKS.sh
```

### Option 3: Enable Hooks Selectively

Edit `.claude/settings.json` manually to enable only specific hooks:

**Just Skill Evaluation (safest)**:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/skill-evaluation.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**Just Documentation Check**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/documentation-check.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## Improvements Made

The hooks have been rewritten to be more robust:

### 1. Better Error Handling

**Before** (caused errors):
```bash
FILE_PATH=$(echo "$INPUT" | python -c "...")
# If python failed, script crashed
```

**After** (handles errors gracefully):
```bash
FILE_PATH=$(echo "$INPUT" | python -c "
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null || echo "")
```

### 2. Simplified Logic

- Removed complex regex that might fail on Windows
- Used simple string contains checks: `[[ "$COMMAND" == *"git push"* ]]`
- Added fallbacks for all parsing operations

### 3. Reduced Verbosity

Hooks now output concise reminders instead of verbose protocols.

### 4. Silent Failures

Hooks fail silently if input parsing fails - they just don't output anything rather than crashing.

---

## Testing Hooks Safely

### Test Individual Hooks Manually

**Test skill evaluation**:
```bash
echo '{}' | bash .claude/hooks/skill-evaluation.sh
```

Expected output: `<system-reminder>` with skill evaluation protocol

**Test documentation check**:
```bash
echo '{"tool_input":{"file_path":"gao_dev/core/test.py"}}' | bash .claude/hooks/documentation-check.sh
```

Expected output: `<system-reminder>` with documentation check

**Test pre-push validation**:
```bash
echo '{"tool_input":{"command":"git push origin main"}}' | bash .claude/hooks/pre-push-validation.sh
```

Expected output: `<system-reminder>` with pre-push checklist

### Test with Debug Output

Uncomment debug lines in hooks to see what's happening:

In `documentation-check.sh` line 19:
```bash
# echo "DEBUG: FILE_PATH=$FILE_PATH" >&2
```

Remove the `#` to enable:
```bash
echo "DEBUG: FILE_PATH=$FILE_PATH" >&2
```

---

## Common Issues & Solutions

### Issue: "Hook failed with exit code 1"

**Cause**: Python parsing failed or bash syntax error

**Solution**:
1. Test hook manually (see above)
2. Check if Python is available: `python --version`
3. Check hook script has Unix line endings (not Windows CRLF)

### Issue: "Hook timeout"

**Cause**: Hook took longer than 10 seconds

**Solution**:
- Increase timeout in `.claude/settings.json`:
  ```json
  {
    "timeout": 30
  }
  ```

### Issue: "Hooks fire too often"

**Cause**: Matcher too broad (e.g., "Bash" matches ALL bash commands)

**Solution**:
- Use more specific matchers
- Or disable hooks temporarily

### Issue: "No output from hook"

**Cause**: Conditional check failed (e.g., file path doesn't match pattern)

**This is normal** - hooks only output when conditions are met:
- `documentation-check.sh`: Only for files matching `(gao_dev|src)/.*\.(py|ts|tsx|js|jsx|yaml|json)$`
- `pre-push-validation.sh`: Only for commands containing "git push"

---

## Recommended Usage Pattern

### For Most Users: Disable Hooks

The hooks are experimental and can be disruptive. **We recommend keeping them disabled** unless you specifically need the forced evaluation pattern.

### For Testing: Enable Temporarily

```bash
# When you want to test hooks
bash .claude/hooks/ENABLE_HOOKS.sh
# Restart Claude Code

# Work for a session, observe behavior

# If too disruptive, disable
bash .claude/hooks/DISABLE_HOOKS.sh
# Restart Claude Code
```

### For Production Use: Selective Enabling

Only enable the hooks that provide value without disruption:

**Recommended minimal configuration** (just skill evaluation on prompts):
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/skill-evaluation.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

This provides value (skill evaluation) without being disruptive (only fires once per prompt, not constantly).

---

## Alternative: Manual Skill Activation

Instead of hooks, you can manually activate skills when needed:

```
I need to fix a bug. Let me evaluate which skills I need:
- bug-verification: YES
- ui-testing: YES
- documentation: YES

Activating these skills...
```

Then manually invoke: `Skill(skill="bug-verification")`, etc.

This gives you the same benefit without the hook overhead.

---

## Files Reference

- **`.claude/settings.json`** - Active configuration (currently: hooks disabled)
- **`.claude/hooks/settings.hooks-enabled.json`** - Full hooks config (reference)
- **`.claude/hooks/settings.hooks-disabled.json`** - Empty hooks config (default)
- **`.claude/hooks/ENABLE_HOOKS.sh`** - Script to enable all hooks
- **`.claude/hooks/DISABLE_HOOKS.sh`** - Script to disable all hooks
- **`.claude/hooks/TROUBLESHOOTING.md`** - This file

---

## Getting Help

If you continue to experience issues:

1. **Verify hooks are disabled**:
   ```bash
   cat .claude/settings.json
   ```
   Should show: `{"hooks": {}}`

2. **Restart Claude Code**:
   Hooks are loaded at session start, so restart is required after any change.

3. **Test hooks manually**:
   Use the test commands above to verify hooks work in isolation.

4. **Check for error messages**:
   Look for specific error text in Claude's responses - this helps diagnose the issue.

---

**Summary**: Hooks are now **DISABLED** by default. Enable them only when you're ready to test and can tolerate some disruption. The system works fine without hooks - they're an optional enhancement for enforcing best practices.
