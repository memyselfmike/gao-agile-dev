"""
Prompt template domain model.

This module contains the data model for managing prompt templates,
including variable substitution and YAML loading.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


@dataclass
class PromptTemplate:
    """
    Prompt template with variable substitution support.

    Provides a structured way to define prompts with:
    - System and user prompts
    - Variable substitution using {{mustache}} syntax
    - JSON response schemas
    - LLM configuration (max_tokens, temperature)
    - Metadata for categorization

    Attributes:
        name: Unique identifier for the prompt
        description: Human-readable description
        system_prompt: Optional system-level prompt
        user_prompt: User-level prompt with {{variables}}
        variables: Dictionary of variable definitions with defaults
        schema: Optional JSON schema for structured responses
        max_tokens: Maximum tokens for response
        temperature: LLM temperature setting (0.0-1.0)
        metadata: Additional metadata (category, tags, etc.)

    Example:
        ```python
        # Create from YAML
        template = PromptTemplate.from_yaml(Path("prompts/prd.yaml"))

        # Render with variables
        rendered = template.render({"project_name": "MyApp"})
        ```
    """

    name: str
    description: str
    system_prompt: Optional[str]
    user_prompt: str
    variables: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate prompt template."""
        if not self.name:
            raise ValueError("Prompt name cannot be empty")
        if not self.user_prompt:
            raise ValueError("User prompt cannot be empty")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature must be 0.0-1.0, got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"Max tokens must be >= 1, got {self.max_tokens}")

    def render(self, variables: Dict[str, Any]) -> str:
        """
        Render prompt with variable substitution.

        Replaces all {{variable}} placeholders with provided values.
        Uses template defaults for missing variables.

        Args:
            variables: Dictionary of variable values

        Returns:
            Rendered prompt string

        Example:
            ```python
            template = PromptTemplate(
                name="greeting",
                description="Greeting template",
                system_prompt=None,
                user_prompt="Hello {{name}}!",
                variables={"name": "World"}
            )
            print(template.render({"name": "Alice"}))  # "Hello Alice!"
            print(template.render({}))  # "Hello World!"
            ```
        """
        # Merge template defaults with provided variables
        merged = {**self.variables, **variables}

        # Start with user prompt
        prompt = self.user_prompt

        # Replace all {{variable}} placeholders
        for key, value in merged.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    def render_system_prompt(self, variables: Dict[str, Any]) -> Optional[str]:
        """
        Render system prompt with variable substitution.

        Args:
            variables: Dictionary of variable values

        Returns:
            Rendered system prompt or None
        """
        if not self.system_prompt:
            return None

        # Merge template defaults with provided variables
        merged = {**self.variables, **variables}

        # Start with system prompt
        prompt = self.system_prompt

        # Replace all {{variable}} placeholders
        for key, value in merged.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PromptTemplate":
        """
        Load prompt template from YAML file.

        Expected YAML structure:
        ```yaml
        name: prd
        description: Create product requirements document
        system_prompt: You are a product manager...
        user_prompt: Create a PRD for {{project_name}}
        variables:
          project_name: MyProject
        response:
          schema:
            type: object
            properties:
              prd: { type: string }
          max_tokens: 4000
          temperature: 0.7
        metadata:
          category: planning
          phase: 2
        ```

        Args:
            yaml_path: Path to YAML file

        Returns:
            PromptTemplate instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {yaml_path}")

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {yaml_path}: {e}")

        if not data:
            raise ValueError(f"Empty YAML file: {yaml_path}")

        # Validate required fields
        if "name" not in data:
            raise ValueError(f"Missing 'name' field in {yaml_path}")
        if "description" not in data:
            raise ValueError(f"Missing 'description' field in {yaml_path}")
        if "user_prompt" not in data:
            raise ValueError(f"Missing 'user_prompt' field in {yaml_path}")

        # Extract response configuration
        response_config = data.get("response", {})

        return cls(
            name=data["name"],
            description=data["description"],
            system_prompt=data.get("system_prompt"),
            user_prompt=data["user_prompt"],
            variables=data.get("variables", {}),
            schema=response_config.get("schema"),
            max_tokens=response_config.get("max_tokens", 4000),
            temperature=response_config.get("temperature", 0.7),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of prompt template
        """
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "variables": self.variables,
            "schema": self.schema,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "metadata": self.metadata,
        }

    def to_yaml(self, yaml_path: Path) -> None:
        """
        Save prompt template to YAML file.

        Args:
            yaml_path: Path where YAML file will be written
        """
        data = {
            "name": self.name,
            "description": self.description,
            "user_prompt": self.user_prompt,
            "variables": self.variables,
            "metadata": self.metadata,
        }

        if self.system_prompt:
            data["system_prompt"] = self.system_prompt

        if self.schema or self.max_tokens != 4000 or self.temperature != 0.7:
            data["response"] = {}
            if self.schema:
                data["response"]["schema"] = self.schema
            if self.max_tokens != 4000:
                data["response"]["max_tokens"] = self.max_tokens
            if self.temperature != 0.7:
                data["response"]["temperature"] = self.temperature

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def __str__(self) -> str:
        """String representation."""
        return f"PromptTemplate('{self.name}')"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"PromptTemplate(name='{self.name}', description='{self.description}')"
