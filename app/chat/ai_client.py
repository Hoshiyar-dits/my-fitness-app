"""The only file that talks to the LLM provider.

Uses the OpenAI SDK against any OpenAI-compatible endpoint, configured in .env:
  AI_BASE_URL  e.g. https://api.groq.com/openai/v1 (Groq, free tier); leave unset for OpenAI itself
  AI_API_KEY   the key for that provider
  AI_MODEL     a model name that provider offers
"""
import logging
import os
import openai
from fastapi import HTTPException

logger = logging.getLogger(__name__)

REFUSAL_REPLY = "Sorry, I can't help with that one. Could you ask it a different way?"

_client = None

def _get_client() -> openai.OpenAI:
    global _client
    if not os.getenv("AI_API_KEY"):
        raise HTTPException(status_code=503, detail="AI coach is not configured: set AI_API_KEY in .env")
    if _client is None:
        _client = openai.OpenAI(api_key=os.getenv("AI_API_KEY"), base_url=os.getenv("AI_BASE_URL") or None)
    return _client

def generate_reply(system_prompt: str, messages: list) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...], starting with a user message."""
    client = _get_client()
    try:
        # Chat Completions is the format every OpenAI-compatible provider supports
        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-5-mini"),
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
    except openai.AuthenticationError:
        logger.exception("AI provider authentication failed")
        raise HTTPException(status_code=503, detail="AI coach is misconfigured (invalid AI_API_KEY)")
    except openai.NotFoundError:
        logger.exception("AI provider does not know model %s", os.getenv("AI_MODEL"))
        raise HTTPException(status_code=503, detail="AI coach is misconfigured (unknown AI_MODEL)")
    except openai.RateLimitError:
        # also raised when a free tier's limit or a paid account's credit is used up
        logger.exception("AI provider rate limit / quota error")
        raise HTTPException(status_code=429, detail="AI coach is busy or over its limit, please try again later")
    except openai.APIStatusError as e:
        logger.exception("AI provider error (status %s)", e.status_code)
        raise HTTPException(status_code=502, detail="AI coach is unavailable right now")
    except openai.APIConnectionError:
        logger.exception("Could not reach AI provider")
        raise HTTPException(status_code=502, detail="AI coach is unavailable right now")

    choice = response.choices[0] if response.choices else None
    text = (choice.message.content or "").strip() if choice else ""
    if not text:
        logger.warning("Empty AI reply (finish_reason %s)", choice.finish_reason if choice else None)
    return text or REFUSAL_REPLY
