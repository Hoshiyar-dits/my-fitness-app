from fastapi import Depends, HTTPException
from app.meals.repository import MealRepository

NOT_NULL_FIELDS = ("meal_date", "meal_type", "name", "calories", "nutrition_accuracy")

class MealService():
    def __init__(self, repository: MealRepository = Depends()):
        self.repository = repository

    def create(self, user_id: int, data):
        return self.repository.create(user_id, data.model_dump())

    def get(self, user_id: int, meal_id: int):
        meal = self.repository.get(user_id, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
        return meal

    def list(self, user_id: int, from_date, to_date, limit: int, offset: int):
        return self.repository.list(user_id, from_date, to_date, limit, offset)

    def update(self, user_id: int, meal_id: int, data):
        meal = self.get(user_id, meal_id)
        changes = data.model_dump(exclude_unset=True)
        for field in NOT_NULL_FIELDS:
            if field in changes and changes[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        return self.repository.update(meal, changes)

    def delete(self, user_id: int, meal_id: int):
        self.repository.delete(self.get(user_id, meal_id))
