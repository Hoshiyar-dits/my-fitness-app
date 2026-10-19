from typing import List, Optional
from pydantic import BaseModel
from app.chat.dto.ChatMessageResponse import ChatMessageResponse

class ChatAction(BaseModel):
    """A tool the coach used while answering (e.g. a proposed or confirmed plan id)."""
    tool: str
    ok: bool
    plan_ids: Optional[List[int]] = None

class ChatReply(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    actions: List[ChatAction] = []
