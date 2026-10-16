from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.users.router import router as user_router
from app.auth.router import router as auth_router
from app.workouts.router import router as workout_router
from app.meals.router import router as meal_router
from app.body_metrics.router import router as body_metric_router
from app.progress.router import router as progress_router
from app.chat.router import router as chat_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Fitness Tracker API")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(workout_router)
app.include_router(meal_router)
app.include_router(body_metric_router)
app.include_router(progress_router)
app.include_router(chat_router)

app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")
