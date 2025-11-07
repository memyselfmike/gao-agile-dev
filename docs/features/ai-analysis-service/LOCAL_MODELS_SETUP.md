# Local Models Setup Guide

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Version**: 1.0
**Last Updated**: 2025-11-07

---

## Table of Contents

1. [Overview](#overview)
2. [Benefits](#benefits)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Supported Models](#supported-models)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Performance Comparison](#performance-comparison)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Run GAO-Dev with **free local models** using **Ollama** instead of paid Anthropic API. This enables zero-cost development, offline work, and complete privacy.

**What You'll Set Up:**
- Ollama (local model runner)
- DeepSeek-R1 or other models
- AIAnalysisService configured for local use

**Use Cases:**
- Development and testing
- Experimentation without API costs
- Offline development
- Privacy-sensitive projects

---

## Benefits

### Cost Savings
- **$0** for local models vs. **$3-15 per million tokens** for Claude
- Development costs drop to zero
- Unlimited experimentation

### Privacy
- All data stays on your machine
- No data sent to external APIs
- GDPR/compliance friendly

### Offline Capability
- Work without internet
- No network latency
- Reliable availability

### Flexibility
- Switch between models easily
- Try experimental models
- Test model behavior

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB (16GB recommended)
- Disk: 10GB free space
- OS: macOS, Linux, or Windows with WSL

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA GPU with 8GB+ VRAM (optional, for faster inference)
- Disk: 20GB+ free space

### Software Requirements

- Python 3.11+
- GAO-Dev installed
- Internet connection (for initial model download)

---

## Step-by-Step Setup

### Step 1: Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows (WSL):**
```bash
# In WSL terminal
curl -fsSL https://ollama.ai/install.sh | sh
```

**Verify Installation:**
```bash
ollama --version
# Should output: ollama version x.x.x
```

---

### Step 2: Start Ollama Service

```bash
# Start Ollama server
ollama serve
```

Keep this terminal open. Ollama will run on `http://localhost:11434`.

**Verify Service:**
```bash
# In a new terminal
curl http://localhost:11434/api/tags
# Should return JSON with model list
```

---

### Step 3: Pull a Model

**DeepSeek-R1 (Recommended):**
```bash
# Pull 8B model (good balance of speed/quality)
ollama pull deepseek-r1:8b

# Or 14B model (better quality, slower)
ollama pull deepseek-r1:14b
```

**Alternative Models:**
```bash
# Llama 3.1
ollama pull llama3.1:8b

# Mistral
ollama pull mistral:7b

# CodeLlama (for code tasks)
ollama pull codellama:13b
```

**Verify Download:**
```bash
ollama list
# Should show downloaded models
```

---

### Step 4: Test Model

```bash
# Interactive chat
ollama run deepseek-r1:8b

# Type a prompt
> Analyze the complexity of a todo app

# Should get response
# Press Ctrl+D to exit
```

---

### Step 5: Configure AIAnalysisService

**Option A: Environment Variables (Recommended)**

```bash
# For direct Ollama usage (when supported)
export OLLAMA_BASE_URL="http://localhost:11434"
export GAO_DEV_MODEL="deepseek-r1:8b"
```

**Option B: Python Configuration**

```python
from gao_dev.core.services import AIAnalysisService

# Note: Current version uses Anthropic API
# Future versions will support direct Ollama
service = AIAnalysisService(
    default_model="deepseek-r1:8b"
)
```

**Option C: Via OpenCode (Current Method)**

See [DEEPSEEK_R1_VALIDATION_GUIDE.md](./DEEPSEEK_R1_VALIDATION_GUIDE.md) for OpenCode setup.

---

## Supported Models

### DeepSeek-R1 (Recommended)

| Model | Size | RAM | Speed | Quality | Use Case |
|-------|------|-----|-------|---------|----------|
| `deepseek-r1:8b` | 8B | 8GB | Fast | Good | Development, testing |
| `deepseek-r1:14b` | 14B | 16GB | Medium | Better | Production-like testing |
| `deepseek-r1:32b` | 32B | 32GB | Slow | Best | Critical analysis |

### Llama 3.1

| Model | Size | RAM | Speed | Quality | Use Case |
|-------|------|-----|-------|---------|----------|
| `llama3.1:8b` | 8B | 8GB | Fast | Good | General purpose |
| `llama3.1:70b` | 70B | 64GB | Very Slow | Excellent | High-quality analysis |

### Code-Specific Models

| Model | Size | RAM | Speed | Quality | Use Case |
|-------|------|-----|-------|---------|----------|
| `codellama:7b` | 7B | 8GB | Fast | Good | Code analysis |
| `codellama:13b` | 13B | 16GB | Medium | Better | Complex code tasks |

### Mistral

| Model | Size | RAM | Speed | Quality | Use Case |
|-------|------|-----|-------|---------|----------|
| `mistral:7b` | 7B | 8GB | Fast | Good | General purpose |
| `mistral:7b-instruct` | 7B | 8GB | Fast | Good | Instruction following |

---

## Configuration

### Model Selection Strategy

**Development:**
- Use `deepseek-r1:8b` or `llama3.1:8b`
- Fast iteration, acceptable quality

**Testing:**
- Use `deepseek-r1:14b` or `codellama:13b`
- Balance speed and quality

**Critical Analysis:**
- Use `deepseek-r1:32b` or `llama3.1:70b`
- Best quality, slower

### Resource Management

**Control Memory Usage:**
```bash
# Set max concurrent requests
export OLLAMA_MAX_LOADED_MODELS=1

# Set context window
export OLLAMA_NUM_CTX=2048  # Smaller = less RAM
```

**GPU Acceleration (NVIDIA):**
```bash
# Ollama automatically uses GPU if available
# Verify GPU usage
nvidia-smi
# Should show ollama process if using GPU
```

---

## Testing

### Test 1: Simple Prompt

```bash
# Test Ollama directly
ollama run deepseek-r1:8b "Analyze complexity of: def add(a,b): return a+b"
```

### Test 2: With AIAnalysisService

```python
import asyncio
from gao_dev.core.services import AIAnalysisService

async def test():
    service = AIAnalysisService()

    result = await service.analyze(
        prompt="Rate complexity 1-10: def add(a, b): return a + b",
        response_format="json"
    )

    print(result.response)
    print(f"Tokens: {result.tokens_used}")
    print(f"Duration: {result.duration_ms}ms")

asyncio.run(test())
```

### Test 3: Benchmark

```bash
# Run benchmark with local model (via OpenCode)
export AGENT_PROVIDER=opencode-sdk
export GAO_DEV_MODEL=deepseek-r1:8b

gao-dev sandbox run sandbox/benchmarks/simple-todo-deepseek.yaml
```

---

## Performance Comparison

### Speed

| Model | Average Response Time | Use Case |
|-------|----------------------|----------|
| Claude Sonnet 4.5 (API) | 2-5 seconds | Production |
| DeepSeek-R1 8B (local) | 5-15 seconds (CPU) | Development |
| DeepSeek-R1 8B (GPU) | 2-8 seconds | Development/Testing |
| Llama 3.1 70B (GPU) | 10-30 seconds | High-quality analysis |

### Cost

| Provider | Cost per Analysis | Daily Dev Cost (50 analyses) |
|----------|------------------|------------------------------|
| Claude Sonnet 4.5 | $0.01-0.05 | $0.50-2.50 |
| Local Model | $0.00 | $0.00 |

**Savings**: $10-50/month for active development

### Quality

| Task | Claude Sonnet 4.5 | DeepSeek-R1 8B | DeepSeek-R1 32B |
|------|------------------|----------------|-----------------|
| Complexity Analysis | Excellent | Good | Very Good |
| Code Review | Excellent | Good | Very Good |
| Architecture Design | Excellent | Fair | Good |
| JSON Formatting | Excellent | Good | Good |

**Recommendation**: Use local models for development, Claude for production.

---

## Troubleshooting

### Issue: Connection Refused

**Symptoms:**
```
Error connecting to Ollama: Connection refused
```

**Solution:**
```bash
# Ensure Ollama is running
ollama serve

# Check service
curl http://localhost:11434/api/tags
```

---

### Issue: Model Not Found

**Symptoms:**
```
Error: model 'deepseek-r1:8b' not found
```

**Solution:**
```bash
# Pull the model
ollama pull deepseek-r1:8b

# Verify
ollama list
```

---

### Issue: Out of Memory

**Symptoms:**
```
Error: failed to allocate memory
```

**Solution:**
```bash
# Use smaller model
ollama pull deepseek-r1:8b  # Instead of 32b

# Reduce context window
export OLLAMA_NUM_CTX=2048

# Close other applications
```

---

### Issue: Slow Performance

**Symptoms:**
- Responses take 30+ seconds
- High CPU usage

**Solution:**
```bash
# Use smaller model
ollama pull deepseek-r1:8b

# Use GPU if available
# Ollama automatically uses GPU

# Verify GPU usage
nvidia-smi  # For NVIDIA GPUs
```

---

### Issue: JSON Parsing Errors

**Symptoms:**
```
JSONDecodeError: Expecting value
```

**Solution:**
```python
# Add stronger instructions in prompt
prompt = """
IMPORTANT: Return ONLY valid JSON. No markdown, no explanations.

Format:
{"complexity": 5, "rationale": "explanation"}

Task: Analyze this code...
"""

result = await service.analyze(prompt=prompt, response_format="json")
```

---

## Advanced Configuration

### Multiple Models

```python
# Load different models for different tasks
class SmartAnalysisService:
    def __init__(self):
        self.service = AIAnalysisService()

    async def quick_analysis(self, prompt: str):
        """Fast, cheap analysis."""
        return await self.service.analyze(
            prompt=prompt,
            model="deepseek-r1:8b"  # Fast model
        )

    async def detailed_analysis(self, prompt: str):
        """High-quality analysis."""
        return await self.service.analyze(
            prompt=prompt,
            model="deepseek-r1:32b"  # Better model
        )
```

### Model Caching

```bash
# Ollama keeps models in memory
# First call loads model (slow)
# Subsequent calls are fast

# Keep model loaded
ollama run deepseek-r1:8b
# Keep terminal open, model stays in memory
```

### Custom Models

```bash
# Create custom model with specific instructions
cat > Modelfile <<EOF
FROM deepseek-r1:8b
PARAMETER temperature 0.3
SYSTEM You are a code complexity analyzer. Always return JSON.
EOF

# Build custom model
ollama create code-analyzer -f Modelfile

# Use custom model
ollama run code-analyzer
```

---

## Next Steps

1. **Try the setup**: Follow steps 1-5
2. **Test with simple prompts**: Verify models work
3. **Run benchmark**: Test full GAO-Dev integration
4. **Monitor performance**: Compare with Claude API
5. **Optimize**: Adjust models/settings for your needs

---

## See Also

- [DEEPSEEK_R1_VALIDATION_GUIDE.md](./DEEPSEEK_R1_VALIDATION_GUIDE.md) - Full validation guide
- [API_REFERENCE.md](./API_REFERENCE.md) - AIAnalysisService API
- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - How to use the service
- [Ollama Documentation](https://ollama.ai/docs) - Official Ollama docs

---

**Guide Version**: 1.0
**Last Updated**: 2025-11-07
**Support**: Open an issue for help
