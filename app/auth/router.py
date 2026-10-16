from fastapi import APIRouter, Depends, status
from app.auth.dto.LoginRequest import LoginRequest
from app.auth.dto.LoginResponse import LoginResponse
from app.users.dto.CreateUser import CreateUser
from app.users.dto.UserResponse import UserResponse
from app.auth.service import AuthService
from app.users.service import UserService


router = APIRouter(prefix="", tags=['login'])

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, service: AuthService = Depends()):
    return service.validate_login(data)


@router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def sign_up(data: CreateUser, service: UserService = Depends()):
    return service.create_user(data)
