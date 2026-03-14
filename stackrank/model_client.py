"""Model client for handling different AI providers."""

import os
from typing import Any

import anthropic
import openai


class ModelClient:
    """Unified client for multiple AI providers."""

    def __init__(self, provider: str, model_name: str, api_key: str, endpoint: str | None = None):
        """Initialize the model client.

        Args:
            provider: One of 'openai_internal', 'openai', 'anthropic'
            model_name: Model identifier (e.g., 'gpt-4o', 'claude-3-opus-20240229')
            api_key: API key for authentication
            endpoint: Base URL for OpenAI-compatible endpoints (ignored for anthropic)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.endpoint = endpoint

        if provider in ("openai_internal", "openai"):
            base_url = endpoint if provider == "openai_internal" else None
            self.client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key
            )
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a completion request to the AI model.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt with context

        Returns:
            Model's response text

        Raises:
            Exception: If the API call fails
        """
        if self.provider in ("openai_internal", "openai"):
            return self._openai_complete(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return self._anthropic_complete(system_prompt, user_prompt)

    def _openai_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI-compatible API."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content

    def _anthropic_complete(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic Claude API."""
        # Anthropic combines system prompt with first user message
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text