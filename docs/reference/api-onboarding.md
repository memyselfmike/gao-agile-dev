# API Reference: Onboarding Endpoints

OpenAPI specification and examples for GAO-Dev onboarding and setup endpoints.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview

The GAO-Dev web interface exposes REST endpoints for onboarding and configuration. These endpoints are used by both the web UI and can be called directly for automation.

**Base URL:** `http://localhost:8080/api/v1`

**Content Type:** `application/json`

## Authentication

Most onboarding endpoints don't require authentication as they're used for initial setup. Session-based authentication is used after setup.

```bash
# No authentication required for setup endpoints
curl http://localhost:8080/api/v1/health

# Session token required for protected endpoints
curl -H "Authorization: Bearer <session-token>" \
     http://localhost:8080/api/v1/projects
```

## Endpoints

### Health Check

Check system health and readiness.

```
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "database": "connected",
    "provider": "configured",
    "workflows": 55,
    "agents": 8
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Service unavailable

---

### Get Provider Options

List available AI providers for selection.

```
GET /api/v1/onboarding/providers
```

**Response:**
```json
{
  "providers": [
    {
      "id": "claude-code",
      "name": "Claude Code",
      "description": "Anthropic's Claude Code CLI",
      "requirements": {
        "cli": "claude",
        "api_key_env": "ANTHROPIC_API_KEY"
      },
      "available": true,
      "validation_status": "valid"
    },
    {
      "id": "opencode",
      "name": "OpenCode",
      "description": "OpenCode CLI with local models",
      "requirements": {
        "cli": "opencode"
      },
      "available": true,
      "validation_status": "valid"
    },
    {
      "id": "direct-api-anthropic",
      "name": "Direct API (Anthropic)",
      "description": "Direct Anthropic API calls",
      "requirements": {
        "api_key_env": "ANTHROPIC_API_KEY"
      },
      "available": false,
      "validation_status": "missing_api_key"
    }
  ]
}
```

---

### Validate Provider

Validate a specific provider configuration.

```
POST /api/v1/onboarding/providers/validate
```

**Request:**
```json
{
  "provider_id": "claude-code"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "provider_id": "claude-code",
  "details": {
    "cli_version": "1.0.5",
    "api_key_status": "configured",
    "model_available": true
  },
  "warnings": []
}
```

**Response (Failure):**
```json
{
  "valid": false,
  "provider_id": "claude-code",
  "errors": [
    {
      "code": "E102",
      "message": "Claude Code CLI not found",
      "fix_suggestion": "Install from https://claude.ai/code"
    }
  ],
  "warnings": []
}
```

---

### Set Provider

Configure the selected provider.

```
POST /api/v1/onboarding/providers
```

**Request:**
```json
{
  "provider_id": "claude-code",
  "config": {
    "model": "claude-sonnet-4-20250514"
  },
  "save_preference": true
}
```

**Response:**
```json
{
  "success": true,
  "provider": {
    "id": "claude-code",
    "backend": "anthropic",
    "model": "claude-sonnet-4-20250514"
  },
  "preference_saved": true,
  "preference_location": ".gao-dev/provider_preferences.yaml"
}
```

---

### Get Current Provider

Get the currently configured provider.

```
GET /api/v1/onboarding/providers/current
```

**Response:**
```json
{
  "provider": {
    "id": "claude-code",
    "backend": "anthropic",
    "model": "claude-sonnet-4-20250514"
  },
  "source": "preferences_file",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

### Initialize Project

Initialize GAO-Dev tracking in a directory.

```
POST /api/v1/onboarding/projects/init
```

**Request:**
```json
{
  "path": "/path/to/project",
  "project_type": "greenfield",
  "options": {
    "scale_level": 2,
    "language": "python",
    "create_docs": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "project": {
    "path": "/path/to/project",
    "name": "my-project",
    "gao_dev_dir": "/path/to/project/.gao-dev"
  },
  "created": [
    ".gao-dev/",
    ".gao-dev/documents.db",
    ".gao-dev/context.json",
    "docs/"
  ]
}
```

---

### Get Project Status

Get status of a project.

```
GET /api/v1/onboarding/projects/status
```

**Query Parameters:**
- `path` (optional) - Project path. Uses current directory if not specified.

**Response:**
```json
{
  "project": {
    "path": "/path/to/project",
    "name": "my-project",
    "status": "active",
    "scale_level": 2
  },
  "tracking": {
    "initialized": true,
    "documents": 15,
    "epics": 3,
    "stories": 12
  },
  "health": {
    "database": "connected",
    "consistency": "valid"
  }
}
```

---

### Detect Project Type

Auto-detect project type and suggest configuration.

```
POST /api/v1/onboarding/projects/detect
```

**Request:**
```json
{
  "path": "/path/to/project"
}
```

**Response:**
```json
{
  "detected": {
    "project_type": "brownfield",
    "languages": ["python", "javascript"],
    "frameworks": ["fastapi", "react"],
    "has_docs": true,
    "has_tests": true,
    "git_initialized": true
  },
  "suggestions": {
    "scale_level": 3,
    "recommended_workflows": ["analysis", "planning"],
    "agents": ["brian", "winston"]
  }
}
```

---

### Start Session

Start a new GAO-Dev session.

```
POST /api/v1/onboarding/sessions
```

**Request:**
```json
{
  "project_path": "/path/to/project"
}
```

**Response:**
```json
{
  "session": {
    "id": "sess_abc123",
    "project": "/path/to/project",
    "started_at": "2025-01-15T10:30:00Z"
  },
  "token": "eyJ...",
  "websocket_url": "ws://localhost:8080/ws/sess_abc123"
}
```

---

### Get Onboarding Checklist

Get checklist of onboarding steps.

```
GET /api/v1/onboarding/checklist
```

**Response:**
```json
{
  "checklist": [
    {
      "id": "provider_selected",
      "title": "Select AI Provider",
      "status": "completed",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "id": "project_initialized",
      "title": "Initialize Project",
      "status": "pending",
      "required": true
    },
    {
      "id": "first_conversation",
      "title": "Start First Conversation",
      "status": "pending",
      "required": false
    }
  ],
  "progress": {
    "completed": 1,
    "total": 3,
    "percentage": 33
  }
}
```

---

## Data Models

### Provider

```typescript
interface Provider {
  id: string;
  name: string;
  description: string;
  requirements: {
    cli?: string;
    api_key_env?: string;
  };
  available: boolean;
  validation_status: 'valid' | 'missing_cli' | 'missing_api_key' | 'invalid';
}
```

### ValidationResult

```typescript
interface ValidationResult {
  valid: boolean;
  provider_id: string;
  errors?: Array<{
    code: string;
    message: string;
    fix_suggestion?: string;
  }>;
  warnings?: string[];
  details?: Record<string, any>;
}
```

### Project

```typescript
interface Project {
  path: string;
  name: string;
  status: 'active' | 'archived' | 'uninitialized';
  scale_level: 0 | 1 | 2 | 3 | 4;
  gao_dev_dir?: string;
}
```

### Session

```typescript
interface Session {
  id: string;
  project: string;
  started_at: string;
  provider?: string;
  active: boolean;
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "E001",
    "message": "API key not found",
    "details": {
      "provider": "claude-code",
      "required_env": "ANTHROPIC_API_KEY"
    },
    "fix_suggestion": "Set environment variable: export ANTHROPIC_API_KEY=sk-..."
  }
}
```

**HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized (invalid token) |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Internal server error |
| 503 | Service unavailable |

## Examples

### Complete Onboarding Flow

```bash
# 1. Check system health
curl http://localhost:8080/api/v1/health

# 2. Get available providers
curl http://localhost:8080/api/v1/onboarding/providers

# 3. Validate selected provider
curl -X POST http://localhost:8080/api/v1/onboarding/providers/validate \
  -H "Content-Type: application/json" \
  -d '{"provider_id": "claude-code"}'

# 4. Set provider
curl -X POST http://localhost:8080/api/v1/onboarding/providers \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "claude-code",
    "save_preference": true
  }'

# 5. Initialize project
curl -X POST http://localhost:8080/api/v1/onboarding/projects/init \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project",
    "project_type": "greenfield",
    "options": {"scale_level": 2}
  }'

# 6. Start session
curl -X POST http://localhost:8080/api/v1/onboarding/sessions \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/path/to/project"}'
```

### Python Client Example

```python
import requests

class GAODevClient:
    def __init__(self, base_url="http://localhost:8080/api/v1"):
        self.base_url = base_url
        self.token = None

    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def get_providers(self):
        response = requests.get(f"{self.base_url}/onboarding/providers")
        return response.json()

    def set_provider(self, provider_id, save_preference=True):
        response = requests.post(
            f"{self.base_url}/onboarding/providers",
            json={
                "provider_id": provider_id,
                "save_preference": save_preference
            }
        )
        return response.json()

    def init_project(self, path, project_type="greenfield", scale_level=2):
        response = requests.post(
            f"{self.base_url}/onboarding/projects/init",
            json={
                "path": path,
                "project_type": project_type,
                "options": {"scale_level": scale_level}
            }
        )
        return response.json()

    def start_session(self, project_path):
        response = requests.post(
            f"{self.base_url}/onboarding/sessions",
            json={"project_path": project_path}
        )
        data = response.json()
        self.token = data.get("token")
        return data


# Usage
client = GAODevClient()

# Check health
print(client.health_check())

# Set up provider
client.set_provider("claude-code")

# Initialize project
client.init_project("/path/to/my-project")

# Start session
session = client.start_session("/path/to/my-project")
print(f"Session ID: {session['session']['id']}")
```

### JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8080/api/v1';

async function onboardingFlow() {
  // 1. Check health
  const health = await fetch(`${BASE_URL}/health`).then(r => r.json());
  console.log('Health:', health.status);

  // 2. Get and select provider
  const providers = await fetch(`${BASE_URL}/onboarding/providers`)
    .then(r => r.json());

  const selectedProvider = providers.providers.find(p => p.available);

  // 3. Set provider
  await fetch(`${BASE_URL}/onboarding/providers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider_id: selectedProvider.id,
      save_preference: true
    })
  });

  // 4. Initialize project
  const project = await fetch(`${BASE_URL}/onboarding/projects/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: '/path/to/project',
      project_type: 'greenfield',
      options: { scale_level: 2 }
    })
  }).then(r => r.json());

  console.log('Project initialized:', project.project.name);

  // 5. Start session
  const session = await fetch(`${BASE_URL}/onboarding/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      project_path: '/path/to/project'
    })
  }).then(r => r.json());

  return session;
}
```

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

```
GET /api/v1/openapi.json
```

Or in YAML format:

```
GET /api/v1/openapi.yaml
```

Import into tools like Swagger UI, Postman, or Insomnia for interactive documentation.

---

**See Also:**
- [Quick Start Guide](../getting-started/quick-start.md)
- [Web Interface Documentation](../features/browser-based-interface/README.md)
- [Environment Variables Reference](../guides/environment-variables.md)

---

**Last Updated**: 2025-11-19
