"""
ai_integration.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – External AI Integration Module
─────────────────────────────────────────────────────────────────────────────
Provides integration capabilities with external AI systems:
  • OpenAI GPT models
  • Anthropic Claude
  • Google Gemini (direct API)
  • Custom AI endpoints

This module allows external AI systems to:
  • Query the current network state
  • Send messages to the network
  • Update reputation scores
  • Add memories
  • Subscribe to network events
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Callable

import aiohttp
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [AI-Integration] %(message)s")
logger = logging.getLogger(__name__)


class AIIntegration:
    """Base class for external AI integration."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize AI integration.

        Args:
            api_base_url: Base URL of the Lex Amoris API (default: http://localhost:8000)
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_state(self) -> dict[str, Any]:
        """
        Get current network state.

        Returns:
            Dictionary containing messages, reputation, memory, and chain info
        """
        async with self.session.get(f"{self.api_base_url}/state") as resp:
            return await resp.json()

    async def send_message(self, role: str, data: str, node_id: str | None = None) -> dict:
        """
        Send a message to the network.

        Args:
            role: Role identifier (e.g., 'AI', 'EXTERNAL', 'GPT')
            data: Message content
            node_id: Optional node identifier

        Returns:
            Response from the API
        """
        payload = {"role": role, "data": data}
        if node_id:
            payload["node_id"] = node_id

        async with self.session.post(
            f"{self.api_base_url}/message",
            json=payload,
        ) as resp:
            return await resp.json()

    async def update_reputation(self, node_id: str, score: float) -> dict:
        """
        Update a node's reputation score.

        Args:
            node_id: Node identifier
            score: Reputation score (0.0 to 1.0)

        Returns:
            Response from the API
        """
        async with self.session.post(
            f"{self.api_base_url}/reputation",
            json={"node_id": node_id, "score": score},
        ) as resp:
            return await resp.json()

    async def add_memory(self, text: str, role: str | None = None, trust: float = 0.5) -> dict:
        """
        Add a memory entry to the shared memory.

        Args:
            text: Memory content
            role: Optional role identifier
            trust: Trust level (0.0 to 1.0, default: 0.5)

        Returns:
            Response from the API
        """
        async with self.session.post(
            f"{self.api_base_url}/memory",
            json={"text": text, "role": role, "trust": trust},
        ) as resp:
            return await resp.json()

    async def get_reputation(self) -> dict[str, float]:
        """
        Get all reputation scores.

        Returns:
            Dictionary mapping node IDs to reputation scores
        """
        async with self.session.get(f"{self.api_base_url}/reputation/all") as resp:
            result = await resp.json()
            return result.get("reputation", {})


class OpenAIIntegration(AIIntegration):
    """Integration with OpenAI GPT models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4",
        api_base_url: str = "http://localhost:8000",
    ):
        """
        Initialize OpenAI integration.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4)
            api_base_url: Base URL of the Lex Amoris API
        """
        super().__init__(api_base_url)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.openai_base = "https://api.openai.com/v1"

    async def query_gpt(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Query OpenAI GPT model.

        Args:
            prompt: Prompt for GPT
            max_tokens: Maximum tokens in response

        Returns:
            GPT response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }

        async with self.session.post(
            f"{self.openai_base}/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            result = await resp.json()
            return result["choices"][0]["message"]["content"]

    async def interact_with_network(self, system_prompt: str | None = None):
        """
        Let GPT interact autonomously with the network.

        Args:
            system_prompt: Optional system prompt for GPT behavior
        """
        # Get current network state
        state = await self.get_state()

        # Build context for GPT
        recent_messages = state.get("messages", [])[-5:]  # Last 5 messages
        reputation = state.get("reputation", {})

        context = f"""
You are an AI agent interacting with the Lex Amoris cooperative AI network.

Current network state:
- Recent messages: {len(recent_messages)}
- Node reputations: {reputation}

Recent activity:
{json.dumps(recent_messages, indent=2)}

{system_prompt or 'Generate a helpful, cooperative message for the network.'}
"""

        # Query GPT
        gpt_response = await self.query_gpt(context)
        logger.info("GPT generated: %s", gpt_response[:100])

        # Send to network
        result = await self.send_message(
            role="OpenAI-GPT",
            data=gpt_response,
            node_id=f"gpt-{self.model}",
        )
        logger.info("Message sent to network: %s", result)

        return gpt_response


class AnthropicIntegration(AIIntegration):
    """Integration with Anthropic Claude models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-sonnet-20240229",
        api_base_url: str = "http://localhost:8000",
    ):
        """
        Initialize Anthropic integration.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            api_base_url: Base URL of the Lex Amoris API
        """
        super().__init__(api_base_url)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.anthropic_base = "https://api.anthropic.com/v1"

    async def query_claude(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Query Anthropic Claude model.

        Args:
            prompt: Prompt for Claude
            max_tokens: Maximum tokens in response

        Returns:
            Claude response text
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }

        async with self.session.post(
            f"{self.anthropic_base}/messages",
            headers=headers,
            json=payload,
        ) as resp:
            result = await resp.json()
            return result["content"][0]["text"]

    async def interact_with_network(self, system_prompt: str | None = None):
        """
        Let Claude interact autonomously with the network.

        Args:
            system_prompt: Optional system prompt for Claude behavior
        """
        state = await self.get_state()
        recent_messages = state.get("messages", [])[-5:]

        context = f"""
You are Claude, interacting with the Lex Amoris cooperative AI network.

Recent network activity:
{json.dumps(recent_messages, indent=2)}

{system_prompt or 'Provide thoughtful, ethical input to the network.'}
"""

        claude_response = await self.query_claude(context)
        logger.info("Claude generated: %s", claude_response[:100])

        result = await self.send_message(
            role="Anthropic-Claude",
            data=claude_response,
            node_id=f"claude-{self.model}",
        )
        logger.info("Message sent to network: %s", result)

        return claude_response


class NetworkEventSubscriber:
    """Subscribe to network events via WebSocket."""

    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        """
        Initialize event subscriber.

        Args:
            ws_url: WebSocket URL for network events
        """
        self.ws_url = ws_url
        self.callbacks: dict[str, list[Callable]] = {}

    def on(self, event_type: str, callback: Callable):
        """
        Register a callback for an event type.

        Args:
            event_type: Event type (e.g., 'message', 'reputation', 'memory')
            callback: Async callback function
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    async def subscribe(self):
        """Subscribe to network events and trigger callbacks."""
        import websockets  # noqa: PLC0415

        async with websockets.connect(self.ws_url) as websocket:
            logger.info("Connected to network events at %s", self.ws_url)

            async for message in websocket:
                try:
                    data = json.loads(message)
                    event_type = data.get("type")

                    if event_type in self.callbacks:
                        for callback in self.callbacks[event_type]:
                            await callback(data.get("payload", data))

                except json.JSONDecodeError:
                    logger.warning("Failed to parse message: %s", message)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Error processing event: %s", exc)


# Synchronous wrapper for simple use cases
class SyncAIIntegration:
    """Synchronous wrapper for AI integration."""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize synchronous AI integration.

        Args:
            api_base_url: Base URL of the Lex Amoris API
        """
        self.api_base_url = api_base_url.rstrip("/")

    def get_state(self) -> dict[str, Any]:
        """Get current network state."""
        resp = requests.get(f"{self.api_base_url}/state", timeout=10)
        return resp.json()

    def send_message(self, role: str, data: str, node_id: str | None = None) -> dict:
        """Send a message to the network."""
        payload = {"role": role, "data": data}
        if node_id:
            payload["node_id"] = node_id
        resp = requests.post(f"{self.api_base_url}/message", json=payload, timeout=10)
        return resp.json()

    def update_reputation(self, node_id: str, score: float) -> dict:
        """Update a node's reputation score."""
        resp = requests.post(
            f"{self.api_base_url}/reputation",
            json={"node_id": node_id, "score": score},
            timeout=10,
        )
        return resp.json()

    def add_memory(self, text: str, role: str | None = None, trust: float = 0.5) -> dict:
        """Add a memory entry."""
        resp = requests.post(
            f"{self.api_base_url}/memory",
            json={"text": text, "role": role, "trust": trust},
            timeout=10,
        )
        return resp.json()
