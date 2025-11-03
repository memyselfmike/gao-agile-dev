# Story 10.5: Prompt Management System

**Epic**: 10 - Prompt & Agent Abstraction
**Story Points**: 8
**Priority**: High
**Dependencies**: None (Foundation story)

---

## Story

**As a** developer
**I want** infrastructure for loading and rendering prompts
**So that** I can manage prompts declaratively

---

## Acceptance Criteria

### 1. Core Components
- [ ] `gao_dev/core/prompt_loader.py` implemented
- [ ] `gao_dev/core/prompt_registry.py` implemented
- [ ] `gao_dev/core/models/prompt_template.py` data model created

### 2. PromptLoader Features
- [ ] Load YAML prompt templates
- [ ] Render templates with `{{variable}}` substitution
- [ ] Resolve `@file:path` references
- [ ] Resolve `@config:key` references
- [ ] Cache loaded prompts

### 3. PromptRegistry Features
- [ ] Discover prompts in directories
- [ ] Register prompts (for plugins)
- [ ] Get prompt by name
- [ ] List prompts by category
- [ ] Override prompts

### 4. PromptTemplate Model
- [ ] name, description fields
- [ ] system_prompt, user_prompt fields
- [ ] variables dict
- [ ] schema for JSON responses
- [ ] max_tokens, temperature config
- [ ] render() method
- [ ] from_yaml() class method

### 5. Tests
- [ ] PromptLoader unit tests (80%+ coverage)
- [ ] PromptRegistry unit tests
- [ ] Variable substitution tests
- [ ] File reference tests
- [ ] Config reference tests
- [ ] Caching tests

---

## Technical Details

### PromptTemplate Model

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

@dataclass
class PromptTemplate:
    name: str
    description: str
    system_prompt: Optional[str]
    user_prompt: str
    variables: Dict[str, Any]
    schema: Optional[Dict] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self, variables: Dict[str, Any]) -> str:
        """Render prompt with variables."""
        prompt = self.user_prompt
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
        return prompt

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PromptTemplate":
        """Load from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return cls(
            name=data["name"],
            description=data["description"],
            system_prompt=data.get("system_prompt"),
            user_prompt=data["user_prompt"],
            variables=data.get("variables", {}),
            schema=data.get("response", {}).get("schema"),
            max_tokens=data.get("response", {}).get("max_tokens", 4000),
            temperature=data.get("response", {}).get("temperature", 0.7),
            metadata=data.get("metadata", {})
        )
```

### PromptLoader

```python
from pathlib import Path
from typing import Dict, Any
import yaml

class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}

    def load_prompt(self, prompt_name: str) -> PromptTemplate:
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        # Find prompt file
        prompt_file = self._find_prompt_file(prompt_name)
        template = PromptTemplate.from_yaml(prompt_file)

        self._cache[prompt_name] = template
        return template

    def render_prompt(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        # Resolve references first
        resolved = self._resolve_references(template.variables, variables)
        return template.render(resolved)

    def _resolve_references(self, template_vars: Dict, user_vars: Dict) -> Dict:
        resolved = {**template_vars, **user_vars}

        for key, value in resolved.items():
            if isinstance(value, str):
                if value.startswith("@file:"):
                    path = value[6:]  # Remove @file:
                    resolved[key] = self._load_file(path)
                elif value.startswith("@config:"):
                    config_key = value[8:]  # Remove @config:
                    resolved[key] = self._load_config(config_key)

        return resolved
```

---

## Testing

```python
def test_prompt_loader_loads_yaml():
    loader = PromptLoader(Path("gao_dev/prompts"))
    template = loader.load_prompt("test_prompt")
    assert template.name == "test_prompt"

def test_variable_substitution():
    template = PromptTemplate(
        name="test",
        user_prompt="Hello {{name}}",
        variables={}
    )
    rendered = template.render({"name": "World"})
    assert rendered == "Hello World"

def test_file_reference_resolution():
    loader = PromptLoader(Path("gao_dev/prompts"))
    template = loader.load_prompt("prompt_with_file_ref")
    rendered = loader.render_prompt(template, {})
    assert "@file:" not in rendered

def test_caching():
    loader = PromptLoader(Path("gao_dev/prompts"))
    t1 = loader.load_prompt("test")
    t2 = loader.load_prompt("test")
    assert t1 is t2  # Same object (cached)
```

---

## Performance Targets

- Cold load: <100ms
- Cached load: <10ms
- Render: <10ms
- Total overhead: <5%

---

## Definition of Done

- [ ] PromptLoader implemented
- [ ] PromptRegistry implemented
- [ ] PromptTemplate model created
- [ ] Variable substitution working
- [ ] File/config references working
- [ ] Caching implemented
- [ ] 80%+ test coverage
- [ ] Performance benchmarks pass
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Atomic commit
