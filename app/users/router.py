from fastapi import APIRouter
from app.users.dto.CreateUser import CreateUser
from app.users.service import UserService

router = APIRouter(prefix="/user", tags=['user'])

@router.post("")
def create_user(data: CreateUser):
    return UserService.create_user(data)