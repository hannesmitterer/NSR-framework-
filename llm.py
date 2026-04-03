"""
llm.py
─────────────────────────────────────────────────────────────────────────────
LEX AMORIS ECOSYSTEM – Unified LLM wrapper
─────────────────────────────────────────────────────────────────────────────
Provides a single, consistent interface for calling:
  • OpenAI GPT  (call_gpt)
  • Google Gemini  (call_gemini)

API keys are read from environment variables:
  OPENAI_API_KEY
  GEMINI_API_KEY

If a key is missing the corresponding function returns a placeholder so the
rest of the system keeps running in "demo mode".
"""

from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
_openai_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI  # lazy import
            _openai_client = OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("openai package not installed")
            return None
    return _openai_client


def call_gpt(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 256) -> str:
    """Call OpenAI chat completion and return the text response."""
    client = _get_openai()
    if client is None:
        logger.warning("OPENAI_API_KEY not set – returning stub response")
        return f"[GPT-STUB] {prompt[:80]}…"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            timeout=30,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:  # noqa: BLE001
        logger.error("OpenAI error: %s", exc)
        return f"[GPT-ERROR] {exc}"


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------
_gemini_model = None


def _get_gemini():
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            import google.generativeai as genai  # lazy import
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        except ImportError:
            logger.warning("google-generativeai package not installed")
            return None
    return _gemini_model


def call_gemini(prompt: str) -> str:
    """Call Google Gemini and return the text response."""
    model = _get_gemini()
    if model is None:
        logger.warning("GEMINI_API_KEY not set – returning stub response")
        return f"[GEMINI-STUB] {prompt[:80]}…"
    try:
        response = model.generate_content(prompt)
        return response.text or ""
    except Exception as exc:  # noqa: BLE001
        logger.error("Gemini error: %s", exc)
        return f"[GEMINI-ERROR] {exc}"
