# Example: Advanced Usage

This example shows advanced configurations and power user tips.

## Custom Provider Configuration

### Editing Preferences File

```yaml
# .gao-dev/provider_preferences.yaml
version: "1.0.0"
provider:
  name: "opencode"
  model: "deepseek-r1"
  config:
    ai_provider: "ollama"
    use_local: true
    timeout: 7200  # 2 hours for long-running tasks
    max_retries: 5  # Increase retry attempts
    base_url: "http://localhost:11434"  # Custom Ollama URL
metadata:
  last_updated: "2025-01-12T10:30:00Z"
  cli_version: "1.0.0"
  custom_notes: "Production configuration for large codebase"
```

## Per-Project Provider Selection

### Different Providers for Different Projects

```bash
# Project A: Use Claude Code (high quality)
cd ~/projects/critical-app
export AGENT_PROVIDER=claude-code
gao-dev start

# Project B: Use local Ollama (experimentation)
cd ~/projects/experimental-app
export AGENT_PROVIDER=opencode:deepseek-r1
gao-dev start

# Project C: Use OpenCode + GPT-4 (cost-effective)
cd ~/projects/standard-app
export AGENT_PROVIDER=opencode
# Configure for cloud GPT-4
```

Each project has its own `.gao-dev/provider_preferences.yaml`.

## Environment Variable Patterns

### Project-Specific .env File

```bash
# .env
AGENT_PROVIDER=claude-code
ANTHROPIC_API_KEY=sk-ant-...
```

```bash
# Load .env
source .env
gao-dev start
```

### Shell Aliases

```bash
# ~/.bashrc or ~/.zshrc

# Quick start with Claude Code
alias gao-claude='AGENT_PROVIDER=claude-code gao-dev start'

# Quick start with local Ollama
alias gao-local='AGENT_PROVIDER=opencode:deepseek-r1 gao-dev start'

# Quick start with GPT-4
alias gao-gpt4='AGENT_PROVIDER=opencode:gpt-4 gao-dev start'
```

Usage:
```bash
gao-claude  # Starts with Claude Code
gao-local   # Starts with Ollama
gao-gpt4    # Starts with GPT-4
```

## A/B Testing Providers

### Script to Compare Providers

```bash
#!/bin/bash
# compare_providers.sh

PROVIDERS=("claude-code" "opencode:deepseek-r1" "opencode:gpt-4")

for PROVIDER in "${PROVIDERS[@]}"; do
    echo "Testing with $PROVIDER..."
    export AGENT_PROVIDER=$PROVIDER

    # Run your test workflow
    gao-dev start <<EOF
create simple todo app
exit
EOF

    # Collect metrics
    echo "Completed $PROVIDER"
done

# Compare results
gao-dev metrics report compare run-1 run-2 run-3
```

## Provider Fallback Strategy

### Automatic Fallback on Failure

```python
# custom_provider_selector.py

from gao_dev.cli.provider_selector import ProviderSelector

class FallbackProviderSelector(ProviderSelector):
    """Provider selector with automatic fallback."""

    def select_provider_with_fallback(self):
        """Try primary, fallback to secondary on failure."""
        providers = [
            ('claude-code', 'sonnet-4.5'),
            ('opencode', 'deepseek-r1'),  # Local fallback
        ]

        for provider, model in providers:
            try:
                config = {'provider': provider, 'model': model}
                result = self.provider_validator.validate_configuration(
                    provider, config
                )
                if result.success:
                    return config
            except Exception as e:
                print(f"{provider} failed: {e}")
                continue

        raise Exception("All providers failed")
```

## Performance Optimization

### Disable Ollama Detection (Faster Startup)

If you know Ollama is not needed:

```bash
# Set provider directly
export AGENT_PROVIDER=claude-code

# Bypasses Ollama detection entirely
gao-dev start
```

### Cache Provider Validation

```python
# In production environments, cache validation results

import json
from pathlib import Path
from datetime import datetime, timedelta

class CachedValidator:
    """Validator with 1-hour cache."""

    def __init__(self):
        self.cache_file = Path('.gao-dev/validation_cache.json')
        self.cache_duration = timedelta(hours=1)

    def is_cached_valid(self, provider):
        if not self.cache_file.exists():
            return False

        cache = json.loads(self.cache_file.read_text())
        if provider not in cache:
            return False

        cached_time = datetime.fromisoformat(cache[provider]['time'])
        if datetime.now() - cached_time > self.cache_duration:
            return False

        return cache[provider]['valid']

    def cache_result(self, provider, valid):
        cache = {}
        if self.cache_file.exists():
            cache = json.loads(self.cache_file.read_text())

        cache[provider] = {
            'valid': valid,
            'time': datetime.now().isoformat()
        }

        self.cache_file.write_text(json.dumps(cache))
```

## Integration with Monitoring

### Track Provider Performance

```python
# Log provider metrics
import structlog

logger = structlog.get_logger()

def log_provider_usage(provider, model, duration, tokens, cost):
    logger.info(
        "provider_usage",
        provider=provider,
        model=model,
        duration_seconds=duration,
        tokens_used=tokens,
        cost_usd=cost
    )
```

### Alerting on Provider Failures

```python
# Alert on repeated failures

class ProviderHealthMonitor:
    """Monitor provider health and alert on issues."""

    def __init__(self, alert_threshold=3):
        self.failure_counts = {}
        self.alert_threshold = alert_threshold

    def record_failure(self, provider):
        self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1

        if self.failure_counts[provider] >= self.alert_threshold:
            self.send_alert(provider)

    def send_alert(self, provider):
        # Send to monitoring system (PagerDuty, Slack, etc.)
        print(f"ALERT: Provider {provider} has failed {self.failure_counts[provider]} times")
```

## Security Hardening

### Read-Only Preferences

```bash
# Make preferences immutable (Unix)
chmod 400 .gao-dev/provider_preferences.yaml

# GAO-Dev can read but not modify
# Prevents accidental overwrites
```

### Audit Logging

```python
# Log all provider selections

def audit_provider_selection(user, provider, timestamp):
    with open('/var/log/gao-dev-audit.log', 'a') as f:
        f.write(f"{timestamp},{user},{provider}\n")
```

## Custom Provider Implementation

### Adding Your Own Provider

```python
# my_custom_provider.py

from gao_dev.core.providers.base import BaseProvider

class MyCustomProvider(BaseProvider):
    """Custom provider for internal API."""

    def __init__(self, config):
        self.api_endpoint = config.get('api_endpoint')
        self.api_key = config.get('api_key')

    def execute(self, prompt):
        # Call your internal API
        response = requests.post(
            self.api_endpoint,
            headers={'Authorization': f'Bearer {self.api_key}'},
            json={'prompt': prompt}
        )
        return response.json()['output']
```

Register in ProviderFactory:

```python
# In gao_dev/core/providers/factory.py
from my_custom_provider import MyCustomProvider

factory.register_provider('my-provider', MyCustomProvider)
```

Add to ProviderSelector:

```python
# In gao_dev/cli/provider_selector.py
AVAILABLE_PROVIDERS = [
    "claude-code",
    "opencode",
    "direct-api-anthropic",
    "my-provider",
]
```

## Tips and Tricks

### 1. Quick Provider Switch

```bash
# Function to switch providers quickly
function gao-switch() {
    rm .gao-dev/provider_preferences.yaml
    export AGENT_PROVIDER=$1
    gao-dev start
}

# Usage
gao-switch claude-code
gao-switch opencode:deepseek-r1
```

### 2. Provider Presets

```bash
# ~/.gao-dev/presets.yaml
presets:
  production:
    provider: claude-code
    model: sonnet-4.5
  development:
    provider: opencode
    model: deepseek-r1
  testing:
    provider: opencode
    model: gpt-4
```

### 3. Context-Aware Selection

```bash
# Select provider based on project type
if [ -f "package.json" ]; then
    export AGENT_PROVIDER=claude-code  # Node.js project
elif [ -f "requirements.txt" ]; then
    export AGENT_PROVIDER=opencode:deepseek-r1  # Python project
fi

gao-dev start
```

---

**See Also**:
- [API_REFERENCE.md](../API_REFERENCE.md) - API documentation
- [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md) - Custom providers
- [USER_GUIDE.md](../USER_GUIDE.md) - User guide
