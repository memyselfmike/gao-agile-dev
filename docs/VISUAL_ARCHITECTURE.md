# Visual Architecture Guide

**TL;DR**: Visual diagrams showing GAO-Dev's system architecture, workflow execution, agent collaboration, and data flow. All diagrams render automatically in GitHub.

**Quick Links**:
- [System Architecture](#system-architecture) - Component overview
- [Workflow Execution Flow](#workflow-execution-flow) - How workflows execute
- [Agent Collaboration](#agent-collaboration) - Multi-agent coordination
- [Web Interface Architecture](#web-interface-architecture) - Frontend/backend integration
- [Git-Integrated State Management](#git-integrated-state-management) - Atomic operations
- [Scale-Adaptive Routing](#scale-adaptive-routing) - Brian's decision logic

---

## System Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Commands]
        WebUI[Web Interface<br/>React 19 + TypeScript]
    end

    subgraph "Orchestration Layer"
        Brian[Brian<br/>Workflow Coordinator]
        Orchestrator[GAODevOrchestrator<br/>Main Engine]
        WorkflowExec[WorkflowExecutor<br/>Template Renderer]
    end

    subgraph "Agent Layer"
        Mary[Mary<br/>Business Analyst]
        John[John<br/>Product Manager]
        Winston[Winston<br/>Tech Architect]
        Sally[Sally<br/>UX Designer]
        Bob[Bob<br/>Scrum Master]
        Amelia[Amelia<br/>Developer]
        Murat[Murat<br/>Test Architect]
        Diana[Diana<br/>Doc Keeper]
    end

    subgraph "Service Layer"
        StateManager[GitIntegratedStateManager<br/>Atomic Operations]
        ContextLoader[FastContextLoader<br/>LRU Cache]
        GitManager[GitManager<br/>Git Operations]
        EventBus[WebEventBus<br/>WebSocket Events]
    end

    subgraph "Data Layer"
        FileSystem[File System<br/>docs/, src/, gao_dev/]
        Database[(SQLite Database<br/>.gao-dev/documents.db)]
        GitRepo[Git Repository<br/>.git/]
    end

    subgraph "External Services"
        Anthropic[Anthropic API<br/>Claude]
        OpenAI[OpenAI API<br/>GPT]
        Ollama[Ollama<br/>Local Models]
    end

    CLI --> Orchestrator
    WebUI --> EventBus
    WebUI --> Orchestrator

    Orchestrator --> Brian
    Brian --> WorkflowExec
    WorkflowExec --> Mary & John & Winston & Sally & Bob & Amelia & Murat & Diana

    Orchestrator --> StateManager
    Orchestrator --> ContextLoader
    StateManager --> GitManager
    StateManager --> EventBus

    StateManager --> FileSystem
    StateManager --> Database
    GitManager --> GitRepo

    Mary & John & Winston & Sally & Bob & Amelia & Murat & Diana --> Anthropic & OpenAI & Ollama

    style Brian fill:#4CAF50,color:#fff
    style WebUI fill:#2196F3,color:#fff
    style StateManager fill:#FF9800,color:#fff
    style EventBus fill:#9C27B0,color:#fff
```

### Technology Stack

```mermaid
graph LR
    subgraph "Frontend"
        React[React 19]
        TS[TypeScript]
        Vite[Vite]
        Zustand[Zustand]
        ShadcnUI[shadcn/ui]
        Monaco[Monaco Editor]
    end

    subgraph "Backend"
        Python[Python 3.11+]
        FastAPI[FastAPI]
        WebSocket[WebSocket]
        SQLite[SQLite]
        Structlog[structlog]
    end

    subgraph "Infrastructure"
        Git[Git]
        Docker[Docker]
        Pytest[pytest]
        MyPy[MyPy]
        Black[Black]
    end

    React --> TS
    TS --> Vite
    Zustand --> React
    ShadcnUI --> React
    Monaco --> React

    Python --> FastAPI
    FastAPI --> WebSocket
    Python --> SQLite
    Python --> Structlog

    Git --> Python
    Docker --> Python
    Pytest --> Python
    MyPy --> Python
    Black --> Python

    style React fill:#61DAFB,color:#000
    style FastAPI fill:#009688,color:#fff
    style Git fill:#F05032,color:#fff
```

---

## Workflow Execution Flow

### Complete Workflow Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Brian
    participant Orchestrator
    participant WorkflowExec
    participant Agent
    participant StateManager
    participant Git

    User->>Brian: "Build a todo app with auth"

    Note over Brian: 1. Analyze Request
    Brian->>Brian: Extract requirements
    Brian->>Brian: Determine scale level (0-4)
    Brian->>Brian: Select workflow sequence

    Note over Brian: Scale Level 4 detected<br/>Greenfield App

    Brian->>Orchestrator: Execute workflow sequence<br/>PRD → Architecture → Stories

    loop For each workflow
        Orchestrator->>WorkflowExec: Load workflow template
        WorkflowExec->>WorkflowExec: Resolve variables<br/>{{prd_location}} → docs/PRD.md
        WorkflowExec->>WorkflowExec: Render template with context

        WorkflowExec->>Agent: Execute with rendered instructions
        Agent->>Agent: Process request (LLM call)
        Agent->>StateManager: Create artifact

        StateManager->>StateManager: Validate file path
        StateManager->>StateManager: BEGIN TRANSACTION
        StateManager->>StateManager: Write file
        StateManager->>StateManager: Insert DB record
        StateManager->>Git: Stage + Commit
        StateManager->>StateManager: COMMIT TRANSACTION

        StateManager-->>Agent: Artifact created (atomic)
        Agent-->>WorkflowExec: Workflow complete
        WorkflowExec-->>Orchestrator: Success
    end

    Orchestrator->>Orchestrator: Collect metrics
    Orchestrator->>Orchestrator: Validate success criteria
    Orchestrator-->>Brian: All workflows complete
    Brian-->>User: ✅ Todo app scaffolded<br/>PRD, Architecture, 40+ stories
```

### Variable Resolution Priority

```mermaid
graph TD
    Start[Variable Needed<br/>e.g., {{prd_location}}]

    Start --> Runtime{1. Runtime<br/>Parameters?}
    Runtime -->|Yes| UseRuntime[Use Runtime Value]
    Runtime -->|No| Workflow{2. Workflow YAML<br/>Defaults?}

    Workflow -->|Yes| UseWorkflow[Use Workflow Value]
    Workflow -->|No| Config{3. Config<br/>Defaults?}

    Config -->|Yes| UseConfig[Use Config Value]
    Config -->|No| Common{4. Common<br/>Variables?}

    Common -->|Yes| UseCommon[Auto-generate<br/>date, project_name, etc.]
    Common -->|No| Error[❌ Unresolved Variable<br/>Fail workflow]

    UseRuntime --> Resolved[✅ Variable Resolved]
    UseWorkflow --> Resolved
    UseConfig --> Resolved
    UseCommon --> Resolved

    style Start fill:#2196F3,color:#fff
    style Resolved fill:#4CAF50,color:#fff
    style Error fill:#F44336,color:#fff
```

---

## Agent Collaboration

### Multi-Agent Ceremony Flow

```mermaid
sequenceDiagram
    participant User
    participant Brian
    participant Mary
    participant John
    participant Winston
    participant Bob
    participant StateManager

    User->>Brian: "I have a vague idea for an app"

    Brian->>Brian: Detect vague requirements
    Brian->>Mary: Trigger Vision Elicitation

    Note over Mary: Vision Elicitation Ceremony
    Mary->>User: Ask clarifying questions<br/>(Vision Canvas, 5W1H)
    User->>Mary: Provide answers
    Mary->>Mary: Synthesize vision
    Mary->>StateManager: Save vision.md

    Note over Mary,John: Handoff: Vision → PRD
    Mary->>John: Vision complete, create PRD

    Note over John: PRD Creation
    John->>John: Read vision.md
    John->>John: Create PRD structure
    John->>StateManager: Save PRD.md

    Note over John,Winston: Handoff: PRD → Architecture
    John->>Winston: PRD complete, create architecture

    Note over Winston: Architecture Design
    Winston->>Winston: Read PRD.md
    Winston->>Winston: Design system architecture
    Winston->>StateManager: Save ARCHITECTURE.md

    Note over Winston,Bob: Handoff: Architecture → Stories
    Winston->>Bob: Architecture complete, create stories

    Note over Bob: Story Creation
    Bob->>Bob: Read PRD.md + ARCHITECTURE.md
    Bob->>Bob: Break down into epics & stories

    loop For each story
        Bob->>StateManager: Create story file + DB record
    end

    Bob->>Brian: Stories ready for implementation
    Brian->>User: ✅ Project scoped: Vision → PRD → Architecture → 40+ stories
```

### Agent Specialization Matrix

```mermaid
graph LR
    subgraph "Discovery Phase"
        Mary[Mary<br/>Business Analyst<br/>⭐ Vision Elicitation<br/>⭐ Brainstorming<br/>⭐ Requirements]
    end

    subgraph "Planning Phase"
        John[John<br/>Product Manager<br/>⭐ PRDs<br/>⭐ Features<br/>⭐ Prioritization]

        Winston[Winston<br/>Architect<br/>⭐ System Design<br/>⭐ Tech Specs<br/>⭐ Patterns]

        Sally[Sally<br/>UX Designer<br/>⭐ Wireframes<br/>⭐ User Flows<br/>⭐ Design Systems]
    end

    subgraph "Execution Phase"
        Bob[Bob<br/>Scrum Master<br/>⭐ Stories<br/>⭐ Sprints<br/>⭐ Coordination]

        Amelia[Amelia<br/>Developer<br/>⭐ Implementation<br/>⭐ Code Reviews<br/>⭐ Testing]

        Murat[Murat<br/>Test Architect<br/>⭐ Test Strategy<br/>⭐ QA<br/>⭐ Automation]
    end

    subgraph "Support"
        Diana[Diana<br/>Doc Keeper<br/>⭐ Documentation<br/>⭐ Guides<br/>⭐ API Refs]

        Brian[Brian<br/>Coordinator<br/>⭐ Workflow Selection<br/>⭐ Scale Routing<br/>⭐ Orchestration]
    end

    Mary --> John
    John --> Winston & Sally
    Winston & Sally --> Bob
    Bob --> Amelia & Murat
    Amelia & Murat --> Diana

    Brian -.->|Coordinates| Mary & John & Winston & Sally & Bob & Amelia & Murat & Diana

    style Brian fill:#4CAF50,color:#fff
    style Mary fill:#E91E63,color:#fff
    style John fill:#2196F3,color:#fff
    style Winston fill:#FF9800,color:#fff
    style Sally fill:#9C27B0,color:#fff
    style Bob fill:#00BCD4,color:#fff
    style Amelia fill:#4CAF50,color:#fff
    style Murat fill:#F44336,color:#fff
    style Diana fill:#795548,color:#fff
```

---

## Web Interface Architecture

### Frontend-Backend Integration

```mermaid
graph TB
    subgraph "Browser (Frontend)"
        UI[React Components]
        Stores[Zustand Stores<br/>8 core stores]
        WSClient[WebSocket Client]
        APIClient[API Client<br/>fetch()]
    end

    subgraph "Server (Backend)"
        FastAPI[FastAPI Server<br/>:3000]
        APIRouters[REST API Routers<br/>50+ endpoints]
        WSManager[WebSocket Manager]
        EventBus[WebEventBus<br/>Event Aggregation]
    end

    subgraph "Business Logic"
        BrianAdapter[BrianWebAdapter<br/>Thin Delegation]
        ChatSession[ChatSession<br/>Epic 30]
        StateManager[GitIntegratedStateManager<br/>Atomic Operations]
        FileWatcher[FileSystemWatcher<br/>Real-time Detection]
    end

    subgraph "Data"
        Files[File System]
        DB[(SQLite DB)]
        Git[Git Repo]
    end

    UI --> Stores
    UI --> APIClient
    UI --> WSClient

    APIClient -->|HTTP| FastAPI
    WSClient -->|WebSocket| FastAPI

    FastAPI --> APIRouters
    FastAPI --> WSManager

    APIRouters --> BrianAdapter
    APIRouters --> StateManager
    WSManager --> EventBus

    BrianAdapter --> ChatSession
    ChatSession --> EventBus
    StateManager --> EventBus
    FileWatcher --> EventBus

    EventBus -->|Broadcast| WSManager
    WSManager -->|Push Events| WSClient
    WSClient --> Stores

    StateManager --> Files & DB & Git

    style UI fill:#61DAFB,color:#000
    style FastAPI fill:#009688,color:#fff
    style EventBus fill:#9C27B0,color:#fff
    style StateManager fill:#FF9800,color:#fff
```

### WebSocket Event Flow

```mermaid
sequenceDiagram
    participant User
    participant React
    participant WSClient
    participant WSManager
    participant EventBus
    participant Agent
    participant FileWatcher

    Note over User,FileWatcher: 1. User Sends Message
    User->>React: Type message + click send
    React->>WSClient: Send chat message
    WSClient->>WSManager: WebSocket message
    WSManager->>EventBus: Publish MESSAGE_SENT
    EventBus->>Agent: Process message

    Note over User,FileWatcher: 2. Agent Processes
    Agent->>Agent: LLM call (streaming)

    loop Streaming chunks
        Agent->>EventBus: Publish STREAMING_CHUNK
        EventBus->>WSManager: Broadcast chunk
        WSManager->>WSClient: Push chunk
        WSClient->>React: Update UI (streaming text)
    end

    Note over User,FileWatcher: 3. Agent Creates File
    Agent->>Agent: Create docs/PRD.md
    Agent->>EventBus: Publish MESSAGE_COMPLETE

    Note over User,FileWatcher: 4. File System Detection
    FileWatcher->>FileWatcher: Detect file change
    FileWatcher->>EventBus: Publish FILE_CREATED

    Note over User,FileWatcher: 5. Real-time UI Update
    EventBus->>WSManager: Broadcast FILE_CREATED
    WSManager->>WSClient: Push event
    WSClient->>React: Update file tree
    React->>User: Show new file in tree
```

---

## Git-Integrated State Management

### Atomic Transaction Flow

```mermaid
flowchart TD
    Start[Agent creates artifact]

    Start --> Validate{Validate<br/>File Path}
    Validate -->|Invalid| Reject[❌ Reject<br/>Path traversal detected]
    Validate -->|Valid| Begin[BEGIN TRANSACTION]

    Begin --> Step1[Step 1: Write File<br/>docs/epics/epic-1.md]
    Step1 --> Check1{Success?}
    Check1 -->|No| Rollback1[ROLLBACK<br/>Nothing to undo]
    Check1 -->|Yes| Step2[Step 2: Insert DB Record<br/>documents.db]

    Step2 --> Check2{Success?}
    Check2 -->|No| Rollback2[ROLLBACK<br/>1. Delete file]
    Check2 -->|Yes| Step3[Step 3: Git Commit<br/>git add + commit]

    Step3 --> Check3{Success?}
    Check3 -->|No| Rollback3[ROLLBACK<br/>1. Delete DB record<br/>2. Delete file]
    Check3 -->|Yes| Commit[COMMIT TRANSACTION]

    Commit --> Emit[Emit WebSocket Event<br/>EPIC_CREATED]
    Emit --> Success[✅ Success<br/>All 3 operations complete]

    Rollback1 --> Fail[❌ Failed<br/>No changes persisted]
    Rollback2 --> Fail
    Rollback3 --> Fail
    Reject --> Fail

    style Start fill:#2196F3,color:#fff
    style Success fill:#4CAF50,color:#fff
    style Fail fill:#F44336,color:#fff
    style Commit fill:#FF9800,color:#fff
```

### State Manager Architecture

```mermaid
graph TB
    subgraph "API Layer"
        CreateEpic[create_epic]
        CreateStory[create_story]
        UpdateStory[update_story]
        TransitionState[transition_state]
    end

    subgraph "GitIntegratedStateManager"
        Validator[Path Validator<br/>Security Check]
        TransactionMgr[Transaction Manager<br/>BEGIN/COMMIT/ROLLBACK]
        FileOps[File Operations<br/>Write/Read/Delete]
        DBOps[Database Operations<br/>Insert/Update/Delete]
        GitOps[Git Operations<br/>Stage/Commit]
        EventEmitter[Event Emitter<br/>WebSocket Events]
    end

    subgraph "Dependencies"
        GitManager[GitManager<br/>Git Commands]
        Database[(SQLite Database)]
        FileSystem[File System]
        EventBus[WebEventBus]
    end

    CreateEpic & CreateStory & UpdateStory & TransitionState --> Validator

    Validator --> TransactionMgr
    TransactionMgr --> FileOps
    TransactionMgr --> DBOps
    TransactionMgr --> GitOps
    TransactionMgr --> EventEmitter

    FileOps --> FileSystem
    DBOps --> Database
    GitOps --> GitManager
    GitManager --> FileSystem
    EventEmitter --> EventBus

    style Validator fill:#F44336,color:#fff
    style TransactionMgr fill:#FF9800,color:#fff
    style EventEmitter fill:#9C27B0,color:#fff
```

---

## Scale-Adaptive Routing

### Brian's Decision Logic

```mermaid
flowchart TD
    Start[User Prompt]

    Start --> Analyze[Brian: Analyze Request]
    Analyze --> Extract[Extract:<br/>- Requirements<br/>- Complexity<br/>- Scope]

    Extract --> EstimateStories{Estimate<br/>Story Count}

    EstimateStories -->|0 stories| Level0[Level 0: Chore<br/>Duration: <1 hour]
    EstimateStories -->|0-1 stories| Level1[Level 1: Bug Fix<br/>Duration: 1-4 hours]
    EstimateStories -->|3-8 stories| Level2[Level 2: Small Feature<br/>Duration: 1-2 weeks]
    EstimateStories -->|12-40 stories| Level3[Level 3: Medium Feature<br/>Duration: 1-2 months]
    EstimateStories -->|40+ stories| Level4[Level 4: Greenfield App<br/>Duration: 2-6 months]

    Level0 --> W0[Workflows:<br/>Direct execution<br/>No planning]
    Level1 --> W1[Workflows:<br/>Minimal planning<br/>Retro on failure]
    Level2 --> W2[Workflows:<br/>PRD → Arch → Stories<br/>Optional ceremonies]
    Level3 --> W3[Workflows:<br/>Full BMAD<br/>Planning + Retros]
    Level4 --> W4[Workflows:<br/>Comprehensive<br/>Full ceremonies]

    W0 --> Execute[Execute Workflow Sequence]
    W1 --> Execute
    W2 --> Execute
    W3 --> Execute
    W4 --> Execute

    Execute --> Orchestrate[Orchestrate Agents]
    Orchestrate --> Deliver[Deliver Artifacts]

    style Start fill:#2196F3,color:#fff
    style Analyze fill:#4CAF50,color:#fff
    style Level0 fill:#9E9E9E,color:#fff
    style Level1 fill:#03A9F4,color:#fff
    style Level2 fill:#FF9800,color:#fff
    style Level3 fill:#F44336,color:#fff
    style Level4 fill:#9C27B0,color:#fff
```

### Workflow Selection Matrix

```mermaid
graph TB
    subgraph "Scale Level 0 - Chore"
        C0[Direct Execution<br/>No workflows needed]
    end

    subgraph "Scale Level 1 - Bug Fix"
        C1[1. Diagnose<br/>2. Fix<br/>3. Test<br/>4. Retro on failure]
    end

    subgraph "Scale Level 2 - Small Feature"
        C2[1. Create PRD<br/>2. Create Architecture<br/>3. Create Stories<br/>4. Implement<br/>5. Optional Retro]
    end

    subgraph "Scale Level 3 - Medium Feature"
        C3[1. Vision Elicitation Mary<br/>2. Create PRD John<br/>3. Create Architecture Winston<br/>4. Create Stories Bob<br/>5. Planning Ceremony<br/>6. Implementation Amelia<br/>7. Retrospective]
    end

    subgraph "Scale Level 4 - Greenfield App"
        C4[1. Vision Elicitation Mary<br/>2. Brainstorming Mary<br/>3. Create PRD John<br/>4. Create Architecture Winston<br/>5. UX Design Sally<br/>6. Create Stories Bob<br/>7. Planning Ceremony<br/>8. Implementation Amelia<br/>9. Testing Strategy Murat<br/>10. Daily Standups<br/>11. Sprint Reviews<br/>12. Retrospectives]
    end

    style C0 fill:#9E9E9E,color:#fff
    style C1 fill:#03A9F4,color:#fff
    style C2 fill:#FF9800,color:#fff
    style C3 fill:#F44336,color:#fff
    style C4 fill:#9C27B0,color:#fff
```

---

## Performance Characteristics

### Context Loading Performance

```mermaid
graph LR
    subgraph "First Request (Cache Miss)"
        R1[Request File]
        R1 --> FS1[Read from FileSystem<br/>~50ms]
        FS1 --> Cache1[Store in LRU Cache<br/>~1ms]
        Cache1 --> Return1[Return Content<br/>Total: ~51ms]
    end

    subgraph "Subsequent Requests (Cache Hit)"
        R2[Request Same File]
        R2 --> Cache2[Read from LRU Cache<br/>~4ms]
        Cache2 --> Return2[Return Content<br/>Total: ~4ms]
    end

    style R1 fill:#F44336,color:#fff
    style R2 fill:#4CAF50,color:#fff
    style Cache1 fill:#FF9800,color:#fff
    style Cache2 fill:#4CAF50,color:#fff
```

### Cache Statistics (Production)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Cache Hit Rate** | >80% | >85% | ✅ Exceeded |
| **Cache Hit Latency** | <5ms | ~4ms | ✅ Exceeded |
| **Cache Miss Latency** | <50ms | ~45ms | ✅ Exceeded |
| **Cache Size** | 128 entries | 128 entries | ✅ Met |

---

## Deployment Architecture

### Multi-Environment Support

```mermaid
graph TB
    subgraph "Desktop Environment"
        Desktop[Desktop Browser]
        Desktop --> WebWizard[Web Wizard<br/>Visual onboarding]
        WebWizard --> Desktop
    end

    subgraph "Docker Environment"
        Docker[Docker Container]
        Docker --> TUIWizard[TUI Wizard<br/>Terminal onboarding]
        TUIWizard --> Docker
    end

    subgraph "SSH/Remote Environment"
        SSH[SSH Session]
        SSH --> TUIWizard2[TUI Wizard<br/>Terminal onboarding]
        TUIWizard2 --> SSH
    end

    subgraph "CI/CD Environment"
        CICD[CI/CD Pipeline]
        CICD --> Headless[Headless Mode<br/>Env vars only]
        Headless --> CICD
    end

    subgraph "GAO-Dev Core"
        Core[gao-dev start<br/>Unified Entry Point]
        EnvDetect[Environment Detection]

        Core --> EnvDetect
        EnvDetect -->|GUI available| WebWizard
        EnvDetect -->|Terminal only| TUIWizard & TUIWizard2
        EnvDetect -->|GAO_DEV_HEADLESS=1| Headless
    end

    style Core fill:#4CAF50,color:#fff
    style EnvDetect fill:#FF9800,color:#fff
    style WebWizard fill:#2196F3,color:#fff
    style TUIWizard fill:#9C27B0,color:#fff
    style TUIWizard2 fill:#9C27B0,color:#fff
    style Headless fill:#607D8B,color:#fff
```

---

## See Also

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) - Text-based architecture description
- [Quick Start Guide](QUICK_START.md) - Integration examples
- [API Reference](API_REFERENCE.md) - Complete endpoint catalog
- [Development Patterns](developers/DEVELOPMENT_PATTERNS.md) - Development workflow
- [Web Interface Architecture](features/web-interface/ARCHITECTURE.md) - Detailed web specs
- [Git-Integrated Hybrid Wisdom](features/git-integrated-hybrid-wisdom/) - State management details

---

**Note**: All diagrams are rendered automatically in GitHub using Mermaid. If viewing locally, use a Mermaid-compatible markdown viewer or GitHub preview.
