from app.database.database import get_db
from app.users.repository import UserRepository
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from app.auth.dto.LoginResponse import LoginResponse
import os
import jwt

db = get_db()
password_hash = PasswordHash.recommended()
algorithm =  os.getenv("ALOGORITHM")
secret = os.getenv("JWT_SECRET_KEY")
expire = os.getenv("ACCESS_TOKEN_EXPIRY")

class AuthService():
    def __init__(self,repository: UserRepository):
            self.repository = repository

    def validate_login(self, data) -> LoginResponse:
        try:
            user = self.repository.get_by_email(data.email)
            if not user or not password_hash.verify(data.password,user.password):
                raise Exception("Invalid email or password")

            expiry_time = datetime.now(timezone.utc) + timedelta(minutes=expire)
            token = jwt.encode({"sub": user.id , "exp": expiry_time}, secret , algorithm)
            return LoginResponse(access_token=token,token_type="bareer")
        except Exception:
             raise