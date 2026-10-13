from app.database.database import get_db
from app.users.model import User
class UserRepository():
    def __init__(self):
        self.db = get_db()

    def create(self, data):
        user = User(name=data.name, email=data.email, password=data.password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user