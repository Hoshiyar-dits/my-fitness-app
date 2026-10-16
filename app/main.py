from fastapi import FastAPI
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.workouts.router import router as workout_router
from app.meals.router import router as meal_router
from app.body_metrics.router import router as body_metric_router
from app.progress.router import router as progress_router

app = FastAPI(title="Fitness Tracker API")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(workout_router)
app.include_router(meal_router)
app.include_router(body_metric_router)
app.include_router(progress_router)
