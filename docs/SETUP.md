# GAO-Dev Setup Guide

Quick setup instructions for running GAO-Dev benchmarks.

## Prerequisites

- Python 3.10+
- Anthropic API key (for autonomous benchmark execution)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gao-agile-dev
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Verify installation:
   ```bash
   gao-dev --version
   gao-dev health
   ```

## API Key Configuration

To run autonomous benchmarks, you need an Anthropic API key. There are three ways to provide it:

### Option 1: .env File (Recommended)

This is the easiest method for local development:

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```bash
   # .env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

3. The API key will be automatically loaded when running commands:
   ```bash
   gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml
   ```

**Note**: The `.env` file is already in `.gitignore` and will never be committed to version control.

### Option 2: Environment Variable

Set the environment variable in your shell:

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml
```

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-...
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml
```

### Option 3: Command Line Argument

Pass the API key directly to the command:

```bash
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml --api-key sk-ant-api03-...
```

### Priority Order

If you provide the API key in multiple ways, the priority is:
1. Command line argument (`--api-key`)
2. `.env` file
3. Environment variable

This allows you to override the default for specific runs.

## Getting an Anthropic API Key

1. Go to [https://console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Sign in or create an account
3. Create a new API key
4. Copy the key (it starts with `sk-ant-api03-...`)
5. Add it to your `.env` file or environment

## Running Your First Benchmark

Once you have your API key configured:

```bash
# Run the todo app baseline benchmark
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml

# This will:
# - Create a new sandbox project
# - Execute all 7 phases with specialized agents
# - Complete all 103 story points across 5 epics
# - Generate comprehensive metrics report
# - Create a production-ready Next.js todo application
```

Expected duration: ~130 minutes
Expected cost: ~$15-20

## Verifying Configuration

To check if your API key is configured correctly:

```bash
# Try running a benchmark - it will tell you if API key is missing
gao-dev sandbox run sandbox/benchmarks/todo-app-baseline.yaml

# If configured correctly, you'll see:
# >> Executing Benchmark Autonomously
#   Mode: Full autonomous execution with GAO-Dev agents
#   API: Anthropic Claude
#   API Key: sk-ant-api... (from .env file)
```

## Troubleshooting

### "No API key detected"

If you see this message:
```
[INFO] No API key detected - Interactive mode recommended
```

**Solution**: Add your API key using one of the three methods above.

### "API key not found" error

If you get this error:
```
ValueError: API key not found. Set ANTHROPIC_API_KEY environment variable
```

**Solution**:
1. Check that your `.env` file exists: `ls .env` (or `dir .env` on Windows)
2. Check that the file contains: `ANTHROPIC_API_KEY=sk-ant-...`
3. Make sure there are no extra spaces or quotes around the key

### Wrong API key source shown

If the CLI shows the wrong source (e.g., "environment variable" when you're using `.env`):

This is just a display issue and doesn't affect functionality. The API key is being loaded correctly.

## Optional Configuration

You can also configure these in your `.env` file:

```bash
# Optional: Override default sandbox root directory
SANDBOX_ROOT=./sandbox

# Optional: Override default metrics output directory
METRICS_OUTPUT_DIR=./sandbox/metrics

# Optional: Default benchmark timeout in seconds
BENCHMARK_TIMEOUT_SECONDS=14400

# Optional: Enable verbose debug logging
GAO_DEV_DEBUG=false
```

## Security Best Practices

1. **Never commit `.env` file**: Already in `.gitignore`
2. **Never share your API key**: Keep it private
3. **Rotate keys regularly**: Create new keys periodically
4. **Use different keys for dev/prod**: Don't use the same key everywhere
5. **Check costs**: Monitor your Anthropic API usage

## Next Steps

- Read the [Autonomous Benchmark Guide](./sandbox-autonomous-benchmark-guide.md)
- Try running your first benchmark
- Review the generated metrics and logs
- Create your own custom benchmarks

## Support

For issues or questions:
- Check the logs in `sandbox/metrics/`
- Review documentation in `docs/`
- Check agent personas in `gao_dev/agents/`

---

**Last Updated**: 2025-01-27
