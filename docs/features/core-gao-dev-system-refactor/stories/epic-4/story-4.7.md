# Story 4.7: Create Example Plugins and Dev Guide

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 4
**Priority**: P1 (High)
**Status**: Done

---

## User Story

**As a** plugin developer
**I want** comprehensive examples and documentation
**So that** I can quickly create custom plugins without deep system knowledge

---

## Description

Create complete, production-quality example plugins and comprehensive developer documentation. This serves as both validation of the plugin API and as a template/reference for community plugin developers.

**Current State**: Basic example plugins exist for testing but lack comprehensive documentation and real-world use cases.

**Target State**: 3+ example plugins demonstrating different plugin types, hooks, permissions, and use cases. Complete plugin development guide with API reference.

---

## Acceptance Criteria

### Example Plugins

- [ ] **Example 1: Custom Agent Plugin** (complete implementation)
  - Name: `sentiment-analysis-agent`
  - Purpose: Analyze text sentiment in code reviews
  - Demonstrates: Agent plugin, permissions, configuration
  - Location: `examples/plugins/sentiment_analysis_agent/`
  - Features:
    - Custom agent with specialized tools
    - FILE_READ permission for analyzing files
    - Configuration via plugin.yaml
    - README with installation and usage
    - Complete test suite

- [ ] **Example 2: Custom Workflow Plugin** (complete implementation)
  - Name: `api-doc-generator-workflow`
  - Purpose: Generate API documentation from code
  - Demonstrates: Workflow plugin, hooks, multi-phase workflow
  - Location: `examples/plugins/api_doc_generator/`
  - Features:
    - Multi-step workflow implementation
    - Hooks into WORKFLOW_START for preprocessing
    - FILE_READ and FILE_WRITE permissions
    - Tool integration (Read, Write, Grep)
    - README with usage examples

- [ ] **Example 3: Monitoring Plugin** (complete implementation)
  - Name: `workflow-metrics-plugin`
  - Purpose: Collect and export workflow metrics
  - Demonstrates: Hooks, event listening, no agent/workflow
  - Location: `examples/plugins/workflow_metrics/`
  - Features:
    - Registers hooks for lifecycle events
    - Collects timing and success metrics
    - DATABASE_WRITE permission for storing metrics
    - No custom agent/workflow (pure event listener)
    - README with metrics explanation

### Plugin Development Guide

- [ ] **Main guide created**: `docs/plugin-development-guide.md`
  - Table of contents with clear sections
  - Getting started (5 minute quick start)
  - Plugin types explained (agent, workflow, hooks-only)
  - API reference for all base classes
  - Permission system explained
  - Hook system explained
  - Best practices and patterns
  - Troubleshooting common issues
  - < 5000 words (concise but comprehensive)

### Guide Sections

- [ ] **1. Introduction**
  - What are GAO-Dev plugins?
  - Use cases for plugins
  - Plugin architecture overview

- [ ] **2. Quick Start**
  - Prerequisites (Python, GAO-Dev installed)
  - Create your first plugin (5 min tutorial)
  - Directory structure
  - plugin.yaml format
  - Load and test your plugin

- [ ] **3. Plugin Types**
  - Agent plugins (BaseAgentPlugin)
  - Workflow plugins (BaseWorkflowPlugin)
  - Hook-only plugins (BasePlugin)
  - Choosing the right type

- [ ] **4. Core Concepts**
  - Plugin discovery and loading
  - Lifecycle methods (initialize, cleanup)
  - Permissions and security
  - Configuration management
  - Error handling

- [ ] **5. Agent Plugins**
  - BaseAgentPlugin API reference
  - Creating custom agents
  - Agent metadata (role, tools, capabilities)
  - Example: Sentiment analysis agent
  - Testing agent plugins

- [ ] **6. Workflow Plugins**
  - BaseWorkflowPlugin API reference
  - Creating custom workflows
  - Workflow metadata (phase, tags, tools)
  - Multi-step workflows
  - Example: API doc generator
  - Testing workflow plugins

- [ ] **7. Hooks System**
  - Hook event types reference
  - Registering hooks
  - Hook execution order (priority)
  - Event data format for each hook type
  - Example: Metrics collection plugin
  - Async vs sync hooks

- [ ] **8. Permissions**
  - Permission system overview
  - Available permissions (FILE_READ, etc.)
  - Declaring permissions in plugin.yaml
  - Runtime permission checks
  - Permission best practices

- [ ] **9. Configuration**
  - plugin.yaml complete schema
  - Required vs optional fields
  - Versioning and dependencies
  - Timeout configuration
  - Example configurations

- [ ] **10. Testing**
  - Unit testing plugins
  - Integration testing with GAO-Dev
  - Fixtures and mocks
  - Test coverage requirements
  - Example test suites

- [ ] **11. Best Practices**
  - Plugin naming conventions
  - Code organization
  - Error handling patterns
  - Logging best practices
  - Performance considerations
  - Backward compatibility

- [ ] **12. Troubleshooting**
  - Common errors and solutions
  - Plugin not discovered (reasons and fixes)
  - Permission denied errors
  - Timeout errors
  - Import errors
  - Debugging techniques

- [ ] **13. API Reference**
  - BasePlugin class reference
  - BaseAgentPlugin class reference
  - BaseWorkflowPlugin class reference
  - HookManager class reference
  - PluginMetadata reference
  - All permission types
  - All hook event types

### Plugin Template

- [ ] **Template created**: `examples/plugin-template/`
  - Copyable template with placeholders
  - Clear instructions for customization
  - Works out-of-the-box as test plugin
  - README with customization guide

### Testing Documentation

- [ ] **Each example plugin** has tests:
  - Unit tests (80%+ coverage)
  - Integration test with GAO-Dev
  - Test README explaining test approach

### Installation Guide

- [ ] **Plugin installation guide** section:
  - Installing from local directory
  - Installing from git repository
  - Plugin directory configuration
  - Enabling/disabling plugins
  - Verifying plugin loaded

---

## Technical Details

### Example Plugin Structures

#### Example 1: Sentiment Analysis Agent

```
examples/plugins/sentiment_analysis_agent/
  __init__.py
  plugin.yaml                    # Metadata with permissions
  agent.py                       # IAgent implementation
  agent_plugin.py                # BaseAgentPlugin implementation
  sentiment_analyzer.py          # Core logic
  requirements.txt               # textblob, etc.
  README.md                      # Complete usage guide
  tests/
    __init__.py
    test_sentiment_agent.py
    test_integration.py
```

plugin.yaml:
```yaml
name: sentiment-analysis-agent
version: 1.0.0
type: agent
entry_point: sentiment_analysis_agent.agent_plugin.SentimentAnalysisAgentPlugin
description: "Analyzes code review comments for sentiment"
author: "GAO-Dev Team"
enabled: true
permissions:
  - file:read
  - config:read
timeout_seconds: 30
```

#### Example 2: API Doc Generator Workflow

```
examples/plugins/api_doc_generator/
  __init__.py
  plugin.yaml
  workflow.py                    # IWorkflow implementation
  workflow_plugin.py             # BaseWorkflowPlugin implementation
  doc_generator.py               # Core generation logic
  templates/
    api_doc_template.md
  README.md
  tests/
    __init__.py
    test_workflow.py
    test_integration.py
```

#### Example 3: Workflow Metrics Plugin

```
examples/plugins/workflow_metrics/
  __init__.py
  plugin.yaml
  metrics_plugin.py              # BasePlugin with hooks only
  metrics_collector.py           # Core metrics logic
  models.py                      # Metric data models
  README.md
  tests/
    __init__.py
    test_metrics.py
```

### Plugin Development Guide Structure

```markdown
# GAO-Dev Plugin Development Guide

## Table of Contents
- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Plugin Types](#plugin-types)
- [Core Concepts](#core-concepts)
- [Agent Plugins](#agent-plugins)
- [Workflow Plugins](#workflow-plugins)
- [Hooks System](#hooks-system)
- [Permissions](#permissions)
- [Configuration](#configuration)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Introduction

GAO-Dev's plugin system allows you to extend the platform with custom agents, workflows, and integrations without modifying core code...

## Quick Start

Create your first plugin in 5 minutes:

1. Create plugin directory:
   ```bash
   mkdir -p plugins/my_plugin
   cd plugins/my_plugin
   ```

2. Create `plugin.yaml`:
   ```yaml
   name: my-plugin
   version: 1.0.0
   type: agent
   entry_point: my_plugin.plugin.MyPlugin
   ```

3. Create `__init__.py` and `plugin.py`:
   ```python
   from gao_dev.plugins import BaseAgentPlugin
   # ... implementation ...
   ```

4. Test your plugin:
   ```bash
   gao-dev load-plugins
   gao-dev list-agents  # Your plugin agent should appear
   ```

...

## API Reference

### BasePlugin

Base class for all plugins.

**Methods:**

- `initialize() -> bool`
  - Called after plugin is loaded
  - Return False to prevent plugin activation
  - Use for setup (connections, resources)
  - Optional (default returns True)

- `cleanup() -> None`
  - Called before plugin is unloaded
  - Use for teardown (close connections, free resources)
  - Optional

- `register_hooks() -> None`
  - Called after initialize()
  - Register hook handlers for lifecycle events
  - Access via `self._hook_manager`
  - Optional

...
```

---

## Dependencies

- **Depends On**:
  - Story 4.1 complete (PluginDiscovery)
  - Story 4.2 complete (PluginLoader)
  - Story 4.3 complete (BaseAgentPlugin)
  - Story 4.4 complete (BaseWorkflowPlugin)
  - Story 4.5 complete (Hooks)
  - Story 4.6 complete (Security/Permissions)

- **Blocks**: Nothing (final story in Epic 4)

---

## Definition of Done

- [ ] 3+ complete example plugins implemented
- [ ] Each example plugin has README
- [ ] Each example plugin has tests (80%+ coverage)
- [ ] Plugin development guide created (< 5000 words)
- [ ] Guide covers all 13 sections
- [ ] API reference complete for all classes
- [ ] Plugin template created and documented
- [ ] Examples demonstrate all major features
- [ ] Installation guide included
- [ ] Troubleshooting section comprehensive
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

### Example Plugins

1. `examples/plugins/sentiment_analysis_agent/` (complete plugin)
2. `examples/plugins/api_doc_generator/` (complete plugin)
3. `examples/plugins/workflow_metrics/` (complete plugin)
4. `examples/plugin-template/` (copyable template)

### Documentation

5. `docs/plugin-development-guide.md` (comprehensive guide)
6. `docs/plugin-api-reference.md` (detailed API reference)
7. `examples/README.md` (overview of examples)

### Tests

8. `examples/plugins/sentiment_analysis_agent/tests/`
9. `examples/plugins/api_doc_generator/tests/`
10. `examples/plugins/workflow_metrics/tests/`

---

## Files to Modify

1. `README.md` - Add link to plugin development guide
2. `docs/README.md` - Add plugin documentation section

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.6 - Implement Plugin Security and Sandboxing
- **Next Epic**: Epic 5 - Methodology Abstraction
- **Documentation**: Plugin Development Guide, API Reference

---

## Test Plan

### Example Plugin Tests

1. **Test each example plugin**:
   - Loads successfully
   - Initializes without errors
   - Executes core functionality
   - Cleanup works properly
   - Permissions enforced correctly

2. **Integration tests**:
   - Sentiment agent analyzes test file
   - API doc workflow generates documentation
   - Metrics plugin collects workflow data
   - All hooks fire correctly

### Documentation Tests

1. **Quick start tutorial**:
   - Follow quick start guide exactly
   - Verify created plugin loads
   - Verify it executes

2. **Template verification**:
   - Copy plugin template
   - Customize and load
   - Verify it works

---

## Success Metrics

- [ ] Plugin guide < 5000 words (concise)
- [ ] Quick start takes < 5 minutes
- [ ] 3 working example plugins
- [ ] Each example demonstrates different features
- [ ] API reference covers all public classes
- [ ] Troubleshooting covers common issues
- [ ] Examples have 80%+ test coverage

---

## Notes

- Examples should be production-quality (not just demos)
- Guide should be accessible to intermediate Python developers
- API reference generated from docstrings (where possible)
- Examples demonstrate real-world use cases
- Template is immediately usable
- Focus on clarity and completeness
- Include diagrams where helpful (plugin lifecycle, hook flow)
- Link to related documentation throughout guide
