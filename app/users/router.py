from fastapi import APIRouter, Depends, status
from app.users.dto.CreateUser import CreateUser
from app.users.dto.CreateUserProfile import CreateUserProfile
from app.users.dto.UpdateUserProfile import UpdateUserProfile
from app.users.dto.UserProfileResponse import UserProfileResponse
from app.users.dto.UserResponse import UserResponse
from app.users.service import UserService
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=['user'])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: CreateUser, service: UserService = Depends()):
    return service.create_user(data)

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user = Depends(get_current_user), service: UserService = Depends()):
    return service.get_profile(current_user.id)

@router.post("/profile", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(data: CreateUserProfile, current_user = Depends(get_current_user), service: UserService = Depends()):
    return service.create_profile(current_user.id, data)

@router.patch("/profile", response_model=UserProfileResponse)
def update_profile(data: UpdateUserProfile, current_user = Depends(get_current_user), service: UserService = Depends()):
    return service.update_profile(current_user.id, data)
