from fastapi import Depends, HTTPException, status
from app.users.repository import UserRepository
from app.users.service import password_hash
from datetime import datetime, timedelta, timezone
from app.auth.dto.LoginResponse import LoginResponse
import os
import jwt

algorithm = os.getenv("ALOGORITHM", "HS256")
secret = os.getenv("JWT_SECRET_KEY")
expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRY", "60"))

if not secret:
    raise RuntimeError("JWT_SECRET_KEY is not set in the environment / .env")

class AuthService():
    def __init__(self, repository: UserRepository = Depends()):
        self.repository = repository

    def validate_login(self, data) -> LoginResponse:
        user = self.repository.get_by_email(data.email)
        if not user or not password_hash.verify(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        expiry_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        # PyJWT requires "sub" to be a string
        token = jwt.encode({"sub": str(user.id), "exp": expiry_time}, secret, algorithm)
        return LoginResponse(access_token=token)
