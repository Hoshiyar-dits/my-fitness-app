from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.chat.models.chat_message import ChatMessage

class ChatRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def recent(self, user_id: int, limit: int):
        rows = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))  # oldest first

    def add_exchange(self, user_id: int, user_text: str, assistant_text: str):
        try:
            user_message = ChatMessage(user_id=user_id, role="user", content=user_text)
            assistant_message = ChatMessage(user_id=user_id, role="assistant", content=assistant_text)
            self.db.add_all([user_message, assistant_message])
            self.db.commit()
            self.db.refresh(user_message)
            self.db.refresh(assistant_message)
            return user_message, assistant_message
        except Exception:
            self.db.rollback()
            raise

    def clear(self, user_id: int):
        try:
            self.db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
