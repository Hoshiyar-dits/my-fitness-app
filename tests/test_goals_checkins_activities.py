from datetime import date, timedelta


def goal(**overrides):
    body = {"goal_type": "running_time", "reference_distance_m": "3000", "target_date": str(date.today() + timedelta(days=24)),
            "baseline_value": "900", "target_value": "860"}
    body.update(overrides)
    return body


def test_goal_create_get_update(client, auth):
    created = client.post("/api/v1/goals", json=goal(), headers=auth)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["unit"] == "s" and data["lower_is_better"] is True and data["status"] == "active"
    goal_id = data["id"]
    assert client.get(f"/api/v1/goals/{goal_id}", headers=auth).json()["target_value"] == "860.000"
    updated = client.patch(f"/api/v1/goals/{goal_id}", json={"current_value": "880"}, headers=auth).json()
    assert updated["progress_pct"] == 50.0 and updated["current_value_date"] == date.today().isoformat()
    assert client.patch(f"/api/v1/goals/{goal_id}", json={"status": "abandoned"}, headers=auth).json()["status"] == "abandoned"
    assert client.get("/api/v1/goals?status=active", headers=auth).json() == []


def test_goal_validation(client, auth):
    assert client.post("/api/v1/goals", json=goal(unit="min"), headers=auth).status_code == 422
    assert client.post("/api/v1/goals", json=goal(reference_distance_m=None), headers=auth).status_code == 422
    assert client.post("/api/v1/goals", json=goal(goal_type="long_jump", unit="cm"), headers=auth).status_code == 422  # distance on a jump goal
    assert client.post("/api/v1/goals", json=goal(target_date=str(date.today())), headers=auth).status_code == 422
    body_fat = goal(goal_type="body_fat", reference_distance_m=None, baseline_value="25", target_value="120")
    assert client.post("/api/v1/goals", json=body_fat, headers=auth).status_code == 422
    assert client.get("/api/v1/goals/999", headers=auth).status_code == 404
    assert client.post("/api/v1/goals", json=goal(program_id=999), headers=auth).status_code == 404


def test_activity_updates_only_comparable_goals(client, auth):
    goal_id = client.post("/api/v1/goals", json=goal(), headers=auth).json()["id"]
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "5000", "elapsed_seconds": "1500"}, headers=auth)
    assert client.get(f"/api/v1/goals/{goal_id}", headers=auth).json()["current_value"] is None
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "3000", "elapsed_seconds": "885"}, headers=auth)
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "3000", "elapsed_seconds": "895"}, headers=auth)
    assert client.get(f"/api/v1/goals/{goal_id}", headers=auth).json()["current_value"] == "885.000"  # best of the day kept


def test_activity_validation_and_derived_metrics(client, auth):
    run = client.post("/api/v1/activities", json={
        "activity_type": "run", "distance_m": "3000", "elapsed_seconds": "900", "measurement_method": "gps_watch",
        "splits": [{"distance_m": "1000", "elapsed_seconds": "290"}, {"distance_m": "1000", "elapsed_seconds": "300"}],
    }, headers=auth)
    assert run.status_code == 201, run.text
    body = run.json()
    assert body["pace_seconds_per_km"] == 300.0 and body["speed_m_per_s"] == 3.33
    assert [s["pace_seconds_per_km"] for s in body["splits"]] == [290.0, 300.0]

    bad = [
        {"activity_type": "run", "distance_m": "3000"},
        {"activity_type": "long_jump", "distance_m": "3"},
        {"activity_type": "high_jump", "jump_cm": "450"},
        {"activity_type": "run", "distance_m": "1000", "elapsed_seconds": "300", "splits": [{"distance_m": "2000", "elapsed_seconds": "100"}]},
        {"activity_type": "sprint", "distance_m": "30", "elapsed_seconds": "5", "activity_date": str(date.today() + timedelta(days=1))},
    ]
    for payload in bad:
        assert client.post("/api/v1/activities", json=payload, headers=auth).status_code == 422, payload

    jump = client.post("/api/v1/activities", json={"activity_type": "long_jump", "jump_cm": "215", "technique": "standing"}, headers=auth).json()
    assert jump["pace_seconds_per_km"] is None
    history = client.get("/api/v1/activities/history?activity_type=run", headers=auth).json()
    assert len(history) == 1
    assert client.post("/api/v1/activities", json={"activity_type": "long_jump", "jump_cm": "215", "planned_workout_id": 999}, headers=auth).status_code == 404


def test_checkin_lifecycle_and_body_metric(client, auth):
    assert client.get("/api/v1/checkins/today", headers=auth).status_code == 404
    created = client.post("/api/v1/checkins", json={"sleep_hours": "7.5", "energy_level": 4, "weight_kg": "81.2"}, headers=auth)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["body_metric"]["weight_kg"] == "81.20" and data["safety_alert"] is None
    assert client.post("/api/v1/checkins", json={}, headers=auth).status_code == 409
    assert client.get("/api/v1/checkins/today", headers=auth).json()["id"] == data["id"]

    patched = client.patch(f"/api/v1/checkins/{data['id']}", json={"warning_symptoms": ["dizziness"], "body_fat_pct": "20.5",
                                                                    "body_fat_method": "smart_scale"}, headers=auth).json()
    assert "medical" in patched["safety_alert"]
    assert patched["body_metric"]["body_fat_pct"] == "20.5" and patched["body_metric"]["weight_kg"] == "81.20"
    assert patched["sleep_hours"] == "7.5"  # untouched fields keep their values
    assert len(client.get("/api/v1/checkins/history", headers=auth).json()) == 1
    assert client.get("/api/v1/body-metrics", headers=auth).json()[0]["body_fat_method"] == "smart_scale"


def test_checkin_optional_fields_and_validation(client, auth):
    yesterday = str(date.today() - timedelta(days=1))
    minimal = client.post("/api/v1/checkins", json={"checkin_date": yesterday}, headers=auth)
    assert minimal.status_code == 201 and minimal.json()["body_metric"] is None
    assert client.post("/api/v1/checkins", json={"body_fat_pct": "20"}, headers=auth).status_code == 422  # no weigh-in that day
    assert client.post("/api/v1/checkins", json={"energy_level": 9}, headers=auth).status_code == 422
    assert client.post("/api/v1/checkins", json={"warning_symptoms": ["sneezing"]}, headers=auth).status_code == 422
    assert client.post("/api/v1/checkins", json={"checkin_date": str(date.today() + timedelta(days=1))}, headers=auth).status_code == 422
    assert client.patch("/api/v1/checkins/999", json={}, headers=auth).status_code == 404
