"""LangChain tool-calling loop: ask the chat model, run the tools it requests, feed back results, repeat."""
import json
import logging
import re
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from app.chat import ai_client
from app.chat.tools import FitnessToolbox

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6


def run(system_prompt: str, messages: list, toolbox: FitnessToolbox) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...], ending with the new user message."""
    conversation: list[BaseMessage] = [SystemMessage(system_prompt)]
    conversation += [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in messages]
    tools = toolbox.langchain_tools()
    tools_by_name = {tool.name: tool for tool in tools}

    for _ in range(MAX_TOOL_ROUNDS):
        reply = ai_client.invoke(conversation, tools=tools)
        if not reply.tool_calls and not reply.invalid_tool_calls:
            if not reply.text.strip():
                logger.warning("Empty AI reply, asking once more")
                reply = ai_client.invoke(conversation, tools=tools)
            return _text(reply)
        conversation.append(reply)
        for call in reply.tool_calls:
            tool = tools_by_name.get(call["name"])
            if tool is None:
                conversation.append(_tool_error(call["id"], f"Unknown tool '{call['name']}'"))
            else:
                conversation.append(tool.invoke(call))  # a ToolCall in gives a ToolMessage out
        for call in reply.invalid_tool_calls:  # arguments that were not valid JSON
            conversation.append(_tool_error(call["id"], f"Invalid arguments for '{call['name']}': {call.get('error') or 'not valid JSON'}"))

    # tool budget used up: ask for a final answer from what has been gathered
    logger.warning("AI coach hit the tool round limit (%s)", MAX_TOOL_ROUNDS)
    return _text(ai_client.invoke(conversation, tools=tools, tool_choice="none"))


def _tool_error(tool_call_id: str, error: str) -> ToolMessage:
    return ToolMessage(json.dumps({"ok": False, "error": error}), tool_call_id=tool_call_id)


def _text(reply: AIMessage) -> str:
    text = reply.text.strip()
    if not text:
        logger.warning("Empty AI reply (finish_reason %s)", reply.response_metadata.get("finish_reason"))
    # the chat UI shows plain text, so drop Markdown emphasis markers the model sometimes adds anyway
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text or ai_client.REFUSAL_REPLY
