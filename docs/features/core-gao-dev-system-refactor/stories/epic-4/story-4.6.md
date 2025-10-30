# Story 4.6: Implement Plugin Security and Sandboxing

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Done

---

## User Story

**As a** system administrator
**I want** plugins to run in a secure sandbox
**So that** malicious or buggy plugins cannot harm the system or access unauthorized resources

---

## Description

Implement security controls and sandboxing for the plugin system. This includes permission management, resource limits, timeout controls, and validation to prevent malicious plugins from compromising system integrity.

**Current State**: Plugins have unrestricted access to system resources. No security controls exist.

**Target State**: PluginSandbox enforces permissions, timeouts, and resource limits. Plugins declare required permissions and are validated before loading.

---

## Acceptance Criteria

### PluginSandbox Implementation

- [ ] **Class created**: `gao_dev/plugins/sandbox.py`
- [ ] **Size**: < 350 lines
- [ ] **Single responsibility**: Enforce plugin security and resource limits

### Core Methods

- [ ] **validate_plugin(metadata)** -> ValidationResult
  - Check plugin metadata for security issues
  - Validate entry point format
  - Check for suspicious code patterns (import os, subprocess, etc.)
  - Verify plugin signature (if configured)
  - Return validation result with warnings/errors

- [ ] **check_permissions(plugin, operation)** -> bool
  - Verify plugin has permission for operation
  - Operations: FILE_READ, FILE_WRITE, NETWORK, SUBPROCESS, HOOK
  - Plugins declare required permissions in plugin.yaml
  - Return true if permitted, false otherwise

- [ ] **execute_with_timeout(func, timeout_seconds)** -> Any
  - Execute function with timeout limit
  - Use threading/multiprocessing for isolation
  - Raise TimeoutError if exceeded
  - Clean up resources on timeout

- [ ] **monitor_resources(plugin)** -> ResourceUsage
  - Track plugin CPU, memory, I/O usage
  - Warning logs if thresholds exceeded
  - Option to terminate excessive plugins
  - Return resource usage metrics

### Permission System

- [ ] **PluginPermission enum** created:
  - FILE_READ = "file:read"
  - FILE_WRITE = "file:write"
  - FILE_DELETE = "file:delete"
  - NETWORK_REQUEST = "network:request"
  - SUBPROCESS_EXECUTE = "subprocess:execute"
  - HOOK_REGISTER = "hook:register"
  - CONFIG_READ = "config:read"
  - CONFIG_WRITE = "config:write"
  - DATABASE_READ = "database:read"
  - DATABASE_WRITE = "database:write"

- [ ] **plugin.yaml permissions field** supported:
  ```yaml
  permissions:
    - file:read
    - file:write
    - hook:register
  ```

- [ ] **Permission validation** before plugin operations:
  - Check declared permissions before file access
  - Check before network requests
  - Check before subprocess execution
  - Raise PermissionDeniedError if not permitted

### Timeout Controls

- [ ] **Plugin initialization timeout**: 30 seconds default
  - Configurable via plugin.yaml
  - Kill plugin if initialization exceeds timeout
  - Log timeout error

- [ ] **Hook execution timeout**: 5 seconds default per hook
  - Configurable via config
  - Cancel hook execution if exceeded
  - Log timeout warning

- [ ] **Workflow/Agent execution timeout**: 300 seconds default
  - Configurable per plugin
  - Terminate if exceeded
  - Log timeout error

### Resource Limits

- [ ] **Memory limit**: 500MB default per plugin
  - Configurable via config
  - Warning log at 80% threshold
  - Option to terminate at 100%

- [ ] **CPU limit**: 80% of one core default
  - Configurable via config
  - Warning log if sustained high usage

- [ ] **File size limit**: 100MB default for file operations
  - Prevent plugins from creating huge files
  - Raise FileSizeError if exceeded

### Code Validation

- [ ] **Static analysis** of plugin code:
  - Scan for dangerous imports (os.system, subprocess.call, eval, exec)
  - Scan for file system manipulation (shutil.rmtree, os.remove)
  - Scan for network access (urllib, requests, socket)
  - Issue warnings (don't block, just inform)

- [ ] **Entry point validation**:
  - Verify entry point class exists
  - Verify class inherits from appropriate base (BaseAgentPlugin, etc.)
  - Reject invalid entry points

### PluginLoader Integration

- [ ] **Sandbox enforcement** in PluginLoader:
  - Validate plugin before loading
  - Check permissions before operations
  - Apply timeouts to initialization
  - Monitor resource usage during execution
  - Unload plugin if violations detected

- [ ] **Sandboxed plugin execution**:
  - Plugin methods wrapped with permission checks
  - Timeout enforced on all plugin calls
  - Resource monitoring during execution
  - Automatic cleanup on violations

### Testing

- [ ] Unit tests for PluginSandbox (85%+ coverage)
- [ ] Unit tests for permission checks
- [ ] Unit tests for timeout enforcement
- [ ] Unit tests for resource monitoring
- [ ] Integration test: Plugin denied permission raises error
- [ ] Integration test: Plugin timeout terminates gracefully
- [ ] Integration test: Valid plugin with permissions loads successfully
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create PluginSandbox class**:
   ```python
   class PluginSandbox:
       """Enforces security and resource limits for plugins.

       Provides permission management, timeout controls, and resource
       monitoring to prevent malicious or buggy plugins from harming
       the system.
       """

       def __init__(self, config: Optional[Dict[str, Any]] = None):
           self.config = config or {}
           self._resource_monitor = ResourceMonitor()
           self._permission_manager = PermissionManager()

       def validate_plugin(self, metadata: PluginMetadata) -> ValidationResult:
           """Validate plugin for security issues."""
           errors = []
           warnings = []

           # Validate entry point format
           if not self._is_valid_entry_point(metadata.entry_point):
               errors.append(f"Invalid entry point format: {metadata.entry_point}")

           # Check for suspicious code patterns
           plugin_path = metadata.plugin_path
           if plugin_path.exists():
               code_warnings = self._scan_plugin_code(plugin_path)
               warnings.extend(code_warnings)

           # Validate permissions
           if metadata.permissions:
               for perm in metadata.permissions:
                   if not self._is_valid_permission(perm):
                       errors.append(f"Invalid permission: {perm}")

           return ValidationResult(
               valid=len(errors) == 0,
               errors=errors,
               warnings=warnings
           )

       def check_permission(
           self,
           plugin_name: str,
           operation: PluginPermission
       ) -> bool:
           """Check if plugin has permission for operation."""
           return self._permission_manager.has_permission(plugin_name, operation)

       async def execute_with_timeout(
           self,
           func: Callable,
           timeout_seconds: float,
           *args,
           **kwargs
       ) -> Any:
           """Execute function with timeout."""
           try:
               if asyncio.iscoroutinefunction(func):
                   result = await asyncio.wait_for(
                       func(*args, **kwargs),
                       timeout=timeout_seconds
                   )
               else:
                   loop = asyncio.get_event_loop()
                   result = await asyncio.wait_for(
                       loop.run_in_executor(None, func, *args, **kwargs),
                       timeout=timeout_seconds
                   )
               return result

           except asyncio.TimeoutError:
               logger.error(
                   "plugin_timeout",
                   function=func.__name__,
                   timeout=timeout_seconds
               )
               raise PluginTimeoutError(
                   f"Plugin execution exceeded timeout of {timeout_seconds}s"
               )

       def _scan_plugin_code(self, plugin_path: Path) -> List[str]:
           """Scan plugin code for security issues."""
           warnings = []

           for py_file in plugin_path.glob("**/*.py"):
               try:
                   code = py_file.read_text()

                   # Check for dangerous patterns
                   if "os.system" in code or "subprocess.call" in code:
                       warnings.append(
                           f"{py_file.name}: Uses subprocess execution"
                       )
                   if "eval(" in code or "exec(" in code:
                       warnings.append(
                           f"{py_file.name}: Uses dynamic code execution"
                       )
                   if "shutil.rmtree" in code or "__import__" in code:
                       warnings.append(
                           f"{py_file.name}: Uses dangerous file operations"
                       )

               except Exception as e:
                   logger.warning("code_scan_failed", file=str(py_file), error=str(e))

           return warnings
   ```

2. **Create PermissionManager**:
   ```python
   class PermissionManager:
       """Manages plugin permissions."""

       def __init__(self):
           self._permissions: Dict[str, Set[PluginPermission]] = {}

       def grant_permissions(
           self,
           plugin_name: str,
           permissions: List[str]
       ) -> None:
           """Grant permissions to plugin."""
           if plugin_name not in self._permissions:
               self._permissions[plugin_name] = set()

           for perm_str in permissions:
               try:
                   perm = PluginPermission(perm_str)
                   self._permissions[plugin_name].add(perm)
               except ValueError:
                   logger.warning(
                       "invalid_permission",
                       plugin=plugin_name,
                       permission=perm_str
                   )

       def has_permission(
           self,
           plugin_name: str,
           operation: PluginPermission
       ) -> bool:
           """Check if plugin has permission."""
           return operation in self._permissions.get(plugin_name, set())

       def revoke_all_permissions(self, plugin_name: str) -> None:
           """Revoke all permissions from plugin."""
           if plugin_name in self._permissions:
               del self._permissions[plugin_name]
   ```

3. **Create ResourceMonitor**:
   ```python
   class ResourceMonitor:
       """Monitors plugin resource usage."""

       def __init__(self):
           self._usage: Dict[str, ResourceUsage] = {}

       def start_monitoring(self, plugin_name: str) -> None:
           """Start monitoring plugin resource usage."""
           self._usage[plugin_name] = ResourceUsage(
               cpu_percent=0.0,
               memory_mb=0.0,
               start_time=time.time()
           )

       def get_usage(self, plugin_name: str) -> Optional[ResourceUsage]:
           """Get current resource usage."""
           return self._usage.get(plugin_name)

       def check_limits(
           self,
           plugin_name: str,
           max_memory_mb: float = 500.0,
           max_cpu_percent: float = 80.0
       ) -> bool:
           """Check if plugin exceeds resource limits."""
           usage = self._usage.get(plugin_name)
           if not usage:
               return True

           if usage.memory_mb > max_memory_mb:
               logger.warning(
                   "plugin_memory_exceeded",
                   plugin=plugin_name,
                   memory_mb=usage.memory_mb,
                   limit=max_memory_mb
               )
               return False

           if usage.cpu_percent > max_cpu_percent:
               logger.warning(
                   "plugin_cpu_exceeded",
                   plugin=plugin_name,
                   cpu_percent=usage.cpu_percent,
                   limit=max_cpu_percent
               )
               return False

           return True
   ```

4. **Update PluginMetadata to support permissions**:
   ```python
   @dataclass
   class PluginMetadata:
       name: str
       version: str
       type: PluginType
       entry_point: str
       plugin_path: Path
       description: str = ""
       enabled: bool = True
       permissions: List[str] = field(default_factory=list)  # NEW
       timeout_seconds: int = 30  # NEW
   ```

5. **Integrate sandbox into PluginLoader**:
   ```python
   class PluginLoader:
       def __init__(self, sandbox: Optional[PluginSandbox] = None):
           self._sandbox = sandbox or PluginSandbox()

       def load_plugin(self, metadata: PluginMetadata) -> None:
           # Validate plugin security
           validation = self._sandbox.validate_plugin(metadata)
           if not validation.valid:
               raise PluginValidationError(validation.errors)

           # Log warnings
           for warning in validation.warnings:
               logger.warning("plugin_security_warning", warning=warning)

           # Load with timeout
           async def _load():
               # ... existing load logic ...
               pass

           asyncio.run(
               self._sandbox.execute_with_timeout(
                   _load,
                   timeout_seconds=metadata.timeout_seconds
               )
           )
   ```

---

## Dependencies

- **Depends On**:
  - Story 4.2 complete (PluginLoader to integrate with)
  - Story 4.5 complete (Hook security controls)

- **Blocks**:
  - Story 4.7 (Examples should demonstrate permissions)

---

## Definition of Done

- [ ] PluginSandbox class < 350 lines
- [ ] PermissionManager implemented
- [ ] ResourceMonitor implemented
- [ ] 10+ permissions defined
- [ ] Timeout controls implemented
- [ ] Code validation implemented
- [ ] PluginLoader integrated with sandbox
- [ ] 85%+ test coverage for new code
- [ ] All existing tests pass (100%)
- [ ] Integration test: Permission denied works
- [ ] Integration test: Timeout enforcement works
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/plugins/sandbox.py` (PluginSandbox)
2. `gao_dev/plugins/permission_manager.py` (PermissionManager)
3. `gao_dev/plugins/resource_monitor.py` (ResourceMonitor)
4. `gao_dev/plugins/exceptions.py` (PermissionDeniedError, PluginTimeoutError)
5. `tests/plugins/test_sandbox.py`
6. `tests/plugins/test_permission_manager.py`
7. `tests/plugins/test_resource_monitor.py`
8. `tests/plugins/fixtures/malicious_plugin/` (for testing security)

---

## Files to Modify

1. `gao_dev/plugins/models.py` - Add permissions and timeout to PluginMetadata
2. `gao_dev/plugins/loader.py` - Integrate PluginSandbox
3. `gao_dev/plugins/__init__.py` - Export security classes
4. `tests/plugins/fixtures/example_agent_plugin/plugin.yaml` - Add permissions
5. `tests/plugins/fixtures/example_workflow_plugin/plugin.yaml` - Add permissions

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.5 - Implement Extension Points (Hooks)
- **Next Story**: Story 4.7 - Create Example Plugins and Dev Guide
- **Interfaces**: PluginSandbox, PermissionManager
- **Dependencies**: PluginLoader, PluginMetadata

---

## Test Plan

### Unit Tests

1. **Test PluginSandbox**:
   - Validate plugin with valid metadata
   - Validate plugin with invalid entry point
   - Validate plugin with suspicious code
   - Check permissions (granted and denied)
   - Execute with timeout (success and timeout)

2. **Test PermissionManager**:
   - Grant permissions to plugin
   - Check granted permissions
   - Check denied permissions
   - Revoke permissions

3. **Test ResourceMonitor**:
   - Start monitoring plugin
   - Get usage metrics
   - Check limits (under and over)

### Integration Tests

1. **Permission enforcement**:
   - Load plugin with permissions
   - Plugin operation succeeds with permission
   - Plugin operation fails without permission
   - PermissionDeniedError raised

2. **Timeout enforcement**:
   - Load plugin with fast initialization
   - Load plugin with slow initialization (should timeout)
   - Execute plugin method with timeout

3. **Security validation**:
   - Load valid plugin (no warnings)
   - Load plugin with suspicious code (warnings logged)
   - Load plugin with invalid entry point (fails)

---

## Security Considerations

- **Critical**: This story implements core security controls
- Permissions are declarative (plugin.yaml) and enforced at runtime
- Timeout prevents infinite loops or hanging plugins
- Resource monitoring prevents DoS attacks
- Code scanning is informational (warnings, not blocks)
- Future enhancement: Cryptographic plugin signing
- Future enhancement: Network request proxying
- Future enhancement: File system virtualization (chroot)

---

## Notes

- Start with permission system (most critical)
- Timeouts prevent system hangs
- Resource monitoring is best-effort (not hard limits yet)
- Code scanning uses simple pattern matching (not AST analysis)
- Plugin signatures (crypto) deferred to future enhancement
- Sandbox is not OS-level isolation (use containers for that)
- Windows/Linux/Mac compatibility for resource monitoring
- Permissions are all-or-nothing (no fine-grained file paths yet)
