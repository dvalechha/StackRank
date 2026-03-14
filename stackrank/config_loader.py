"""Load and validate configuration from config.yaml."""

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


def load_config(config_path: str | Path, output_override: str | None = None) -> dict[str, Any]:
    """Load and validate config.yaml.

    Args:
        config_path: Path to config.yaml
        output_override: Optional override for output folder

    Returns:
        Validated configuration dict

    Raises:
        ConfigError: If required fields are missing
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate required sections
    if "model" not in config:
        raise ConfigError("Missing required section: model")

    model = config["model"]
    required_model_fields = ["provider", "model_name", "api_key_env"]
    for field in required_model_fields:
        if field not in model:
            raise ConfigError(f"Missing required field in model: {field}")

    # Validate provider
    valid_providers = ["openai_internal", "openai", "anthropic"]
    if model["provider"] not in valid_providers:
        raise ConfigError(f"Invalid provider: {model['provider']}. Must be one of {valid_providers}")

    # Validate output section
    if "output" not in config:
        raise ConfigError("Missing required section: output")

    if output_override:
        config["output"]["folder"] = output_override

    if "folder" not in config["output"]:
        raise ConfigError("Missing required field in output: folder")

    return config


def get_api_key(config: dict[str, Any]) -> str:
    """Get API key from environment variable specified in config.

    Args:
        config: Configuration dict

    Returns:
        API key string

    Raises:
        ConfigError: If API key is not set in environment
    """
    env_var = config["model"]["api_key_env"]
    api_key = os.getenv(env_var)

    if not api_key:
        raise ConfigError(f"API key not found in environment: {env_var}. Set it in .env file.")

    return api_key