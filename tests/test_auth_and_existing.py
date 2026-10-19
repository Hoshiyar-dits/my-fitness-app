from datetime import date


def test_sign_up_login_and_me(client, make_user):
    headers = make_user(first_name="Ana")
    response = client.get("/api/v1/user/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Ana"


def test_wrong_password_and_missing_token_are_rejected(client):
    client.post("/sign-up", json={"first_name": "A", "last_name": "B", "email": "x@example.com", "password": "password123"})
    assert client.post("/login", json={"email": "x@example.com", "password": "wrong-password"}).status_code == 401
    assert client.get("/api/v1/user/me").status_code in (401, 403)
    assert client.get("/api/v1/goals", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_duplicate_email_conflicts(client):
    body = {"first_name": "A", "last_name": "B", "email": "dup@example.com", "password": "password123"}
    assert client.post("/sign-up", json=body).status_code == 201
    assert client.post("/sign-up", json=body).status_code == 409


def test_legacy_unversioned_paths_still_work(client, auth):
    """The bundled frontend calls unprefixed paths."""
    for path in ("/user/me", "/dashboard", "/workouts?limit=15", "/meals?limit=15", "/body-metrics?limit=15", "/chat/history?limit=50"):
        assert client.get(path, headers=auth).status_code == 200, path


def test_profile_crud(client, auth):
    body = {"date_of_birth": "1995-05-01", "height_cm": "178.5", "activity_level": "moderate"}
    assert client.post("/api/v1/user/profile", json=body, headers=auth).status_code == 201
    assert client.post("/api/v1/user/profile", json=body, headers=auth).status_code == 409
    response = client.patch("/api/v1/user/profile", json={"height_cm": "179"}, headers=auth)
    assert response.status_code == 200 and response.json()["height_cm"] == "179.00"


def test_workout_crud_still_works(client, auth):
    created = client.post("/api/v1/workouts", json={"workout_type": "cardio", "name": "Run", "duration_minutes": 30}, headers=auth)
    assert created.status_code == 201
    workout_id = created.json()["id"]
    assert client.patch(f"/api/v1/workouts/{workout_id}", json={"duration_minutes": 35}, headers=auth).json()["duration_minutes"] == 35
    assert client.delete(f"/api/v1/workouts/{workout_id}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/workouts/{workout_id}", headers=auth).status_code == 404


def test_meals_default_to_estimated_and_daily_summary_splits_verified(client, auth):
    old_style = client.post("/meals", json={"meal_type": "lunch", "name": "Rice bowl", "calories": 600}, headers=auth)
    assert old_style.status_code == 201
    assert old_style.json()["nutrition_accuracy"] == "estimated"
    verified = client.post("/api/v1/meals", json={
        "meal_type": "snack", "name": "Protein bar", "calories": 200, "meal_time": "16:30:00",
        "nutrition_accuracy": "verified", "nutrition_source": "package label",
    }, headers=auth)
    assert verified.status_code == 201 and verified.json()["meal_time"] == "16:30:00"
    daily = client.get("/api/v1/progress/daily", headers=auth).json()
    assert daily["calories_consumed"] == 800
    assert daily["calories_verified"] == 200
    assert client.patch(f"/api/v1/meals/{verified.json()['id']}", json={"nutrition_accuracy": None}, headers=auth).status_code == 422


def test_body_metrics_with_method(client, auth):
    response = client.put("/api/v1/body-metrics", json={"weight_kg": "80.5", "body_fat_pct": "21.0", "body_fat_method": "smart_scale"}, headers=auth)
    assert response.status_code == 200
    assert response.json()["body_fat_method"] == "smart_scale"
    assert client.put("/api/v1/body-metrics", json={"weight_kg": "80", "body_fat_method": "calipers"}, headers=auth).status_code == 422
    assert client.get("/body-metrics", headers=auth).json()[0]["log_date"] == date.today().isoformat()


def test_dashboard(client, auth):
    client.post("/api/v1/workouts", json={"workout_type": "strength", "name": "Gym", "duration_minutes": 45}, headers=auth)
    data = client.get("/api/v1/dashboard", headers=auth).json()
    assert data["today"]["workouts_count"] == 1
    assert data["workout_streak_days"] == 1
