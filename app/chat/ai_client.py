"""The only file that talks to the LLM provider, through LangChain's ChatOpenAI.

Works with any OpenAI-compatible endpoint, configured in .env:
  AI_BASE_URL  e.g. https://api.groq.com/openai/v1 (Groq) or http://localhost:11434/v1 (Ollama); empty for OpenAI
  AI_API_KEY   the key for that provider (any non-empty text for Ollama)
  AI_MODEL     a model name that provider offers and that supports tool calling
"""
import logging
import os
from typing import Optional, Sequence
import openai
from fastapi import HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

REFUSAL_REPLY = "Sorry, I can't help with that one. Could you ask it a different way?"
REQUEST_TIMEOUT_SECONDS = 180  # local models on CPU can be slow

_model = None
_model_config = None

def _get_model() -> ChatOpenAI:
    global _model, _model_config
    if not os.getenv("AI_API_KEY"):
        raise HTTPException(status_code=503, detail="AI coach is not configured: set AI_API_KEY in .env")
    config = (os.getenv("AI_API_KEY"), os.getenv("AI_BASE_URL") or None, os.getenv("AI_MODEL", "gpt-5-mini"))
    if _model is None or _model_config != config:
        api_key, base_url, model = config
        # retries are handled below, so provider errors surface immediately
        _model = ChatOpenAI(model=model, api_key=api_key, base_url=base_url, max_retries=0, timeout=REQUEST_TIMEOUT_SECONDS)
        _model_config = config
    return _model

def _is_malformed_tool_call(error: openai.BadRequestError) -> bool:
    # Groq returns 400 "tool_use_failed" when the model emits an invalid or unknown tool call; it is usually transient
    body = error.body if isinstance(error.body, dict) else {}
    details = body.get("error", body) if isinstance(body.get("error", body), dict) else {}
    return details.get("code") == "tool_use_failed"

def invoke(messages: Sequence[BaseMessage], tools: Optional[list] = None, tool_choice: Optional[str] = None, retries: int = 1) -> AIMessage:
    """One chat model call with optional LangChain tools bound. Provider errors become HTTPExceptions,
    so callers never see a half-finished success."""
    model = _get_model()
    runnable = model.bind_tools(tools, tool_choice=tool_choice or "auto") if tools else model
    try:
        return runnable.invoke(list(messages))
    except openai.BadRequestError as e:
        if _is_malformed_tool_call(e) and retries > 0:
            logger.warning("AI model produced a malformed tool call, retrying")
            return invoke(messages, tools, tool_choice, retries - 1)
        logger.exception("AI provider rejected the request")
        raise HTTPException(status_code=502, detail="AI coach is unavailable right now")
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
    except (openai.APIConnectionError, openai.APITimeoutError):
        logger.exception("Could not reach AI provider")
        raise HTTPException(status_code=502, detail="AI coach is unavailable right now")

def generate_reply(system_prompt: str, messages: list) -> str:
    """Plain reply without tools. messages: [{"role": "user"|"assistant", "content": str}, ...]."""
    history = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in messages]
    text = invoke([SystemMessage(system_prompt), *history]).text.strip()
    return text or REFUSAL_REPLY
