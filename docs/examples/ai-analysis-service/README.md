# AIAnalysisService Examples

This directory contains working examples demonstrating how to use the AIAnalysisService.

## Examples

### 1. basic_usage.py
**What it does**: Demonstrates basic AIAnalysisService usage
**Key concepts**:
- Creating service instance
- Making analysis requests
- Accessing response and metadata
- Parsing JSON responses
- Estimating costs

**Run it**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python docs/examples/ai-analysis-service/basic_usage.py
```

---

### 2. custom_model.py
**What it does**: Compares different models for same task
**Key concepts**:
- Using different Claude models
- Performance comparison
- Cost comparison
- Model selection strategy

**Run it**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python docs/examples/ai-analysis-service/custom_model.py
```

---

### 3. error_handling.py
**What it does**: Demonstrates comprehensive error handling
**Key concepts**:
- Handling different error types
- Retry logic
- Fallback strategies
- JSON validation with fallback

**Run it**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python docs/examples/ai-analysis-service/error_handling.py
```

---

### 4. testing_example.py
**What it does**: Shows how to test components using AIAnalysisService
**Key concepts**:
- Mocking with Mock + AsyncMock
- Unit testing patterns
- Integration testing
- Testing retry logic

**Run tests**:
```bash
# Run all tests
pytest docs/examples/ai-analysis-service/testing_example.py

# Run without integration tests
pytest docs/examples/ai-analysis-service/testing_example.py -m "not integration"

# Run with verbose output
pytest docs/examples/ai-analysis-service/testing_example.py -v
```

---

## Prerequisites

All examples require:
- Python 3.11+
- GAO-Dev installed (`pip install -e .`)
- ANTHROPIC_API_KEY environment variable set

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

## Quick Start

```bash
# 1. Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Run basic example
python docs/examples/ai-analysis-service/basic_usage.py

# 3. Run tests
pytest docs/examples/ai-analysis-service/testing_example.py
```

## Documentation

For complete documentation, see:
- [API Reference](../../features/ai-analysis-service/API_REFERENCE.md)
- [Usage Guide](../../features/ai-analysis-service/USAGE_GUIDE.md)
- [Architecture](../../features/ai-analysis-service/ARCHITECTURE.md)
- [Migration Guide](../../features/ai-analysis-service/MIGRATION_GUIDE.md)
- [Local Models Setup](../../features/ai-analysis-service/LOCAL_MODELS_SETUP.md)

## Support

For issues or questions:
- Check [USAGE_GUIDE.md](../../features/ai-analysis-service/USAGE_GUIDE.md#troubleshooting)
- Open an issue on GitHub
- Review Epic 21 documentation
