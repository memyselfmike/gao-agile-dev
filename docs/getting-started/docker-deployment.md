# Docker Deployment Guide

Deploy GAO-Dev in containerized environments using Docker, Docker Compose, or Kubernetes.

## Table of Contents

- [Quick Start with Docker](#quick-start-with-docker)
- [Docker Compose Setup](#docker-compose-setup)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Persistent Configuration](#persistent-configuration)
- [Environment Configuration](#environment-configuration)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

## Quick Start with Docker

### Basic Docker Run

```bash
# Run GAO-Dev with minimal configuration
docker run -it \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/projects:/app/projects \
  gao-dev/gao-dev:latest \
  gao-dev start
```

### Full Docker Run with All Options

```bash
docker run -it \
  --name gao-dev \
  -e AGENT_PROVIDER=claude-code \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GAO_DEV_DEBUG=false \
  -v $(pwd)/projects:/app/projects \
  -v $(pwd)/.gao-dev:/app/.gao-dev \
  -v $(pwd)/sandbox:/app/sandbox \
  -p 8080:8080 \
  gao-dev/gao-dev:latest \
  gao-dev start
```

### Parameter Explanation

| Parameter | Description |
|-----------|-------------|
| `-it` | Interactive mode with TTY |
| `--name gao-dev` | Container name for easy reference |
| `-e AGENT_PROVIDER` | Skip provider selection prompt |
| `-e ANTHROPIC_API_KEY` | API key for AI provider |
| `-v $(pwd)/projects:/app/projects` | Mount projects directory |
| `-v $(pwd)/.gao-dev:/app/.gao-dev` | Persist GAO-Dev configuration |
| `-p 8080:8080` | Expose web interface (if enabled) |

## Docker Compose Setup

### Basic docker-compose.yaml

```yaml
version: '3.8'

services:
  gao-dev:
    image: gao-dev/gao-dev:latest
    container_name: gao-dev
    stdin_open: true
    tty: true
    environment:
      - AGENT_PROVIDER=claude-code
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./projects:/app/projects
      - gao-dev-config:/app/.gao-dev
      - ./sandbox:/app/sandbox
    ports:
      - "8080:8080"

volumes:
  gao-dev-config:
    driver: local
```

### Production docker-compose.yaml

```yaml
version: '3.8'

services:
  gao-dev:
    image: gao-dev/gao-dev:latest
    container_name: gao-dev-prod
    stdin_open: true
    tty: true
    restart: unless-stopped
    environment:
      # Provider configuration
      - AGENT_PROVIDER=${AGENT_PROVIDER:-claude-code}

      # API keys (from .env file or secrets)
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}

      # Optional configuration
      - GAO_DEV_DEBUG=${GAO_DEV_DEBUG:-false}
      - GAO_DEV_MODEL=${GAO_DEV_MODEL:-}
      - SANDBOX_ROOT=/app/sandbox
      - METRICS_OUTPUT_DIR=/app/sandbox/metrics

    volumes:
      # Project workspace (persistent)
      - ./projects:/app/projects

      # GAO-Dev configuration (persistent)
      - gao-dev-config:/app/.gao-dev

      # Sandbox for benchmarks (persistent)
      - ./sandbox:/app/sandbox

      # Optional: Mount custom prompts/agents
      - ./custom/prompts:/app/custom/prompts:ro
      - ./custom/agents:/app/custom/agents:ro

    ports:
      - "8080:8080"

    healthcheck:
      test: ["CMD", "gao-dev", "health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

volumes:
  gao-dev-config:
    driver: local
```

### Using .env File with Docker Compose

Create a `.env` file:

```bash
# .env
AGENT_PROVIDER=claude-code
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
GAO_DEV_DEBUG=false
```

Run with:

```bash
docker-compose up -d
docker-compose exec gao-dev gao-dev start
```

## Kubernetes Deployment

### StatefulSet Configuration

GAO-Dev requires persistent storage for configuration and project data. Use a StatefulSet:

```yaml
# gao-dev-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: gao-dev
  namespace: dev-tools
spec:
  serviceName: gao-dev
  replicas: 1
  selector:
    matchLabels:
      app: gao-dev
  template:
    metadata:
      labels:
        app: gao-dev
    spec:
      containers:
        - name: gao-dev
          image: gao-dev/gao-dev:latest
          stdin: true
          tty: true
          env:
            - name: AGENT_PROVIDER
              valueFrom:
                configMapKeyRef:
                  name: gao-dev-config
                  key: AGENT_PROVIDER
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: gao-dev-secrets
                  key: ANTHROPIC_API_KEY
            - name: GAO_DEV_DEBUG
              value: "false"
          volumeMounts:
            - name: gao-dev-data
              mountPath: /app/.gao-dev
            - name: projects
              mountPath: /app/projects
            - name: sandbox
              mountPath: /app/sandbox
          ports:
            - containerPort: 8080
              name: web
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            exec:
              command:
                - gao-dev
                - health
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            exec:
              command:
                - gao-dev
                - health
            initialDelaySeconds: 5
            periodSeconds: 10
  volumeClaimTemplates:
    - metadata:
        name: gao-dev-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 1Gi
    - metadata:
        name: projects
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 10Gi
    - metadata:
        name: sandbox
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 5Gi
```

### ConfigMap

```yaml
# gao-dev-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gao-dev-config
  namespace: dev-tools
data:
  AGENT_PROVIDER: "claude-code"
  GAO_DEV_DEBUG: "false"
  SANDBOX_ROOT: "/app/sandbox"
```

### Secret

```yaml
# gao-dev-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: gao-dev-secrets
  namespace: dev-tools
type: Opaque
stringData:
  ANTHROPIC_API_KEY: "sk-ant-api03-..."
  OPENAI_API_KEY: "sk-..."
```

### Service

```yaml
# gao-dev-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: gao-dev
  namespace: dev-tools
spec:
  selector:
    app: gao-dev
  ports:
    - port: 8080
      targetPort: 8080
      name: web
  type: ClusterIP
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace dev-tools

# Apply configurations
kubectl apply -f gao-dev-configmap.yaml
kubectl apply -f gao-dev-secret.yaml
kubectl apply -f gao-dev-statefulset.yaml
kubectl apply -f gao-dev-service.yaml

# Access the container
kubectl exec -it gao-dev-0 -n dev-tools -- gao-dev start
```

## Persistent Configuration

GAO-Dev persists data in these locations:

| Path | Purpose | Persistence Required |
|------|---------|---------------------|
| `/app/.gao-dev/` | GAO-Dev configuration and state | Yes |
| `/app/projects/` | User projects | Yes |
| `/app/sandbox/` | Benchmark sandbox | Recommended |

### Configuration Files

**Provider Preferences** (`.gao-dev/provider_preferences.yaml`):
```yaml
provider: claude-code
backend: anthropic
model: claude-sonnet-4-20250514
timestamp: '2025-01-15T10:30:00Z'
```

**Document Database** (`.gao-dev/documents.db`):
- SQLite database tracking document lifecycle
- Automatically created on first run
- Should be persisted for project continuity

### Volume Best Practices

1. **Named Volumes**: Use named volumes for configuration
2. **Bind Mounts**: Use bind mounts for projects you want to access from host
3. **Backup Strategy**: Regularly backup `.gao-dev/` directory

```bash
# Backup GAO-Dev configuration
docker cp gao-dev:/app/.gao-dev ./backup/

# Restore configuration
docker cp ./backup/.gao-dev gao-dev:/app/
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENT_PROVIDER` | Skip provider selection | `claude-code` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-api03-...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `GAO_DEV_DEBUG` | Enable debug logging | `false` |
| `GAO_DEV_MODEL` | Override model | Provider default |
| `SANDBOX_ROOT` | Sandbox directory | `/app/sandbox` |
| `METRICS_OUTPUT_DIR` | Metrics output | `/app/sandbox/metrics` |

See [Environment Variables Reference](../guides/environment-variables.md) for complete list.

## Health Checks

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD gao-dev health || exit 1
```

### Manual Health Check

```bash
# Inside container
gao-dev health

# From host
docker exec gao-dev gao-dev health
```

Expected output:
```
GAO-Dev Health Check
+-- System Status: OK
+-- Database: Connected
+-- Provider: claude-code (valid)
+-- Workflows: 55 loaded
+-- Agents: 8 available
```

## Building Custom Images

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install GAO-Dev
COPY . /app
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/.gao-dev /app/projects /app/sandbox

# Set environment defaults
ENV AGENT_PROVIDER=claude-code
ENV SANDBOX_ROOT=/app/sandbox

# Health check
HEALTHCHECK --interval=30s --timeout=10s CMD gao-dev health

# Default command
CMD ["gao-dev", "start"]
```

### Build and Push

```bash
# Build image
docker build -t gao-dev/gao-dev:latest .

# Tag for registry
docker tag gao-dev/gao-dev:latest your-registry/gao-dev:v2.0.0

# Push to registry
docker push your-registry/gao-dev:v2.0.0
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs gao-dev

# Check environment variables
docker exec gao-dev env | grep -E "AGENT_|ANTHROPIC|GAO_DEV"
```

### Provider Not Found

```bash
# Verify provider setting
docker exec gao-dev echo $AGENT_PROVIDER

# Check provider validation
docker exec gao-dev gao-dev health
```

### Permission Issues

```bash
# Fix volume permissions
docker exec gao-dev chown -R $(id -u):$(id -g) /app/.gao-dev

# Or run with specific user
docker run --user $(id -u):$(id -g) ...
```

### Database Locked

```bash
# Check for running processes
docker exec gao-dev ps aux | grep gao-dev

# Reset database lock
docker exec gao-dev rm -f /app/.gao-dev/documents.db-journal
```

See [Common Errors](../troubleshooting/common-errors.md) for more solutions.

## Security Considerations

1. **Never commit secrets**: Use environment variables or secret managers
2. **Use read-only mounts**: For custom prompts/agents
3. **Limit resources**: Set memory and CPU limits
4. **Regular updates**: Keep base image updated
5. **Network isolation**: Use internal networks where possible

---

**Last Updated**: 2025-11-19
