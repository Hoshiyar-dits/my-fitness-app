from fastapi import Depends, HTTPException
from app.database.database import get_db
from app.users.repository import UserRepository

db = get_db()

class UserService():
    def __init__(self,repository: UserRepository):
        self.repository = repository

    def create_user(self, data):
        return self.repository.create(data)

    def get_profile(self, user_id: int):
        profile = self.repository.get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    def create_profile(self, user_id: int, data):
        if self.repository.get_profile(user_id):
            raise HTTPException(status_code=409, detail="Profile already exists")
        return self.repository.create_profile(user_id, data)

    def update_profile(self, user_id: int, data):
        profile = self.get_profile(user_id)
        changes = data.model_dump(exclude_unset=True)
        for field in ("date_of_birth", "height_cm", "activity_level"):
            if field in changes and changes[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        if changes.get("activity_level"):
            changes["activity_level"] = changes["activity_level"].value
        return self.repository.update_profile(profile, changes)
