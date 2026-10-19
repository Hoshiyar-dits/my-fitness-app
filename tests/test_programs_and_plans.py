from datetime import date, timedelta
from app.workouts.models.workout import Workout
from tests.helpers import create_program, plan_on, shift_program_start


def test_program_creates_calendar_goals_and_baseline(client, auth):
    data = create_program(client, auth)
    assert data["sessions_created"] == 25 and data["goals_created"] == 3 and data["safety_message"] is None
    program = data["program"]
    assert program["status"] == "active" and program["assessment_run_distance_m"] == "3000.00"
    assert program["end_date"] == str(date.today() + timedelta(days=24))

    plans = client.get(f"/api/v1/plans?from_date={program['start_date']}&to_date={program['end_date']}&limit=100", headers=auth).json()
    assert len(plans) == 25
    assert all(p["status"] == "confirmed" and p["source"] == "program_template" for p in plans)
    assert plans[0]["session_type"] == "assessment" and plans[0]["exercises"][0]["exercise_name"]
    # no high-impact sessions on consecutive days
    assert not any(a["is_high_impact"] and b["is_high_impact"] for a, b in zip(plans, plans[1:]))

    goals = {g["goal_type"]: g for g in client.get("/api/v1/goals", headers=auth).json()}
    assert goals["running_time"]["baseline_value"] == "900.000" and goals["running_time"]["reference_distance_m"] == "3000.00"
    assert goals["long_jump"]["technique"] == "standing"
    assert goals["body_weight"]["baseline_value"] == "82.000"

    assert len(client.get("/api/v1/activities/history", headers=auth).json()) == 2  # self-reported run + jump
    assert client.get("/api/v1/body-metrics", headers=auth).json()[0]["weight_kg"] == "82.00"
    assert client.get("/api/v1/programs/current", headers=auth).json()["id"] == program["id"]
    assert client.post("/api/v1/programs", json={"experience_level": "beginner", "available_minutes_per_day": 30}, headers=auth).status_code == 409


def test_baseline_over_other_distance_is_not_used_as_goal_baseline(client, auth):
    data = create_program(client, auth, baseline={"run_distance_m": "5000", "run_elapsed_seconds": "1500"},
                          targets={"run_elapsed_seconds": "860"})
    goal = client.get("/api/v1/goals", headers=auth).json()[0]
    assert data["goals_created"] == 1 and goal["baseline_value"] is None and goal["reference_distance_m"] == "3000.00"


def test_missing_information_is_reported(client, auth):
    data = create_program(client, auth, baseline=None, targets=None)
    joined = " ".join(data["missing_information"])
    assert "profile" in joined and "running assessment" in joined and "high jump" in joined


def test_pain_or_restrictions_require_clearance_before_calendar(client, auth):
    data = create_program(client, auth, current_pain="left knee aches when running")
    assert data["program"]["status"] == "awaiting_clearance" and data["sessions_created"] == 0
    assert "clearance" in data["safety_message"]
    program_id = data["program"]["id"]
    assert client.get("/api/v1/plans", headers=auth).json() == []

    cleared = client.patch(f"/api/v1/programs/{program_id}", json={"medical_clearance_confirmed": True}, headers=auth)
    assert cleared.status_code == 200 and cleared.json()["status"] == "active"
    assert len(client.get("/api/v1/plans?limit=100", headers=auth).json()) == 25
    assert client.patch(f"/api/v1/programs/{program_id}", json={"medical_clearance_confirmed": True}, headers=auth).status_code == 409


def test_invalid_program_input(client, auth):
    assert client.post("/api/v1/programs", json={"experience_level": "pro", "available_minutes_per_day": 30}, headers=auth).status_code == 422
    assert client.post("/api/v1/programs", json={"experience_level": "beginner", "available_minutes_per_day": 5}, headers=auth).status_code == 422
    body = {"experience_level": "beginner", "available_minutes_per_day": 30, "baseline": {"run_distance_m": "3000"}}
    assert client.post("/api/v1/programs", json=body, headers=auth).status_code == 422
    # equal baseline and target is rejected and leaves nothing behind
    body = {"experience_level": "beginner", "available_minutes_per_day": 30, "baseline": {"weight_kg": "80"}, "targets": {"weight_kg": "80"}}
    assert client.post("/api/v1/programs", json=body, headers=auth).status_code == 422
    assert client.get("/api/v1/programs/current", headers=auth).status_code == 404
    assert client.get("/api/v1/plans", headers=auth).json() == []


def test_cancel_program_cancels_upcoming_sessions(client, auth):
    program_id = create_program(client, auth)["program"]["id"]
    assert client.patch(f"/api/v1/programs/{program_id}", json={"status": "cancelled"}, headers=auth).json()["status"] == "cancelled"
    assert client.get("/api/v1/plans?status=confirmed", headers=auth).json() == []
    assert client.patch(f"/api/v1/programs/{program_id}", json={}, headers=auth).status_code in (409, 422)


def test_complete_plan_logs_workout_and_activities(client, auth, db):
    create_program(client, auth)
    today_plan = client.get("/api/v1/plans/today", headers=auth).json()[0]
    exercise_id = today_plan["exercises"][0]["exercise_id"]
    response = client.post(f"/api/v1/plans/{today_plan['id']}/complete", json={
        "actual_duration_minutes": 50, "perceived_effort": 7, "notes": "felt good",
        "performed_exercises": [{"exercise_id": exercise_id, "sets": 2, "distance_m": "20"}],
        "activities": [{"activity_type": "long_jump", "jump_cm": "218", "technique": "standing", "is_assessment": True},
                       {"activity_type": "sprint", "distance_m": "30", "elapsed_seconds": "4.65", "is_assessment": True}],
    }, headers=auth)
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["completion_status"] == "completed" and plan["perceived_effort"] == 7 and plan["completed_at"]
    assert plan["performed_exercises"][0]["sets"] == 2
    workout = db.get(Workout, plan["workout_id"])
    assert workout.duration_minutes == 50 and workout.workout_type == "sports"
    assert client.get("/api/v1/dashboard", headers=auth).json()["today"]["workout_minutes"] == 50
    linked = [a for a in client.get("/api/v1/activities/history", headers=auth).json() if a["planned_workout_id"] == plan["id"]]
    assert len(linked) == 2
    goals = {g["goal_type"]: g for g in client.get("/api/v1/goals", headers=auth).json()}
    assert goals["long_jump"]["current_value"] == "218.000"
    # completing twice is rejected
    assert client.post(f"/api/v1/plans/{plan['id']}/complete", json={"actual_duration_minutes": 10}, headers=auth).status_code == 409


def test_completion_rules(client, auth):
    program = create_program(client, auth)["program"]
    start = date.fromisoformat(program["start_date"])
    tomorrow_plan = plan_on(client, auth, start + timedelta(days=1))
    assert client.post(f"/api/v1/plans/{tomorrow_plan['id']}/complete", json={"actual_duration_minutes": 30}, headers=auth).status_code == 422
    rest = next(p for p in client.get("/api/v1/plans?limit=100", headers=auth).json() if p["session_type"] == "rest")
    assert client.post(f"/api/v1/plans/{rest['id']}/complete", json={"actual_duration_minutes": 30}, headers=auth).status_code == 422
    today = client.get("/api/v1/plans/today", headers=auth).json()[0]
    bad_exercise = {"actual_duration_minutes": 30, "performed_exercises": [{"exercise_id": 9999}]}
    assert client.post(f"/api/v1/plans/{today['id']}/complete", json=bad_exercise, headers=auth).status_code == 422
    assert client.post("/api/v1/plans/999/complete", json={"actual_duration_minutes": 30}, headers=auth).status_code == 404


def test_skip_requires_reason_and_is_recorded(client, auth):
    create_program(client, auth)
    plan = client.get("/api/v1/plans/today", headers=auth).json()[0]
    assert client.post(f"/api/v1/plans/{plan['id']}/skip", json={"reason": ""}, headers=auth).status_code == 422
    skipped = client.post(f"/api/v1/plans/{plan['id']}/skip", json={"reason": "worked late"}, headers=auth).json()
    assert skipped["completion_status"] == "skipped" and skipped["skip_reason"] == "worked late"
    assert client.post(f"/api/v1/plans/{plan['id']}/skip", json={"reason": "again"}, headers=auth).status_code == 409


def test_user_created_plan_and_edits(client, auth):
    exercises = client.get("/api/v1/exercises?category=sprint", headers=auth).json()
    sprint = next(e for e in exercises if e["name"] == "Acceleration sprints")
    created = client.post("/api/v1/plans", json={
        "plan_date": str(date.today() + timedelta(days=2)), "session_type": "sprint", "title": "Extra sprints",
        "intensity": "high", "estimated_duration_minutes": 30, "exercises": [{"exercise_id": sprint["id"], "sets": 4, "distance_m": "30"}],
    }, headers=auth)
    assert created.status_code == 201, created.text
    plan = created.json()
    assert plan["source"] == "user" and plan["status"] == "confirmed" and plan["is_high_impact"] is True
    edited = client.patch(f"/api/v1/plans/{plan['id']}", json={"title": "Short sprints", "estimated_duration_minutes": 20}, headers=auth).json()
    assert edited["title"] == "Short sprints"
    assert client.patch(f"/api/v1/plans/{plan['id']}", json={"plan_date": str(date.today() - timedelta(days=1))}, headers=auth).status_code == 422
    assert client.patch(f"/api/v1/plans/{plan['id']}", json={"status": "confirmed"}, headers=auth).status_code == 409
    assert client.patch(f"/api/v1/plans/{plan['id']}", json={"title": None}, headers=auth).status_code == 422
    unknown = {"plan_date": str(date.today()), "session_type": "strength", "title": "x", "estimated_duration_minutes": 10,
               "exercises": [{"exercise_id": 12345}]}
    assert client.post("/api/v1/plans", json=unknown, headers=auth).status_code == 422


def test_shift_helper_moves_program_into_past(client, auth, db):
    program_id = create_program(client, auth)["program"]["id"]
    shift_program_start(db, program_id, 4)
    assert client.get("/api/v1/plans/today", headers=auth).json()[0]["day_number"] == 5
