# Example: Using Local Ollama Models

This example shows how to set up and use free local models with Ollama.

## Why Local Models?

- **Zero API Costs**: No per-token charges
- **Offline Development**: Work without internet
- **Privacy**: Data never leaves your machine
- **Speed**: Low latency for local processing

## Prerequisites

### Step 1: Install Ollama

**macOS**:
```bash
brew install ollama
```

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows**:
Download installer from [https://ollama.ai/download](https://ollama.ai/download)

### Step 2: Start Ollama Service

```bash
ollama serve
# Should output: Listening on http://127.0.0.1:11434
```

### Step 3: Pull Models

```bash
# Recommended for coding (7B, fast)
ollama pull deepseek-r1

# Alternative models
ollama pull llama2      # General purpose (7B)
ollama pull codellama   # Coding-focused (13B, slower)
ollama pull mistral     # Fast & capable (7B)

# Verify installation
ollama list
```

## GAO-Dev Setup

### First-Time Setup

```bash
gao-dev start
```

**1. Select OpenCode**:
```
Select provider [1-3]: 2
```

**2. Choose local model**:
```
Use local model via Ollama? [y/N]: y
```

**3. Select model**:
```
Available Models
┌────────┬────────────────┐
│ Option │ Model          │
├────────┼────────────────┤
│ 1      │ deepseek-r1    │
│ 2      │ llama2         │
│ 3      │ codellama      │
└────────┴────────────────┘

Select model [1-3]: 1
```

**4. Save preferences**:
```
Save as default? [Y/n]: y
```

## Switching Between Local Models

### Method 1: Change Preferences

```bash
rm .gao-dev/provider_preferences.yaml
gao-dev start
# Select different model
```

### Method 2: Environment Variable

```bash
# Try codellama (13B, more powerful but slower)
AGENT_PROVIDER=opencode:codellama gao-dev start

# Try mistral (7B, fast)
AGENT_PROVIDER=opencode:mistral gao-dev start
```

## Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **deepseek-r1** | 7B | Fast | Good | General coding (recommended) |
| **llama2** | 7B | Fast | Good | General purpose |
| **codellama** | 13B | Slow | Better | Complex coding tasks |
| **mistral** | 7B | Fastest | Good | Quick iterations |

## Performance Tips

### System Requirements

- **7B models**: 8GB RAM minimum, 16GB recommended
- **13B models**: 16GB RAM minimum, 32GB recommended
- **Disk**: 5-10GB per model
- **CPU**: Modern multi-core recommended

### Optimization

**1. Use SSD** (not HDD):
```bash
# Check Ollama model location
ollama list

# Models stored in: ~/.ollama/models
```

**2. Reduce concurrent processes**:
Close other applications to free RAM for model processing.

**3. Choose appropriate model size**:
- Development/testing: 7B models (deepseek-r1)
- Production/complex: 13B models (codellama)

### Troubleshooting

**Issue**: Ollama not detected
```bash
# Check if Ollama running
ollama list

# Start Ollama service
ollama serve

# Verify port
curl http://localhost:11434/api/tags
```

**Issue**: Models slow
- Use 7B models instead of 13B
- Close memory-intensive applications
- Check CPU usage (htop/Activity Monitor)

**Issue**: Out of memory
- Use smaller models (7B instead of 13B)
- Increase swap space (Linux)
- Upgrade RAM

## Cost Savings

**Comparison** (1M tokens):
- **Claude Code** (cloud): ~$3.00 USD
- **OpenCode + GPT-4** (cloud): ~$10.00 USD
- **OpenCode + Ollama** (local): **$0.00** ✅

**Annual Savings** (moderate use):
- 10M tokens/year: ~$30-100 saved
- 100M tokens/year: ~$300-1000 saved

---

**See Also**:
- [USER_GUIDE.md](../USER_GUIDE.md) - Complete user guide
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Library](https://ollama.ai/library)
