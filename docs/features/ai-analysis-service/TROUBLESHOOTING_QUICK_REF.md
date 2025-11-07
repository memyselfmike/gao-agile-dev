# DeepSeek-R1 Troubleshooting Quick Reference

**Quick lookup for common issues** when running GAO-Dev with DeepSeek-R1.

For detailed guide, see: [DEEPSEEK_R1_VALIDATION_GUIDE.md](DEEPSEEK_R1_VALIDATION_GUIDE.md)

---

## Quick Diagnostics

Run this one-liner to check everything:

```bash
ollama --version && ollama list | grep deepseek && opencode --version && curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ All systems ready" || echo "✗ Check failed"
```

---

## Common Errors & Fixes

### "404 - model: deepseek-r1"

**Fix**: Set environment variable
```bash
export AGENT_PROVIDER=opencode-sdk  # macOS/Linux
$env:AGENT_PROVIDER="opencode-sdk"  # Windows
```

Or run the benchmark script (it sets this):
```bash
python run_deepseek_benchmark.py
```

---

### "Connection refused" (Ollama)

**Fix**: Start Ollama service
```bash
ollama serve  # macOS/Linux
Start-Service Ollama  # Windows PowerShell
```

**Verify**:
```bash
curl http://localhost:11434/api/tags
```

---

### "Model not found"

**Fix**: Pull the model
```bash
ollama pull deepseek-r1:8b
```

**Verify**:
```bash
ollama list | grep deepseek
```

---

### "Invalid JSON response"

**Fix**: Retry (DeepSeek occasionally produces malformed JSON)
```bash
python run_deepseek_benchmark.py
```

Usually succeeds on 2nd try.

---

### Slow performance

**Fix**: This is expected (local models slower than API)

**Workarounds**:
- Increase timeout in benchmark config
- Use GPU if available
- Accept slower speed as tradeoff for free usage

---

### Out of memory

**Fix**: Use smaller model
```bash
ollama pull deepseek-r1:1.5b  # Smaller, needs less RAM
```

Update agent configs to use `deepseek-r1:1.5b`

---

### OpenCode not configured

**Fix**: Create `opencode.json` in project root:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "deepseek-r1:8b": {
          "name": "DeepSeek R1 8B (Ollama)",
          "tools": true
        }
      }
    }
  }
}
```

---

## Installation Quick Fixes

### Ollama not installed

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from: https://ollama.ai/download
```

---

### OpenCode not installed

```bash
curl -fsSL https://opencode.ai/install | bash
```

---

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Benchmark config | `sandbox/benchmarks/simple-todo-deepseek.yaml` | Test configuration |
| Run script | `run_deepseek_benchmark.py` | Execution script |
| OpenCode config | `opencode.json` | Provider setup |
| Agent configs | `gao_dev/agents/*.agent.yaml` | Model settings |
| Logs | `sandbox/projects/*/logs/` | Debug info |
| Reports | `sandbox/projects/*/reports/` | Results |

---

## Verification Commands

```bash
# Check all prerequisites
ollama --version          # Ollama installed
ollama list               # Models available
ollama serve              # Start service (if not running)
opencode --version        # OpenCode installed
cat opencode.json         # Config exists
python run_deepseek_benchmark.py  # Run benchmark
```

---

## Getting Help

1. Check logs: `sandbox/projects/simple-todo-deepseek/logs/`
2. Enable debug: `export GAO_DEV_LOG_LEVEL=DEBUG`
3. Review full guide: [DEEPSEEK_R1_VALIDATION_GUIDE.md](DEEPSEEK_R1_VALIDATION_GUIDE.md)
4. Check agent configs: `cat gao_dev/agents/brian.agent.yaml`

---

## Working Setup Checklist

- [ ] Ollama installed (`ollama --version`)
- [ ] Ollama running (`curl http://localhost:11434/api/tags`)
- [ ] DeepSeek-R1 model pulled (`ollama list | grep deepseek`)
- [ ] OpenCode installed (`opencode --version`)
- [ ] opencode.json exists (`cat opencode.json`)
- [ ] Benchmark config exists (`cat sandbox/benchmarks/simple-todo-deepseek.yaml`)
- [ ] Run script exists (`cat run_deepseek_benchmark.py`)
- [ ] Agent configs updated (model: `deepseek-r1:8b`)

**All checked?** Run:
```bash
python run_deepseek_benchmark.py
```

---

**Last Updated**: 2025-11-07
