from datetime import date, timedelta
from tests.helpers import create_program, plan_on, shift_program_start


def test_tomorrow_proceeds_when_recovery_is_fine(client, auth):
    create_program(client, auth)
    client.post("/api/v1/checkins", json={"sleep_hours": "8", "energy_level": 4, "fatigue_level": 2}, headers=auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert result["decision"] == "proceed" and result["requires_confirmation"] is False
    assert result["proposed_plans"] == [] and len(result["scheduled_plans"]) == 1
    assert result["analysis"]["source_refs"]["checkin_id"] is not None


def test_no_checkin_keeps_plan_but_flags_uncertainty(client, auth):
    create_program(client, auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert result["decision"] == "proceed_with_caution" and result["proposed_plans"] == []


def test_fatigue_proposes_lighter_plan_that_needs_confirmation(client, auth, db):
    program_id = create_program(client, auth)["program"]["id"]
    shift_program_start(db, program_id, 3)  # today = day 4 (strength), tomorrow = day 5 (long jump, high impact)
    client.post("/api/v1/checkins", json={"sleep_hours": "5", "pain_level": 2, "pain_location": "ankle"}, headers=auth)

    first = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert first["decision"] == "modify" and first["requires_confirmation"] is True
    proposal = first["proposed_plans"][0]
    original = first["scheduled_plans"][0]
    assert proposal["status"] == "proposed" and proposal["source"] == "rules"
    assert proposal["based_on_plan_id"] == original["id"] and proposal["adjustment_reason"]
    assert proposal["is_high_impact"] is False and original["is_high_impact"] is True

    # the proposal is not the plan until confirmed
    tomorrow = date.today() + timedelta(days=1)
    assert plan_on(client, auth, tomorrow)["id"] == original["id"]
    assert client.post(f"/api/v1/plans/{proposal['id']}/complete", json={"actual_duration_minutes": 20}, headers=auth).status_code == 409

    # asking again replaces the earlier proposal instead of piling up duplicates
    second = client.post("/api/v1/plans/tomorrow", headers=auth).json()["proposed_plans"][0]
    assert client.get(f"/api/v1/plans/{proposal['id']}", headers=auth).json()["status"] == "superseded"

    confirmed = client.patch(f"/api/v1/plans/{second['id']}", json={"status": "confirmed"}, headers=auth).json()
    assert confirmed["status"] == "confirmed" and confirmed["confirmed_at"]
    assert client.get(f"/api/v1/plans/{original['id']}", headers=auth).json()["status"] == "superseded"
    assert plan_on(client, auth, tomorrow)["id"] == second["id"]
    assert client.get("/api/v1/analysis/daily", headers=auth).json()["proposed_plan_id"] == second["id"]


def test_warning_symptoms_replace_tomorrow_with_rest(client, auth):
    create_program(client, auth)
    client.post("/api/v1/checkins", json={"warning_symptoms": ["chest_pain"]}, headers=auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert result["decision"] == "stop" and "emergency" in result["safety_message"]
    assert result["proposed_plans"][0]["session_type"] == "rest"
    assert result["proposed_plans"][0]["exercises"] == []


def test_better_checkin_retires_outdated_proposal(client, auth):
    create_program(client, auth)
    checkin = client.post("/api/v1/checkins", json={"fatigue_level": 5, "soreness_level": 5}, headers=auth).json()
    proposal = client.post("/api/v1/plans/tomorrow", headers=auth).json()["proposed_plans"][0]
    client.patch(f"/api/v1/checkins/{checkin['id']}", json={"fatigue_level": 2, "soreness_level": 2}, headers=auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert result["decision"] == "proceed" and result["proposed_plans"] == []
    assert client.get(f"/api/v1/plans/{proposal['id']}", headers=auth).json()["status"] == "superseded"
    assert result["analysis"]["proposed_plan_id"] is None


def test_rejecting_a_proposal(client, auth):
    create_program(client, auth)
    client.post("/api/v1/checkins", json={"fatigue_level": 5, "soreness_level": 5}, headers=auth)
    proposal = client.post("/api/v1/plans/tomorrow", headers=auth).json()["proposed_plans"][0]
    assert proposal["session_type"] == "recovery"
    assert client.patch(f"/api/v1/plans/{proposal['id']}", json={"status": "rejected"}, headers=auth).json()["status"] == "rejected"
    assert client.patch(f"/api/v1/plans/{proposal['id']}", json={"status": "confirmed"}, headers=auth).status_code == 409


def test_skipped_session_does_not_increase_tomorrow(client, auth):
    create_program(client, auth)
    today = client.get("/api/v1/plans/today", headers=auth).json()[0]
    client.post(f"/api/v1/plans/{today['id']}/skip", json={"reason": "sick child"}, headers=auth)
    client.post("/api/v1/checkins", json={"sleep_hours": "8"}, headers=auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    assert result["proposed_plans"] == []  # tomorrow stays as planned, nothing added
    analysis = client.get("/api/v1/analysis/daily", headers=auth).json()
    assert analysis["metrics"]["skipped_sessions"] == 1 and analysis["metrics"]["skip_reasons"] == ["sick child"]
    assert any("not increased" in r for r in analysis["reasons"])


def test_high_impact_today_prevents_high_impact_tomorrow(client, auth):
    create_program(client, auth)
    # user moves a sprint session onto tomorrow, right after today's jump/sprint assessment
    exercise = next(e for e in client.get("/api/v1/exercises", headers=auth).json() if e["name"] == "Acceleration sprints")
    client.post("/api/v1/plans", json={"plan_date": str(date.today() + timedelta(days=1)), "session_type": "sprint", "title": "Sprints",
                                       "estimated_duration_minutes": 30, "exercises": [{"exercise_id": exercise["id"], "sets": 5}]}, headers=auth)
    today = client.get("/api/v1/plans/today", headers=auth).json()[0]
    client.post(f"/api/v1/plans/{today['id']}/complete", json={"actual_duration_minutes": 40}, headers=auth)
    client.post("/api/v1/checkins", json={"sleep_hours": "8"}, headers=auth)
    result = client.post("/api/v1/plans/tomorrow", headers=auth).json()
    sprint_proposals = [p for p in result["proposed_plans"] if "Sprints" in p["title"]]
    assert sprint_proposals and sprint_proposals[0]["is_high_impact"] is False


def test_daily_analysis_compares_performance(client, auth):
    yesterday = str(date.today() - timedelta(days=10))
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "3000", "elapsed_seconds": "900", "activity_date": yesterday}, headers=auth)
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "3000", "elapsed_seconds": "860"}, headers=auth)
    analysis = client.get("/api/v1/analysis/daily", headers=auth).json()
    run = analysis["metrics"]["performance"][0]
    assert run["comparison"]["improved"] is True and run["comparison"]["change"] == -40.0
    assert "improved" in analysis["summary"]
    assert len(analysis["source_refs"]["activity_ids"]) == 1
    assert client.get(f"/api/v1/analysis/daily?day={date.today() + timedelta(days=1)}", headers=auth).status_code == 422


def test_weekly_progress_includes_training(client, auth):
    create_program(client, auth)
    plan = client.get("/api/v1/plans/today", headers=auth).json()[0]
    client.post(f"/api/v1/plans/{plan['id']}/complete", json={"actual_duration_minutes": 40, "perceived_effort": 6}, headers=auth)
    client.post("/api/v1/checkins", json={"sleep_hours": "7", "fatigue_level": 3}, headers=auth)
    weekly = client.get("/api/v1/progress/weekly", headers=auth).json()
    assert weekly["totals"]["workouts_count"] == 1  # existing fields still present
    training = weekly["training"]
    assert training["adherence"]["completed"] == 1 and training["avg_perceived_effort"] == 6.0
    assert training["checkins"]["avg_sleep_hours"] == 7.0
    # legacy path returns the same shape
    assert "training" in client.get("/progress/weekly", headers=auth).json()


def test_25_day_progress_report(client, auth, db):
    program_id = create_program(client, auth)["program"]["id"]
    shift_program_start(db, program_id, 24)  # today is day 25
    from app.training.models.training import TrainingProgram
    program = db.get(TrainingProgram, program_id)
    program.start_date -= timedelta(days=24)
    program.end_date -= timedelta(days=24)
    db.commit()
    start = program.start_date

    def run(day, seconds, method="stopwatch"):
        client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "3000", "elapsed_seconds": seconds,
                                                "activity_date": str(day), "measurement_method": method, "is_assessment": True}, headers=auth)
    run(start + timedelta(days=2), "900")
    run(start + timedelta(days=12), "880")
    run(start + timedelta(days=24), "850")
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "5000", "elapsed_seconds": "1400",
                                            "activity_date": str(start + timedelta(days=20))}, headers=auth)  # not comparable
    for offset, weight in ((0, "82.0"), (1, "81.8"), (23, "80.9"), (24, "80.7")):
        client.put("/api/v1/body-metrics", json={"log_date": str(start + timedelta(days=offset)), "weight_kg": weight}, headers=auth)
    plan = client.get(f"/api/v1/plans?from_date={start}&to_date={start}", headers=auth).json()[0]
    client.post(f"/api/v1/plans/{plan['id']}/skip", json={"reason": "rain"}, headers=auth)

    report = client.get("/api/v1/progress/25-day", headers=auth).json()
    assert report["day_number"] == 25 and report["days_remaining"] == 0
    # the onboarding self-reported 900 s is dated today, so the earliest comparable is day 3's 900 s
    assert report["running"]["comparison"]["baseline_value"] == 900.0
    assert report["running"]["comparison"]["latest_value"] == 850.0
    assert report["running"]["comparison"]["improved"] is True
    assert report["body_weight"]["change"] == -1.1 and report["body_weight"]["reliable"] is True
    assert report["adherence"]["skipped"] == 1 and report["adherence"]["skipped_sessions"][0]["reason"] == "rain"
    assert report["adherence"]["not_logged"] > 0
    assert {g["goal_type"] for g in report["goals"]} == {"running_time", "long_jump", "body_weight"}
    running_goal = next(g for g in report["goals"] if g["goal_type"] == "running_time")
    assert running_goal["current_value"] == "850.000"
    assert report["sprint"]["comparison"] is None  # no sprint data: no invented comparison


def test_25_day_progress_without_program(client, auth):
    assert client.get("/api/v1/progress/25-day", headers=auth).status_code == 404
