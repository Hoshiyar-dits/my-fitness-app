from pydantic import BaseModel
from app.chat.dto.ChatMessageResponse import ChatMessageResponse

class ChatReply(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
