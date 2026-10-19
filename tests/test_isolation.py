"""One user can never read or change another user's fitness data."""
from datetime import date, timedelta
from tests.helpers import create_program


def test_users_cannot_access_each_others_data(client, make_user):
    alice, bob = make_user("Alice"), make_user("Bob")
    program = create_program(client, alice)["program"]
    goal = client.get("/api/v1/goals", headers=alice).json()[0]
    plan = client.get("/api/v1/plans/today", headers=alice).json()[0]
    checkin = client.post("/api/v1/checkins", json={"sleep_hours": "7"}, headers=alice).json()
    client.post("/api/v1/activities", json={"activity_type": "sprint", "distance_m": "30", "elapsed_seconds": "4.8"}, headers=alice)

    # reads by id are 404 for the other user, not 403, so ids are not even confirmed to exist
    for path in (f"/api/v1/goals/{goal['id']}", f"/api/v1/plans/{plan['id']}", f"/api/v1/checkins/{checkin['id']}",
                 f"/api/v1/programs/{program['id']}"):
        assert client.get(path, headers=bob).status_code == 404, path

    # writes are rejected and leave the data unchanged
    assert client.patch(f"/api/v1/goals/{goal['id']}", json={"target_value": "1"}, headers=bob).status_code == 404
    assert client.patch(f"/api/v1/plans/{plan['id']}", json={"title": "hacked"}, headers=bob).status_code == 404
    assert client.post(f"/api/v1/plans/{plan['id']}/complete", json={"actual_duration_minutes": 5}, headers=bob).status_code == 404
    assert client.post(f"/api/v1/plans/{plan['id']}/skip", json={"reason": "x"}, headers=bob).status_code == 404
    assert client.patch(f"/api/v1/checkins/{checkin['id']}", json={"pain_level": 9}, headers=bob).status_code == 404
    assert client.patch(f"/api/v1/programs/{program['id']}", json={"status": "cancelled"}, headers=bob).status_code == 404
    assert client.post("/api/v1/activities", json={"activity_type": "long_jump", "jump_cm": "200", "planned_workout_id": plan["id"]},
                       headers=bob).status_code == 404
    assert client.get(f"/api/v1/plans/{plan['id']}", headers=alice).json()["title"] == plan["title"]
    assert client.get(f"/api/v1/goals/{goal['id']}", headers=alice).json()["target_value"] == goal["target_value"]

    # lists and reports only show your own rows
    assert client.get("/api/v1/goals", headers=bob).json() == []
    assert client.get("/api/v1/plans?limit=100", headers=bob).json() == []
    assert client.get("/api/v1/checkins/history", headers=bob).json() == []
    assert client.get("/api/v1/activities/history", headers=bob).json() == []
    assert client.get("/api/v1/body-metrics", headers=bob).json() == []
    assert client.get("/api/v1/progress/25-day", headers=bob).status_code == 404
    assert client.get("/api/v1/progress/weekly", headers=bob).json()["training"]["adherence"]["planned_sessions"] == 0
    assert client.get("/api/v1/analysis/daily", headers=bob).json()["source_refs"]["plan_ids"] == []


def test_user_id_in_body_is_ignored(client, make_user, db):
    from app.goals.models.fitness_goal import FitnessGoal
    alice, bob = make_user("Alice"), make_user("Bob")
    alice_id = client.get("/api/v1/user/me", headers=alice).json()["id"]
    body = {"goal_type": "body_weight", "target_date": str(date.today() + timedelta(days=20)), "target_value": "70", "user_id": alice_id}
    created = client.post("/api/v1/goals", json=body, headers=bob).json()
    assert db.get(FitnessGoal, created["id"]).user_id != alice_id
    assert client.get("/api/v1/goals", headers=alice).json() == []


def test_confirming_someone_elses_proposal_is_impossible(client, make_user):
    alice, bob = make_user("Alice"), make_user("Bob")
    create_program(client, alice)
    client.post("/api/v1/checkins", json={"fatigue_level": 5, "soreness_level": 5}, headers=alice)
    proposal = client.post("/api/v1/plans/tomorrow", headers=alice).json()["proposed_plans"][0]
    assert client.patch(f"/api/v1/plans/{proposal['id']}", json={"status": "confirmed"}, headers=bob).status_code == 404
    assert client.get(f"/api/v1/plans/{proposal['id']}", headers=alice).json()["status"] == "proposed"
