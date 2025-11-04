# OpenCode CLI Reference

**Version**: OpenCode v0.1.x
**Target**: GAO-Dev developers
**Last Updated**: 2025-11-04

---

## Table of Contents

1. [Command Overview](#command-overview)
2. [Command Details](#command-details)
3. [Global Flags](#global-flags)
4. [Model Selection](#model-selection)
5. [Output Formats](#output-formats)
6. [Examples](#examples)
7. [Exit Codes](#exit-codes)

---

## Command Overview

OpenCode provides multiple command modes for different use cases:

| Command | Purpose | GAO-Dev Usage |
|---------|---------|---------------|
| `opencode [project]` | Interactive TUI | ❌ Not used |
| `opencode run` | Non-interactive execution | ✅ **Primary** |
| `opencode serve` | HTTP API server | 🔄 Potential future |
| `opencode models` | List available models | ✅ Validation |
| `opencode auth` | Manage API keys | ✅ Setup |
| `opencode agent create` | Create custom agents | 🔄 Potential future |
| `opencode upgrade` | Update OpenCode | ✅ Maintenance |

---

## Command Details

### `opencode [project]`

**Description**: Launch interactive TUI (Terminal UI) mode

**Syntax**:
```bash
opencode [project_path] [options]
```

**Arguments**:
- `project_path` - Optional project directory (default: current directory)

**Options**:
- `--continue, -c` - Continue previous session
- `--session, -s SESSION_ID` - Resume specific session
- `--prompt, -p PROMPT` - Start with initial prompt
- `--model, -m MODEL` - Specify model (provider/model format)
- `--agent AGENT` - Use specific agent
- `--port PORT` - Server port
- `--hostname HOST` - Server hostname

**Examples**:
```bash
# Launch TUI in current directory
opencode

# Launch in specific project
opencode /path/to/project

# Start with prompt
opencode --prompt "Add tests to the API"

# Use specific model
opencode --model anthropic/claude-sonnet-4.5

# Continue previous session
opencode --continue
```

**Interactive Commands** (within TUI):
- `/init` - Analyze project and create AGENTS.md
- `/undo` - Revert recent changes
- `/redo` - Restore undone changes
- `/share` - Create shareable conversation link
- `/models` - Switch between available models
- `@filename` - Reference project files (fuzzy search)
- **Tab** - Toggle between Plan mode and Build mode

**GAO-Dev Usage**: ❌ Not used (TUI incompatible with subprocess model)

---

### `opencode run` ⭐ PRIMARY FOR GAO-DEV

**Description**: Execute prompt in non-interactive mode (print to stdout and exit)

**Syntax**:
```bash
opencode run [message...] [options]
```

**Arguments**:
- `message...` - Prompt text (can be multiple words)

**Options**:
- `--command` - Execute as shell command
- `--continue, -c` - Continue previous session
- `--session, -s SESSION_ID` - Use specific session
- `--share` - Create shareable link after completion
- `--model, -m MODEL` - Specify model (provider/model format)
- `--agent AGENT` - Use specific agent
- `--file, -f FILE` - Read prompt from file
- `--format FORMAT` - Output format (text, json, etc.)
- `--title TITLE` - Session title

**Examples**:
```bash
# Simple execution
opencode run "Write a hello world Python script"

# Multi-word prompt (no quotes needed)
opencode run Create a REST API with FastAPI

# From file
opencode run --file prompt.txt

# Specific model
opencode run --model openai/gpt-4 "Add error handling to main.py"

# With format
opencode run --format json "Analyze the codebase"

# Continue session
opencode run --continue "Now add tests"

# Specific session
opencode run --session abc123 "Update the API"
```

**GAO-Dev Usage**: ✅ **Primary execution mode**

**Implementation Notes**:
- Results printed to stdout
- Exits after completion
- Exit code indicates success/failure
- Suitable for subprocess execution

---

### `opencode serve`

**Description**: Launch headless HTTP server for API access

**Syntax**:
```bash
opencode serve [options]
```

**Options**:
- `--port, -p PORT` - Server port (default: varies)
- `--hostname HOST` - Server hostname (default: localhost)

**Examples**:
```bash
# Start server on default port
opencode serve

# Custom port
opencode serve --port 8080

# Custom hostname
opencode serve --hostname 0.0.0.0 --port 3000
```

**API Endpoints** (inferred, not fully documented):
- `POST /execute` - Execute prompt
- `GET /models` - List available models
- `GET /health` - Health check

**GAO-Dev Usage**: 🔄 Potential future (alternative integration method)

---

### `opencode models`

**Description**: Display available models across configured providers

**Syntax**:
```bash
opencode models
```

**Output Format**:
```
provider_id/model_id
```

**Example Output**:
```
anthropic/claude-sonnet-4.5
anthropic/claude-opus-4.1
openai/gpt-5
openai/gpt-5-codex
google/gemini-2.5-pro
qwen/qwen3-coder
```

**Notes**:
- Only shows models for authenticated providers
- Format: `provider/model` (used with `--model` flag)

**GAO-Dev Usage**: ✅ Validation and model discovery

---

### `opencode auth`

**Description**: Manage provider authentication

**Syntax**:
```bash
opencode auth [subcommand]
```

**Subcommands**:

#### `opencode auth login`
Configure API keys for providers

**Interactive Process**:
1. Select provider from list
2. Enter API key
3. Credentials stored in `~/.local/share/opencode/auth.json`

**Example**:
```bash
opencode auth login
# Follow interactive prompts
```

#### `opencode auth list` / `opencode auth ls`
Display authenticated providers

**Example Output**:
```
Authenticated providers:
- anthropic
- openai
```

#### `opencode auth logout`
Remove provider credentials

**Example**:
```bash
opencode auth logout
# Follow prompts to select provider
```

**GAO-Dev Usage**: ✅ Setup and validation

**Note**: Environment variables recommended over `auth login` for CI/CD

---

### `opencode agent create`

**Description**: Create custom agents with system prompts and tool configuration

**Syntax**:
```bash
opencode agent create
```

**Interactive Process**:
1. Enter agent name
2. Provide system prompt
3. Configure tools and permissions

**Output**: Agent configuration saved to project

**GAO-Dev Usage**: 🔄 Potential future (custom agent support)

---

### `opencode upgrade`

**Description**: Update OpenCode to latest or specific version

**Syntax**:
```bash
opencode upgrade [target_version] [options]
```

**Arguments**:
- `target_version` - Version to install (default: latest)
  - Format: `v0.1.48`, `latest`, `stable`

**Options**:
- `--method, -m METHOD` - Installation method
  - Values: `curl`, `npm`, `pnpm`, `bun`, `brew`

**Examples**:
```bash
# Upgrade to latest
opencode upgrade

# Specific version
opencode upgrade v0.1.48

# With specific method
opencode upgrade --method brew
opencode upgrade v0.1.50 --method npm
```

**GAO-Dev Usage**: ✅ Maintenance

---

## Global Flags

Available across all commands:

| Flag | Description | Example |
|------|-------------|---------|
| `--help, -h` | Show help message | `opencode run --help` |
| `--version, -v` | Show version | `opencode --version` |
| `--print-logs` | Print log output | `opencode --print-logs run "Task"` |
| `--log-level LEVEL` | Set log level | `opencode --log-level debug run "Task"` |

**Log Levels**: `debug`, `info`, `warn`, `error`

---

## Model Selection

### Model Name Format

**Standard**: `provider_id/model_id`

### Supported Providers

Based on Models.dev integration (75+ providers):

**Major Providers**:
- `anthropic/...` - Anthropic (Claude)
- `openai/...` - OpenAI (GPT)
- `google/...` - Google (Gemini)
- `mistral/...` - Mistral AI
- `cohere/...` - Cohere
- `qwen/...` - Qwen (Alibaba)

### Recommended Models

For **code generation** and **tool calling**:

| Provider | Model ID | Best For |
|----------|----------|----------|
| **Anthropic** | `anthropic/claude-sonnet-4.5` | Balanced performance and cost |
| **Anthropic** | `anthropic/claude-opus-4.1` | Most capable, complex tasks |
| **OpenAI** | `openai/gpt-5` | Latest GPT model |
| **OpenAI** | `openai/gpt-5-codex` | Optimized for coding |
| **Google** | `google/gemini-2.5-pro` | Fast, cost-effective |
| **Qwen** | `qwen/qwen3-coder` | Open-source, coding-focused |

### Model Discovery

**List available models**:
```bash
opencode models
```

**Programmatic model list** (GAO-Dev):
```python
# Via subprocess
result = subprocess.run(["opencode", "models"], capture_output=True, text=True)
models = result.stdout.strip().split("\n")
# ['anthropic/claude-sonnet-4.5', 'openai/gpt-4', ...]
```

---

## Output Formats

### Default (Text)

**Format**: Plain text output

**Example**:
```bash
opencode run "Create hello.txt"
# Output:
# Created file: hello.txt
# Content: Hello, World!
```

### JSON Format

**Format**: Structured JSON output

**Example**:
```bash
opencode run --format json "Analyze the codebase"
# Output:
# {"status": "success", "result": {...}}
```

**Note**: JSON format support varies by command, may not be fully implemented.

---

## Examples

### Basic Execution

```bash
# Simple task
opencode run "Write a Python hello world script"

# Multi-file task
opencode run "Create a FastAPI project with routes, models, and tests"
```

### With Model Specification

```bash
# Anthropic Claude
opencode run --model anthropic/claude-sonnet-4.5 "Add type hints to the code"

# OpenAI GPT
opencode run --model openai/gpt-4 "Refactor the authentication module"

# Google Gemini
opencode run --model google/gemini-2.5-pro "Write unit tests"
```

### Reading from File

**prompt.txt**:
```
Implement a REST API with the following endpoints:
1. POST /users - Create user
2. GET /users/:id - Get user
3. PUT /users/:id - Update user
4. DELETE /users/:id - Delete user

Use FastAPI and SQLAlchemy. Include error handling and validation.
```

**Execute**:
```bash
opencode run --file prompt.txt --model anthropic/claude-sonnet-4.5
```

### Session Management

```bash
# Initial task
opencode run "Create a calculator class"
# Note the session ID (if shown)

# Continue in same session
opencode run --session abc123 "Now add error handling"

# Or use --continue
opencode run --continue "Add unit tests"
```

### Scripting

```bash
#!/bin/bash
# automate-tasks.sh

# Task 1: Generate code
opencode run "Create models.py with User and Product models"

# Task 2: Add tests
opencode run "Create tests for models.py"

# Task 3: Add documentation
opencode run "Add docstrings to all functions in models.py"
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | Authentication error |
| `4` | API error (rate limit, network, etc.) |
| `5` | Timeout |

**Note**: Exact exit codes not fully documented, may vary.

**Usage in scripts**:
```bash
#!/bin/bash

opencode run "Create hello.py"

if [ $? -eq 0 ]; then
    echo "Success!"
else
    echo "Failed with exit code $?"
    exit 1
fi
```

---

## Environment Variables

OpenCode recognizes these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `GOOGLE_API_KEY` | Google API key | `AIza...` |
| `OPENCODE_INSTALL_DIR` | Installation directory | `/usr/local/bin` |

---

## Configuration Files

### Global Config

**Location**: `~/.config/opencode/opencode.json`

**Example**:
```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "providers": {
    "anthropic": {
      "apiKey": "{env:ANTHROPIC_API_KEY}"
    },
    "openai": {
      "apiKey": "{env:OPENAI_API_KEY}"
    }
  },
  "debug": false
}
```

### Project Config

**Location**: `.opencode/config.json` (in project root)

**Example**:
```json
{
  "model": "openai/gpt-4",
  "agents": {
    "code-reviewer": {
      "systemPrompt": "You are a code reviewer...",
      "model": "anthropic/claude-opus-4.1"
    }
  }
}
```

**Merge Behavior**: Project config overrides global config

---

## Advanced Usage

### Custom Agents

```bash
# Create agent
opencode agent create

# Use agent
opencode run --agent code-reviewer "Review main.py"
```

### GitHub Integration

```bash
# Install GitHub Actions workflow
opencode github install

# Run in CI
opencode github run --event pull_request --token $GITHUB_TOKEN
```

### Server Mode API

```bash
# Start server
opencode serve --port 8080

# Call API (example)
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write hello world", "model": "anthropic/claude-sonnet-4.5"}'
```

---

## Comparison with Claude Code

| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| **Command** | `claude` | `opencode run` |
| **Model Flag** | `--model MODEL` | `--model PROVIDER/MODEL` |
| **Print Output** | `--print` | (default in `run`) |
| **Working Dir** | `--add-dir DIR` | (use `cd` or project arg) |
| **API Key** | `ANTHROPIC_API_KEY` | Provider-specific env vars |
| **Providers** | Anthropic only | 75+ providers |

**Translation Example**:
```bash
# Claude Code
claude --print --model claude-sonnet-4-5-20250929 --add-dir /project "Task"

# OpenCode Equivalent
cd /project && opencode run --model anthropic/claude-sonnet-4.5 "Task"
```

---

## Resources

- **Official Documentation**: https://opencode.ai/docs
- **CLI Documentation**: https://opencode.ai/docs/cli
- **GitHub**: https://github.com/sst/opencode
- **Models Registry**: https://models.dev

---

## GAO-Dev Integration Summary

**Primary Command**: `opencode run`
**Model Format**: `provider/model` (e.g., `anthropic/claude-sonnet-4.5`)
**Output**: stdout (parse as text)
**Exit Code**: 0 = success, non-zero = error
**API Key**: Environment variables recommended

**Example GAO-Dev Usage**:
```python
import subprocess

cmd = [
    "opencode", "run",
    "--model", "anthropic/claude-sonnet-4.5",
    "Implement the feature"
]

process = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    cwd="/project/path"
)

if process.returncode == 0:
    print(process.stdout)
else:
    print(f"Error: {process.stderr}")
```

---

**End of CLI Reference**

For setup instructions, see [OpenCode Setup Guide](opencode-setup-guide.md).
