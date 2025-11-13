# Interactive Provider Selection - Troubleshooting Guide

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Table of Contents

- [CLI Issues](#cli-issues)
- [Validation Failures](#validation-failures)
- [Permission Errors](#permission-errors)
- [Corrupted Preferences](#corrupted-preferences)
- [Headless Environment Issues](#headless-environment-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)

---

## CLI Issues

### Issue: "claude CLI not found in PATH"

**Symptom**:
```
Validating claude-code...
Checking claude CLI availability...
✗ Error: claude CLI not found
```

**Cause**: Claude Code CLI is not installed or not in system PATH.

**Solution 1**: Install Claude Code CLI:
```bash
npm install -g @anthropic/claude-code
```

**Solution 2**: Verify installation:
```bash
claude --version
# Should output: Claude Code CLI v1.x.x
```

**Solution 3**: Add to PATH (if installed but not in PATH):
```bash
# Find installation location
npm list -g @anthropic/claude-code

# Add to PATH (Unix/macOS ~/.bashrc or ~/.zshrc)
export PATH=$PATH:/path/to/claude/bin

# Add to PATH (Windows)
# System Properties > Environment Variables > Path > Edit > Add path
```

**Solution 4**: Use different provider temporarily:
```bash
AGENT_PROVIDER=direct-api-anthropic gao-dev start
```

---

### Issue: "opencode CLI not found in PATH"

**Symptom**:
```
Validating opencode...
Checking opencode CLI availability...
✗ Error: opencode CLI not found
```

**Cause**: OpenCode CLI is not installed.

**Solution 1**: Install OpenCode CLI:
```bash
npm install -g opencode
```

**Solution 2**: Verify installation:
```bash
opencode --version
# Should output: OpenCode CLI v1.x.x
```

**Solution 3**: Alternative installation:
```bash
# Clone from GitHub
git clone https://github.com/opencodetools/opencode
cd opencode
npm install -g .
```

**Solution 4**: Check npm global directory:
```bash
# Unix/macOS
npm config get prefix
# Should output: /usr/local or similar

# Windows
npm config get prefix
# Should output: C:\Users\<name>\AppData\Roaming\npm
```

---

## Validation Failures

### Issue: "ANTHROPIC_API_KEY not set"

**Symptom**:
```
Validating claude-code...
✗ Error: ANTHROPIC_API_KEY not set
```

**Cause**: API key environment variable is not set.

**Solution 1**: Set API key:
```bash
# Unix/macOS/Linux
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-api03-...

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**Solution 2**: Make permanent (Unix/macOS):
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY=sk-ant-api03-...' >> ~/.bashrc
source ~/.bashrc
```

**Solution 3**: Make permanent (Windows):
```powershell
# PowerShell (user-level)
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-api03-...", "User")

# PowerShell (system-level, requires admin)
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-api03-...", "Machine")
```

**Solution 4**: Get API key:
Visit [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) to generate a new API key.

---

### Issue: "No Ollama models found"

**Symptom**:
```
Checking Ollama models...
Detecting Ollama models (may take a moment)...
✗ Warning: No Ollama models found
```

**Cause**: Ollama is not installed, not running, or no models are pulled.

**Solution 1**: Install Ollama:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/download | sh

# Windows
# Download from https://ollama.ai/download
```

**Solution 2**: Start Ollama service:
```bash
ollama serve
# Should output: Listening on http://127.0.0.1:11434
```

**Solution 3**: Pull a model:
```bash
# Recommended for coding
ollama pull deepseek-r1

# Check models
ollama list
# Should show at least one model
```

**Solution 4**: Check Ollama status:
```bash
# Test Ollama API
curl http://localhost:11434/api/tags
# Should return JSON with models list
```

**Solution 5**: Use cloud provider instead:
```
OpenCode Configuration
Use local model via Ollama? [y/N]: n
```

---

### Issue: Validation timeout

**Symptom**:
```
Detecting Ollama models (may take a moment)...
[Hangs for 10 seconds]
Validation timeout
```

**Cause**: Slow disk (HDD/NAS) or large number of models.

**Solution 1**: Wait for timeout (10 seconds max):
The system will continue after timeout, prompting for manual model entry.

**Solution 2**: Use SSD:
Move Ollama models to SSD for faster detection:
```bash
# Check Ollama model location
ollama list

# Move models to SSD (advanced)
# Stop Ollama, move ~/.ollama to SSD, create symlink
```

**Solution 3**: Reduce model count:
```bash
# Remove unused models
ollama rm model-name
```

**Solution 4**: Use environment variable to bypass:
```bash
export AGENT_PROVIDER=opencode:deepseek-r1
gao-dev start  # Skips detection
```

---

## Permission Errors

### Issue: "Permission denied" when saving preferences

**Symptom**:
```
Failed to save preferences: [Errno 13] Permission denied: '.gao-dev/provider_preferences.yaml'
```

**Cause**: Insufficient permissions for `.gao-dev/` directory.

**Solution 1**: Check permissions:
```bash
ls -la .gao-dev/
# Should show: drwx------ (0700) for directory
# Should show: -rw------- (0600) for files
```

**Solution 2**: Fix directory permissions:
```bash
chmod 700 .gao-dev/
chmod 600 .gao-dev/provider_preferences.yaml
```

**Solution 3**: Check ownership:
```bash
ls -la .gao-dev/
# Should show your username as owner

# Fix ownership if wrong
sudo chown -R $USER:$USER .gao-dev/
```

**Solution 4**: Recreate directory:
```bash
rm -rf .gao-dev/
mkdir .gao-dev
gao-dev start  # Will recreate with correct permissions
```

---

### Issue: "Cannot create .gao-dev directory"

**Symptom**:
```
Failed to create .gao-dev directory: [Errno 13] Permission denied
```

**Cause**: No write permissions in project directory.

**Solution 1**: Check project directory permissions:
```bash
ls -la
# Should show write permissions (w) for user
```

**Solution 2**: Change to writable directory:
```bash
cd ~/my-projects/gao-project
gao-dev start
```

**Solution 3**: Run as correct user:
```bash
# Don't use sudo with gao-dev!
# Instead, fix project ownership:
sudo chown -R $USER:$USER ~/my-projects/gao-project
```

---

## Corrupted Preferences

### Issue: "Invalid YAML in preferences file"

**Symptom**:
```
Preferences file corrupt, attempting backup...
✗ Error: Invalid YAML in preferences file
```

**Cause**: Preferences file has invalid YAML syntax.

**Solution 1**: Delete and regenerate:
```bash
rm .gao-dev/provider_preferences.yaml
gao-dev start  # Triggers fresh setup
```

**Solution 2**: Restore from backup:
```bash
cp .gao-dev/provider_preferences.yaml.bak .gao-dev/provider_preferences.yaml
gao-dev start
```

**Solution 3**: Manually fix YAML:
```bash
# Edit file
nano .gao-dev/provider_preferences.yaml

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.gao-dev/provider_preferences.yaml'))"
```

**Solution 4**: Check for common YAML errors:
- Missing quotes around strings with special characters
- Incorrect indentation (use spaces, not tabs)
- Missing colons after keys
- Unbalanced brackets/braces

---

### Issue: Backup file also corrupted

**Symptom**:
```
Main preferences file corrupt, attempting backup...
✗ Error: Backup file also corrupt
```

**Cause**: Both main and backup files are invalid.

**Solution**: Delete both and start fresh:
```bash
rm .gao-dev/provider_preferences.yaml*
gao-dev start  # Triggers first-time setup
```

---

## Headless Environment Issues

### Issue: "No TTY available" in Docker/CI

**Symptom**:
```
OSError: No TTY available for interactive prompts
```

**Cause**: Running in headless environment without terminal.

**Solution 1**: Set environment variable (recommended):
```bash
# In Dockerfile
ENV AGENT_PROVIDER=claude-code

# In docker-compose.yml
environment:
  AGENT_PROVIDER: claude-code

# In CI config
env:
  AGENT_PROVIDER: claude-code
```

**Solution 2**: System automatically falls back to basic input():
The system should handle this automatically. If not, check logs:
```bash
# Check if fallback triggered
gao-dev start 2>&1 | grep "prompt_toolkit unavailable"
```

**Solution 3**: Disable feature in CI:
```yaml
# gao_dev/config/defaults.yaml (for CI image)
features:
  interactive_provider_selection: false
```

**Solution 4**: Use non-interactive mode (if available):
```bash
gao-dev start --non-interactive --provider claude-code
```

---

### Issue: ImportError for prompt_toolkit in CI

**Symptom**:
```
ImportError: No module named 'prompt_toolkit'
```

**Cause**: prompt_toolkit not installed in CI environment.

**Solution 1**: Install dependencies:
```bash
# In CI script
pip install -r requirements.txt
```

**Solution 2**: Use env var to bypass prompts:
```yaml
# CI config
env:
  AGENT_PROVIDER: claude-code
```

**Solution 3**: Lazy import should handle this automatically:
Check if gao_dev/cli/interactive_prompter.py uses lazy imports (it should).

---

## Performance Issues

### Issue: Slow startup (>5 seconds)

**Symptom**: Provider selection takes longer than 5 seconds.

**Cause**: Multiple factors - slow disk, network latency, Ollama detection.

**Diagnosis**:
```bash
# Time the startup
time gao-dev start
```

**Solution 1**: Use environment variable to skip prompts:
```bash
export AGENT_PROVIDER=claude-code
time gao-dev start  # Should be <2 seconds
```

**Solution 2**: Use saved preferences:
```
# First run (slow due to prompts)
gao-dev start

# Subsequent runs (fast)
gao-dev start  # <1 second
```

**Solution 3**: Optimize Ollama detection:
```bash
# Reduce model count
ollama rm unused-model

# Use SSD instead of HDD
# Move ~/.ollama to SSD location
```

**Solution 4**: Disable slow validations (advanced):
Edit `gao_dev/cli/provider_validator.py` and reduce timeout values.

---

### Issue: High memory usage during validation

**Symptom**: Memory spikes during provider validation.

**Cause**: Large models or multiple concurrent validations.

**Solution 1**: Close other applications:
```bash
# Check memory
free -h  # Linux
top  # Unix/macOS
tasklist  # Windows
```

**Solution 2**: Use smaller models:
```bash
# Use 7B models instead of 13B+
ollama pull deepseek-r1  # 7B
# Instead of codellama:34b (34B)
```

**Solution 3**: Validate one provider at a time:
System already validates sequentially. If issues persist, restart machine.

---

## Integration Issues

### Issue: ProcessExecutor fails to create provider

**Symptom**:
```
Failed to create ProcessExecutor: Provider 'opencode' not found in factory
```

**Cause**: Provider not registered in ProviderFactory.

**Solution 1**: Check provider spelling:
```python
# Valid providers:
# - claude-code
# - opencode or opencode-cli
# - direct-api-anthropic
```

**Solution 2**: Verify ProviderFactory registration:
```python
# In gao_dev/core/providers/factory.py
factory = ProviderFactory()
print(factory.list_providers())
# Should include your provider
```

**Solution 3**: Re-register provider (if custom):
```python
from gao_dev.core.providers.factory import ProviderFactory
factory.register_provider("my-provider", MyProviderClass)
```

---

### Issue: Selected provider not used by REPL

**Symptom**: REPL starts but uses different provider than selected.

**Cause**: Environment variable override or ProcessExecutor misconfiguration.

**Solution 1**: Check environment variables:
```bash
env | grep AGENT_PROVIDER
# Unset if wrong
unset AGENT_PROVIDER
```

**Solution 2**: Verify ProcessExecutor initialization:
Check that ChatREPL passes provider_config correctly to ProcessExecutor.

**Solution 3**: Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
gao-dev start 2>&1 | grep provider
```

---

## Getting More Help

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run command
gao-dev start 2>&1 | tee gao-dev-debug.log

# Share log file when reporting issues
```

### Check System Information

```bash
# GAO-Dev version
gao-dev --version

# Python version
python --version

# OS information
uname -a  # Unix/macOS
systeminfo  # Windows

# Environment
env | grep -E 'AGENT_PROVIDER|ANTHROPIC|OPENAI|GOOGLE'
```

### Report a Bug

When reporting issues, include:

1. **Error message** (exact text)
2. **Command used** (full command with options)
3. **Environment** (OS, Python version, GAO-Dev version)
4. **Debug log** (if available)
5. **Steps to reproduce**

**GitHub Issues**: [Report here](https://github.com/your-org/gao-agile-dev/issues)

**Format**:
```markdown
## Issue Description
[Describe the problem]

## Steps to Reproduce
1. Run `gao-dev start`
2. Select provider...
3. Error occurs...

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.5
- GAO-Dev: 1.0.0
- Provider: claude-code

## Debug Log
```
[Paste log here]
```
```

---

## Related Documentation

- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md) for step-by-step instructions
- **FAQ**: [FAQ.md](FAQ.md) for common questions
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md) for developers
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Version**: 1.0
**Last Updated**: 2025-01-12
**Epic**: 35 - Interactive Provider Selection at Startup
