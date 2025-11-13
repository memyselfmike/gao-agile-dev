# Example: CI/CD Pipeline Usage

This example shows how to use Interactive Provider Selection in CI/CD pipelines.

## Key Principle

**Set `AGENT_PROVIDER` environment variable to bypass all prompts.**

## GitHub Actions

### Example Workflow

```yaml
name: GAO-Dev CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    env:
      # Bypass interactive prompts
      AGENT_PROVIDER: claude-code
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install GAO-Dev
        run: |
          pip install -e .

      - name: Run GAO-Dev tests
        run: |
          gao-dev start --non-interactive
          # Your test commands here
```

### Multi-Provider Matrix

```yaml
jobs:
  test-providers:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        provider:
          - claude-code
          - opencode
          - direct-api-anthropic

    env:
      AGENT_PROVIDER: ${{ matrix.provider }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

    steps:
      - uses: actions/checkout@v3
      - name: Test with ${{ matrix.provider }}
        run: |
          gao-dev start
```

## GitLab CI

### Example Pipeline

```yaml
test:
  image: python:3.11
  variables:
    AGENT_PROVIDER: "claude-code"
  script:
    - pip install -e .
    - gao-dev start
  only:
    - main
    - merge_requests
```

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        AGENT_PROVIDER = 'claude-code'
        ANTHROPIC_API_KEY = credentials('anthropic-api-key')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -e .'
            }
        }

        stage('Test') {
            steps {
                sh 'gao-dev start'
            }
        }
    }
}
```

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set provider (no prompts)
ENV AGENT_PROVIDER=claude-code

# Install GAO-Dev
WORKDIR /app
COPY . .
RUN pip install -e .

# Runtime API key (set at docker run)
CMD ["gao-dev", "start"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  gao-dev:
    build: .
    environment:
      AGENT_PROVIDER: claude-code
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    volumes:
      - ./projects:/app/projects
```

### Run

```bash
export ANTHROPIC_API_KEY=sk-ant-...
docker-compose up
```

## CircleCI

### .circleci/config.yml

```yaml
version: 2.1

jobs:
  test:
    docker:
      - image: python:3.11
    environment:
      AGENT_PROVIDER: claude-code
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -e .
      - run:
          name: Run GAO-Dev
          command: gao-dev start

workflows:
  version: 2
  test-workflow:
    jobs:
      - test
```

## Headless Environment Handling

The system automatically falls back to basic `input()` if TTY unavailable:

### Verification

```bash
# Test headless mode
docker run --rm -it python:3.11 bash
pip install gao-dev
export AGENT_PROVIDER=claude-code
gao-dev start  # Should work without TTY
```

### Fallback Behavior

1. Checks `AGENT_PROVIDER` env var (bypasses prompts) ✅
2. If prompts needed and no TTY:
   - Uses basic `input()` instead of `prompt_toolkit`
   - Simple text output instead of Rich tables
   - Still functional, just less fancy

## Best Practices

### 1. Always Set AGENT_PROVIDER

```yaml
env:
  AGENT_PROVIDER: claude-code  # Explicit provider
```

### 2. Use Secrets for API Keys

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Never commit API keys to repository!**

### 3. Test Multiple Providers

```yaml
strategy:
  matrix:
    provider: [claude-code, opencode, direct-api-anthropic]
```

### 4. Cache Dependencies

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### 5. Set Timeouts

```yaml
timeout-minutes: 30  # Prevent hanging
```

## Troubleshooting

### Issue: "No TTY available"

**Solution**: Set `AGENT_PROVIDER` environment variable.

```yaml
env:
  AGENT_PROVIDER: claude-code
```

### Issue: API key not found

**Solution**: Add secret to CI/CD settings.

**GitHub Actions**: Settings > Secrets > Actions > New repository secret

**GitLab CI**: Settings > CI/CD > Variables > Add variable

**Jenkins**: Credentials > Add credentials

### Issue: Validation fails in CI

**Solution**: Install required CLI tools.

```yaml
- name: Install Claude Code CLI
  run: npm install -g @anthropic/claude-code
```

---

**See Also**:
- [USER_GUIDE.md](../USER_GUIDE.md) - User guide
- [FAQ.md](../FAQ.md) - CI/CD questions
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Headless issues
