from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.auth.dependencies import get_current_user
from app.meals.dto.CreateMeal import CreateMeal
from app.meals.dto.UpdateMeal import UpdateMeal
from app.meals.dto.MealResponse import MealResponse
from app.meals.service import MealService

router = APIRouter(prefix="/meals", tags=['meals'])

@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(data: CreateMeal, current_user = Depends(get_current_user), service: MealService = Depends()):
    return service.create(current_user.id, data)

@router.get("", response_model=List[MealResponse])
def list_meals(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user = Depends(get_current_user),
    service: MealService = Depends(),
):
    return service.list(current_user.id, from_date, to_date, limit, offset)

@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, current_user = Depends(get_current_user), service: MealService = Depends()):
    return service.get(current_user.id, meal_id)

@router.patch("/{meal_id}", response_model=MealResponse)
def update_meal(meal_id: int, data: UpdateMeal, current_user = Depends(get_current_user), service: MealService = Depends()):
    return service.update(current_user.id, meal_id, data)

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, current_user = Depends(get_current_user), service: MealService = Depends()):
    service.delete(current_user.id, meal_id)
