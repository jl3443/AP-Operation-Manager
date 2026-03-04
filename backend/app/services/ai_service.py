"""Core Claude AI service wrapper.

Provides a centralized client for all Claude API interactions with
retry logic, graceful degradation, and token usage logging.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from typing import Any

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Wrapper around the Anthropic Claude API."""

    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None
        self._model = settings.LLM_MODEL
        if settings.LLM_API_KEY:
            self._client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
            logger.info("AIService initialised with model=%s", self._model)
        else:
            logger.warning("LLM_API_KEY not set – AI features will use fallback behaviour")

    @property
    def available(self) -> bool:
        return self._client is not None

    # ── Text completion ──────────────────────────────────────────────────

    def call_claude(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2048,
    ) -> str | None:
        """Send a text-only message to Claude and return the response text."""
        if not self.available:
            return None
        return self._send(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
        )

    # ── Multi-turn conversation ────────────────────────────────────────

    def call_claude_conversation(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> str | None:
        """Send a multi-turn conversation to Claude and return the response text.

        Unlike ``call_claude`` (single user message), this accepts a full message
        history list (e.g. [{"role": "user", "content": "..."}, ...]) suitable
        for chat-style interactions.
        """
        if not self.available:
            return None
        return self._send(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
        )

    # ── Vision completion ────────────────────────────────────────────────

    def call_claude_vision(
        self,
        system_prompt: str,
        image_data: bytes,
        media_type: str,
        user_message: str = "Extract the information from this document.",
        max_tokens: int = 4096,
    ) -> str | None:
        """Send an image/PDF to Claude Vision and return the response text."""
        if not self.available:
            return None

        b64 = base64.standard_b64encode(image_data).decode("utf-8")

        # PDFs use "document" type; images use "image" type
        if media_type == "application/pdf":
            block_type = "document"
        else:
            block_type = "image"

        content: list[dict[str, Any]] = [
            {
                "type": block_type,
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64,
                },
            },
            {"type": "text", "text": user_message},
        ]

        return self._send(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
        )

    def call_claude_with_text(
        self,
        system_prompt: str,
        text_content: str,
        user_message: str = "Extract structured data from this text.",
        max_tokens: int = 4096,
    ) -> str | None:
        """Send extracted text to Claude for structured extraction."""
        if not self.available:
            return None
        combined_message = f"{user_message}\n\n--- DOCUMENT TEXT ---\n{text_content}"
        return self._send(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": combined_message}],
            max_tokens=max_tokens,
        )

    # ── JSON extraction helper ───────────────────────────────────────────

    @staticmethod
    def extract_json(text: str) -> dict[str, Any] | None:
        """Parse JSON from Claude's response, handling markdown code fences."""
        if not text:
            return None
        # Try to find JSON in code fences first
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        candidate = match.group(1).strip() if match else text.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Last resort: find the first { ... } block
            brace_match = re.search(r"\{.*\}", candidate, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse JSON from AI response")
            return None

    # ── Internal send with retry ─────────────────────────────────────────

    def _send(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        retries: int = 3,
    ) -> str | None:
        """Send a request to Claude with exponential-backoff retry.

        Note: Uses synchronous ``time.sleep`` for retry delays. All FastAPI
        endpoints that call this are synchronous ``def`` handlers, so they
        already run in a thread-pool and will not block the async event loop.
        """
        assert self._client is not None
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=messages,
                )

                # Log token usage
                usage = response.usage
                logger.info(
                    "Claude API usage: input=%d output=%d tokens (model=%s)",
                    usage.input_tokens,
                    usage.output_tokens,
                    self._model,
                )

                # Extract text from first text block
                for block in response.content:
                    if block.type == "text":
                        return block.text

                return None

            except (
                anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
            ) as exc:
                last_error = exc
                wait = 2**attempt
                logger.warning(
                    "Claude API attempt %d/%d failed (%s), retrying in %ds",
                    attempt,
                    retries,
                    type(exc).__name__,
                    wait,
                )
                time.sleep(wait)
            except anthropic.APIError as exc:
                logger.error("Claude API error (non-retryable): %s", exc)
                return None

        logger.error("Claude API failed after %d retries: %s", retries, last_error)
        return None


# Module-level singleton
ai_service = AIService()
