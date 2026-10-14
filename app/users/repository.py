from app.database.database import get_db
from app.users.model import User
from fastapi import HTTPException
class UserRepository():
    def __init__(self):
        self.db = get_db()

    def create(self, data):
        try:
            user = User(name=data.name, email=data.email, password=data.password)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()