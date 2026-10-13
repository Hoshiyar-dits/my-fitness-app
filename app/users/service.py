from app.database.database import get_db
from app.users.repository import UserRepository

db = get_db()

class UserService():
    def __init__(self,repository: UserRepository):
        self.repository = repository

    def create_user(self, data):
        return self.repository.create(data)