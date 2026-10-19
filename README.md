# my-fitness-app

FastAPI + MySQL fitness tracker with a 25-day adaptive training program (running, long jump, high jump,
body composition) and an AI coach that works on the user's data through controlled tools.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # add -r requirements-dev.txt for tests and lint
cp .env.example .env                     # then fill in DATABASE_URL, JWT_SECRET_KEY and (optionally) AI_*
alembic upgrade head                     # creates / updates the schema (additive; see "Migrations")
uvicorn app.main:app --reload            # API docs at http://localhost:8000/docs, UI at /ui/
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | yes | `mysql+pymysql://user:password@host:3306/db`. Also used by Alembic |
| `JWT_SECRET_KEY` | yes | Signing key for login tokens (long random string) |
| `ALOGORITHM` | no | JWT algorithm, default `HS256` (name spelled as in the code) |
| `ACCESS_TOKEN_EXPIRY` | no | Token lifetime in minutes, default 60 |
| `AI_API_KEY` | no | Enables the AI coach. Without it `/chat` returns 503; everything else works |
| `AI_BASE_URL` | no | Empty for OpenAI, or any OpenAI-compatible endpoint with tool calling (e.g. Groq) |
| `AI_MODEL` | no | Model name for that provider, default `gpt-5-mini` |

## API

Every route is served under `/api/v1` and, for the bundled frontend and existing clients, at the same
path without the prefix. All fitness data is scoped to the user in the bearer token; ids belonging to
another user return 404.

| Area | Endpoints |
|---|---|
| Auth / profile | `POST /sign-up`, `POST /login`, `GET /user/me`, `GET/POST/PATCH /user/profile` |
| 25-day program | `POST /programs` (initial assessment → calendar), `GET /programs/current`, `GET/PATCH /programs/{id}` (cancel, confirm medical clearance) |
| Plans | `GET /plans/today`, `GET /plans`, `POST /plans`, `GET/PATCH /plans/{id}` (edit, confirm/reject proposal), `POST /plans/{id}/complete`, `POST /plans/{id}/skip`, `POST /plans/tomorrow` |
| Exercises | `GET /exercises` |
| Goals | `POST /goals`, `GET /goals`, `GET/PATCH /goals/{id}` |
| Check-ins | `POST /checkins`, `GET /checkins/today`, `GET /checkins/history`, `GET/PATCH /checkins/{id}` |
| Performance | `POST /activities`, `GET /activities/history` |
| Body measurements | `PUT /body-metrics`, `GET /body-metrics`, `DELETE /body-metrics/{date}` |
| Nutrition (optional) | `/meals` CRUD (with meal time and estimated/verified flag) |
| Progress | `GET /dashboard`, `GET /progress/daily`, `GET /progress/weekly`, `GET /progress/range`, `GET /progress/25-day` |
| Analysis | `GET /analysis/daily` |
| AI coach | `POST /chat`, `GET /chat/history`, `DELETE /chat/history` |
| Logged workouts | `/workouts` CRUD (free-form log; completing a plan also adds an entry here) |

Planned sessions are completed with `POST /plans/{id}/complete`, not under `/workouts/{id}`, because
`/workouts/{id}` already means a logged workout.

## How the 25-day program works

1. **Initial assessment** (`POST /programs`): experience level, minutes per day, equipment, injury history,
   current pain, medical restrictions and optional current performance / weight and targets. Age comes from
   the profile. If current pain or a medical restriction is reported without confirmed clearance, the
   program waits in `awaiting_clearance` and no training is scheduled until clearance is confirmed.
2. **Calendar** (`app/training/program_generator.py`): day 1 baseline jump and sprint assessment, day 3 baseline
   run, a 7-day microcycle of strength, long jump, endurance, recovery, sprint, rest and high jump, a
   mid-cycle run check on day 13, then a taper and final assessments on days 23 and 25 that use the same
   protocol. Volume scales with level, phase and available time. Beginners never get maximal sprints, and
   bar jumps require a high jump setup. High-impact days are never back-to-back.
3. **Daily loop**: check in (`POST /checkins`), complete or skip the session, then `POST /plans/tomorrow`.
   The rules in `app/analysis/readiness.py` decide `proceed`, `proceed_with_caution` (no check-in), `modify`
   (one fatigue sign or mild pain, about 30% less volume, lower intensity, no impact work if there is pain),
   `recovery` (pain ≥ 4/10 or several fatigue signs) or `stop` (warning symptoms: rest and medical advice).
   Missed sessions are never "made up". Any change is saved as a **proposed** plan with its reasons. It only
   replaces the scheduled session when confirmed (`PATCH /plans/{id}` `{"status": "confirmed"}`). The
   day's review is stored in `daily_analyses` with the ids of the rows it used.
4. **Progress** (`/progress/25-day`, `/progress/weekly`): runs are compared only over the same distance and
   jumps only with the same technique, using each session's best result. Changes smaller than typical
   measurement error are reported as "within noise". Weight and body fat are shown as multi-day trends, and
   body fat only from one measurement method, labelled as an estimate.

## AI coach

`POST /chat` runs a LangChain tool-calling loop (`app/chat/agent.py`): `ChatOpenAI` from `langchain-openai`
pointed at any OpenAI-compatible endpoint (OpenAI, Groq, or a local Ollama at `http://localhost:11434/v1`),
with the tools bound as LangChain `StructuredTool`s.
The model can only use the tools in `app/chat/tools.py`: goals, workout history, upcoming plans, check-ins,
running and jump progress, body measurements, nutrition summary, weekly and program progress,
`propose_tomorrow_workout` and `save_confirmed_workout_plan`. The user id is bound on the server and is never
a tool argument. Arguments are validated, there is no free-form database access, and tool errors are returned
as `ok: false`. A plan proposed in the same chat turn cannot be confirmed in that turn, so the user always
sees it before it is saved. If the AI provider is down or not configured, only `/chat` fails.

## Migrations

```bash
alembic upgrade head      # apply
alembic check             # models and database agree
```

`d4e8f2a1b6c7` is additive. It adds new tables, nullable columns on `body_metrics` and `meals`, and
`meals.nutrition_accuracy` with default `'estimated'`, and it seeds the exercise catalog. Back up production
before upgrading anyway. Its `downgrade` deletes all program, goal, check-in, activity and analysis data.

## Tests

```bash
pip install -r requirements-dev.txt
pytest                                   # in-memory SQLite, AI calls mocked, no network
ruff check --isolated --select E,F --ignore E501 app alembic tests
# optional, against EMPTY disposable MySQL databases (tables are created and dropped):
TEST_DATABASE_URL=mysql+pymysql://...           pytest
MIGRATION_TEST_DATABASE_URL=mysql+pymysql://... pytest tests/test_migrations.py
```

## Notes and limits

- This is a training and tracking tool, not medical advice. Results over 25 days are not guaranteed.
- Timestamps on the new tables are stored as UTC and returned timezone-aware. Older tables still use the
  database server's local time. "Today" is the server's local date.
- The bundled frontend (`/ui`) covers the original features only. The program, check-in and plan features are
  API-only for now.
