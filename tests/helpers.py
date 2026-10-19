from datetime import date, timedelta
from app.training.models.training import PlannedWorkout

PROGRAM = {
    "experience_level": "intermediate",
    "available_minutes_per_day": 45,
    "equipment": ["track"],
    "baseline": {"run_distance_m": "3000", "run_elapsed_seconds": "900", "long_jump_cm": "210", "weight_kg": "82.0"},
    "targets": {"run_elapsed_seconds": "860", "long_jump_cm": "220", "weight_kg": "80.5"},
}


def create_program(client, headers, **overrides):
    response = client.post("/api/v1/programs", json={**PROGRAM, **overrides}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def shift_program_start(db, program_id, days_back):
    """Moves a program's sessions into the past so 'today' is a later program day (tests only)."""
    for plan in db.query(PlannedWorkout).filter(PlannedWorkout.program_id == program_id):
        plan.plan_date = plan.plan_date - timedelta(days=days_back)
    db.commit()


def plan_on(client, headers, day: date):
    plans = client.get(f"/api/v1/plans?from_date={day}&to_date={day}&status=confirmed", headers=headers).json()
    return plans[0] if plans else None
