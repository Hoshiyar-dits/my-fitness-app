from fastapi import APIRouter, Depends
from app.users.dto.CreateUser import CreateUser
from app.users.dto.CreateUserProfile import CreateUserProfile
from app.users.dto.UpdateUserProfile import UpdateUserProfile
from app.users.dto.UserProfileResponse import UserProfileResponse
from app.users.service import UserService
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=['user'])

@router.post("")
def create_user(data: CreateUser):
    return UserService.create_user(data)

@router.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return UserService.get_profile(current_user.id)

@router.post("/profile")
def create_profile(data: CreateUserProfile, current_user = Depends(get_current_user)):
    return UserService.create_profile(current_user.id, data)

@router.patch("/profile")
def update_profile(data: UpdateUserProfile, current_user = Depends(get_current_user)):
    return UserService.update_profile(current_user.id, data)
