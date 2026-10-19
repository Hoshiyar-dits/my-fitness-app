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
from app.goals.router import router as goal_router
from app.training.router import router as training_router
from app.checkins.router import router as checkin_router
from app.activities.router import router as activity_router
from app.analysis.router import router as analysis_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
API_PREFIX = "/api/v1"

app = FastAPI(title="Fitness Tracker API")

ROUTERS = [
    auth_router,
    user_router,
    workout_router,
    meal_router,
    body_metric_router,
    progress_router,
    chat_router,
    goal_router,
    training_router,
    checkin_router,
    activity_router,
    analysis_router,
]

for router in ROUTERS:
    app.include_router(router, prefix=API_PREFIX)
    # unversioned paths kept for the bundled frontend and existing clients
    app.include_router(router, include_in_schema=False)

app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/ui/")
