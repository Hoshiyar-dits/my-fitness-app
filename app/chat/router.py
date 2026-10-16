from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.chat.dto.SendChatMessage import SendChatMessage
from app.chat.dto.ChatMessageResponse import ChatMessageResponse
from app.chat.dto.ChatReply import ChatReply
from app.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=['chat'])

@router.post("", response_model=ChatReply)
def send_message(data: SendChatMessage, current_user = Depends(get_current_user), service: ChatService = Depends()):
    return service.send(current_user, data.message)

@router.get("/history", response_model=List[ChatMessageResponse])
def get_history(limit: int = Query(default=50, ge=1, le=200), current_user = Depends(get_current_user), service: ChatService = Depends()):
    return service.history(current_user.id, limit)

@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(current_user = Depends(get_current_user), service: ChatService = Depends()):
    service.clear(current_user.id)
