import os

# Must be set before the app is imported. load_dotenv() does not override variables that already exist,
# so the empty AI_API_KEY stops tests from ever picking up a real key from .env.
# TEST_DATABASE_URL (optional) runs the suite against an EMPTY, disposable database, e.g. MySQL;
# all tables are created and dropped for every test. Defaults to in-memory SQLite.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["AI_API_KEY"] = ""
os.environ["AI_BASE_URL"] = ""

import itertools  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import BigInteger, create_engine, event  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from app.database.database import Base, get_db  # noqa: E402
import app.database.models  # noqa: E402,F401
from app.main import app  # noqa: E402
from app.training.repository import ExerciseRepository  # noqa: E402
from app.training.exercise_catalog import CATALOG  # noqa: E402


@compiles(BigInteger, "sqlite")
def _bigint_as_integer(type_, compiler, **kw):
    # SQLite only auto-increments INTEGER PRIMARY KEY columns
    return "INTEGER"


if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
else:
    engine = create_engine(TEST_DATABASE_URL)


TestingSession = sessionmaker(bind=engine)


def _get_test_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_test_db


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    db = TestingSession()
    repository = ExerciseRepository(db)
    for name, *_ in CATALOG:  # same rows the migration seeds
        repository.get_by_name(name)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


_emails = itertools.count()


@pytest.fixture
def make_user(client):
    def _make(first_name="Test", password="correct-horse-battery"):
        email = f"user{next(_emails)}@example.com"
        response = client.post("/api/v1/sign-up", json={"first_name": first_name, "last_name": "User", "email": email, "password": password})
        assert response.status_code == 201, response.text
        token = client.post("/api/v1/login", json={"email": email, "password": password}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest.fixture
def auth(make_user):
    return make_user()
