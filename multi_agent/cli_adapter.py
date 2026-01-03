"""
CLI adapter system for multi-provider support.

Supports Codex CLI, Claude Code CLI, and Google Gemini CLI.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple


class CLIProvider:
    """Represents a single CLI provider configuration."""

    def __init__(self, provider_id: str, config: Dict[str, Any]) -> None:
        """Initialize provider metadata from a configuration mapping."""
        self.id = provider_id
        self.name = config.get("name", provider_id)
        self.description = config.get("description", "")
        self.command = config.get("command", provider_id)
        self.execution_mode = config.get("execution_mode", "stdin")
        self.env_var = config.get("env_var", f"{provider_id.upper()}_CMD")
        self.default_cmd = config.get("default_cmd", [provider_id])
        self.parameters = config.get("parameters", {})
        self.input_mode = config.get("input_mode", "stdin")
        self.output_mode = config.get("output_mode", "stdout")
        self.supports_json_output = config.get("supports_json_output", False)
        self.json_output_flag = config.get("json_output_flag", "--output-format json")
        self.error_patterns = config.get("error_patterns", {})

    def build_command(
        self,
        prompt: str | None = None,
        custom_params: Dict[str, Any] | None = None,
        timeout_sec: int | None = None,
        model: str | None = None
    ) -> Tuple[List[str], str | None]:
        """
        Build the command line for this provider.

        Returns:
            Tuple of (command_list, stdin_content)
            - command_list: Full command with all parameters
            - stdin_content: Content to send via stdin (None if prompt is in args)

        Notes:
            Resolves model aliases, appends custom parameters, and chooses between
            stdin or argument-based prompt delivery based on provider settings.
        """
        # Start with base command from env or default
        cmd = self._get_base_command()
        stdin_content = None

        # Add model parameter if specified
        if model and "model" in self.parameters:
            model_cfg = self.parameters["model"]
            # Handle model aliases (e.g., "sonnet" -> full model name)
            if "aliases" in model_cfg and model in model_cfg["aliases"]:
                model = model_cfg["aliases"][model]
            cmd.append(model_cfg["flag"])
            cmd.append(model)

        # Add custom parameters
        if custom_params:
            for param_name, param_value in custom_params.items():
                if param_name in self.parameters:
                    param_cfg = self.parameters[param_name]
                    flag = param_cfg["flag"]
                    param_type = param_cfg["type"]

                    if param_type == "boolean":
                        if param_value:
                            cmd.append(flag)
                    else:
                        cmd.append(flag)
                        cmd.append(str(param_value))

        # Handle prompt based on execution mode
        if prompt:
            if self.execution_mode == "stdin":
                # Codex style: codex exec - < stdin
                stdin_content = prompt
            elif self.execution_mode == "flag":
                # Claude/Gemini style: claude -p "prompt" or can use stdin
                if self.input_mode == "flag_or_stdin":
                    # Prefer stdin for long prompts
                    if len(prompt) > 500:
                        stdin_content = prompt
                    else:
                        # Use flag for short prompts
                        cmd.append(prompt)
                else:
                    stdin_content = prompt

        return cmd, stdin_content

    def _get_base_command(self) -> List[str]:
        """Get the base command from environment or defaults."""
        env_value = os.environ.get(self.env_var)
        if env_value:
            # Parse env value into list
            return env_value.split()
        return list(self.default_cmd)

    def detect_error_type(self, stderr: str, stdout: str) -> str | None:
        """
        Detect error type from stderr/stdout.

        Returns error category: "timeout", "rate_limit", "auth", "model_error", or None
        """
        combined = (stderr + " " + stdout).lower()

        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in combined:
                    return error_type

        return None


class CLIAdapter:
    """
    Manages multiple CLI providers and routes commands to the appropriate provider.
    """

    def __init__(self, cli_config_path: Path) -> None:
        """Initialize the adapter and load provider configurations."""
        self.config_path = cli_config_path
        self.providers: Dict[str, CLIProvider] = {}
        self.default_provider_id = "codex"
        self.timeout_multipliers: Dict[str, float] = {}

        self._load_config()

    def _load_config(self) -> None:
        """Load CLI provider configurations from cli_config.json, creating defaults if needed."""
        if not self.config_path.exists():
            # Create default config if missing
            self._create_default_config()

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Load providers
        provider_configs = config.get("cli_providers", {})
        for provider_id, provider_config in provider_configs.items():
            self.providers[provider_id] = CLIProvider(provider_id, provider_config)

        # Load default provider
        self.default_provider_id = config.get("default_provider", "codex")

        # Load timeout multipliers
        self.timeout_multipliers = config.get("timeout_multiplier", {})

    def _create_default_config(self) -> None:
        """Create a minimal default configuration."""
        default_config = {
            "cli_providers": {
                "codex": {
                    "name": "Codex CLI",
                    "description": "OpenAI Codex CLI Interface",
                    "command": "codex",
                    "execution_mode": "stdin",
                    "env_var": "CODEX_CMD",
                    "default_cmd": ["codex", "exec", "-"],
                    "input_mode": "stdin",
                    "output_mode": "stdout"
                }
            },
            "default_provider": "codex"
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

    def get_provider(self, provider_id: str | None = None) -> CLIProvider:
        """
        Get a CLI provider by ID.

        Args:
            provider_id: Provider ID ("codex", "claude", "gemini"), or None for default

        Returns:
            CLIProvider instance

        Raises:
            ValueError: If provider_id is not found
        """
        if provider_id is None:
            provider_id = self.default_provider_id

        if provider_id not in self.providers:
            raise ValueError(
                f"Unknown CLI provider: {provider_id}. "
                f"Available: {', '.join(self.providers.keys())}"
            )

        return self.providers[provider_id]

    def get_timeout_multiplier(self, provider_id: str) -> float:
        """Get timeout multiplier for a provider (default 1.0)."""
        return self.timeout_multipliers.get(provider_id, 1.0)

    def build_command_for_role(
        self,
        provider_id: str | None,
        prompt: str,
        model: str | None = None,
        timeout_sec: int | None = None,
        custom_params: Dict[str, Any] | None = None
    ) -> Tuple[List[str], str | None, float]:
        """
        Build a command for executing a role with a specific provider.

        Args:
            provider_id: CLI provider to use (None for default)
            prompt: The prompt to send
            model: Model to use (provider-specific)
            timeout_sec: Base timeout in seconds
            custom_params: Additional provider-specific parameters

        Returns:
            Tuple of (command_list, stdin_content, timeout_multiplier)
        """
        provider = self.get_provider(provider_id)
        cmd, stdin = provider.build_command(
            prompt=prompt,
            custom_params=custom_params,
            timeout_sec=timeout_sec,
            model=model
        )
        multiplier = self.get_timeout_multiplier(provider.id)

        return cmd, stdin, multiplier

    def list_providers(self) -> List[str]:
        """Get list of available provider IDs."""
        return list(self.providers.keys())

    def get_provider_info(self, provider_id: str) -> Dict[str, Any]:
        """Get detailed information about a provider."""
        provider = self.get_provider(provider_id)
        return {
            "id": provider.id,
            "name": provider.name,
            "description": provider.description,
            "command": provider.command,
            "execution_mode": provider.execution_mode,
            "supports_json_output": provider.supports_json_output,
            "available_parameters": list(provider.parameters.keys())
        }
