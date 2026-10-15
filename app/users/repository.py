from app.database.database import get_db
from app.users.models.user import User
from app.users.models.user_profiles import UserProfile
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
class UserRepository():
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

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

    def get_profile(self, user_id: int):
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def create_profile(self, user_id: int, data):
        try:
            profile = UserProfile(
                user_id=user_id,
                date_of_birth=data.date_of_birth,
                height_cm=data.height_cm,
                gender=data.gender,
                activity_level=data.activity_level.value,
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception:
            self.db.rollback()
            raise

    def update_profile(self, profile: UserProfile, data: dict):
        try:
            for field, value in data.items():
                setattr(profile, field, value)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception:
            self.db.rollback()
            raise
