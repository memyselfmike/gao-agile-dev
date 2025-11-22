# Story 41.2: Web Wizard Backend API

## User Story

As a web frontend developer,
I want well-designed API endpoints for each onboarding step,
So that the web wizard can save progress, validate inputs, and complete setup.

## Acceptance Criteria

- [ ] AC1: `GET /api/onboarding/status` returns current onboarding state, environment, and available wizards
- [ ] AC2: `POST /api/onboarding/project` saves project configuration (name, type, description)
- [ ] AC3: `POST /api/onboarding/git` saves git configuration (name, email, init options)
- [ ] AC4: `POST /api/onboarding/provider` saves provider selection (provider, model)
- [ ] AC5: `POST /api/onboarding/credentials` validates and stores credentials
- [ ] AC6: `POST /api/onboarding/complete` finalizes onboarding and initializes project
- [ ] AC7: All endpoints return consistent response format with `success`, `message`, and `next_step`
- [ ] AC8: Validation errors return 400 status with detailed error messages
- [ ] AC9: Credentials endpoint never logs or returns the actual API key value
- [ ] AC10: Server supports "bootstrap mode" without project context
- [ ] AC11: After completion, server transitions to normal mode with full project context
- [ ] AC12: All endpoints accessible only from localhost (127.0.0.1)

## Technical Notes

### Implementation Details

Create `gao_dev/web/api/onboarding.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

class ProjectConfig(BaseModel):
    name: str
    type: str = "greenfield"
    description: Optional[str] = None

class ProjectConfigResponse(BaseModel):
    success: bool
    message: str
    next_step: str = "git"

@router.get("/status")
async def get_onboarding_status() -> OnboardingStatus:
    """Get current onboarding state and environment."""
    pass

@router.post("/project")
async def configure_project(config: ProjectConfig) -> ProjectConfigResponse:
    """Step 1: Configure project name and type."""
    pass

@router.post("/git")
async def configure_git(config: GitConfig) -> GitConfigResponse:
    """Step 2: Configure git user information."""
    pass

@router.post("/provider")
async def select_provider(config: ProviderConfig) -> ProviderConfigResponse:
    """Step 3: Select AI provider and model."""
    pass

@router.post("/credentials")
async def configure_credentials(config: CredentialsConfig) -> CredentialsResponse:
    """Step 4: Validate and store credentials."""
    pass

@router.post("/complete")
async def complete_onboarding() -> CompleteResponse:
    """Finalize onboarding and initialize project."""
    pass
```

### Request/Response Models

```python
class OnboardingStatus(BaseModel):
    completed: bool
    current_step: Optional[str]
    steps_completed: List[str]
    environment: str
    available_wizards: List[str]

class GitConfig(BaseModel):
    name: str
    email: EmailStr
    init_repository: bool = True
    create_initial_commit: bool = True
    set_global: bool = False

class ProviderConfig(BaseModel):
    provider: str  # "claude-code", "opencode", "direct-api", "ollama"
    model: str
    requires_api_key: bool

class CredentialsConfig(BaseModel):
    provider: str
    api_key: Optional[str] = None  # None if using environment variable
    use_environment: bool = False
```

### Security Considerations

- Bind to 127.0.0.1 only during onboarding
- Never log API key values
- Validate all input with Pydantic
- Rate limit validation endpoint to prevent brute force

### Bootstrap Mode

Server starts with limited routes in bootstrap mode:
- `/api/onboarding/*` - All onboarding endpoints
- `/api/health` - Health check
- Static files for wizard frontend

After `complete` is called, server hot-reloads with full project context.

## Test Scenarios

1. **Status endpoint**: Given onboarding in progress, When `GET /status` called, Then returns current step and completed steps

2. **Project validation**: Given invalid project name with special characters, When `POST /project` called, Then returns 400 with validation error

3. **Git config**: Given valid git config, When `POST /git` called, Then saves config and returns next_step="provider"

4. **Provider selection**: Given valid provider config, When `POST /provider` called, Then saves selection and indicates API key requirement

5. **Credential validation**: Given valid API key, When `POST /credentials` called, Then validates with provider and stores securely

6. **Invalid API key**: Given invalid API key, When `POST /credentials` called, Then returns 400 with "Invalid API key" message

7. **Complete onboarding**: Given all steps complete, When `POST /complete` called, Then initializes project and transitions server

8. **Environment variable credential**: Given `use_environment=true`, When `POST /credentials` called, Then validates env var without storing

9. **Localhost only**: Given request from non-localhost IP, When any endpoint called, Then returns 403 Forbidden

10. **Response consistency**: Given any endpoint, When called, Then response includes `success`, `message` fields

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for API endpoints
- [ ] OpenAPI documentation generated
- [ ] Security review completed
- [ ] Code reviewed
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 40.3: StartupOrchestrator (for bootstrap mode)
- Story 41.4: CredentialManager (for credential storage)
- Story 41.5: Onboarding State Persistence
- Story 41.6: API Key Validation

## Notes

- Consider WebSocket for real-time validation feedback
- Use Pydantic for all request/response validation
- Document API with OpenAPI/Swagger
- Ensure idempotent behavior for all POST endpoints
- Consider adding `PUT` endpoints for updating previous steps
