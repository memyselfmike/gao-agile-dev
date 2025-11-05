# Story 10.6: Schema Validation

**Epic**: 10 - Prompt & Agent Abstraction
**Story Points**: 5
**Priority**: Medium
**Dependencies**: Story 10.1, 10.5

---

## Story

**As a** developer
**I want** JSON Schema validation for all configurations
**So that** errors are caught early with clear messages

---

## Acceptance Criteria

### 1. JSON Schemas Created
- [ ] `gao_dev/schemas/agent.schema.json` - Agent config validation
- [ ] `gao_dev/schemas/prompt.schema.json` - Prompt template validation
- [ ] `gao_dev/schemas/workflow.schema.json` - Workflow config validation

### 2. SchemaValidator Implemented
- [ ] `gao_dev/core/schema_validator.py` created
- [ ] Load JSON Schema files
- [ ] Validate configurations
- [ ] Format clear error messages

### 3. Validation Integrated
- [ ] AgentConfigLoader validates on load
- [ ] PromptLoader validates on load
- [ ] Health check validates all configs
- [ ] Clear error messages with fix suggestions

### 4. Tests
- [ ] Validator unit tests
- [ ] Valid config tests
- [ ] Invalid config tests
- [ ] Error message tests

---

## Technical Details

### Agent Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent Configuration",
  "type": "object",
  "required": ["agent"],
  "properties": {
    "agent": {
      "type": "object",
      "required": ["metadata", "tools"],
      "properties": {
        "metadata": {
          "required": ["name", "role"],
          "properties": {
            "name": {"type": "string"},
            "role": {"type": "string"}
          }
        },
        "tools": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1
        }
      }
    }
  }
}
```

### SchemaValidator

```python
import jsonschema
from pathlib import Path

class SchemaValidator:
    def __init__(self, schemas_dir: Path):
        self.schemas_dir = schemas_dir
        self._schemas = {}

    def validate(self, data: Dict, schema_name: str) -> ValidationResult:
        schema = self._load_schema(schema_name)
        try:
            jsonschema.validate(data, schema)
            return ValidationResult(is_valid=True)
        except jsonschema.ValidationError as e:
            error_msg = self._format_error(e)
            return ValidationResult(is_valid=False, errors=[error_msg])

    def _format_error(self, error: jsonschema.ValidationError) -> str:
        return f"""
        Validation Error: {error.message}
        Location: {' -> '.join(str(p) for p in error.path)}
        Expected: {error.schema.get('description', 'See schema')}
        """
```

---

## Definition of Done

- [ ] 3 JSON schemas created
- [ ] SchemaValidator implemented
- [ ] Validation in all loaders
- [ ] Clear error messages
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Atomic commit
