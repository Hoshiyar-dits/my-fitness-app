from fastapi import APIRouter
from app.auth.dto.LoginRequest import LoginRequest
from app.users.dto.CreateUser import CreateUser
from app.auth.service import AuthService
from app.users.service import UserService


router = APIRouter(prefix="", tags=['login'])

@router.post("/login")
def login(data: LoginRequest):
    return AuthService.validate_login(data)


@router.post("/sign-up")
def sign_up(data: CreateUser):
    return UserService.create_user(data)