"""AI-powered natural language subcommand parser for interactive Brian chat.

Parses natural language variations of commands into structured command, subcommand,
and arguments using AIAnalysisService.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

from typing import Dict, Any, Optional, Tuple
import json
import structlog

from gao_dev.core.services.ai_analysis_service import AIAnalysisService

logger = structlog.get_logger()


class SubcommandParser:
    """
    Parse natural language commands into structured format using AI.

    Handles natural language variations like:
    - "list ceremonies for epic 1" -> (ceremony, list, {epic_num: 1})
    - "show me learning 5" -> (learning, show, {learning_id: 5})
    - "what's the status of story 30.4?" -> (story, show, {epic_num: 30, story_num: 4})
    - "run a retrospective" -> (ceremony, run, {type: "retrospective"})

    Supported Commands:
    - ceremony: list, show, run (with type: planning/standup/review/retrospective)
    - learning: list, show, apply
    - state: show (with epic/story identifiers)
    - story: list, show, status
    - epic: list, show, status

    Example:
        ```python
        parser = SubcommandParser(analysis_service)

        # Parse natural language
        command, subcommand, args = await parser.parse(
            "list ceremonies for epic 1"
        )
        # -> ("ceremony", "list", {"epic_num": 1})

        # Handle parsing failure
        result = await parser.parse("something unclear")
        if result is None:
            print("Could not parse command")
        ```
    """

    # Supported commands and their subcommands
    SUPPORTED_COMMANDS = {
        "ceremony": ["list", "show", "run"],
        "learning": ["list", "show", "apply"],
        "state": ["show"],
        "story": ["list", "show", "status"],
        "epic": ["list", "show", "status"]
    }

    def __init__(self, analysis_service: AIAnalysisService):
        """
        Initialize subcommand parser.

        Args:
            analysis_service: AIAnalysisService for AI-powered parsing
        """
        self.analysis_service = analysis_service
        self.logger = logger.bind(component="subcommand_parser")

    async def parse(
        self,
        natural_language: str
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Parse natural language into (command, subcommand, args).

        Args:
            natural_language: User's natural language input

        Returns:
            Tuple of (command, subcommand, args) if parsed successfully,
            None if parsing fails

        Example:
            ```python
            result = await parser.parse("list ceremonies for epic 1")
            if result:
                command, subcommand, args = result
                print(f"Command: {command}, Sub: {subcommand}, Args: {args}")
            ```
        """
        self.logger.info("parsing_natural_language", input=natural_language)

        try:
            # Use AI to parse
            parsed = await self._ai_parse(natural_language)

            if not parsed:
                return None

            command = parsed.get("command")
            subcommand = parsed.get("subcommand")
            args = parsed.get("args", {})

            # Validate command
            if not self._validate_command(command, subcommand):
                self.logger.warning(
                    "invalid_command_structure",
                    command=command,
                    subcommand=subcommand
                )
                return None

            self.logger.info(
                "command_parsed",
                command=command,
                subcommand=subcommand,
                args=args
            )

            return (command, subcommand, args)

        except Exception as e:
            self.logger.error("parsing_failed", error=str(e))
            return None

    async def _ai_parse(
        self,
        natural_language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Use AI to parse natural language into structured command.

        Args:
            natural_language: User input

        Returns:
            Dictionary with command, subcommand, args or None
        """
        prompt = self._build_parsing_prompt(natural_language)

        try:
            result = await self.analysis_service.analyze(
                prompt=prompt,
                response_format="json",
                max_tokens=300,
                temperature=0.3  # Low temperature for consistent parsing
            )

            # Parse JSON response
            parsed = json.loads(result.response)

            # Validate structure
            if not isinstance(parsed, dict):
                return None

            if "command" not in parsed or "subcommand" not in parsed:
                return None

            return parsed

        except json.JSONDecodeError as e:
            self.logger.warning("json_parse_failed", error=str(e))
            return None
        except Exception as e:
            self.logger.error("ai_parsing_failed", error=str(e))
            return None

    def _build_parsing_prompt(self, natural_language: str) -> str:
        """
        Build prompt for AI parsing.

        Args:
            natural_language: User input

        Returns:
            Prompt string
        """
        supported_list = "\n".join(
            f"- {cmd}: {', '.join(subs)}"
            for cmd, subs in self.SUPPORTED_COMMANDS.items()
        )

        prompt = f"""
Parse this natural language command into structured format.

Input: "{natural_language}"

Supported commands and subcommands:
{supported_list}

Extract:
1. command: Main command (ceremony, learning, state, story, epic)
2. subcommand: Action (list, show, run, status, apply)
3. args: Arguments as JSON object

Argument extraction rules:
- Epic numbers: "epic 1", "epic 30" -> {{"epic_num": 1}}
- Story identifiers: "story 30.4" -> {{"epic_num": 30, "story_num": 4}}
- Learning IDs: "learning 5" -> {{"learning_id": 5}}
- Ceremony types: "retrospective", "planning" -> {{"type": "retrospective"}}

Examples:
- "list ceremonies for epic 1" -> {{"command": "ceremony", "subcommand": "list", "args": {{"epic_num": 1}}}}
- "show story 30.4" -> {{"command": "story", "subcommand": "show", "args": {{"epic_num": 30, "story_num": 4}}}}
- "run a retrospective" -> {{"command": "ceremony", "subcommand": "run", "args": {{"type": "retrospective"}}}}
- "what's the status?" -> {{"command": "state", "subcommand": "show", "args": {{}}}}

Return ONLY valid JSON with structure: {{"command": "...", "subcommand": "...", "args": {{...}}}}

If input doesn't match supported commands, return: {{"command": null, "subcommand": null, "args": {{}}}}
""".strip()

        return prompt

    def _validate_command(
        self,
        command: Optional[str],
        subcommand: Optional[str]
    ) -> bool:
        """
        Validate command and subcommand structure.

        Args:
            command: Main command
            subcommand: Subcommand

        Returns:
            True if valid, False otherwise
        """
        if not command or not subcommand:
            return False

        if command not in self.SUPPORTED_COMMANDS:
            return False

        if subcommand not in self.SUPPORTED_COMMANDS[command]:
            return False

        return True

    def get_supported_commands(self) -> Dict[str, list]:
        """
        Get dictionary of supported commands and subcommands.

        Returns:
            Dictionary mapping commands to subcommand lists
        """
        return self.SUPPORTED_COMMANDS.copy()

    def format_command_help(self) -> str:
        """
        Format help text showing supported commands.

        Returns:
            Formatted help text
        """
        lines = ["**Supported Commands**:\n"]

        for command, subcommands in self.SUPPORTED_COMMANDS.items():
            lines.append(f"- **{command}**: {', '.join(subcommands)}")

        lines.append("\n**Examples**:")
        lines.append("- 'list ceremonies for epic 1'")
        lines.append("- 'show story 30.4'")
        lines.append("- 'run a retrospective'")
        lines.append("- 'what's the status?'")

        return "\n".join(lines)
