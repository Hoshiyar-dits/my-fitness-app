from fastapi import APIRouter

router = APIRouter(prefix="/", tags=['login'])

@router.post("/login")
def login():
    return 