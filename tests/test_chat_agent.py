"""AI coach tests. The LangChain chat model is always mocked: no request leaves the machine."""
import json
import pytest
from fastapi import HTTPException
from langchain_core.messages import AIMessage, ToolMessage
from app.chat import ai_client
from tests.helpers import create_program


def tool_call(name, arguments=None, call_id="call_1"):
    return {"name": name, "args": arguments or {}, "id": call_id, "type": "tool_call"}


def reply(content="", tool_calls=None):
    return AIMessage(content=content or "", tool_calls=tool_calls or [])


class ScriptedModel:
    """Plays back a list of model turns (stands in for ai_client.invoke) and records every request."""
    def __init__(self, *turns):
        self.turns = list(turns)
        self.requests = []

    def __call__(self, messages, tools=None, tool_choice=None, retries=1):
        self.requests.append({"messages": list(messages), "tools": tools, "tool_choice": tool_choice})
        turn = self.turns.pop(0)
        return turn(messages) if callable(turn) else turn  # a callable turn can react to earlier tool results

    def tool_results(self):
        last = self.requests[-1]["messages"]
        return [json.loads(m.content) for m in last if isinstance(m, ToolMessage)]


@pytest.fixture
def model(monkeypatch):
    def install(*turns):
        scripted = ScriptedModel(*turns)
        monkeypatch.setattr(ai_client, "invoke", scripted)
        return scripted
    return install


def test_tools_are_offered_and_receive_only_the_users_data(client, make_user, model):
    alice, bob = make_user("Alice"), make_user("Bob")
    create_program(client, alice)
    client.post("/api/v1/activities", json={"activity_type": "run", "distance_m": "1000", "elapsed_seconds": "240"}, headers=bob)
    scripted = model(
        reply(tool_calls=[tool_call("get_running_progress", {"days": 30}, "c1"), tool_call("get_user_goals", {}, "c2")]),
        reply("You have no runs logged yet."),
    )
    response = client.post("/api/v1/chat", json={"message": "How is my running?"}, headers=bob)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assistant_message"]["content"] == "You have no runs logged yet."
    assert [a["tool"] for a in body["actions"]] == ["get_running_progress", "get_user_goals"]

    tool_names = {t.name for t in scripted.requests[0]["tools"]}
    assert {"get_user_goals", "get_workout_history", "get_daily_checkin", "get_running_progress", "get_jump_performance",
            "get_body_measurement_history", "get_weekly_progress", "propose_tomorrow_workout", "save_confirmed_workout_plan"} <= tool_names
    assert not any("user_id" in json.dumps(t.args) for t in scripted.requests[0]["tools"])

    running, goals = scripted.tool_results()
    assert running["ok"] and [r["elapsed_seconds"] for r in running["data"]["recent"]] == [240.0]  # Bob's own run only
    assert goals["ok"] and goals["data"]["goals"] == []  # Alice's goals are not visible


def test_invalid_and_unknown_tool_calls_return_errors_not_data(client, auth, model):
    scripted = model(
        reply(tool_calls=[tool_call("run_sql", {"query": "select * from users"}, "c1"),
                          tool_call("get_workout_history", {"days": 10000}, "c2")]),
        reply("Sorry, I could not load that."),
    )
    assert client.post("/api/v1/chat", json={"message": "show everything"}, headers=auth).status_code == 200
    unknown, invalid = scripted.tool_results()
    assert unknown == {"ok": False, "error": "Unknown tool 'run_sql'"}
    assert invalid["ok"] is False and "Invalid arguments" in invalid["error"]


def test_proposals_from_chat_stay_unconfirmed_until_user_agrees(client, auth, model):
    create_program(client, auth)
    client.post("/api/v1/checkins", json={"fatigue_level": 5, "soreness_level": 5}, headers=auth)

    # turn 1: the model proposes and immediately tries to save, before the user has seen the proposal
    def save_what_was_just_proposed(messages):
        proposed = json.loads(messages[-1].content)["data"]["plan_ids"][0]
        return reply(tool_calls=[tool_call("save_confirmed_workout_plan", {"plan_id": proposed, "user_confirmed": True}, "c2")])

    scripted = model(
        reply(tool_calls=[tool_call("propose_tomorrow_workout", {}, "c1")]),
        save_what_was_just_proposed,
        reply("I suggest a recovery day tomorrow. Shall I use it?"),
    )
    response = client.post("/api/v1/chat", json={"message": "plan tomorrow please"}, headers=auth).json()
    propose_result, save_result = scripted.tool_results()
    proposed_id = propose_result["data"]["plan_ids"][0]
    assert propose_result["data"]["requires_confirmation"] is True
    assert save_result["ok"] is False and "only just proposed" in save_result["error"]
    assert client.get(f"/api/v1/plans/{proposed_id}", headers=auth).json()["status"] == "proposed"
    assert client.get(f"/api/v1/plans/{proposed_id}", headers=auth).json()["source"] == "ai_agent"
    assert response["actions"][0]["plan_ids"] == [proposed_id]

    # a save without user_confirmed is refused
    scripted = model(reply(tool_calls=[tool_call("save_confirmed_workout_plan", {"plan_id": proposed_id, "user_confirmed": False})]),
                     reply("Okay."))
    client.post("/api/v1/chat", json={"message": "hmm"}, headers=auth)
    assert scripted.tool_results()[0]["ok"] is False
    assert client.get(f"/api/v1/plans/{proposed_id}", headers=auth).json()["status"] == "proposed"

    # turn 3: the user agrees, so the model may save it
    scripted = model(reply(tool_calls=[tool_call("save_confirmed_workout_plan", {"plan_id": proposed_id, "user_confirmed": True})]),
                     reply("Saved. Enjoy the recovery day."))
    assert client.post("/api/v1/chat", json={"message": "yes, use it"}, headers=auth).status_code == 200
    assert scripted.tool_results()[0]["ok"] is True
    assert client.get(f"/api/v1/plans/{proposed_id}", headers=auth).json()["status"] == "confirmed"


def test_ai_cannot_confirm_another_users_plan(client, make_user, model):
    alice, bob = make_user("Alice"), make_user("Bob")
    create_program(client, alice)
    client.post("/api/v1/checkins", json={"fatigue_level": 5, "soreness_level": 5}, headers=alice)
    proposal = client.post("/api/v1/plans/tomorrow", headers=alice).json()["proposed_plans"][0]
    scripted = model(reply(tool_calls=[tool_call("save_confirmed_workout_plan", {"plan_id": proposal["id"], "user_confirmed": True})]),
                     reply("Done"))
    client.post("/api/v1/chat", json={"message": "yes"}, headers=bob)
    assert scripted.tool_results()[0] == {"ok": False, "error": "Plan not found"}
    assert client.get(f"/api/v1/plans/{proposal['id']}", headers=alice).json()["status"] == "proposed"


def test_tool_round_limit_forces_a_final_answer(client, auth, model):
    turns = [reply(tool_calls=[tool_call("get_user_goals", {}, f"c{i}")]) for i in range(6)] + [reply("Here is what I found.")]
    scripted = model(*turns)
    response = client.post("/api/v1/chat", json={"message": "loop"}, headers=auth).json()
    assert response["assistant_message"]["content"] == "Here is what I found."
    assert scripted.requests[-1]["tool_choice"] == "none"


def test_ai_failure_returns_error_and_does_not_break_tracking(client, auth, monkeypatch):
    def unavailable(*args, **kwargs):
        raise HTTPException(status_code=502, detail="AI coach is unavailable right now")
    monkeypatch.setattr(ai_client, "invoke", unavailable)
    response = client.post("/api/v1/chat", json={"message": "hi"}, headers=auth)
    assert response.status_code == 502
    assert client.get("/api/v1/chat/history", headers=auth).json() == []  # no orphan message saved
    assert client.post("/api/v1/checkins", json={"sleep_hours": "7"}, headers=auth).status_code == 201
    assert client.get("/api/v1/progress/weekly", headers=auth).status_code == 200


def test_ai_not_configured_returns_503(client, auth):
    response = client.post("/api/v1/chat", json={"message": "hi"}, headers=auth)
    assert response.status_code == 503 and "AI_API_KEY" in response.json()["detail"]


def test_chat_history_is_saved_after_success(client, auth, model):
    model(reply("Hello!"))
    client.post("/api/v1/chat", json={"message": "hi"}, headers=auth)
    history = client.get("/api/v1/chat/history", headers=auth).json()
    assert [(m["role"], m["content"]) for m in history] == [("user", "hi"), ("assistant", "Hello!")]


def test_empty_reply_is_retried_once_and_bold_is_stripped(client, auth, model):
    scripted = model(reply(""), reply("Aim for **1.6-2.2 g/kg** of protein a day."))
    response = client.post("/api/v1/chat", json={"message": "protein?"}, headers=auth).json()
    assert response["assistant_message"]["content"] == "Aim for 1.6-2.2 g/kg of protein a day."
    assert len(scripted.requests) == 2


def test_malformed_tool_call_from_provider_is_retried(monkeypatch):
    import openai
    import httpx2 as httpx
    error_body = {"error": {"message": "Tool choice is none, but model called a tool", "code": "tool_use_failed"}}
    error = openai.BadRequestError("bad tool call", response=httpx.Response(400, request=httpx.Request("POST", "http://test")), body=error_body)
    calls = []

    class FakeChatModel:
        def bind_tools(self, tools, tool_choice=None):
            return self

        def invoke(self, messages):
            calls.append(messages)
            if len(calls) == 1:
                raise error
            return reply("ok")

    monkeypatch.setattr(ai_client, "_get_model", lambda: FakeChatModel())
    assert ai_client.invoke([], tools=[object()]).text == "ok"
    assert len(calls) == 2

    calls.clear()
    monkeypatch.setattr(FakeChatModel, "invoke", lambda self, messages: (_ for _ in ()).throw(error))
    with pytest.raises(HTTPException) as raised:
        ai_client.invoke([])
    assert raised.value.status_code == 502


def test_tool_calls_with_unparseable_arguments_get_an_error_result(client, auth, model):
    broken = AIMessage(content="", invalid_tool_calls=[{"name": "get_user_goals", "args": "{not json", "id": "c1",
                                                         "error": "bad JSON", "type": "invalid_tool_call"}])
    scripted = model(broken, reply("Could not load your goals."))
    response = client.post("/api/v1/chat", json={"message": "goals?"}, headers=auth).json()
    assert response["assistant_message"]["content"] == "Could not load your goals."
    assert scripted.tool_results() == [{"ok": False, "error": "Invalid arguments for 'get_user_goals': bad JSON"}]


def test_chat_model_uses_configured_provider(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "ollama")
    monkeypatch.setenv("AI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("AI_MODEL", "qwen3:8b")
    chat_model = ai_client._get_model()
    assert chat_model.model_name == "qwen3:8b"
    assert chat_model.openai_api_base == "http://localhost:11434/v1"
    assert chat_model.max_retries == 0
