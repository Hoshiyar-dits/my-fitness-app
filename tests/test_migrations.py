"""Migration consistency. The full check runs only when MIGRATION_TEST_DATABASE_URL points at an EMPTY,
disposable MySQL database (it is migrated up, compared with the models, and downgraded)."""
import os
import re
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.database.database import Base

ROOT = Path(__file__).resolve().parent.parent


def _script():
    return ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))


def test_single_linear_head():
    script = _script()
    assert len(script.get_heads()) == 1
    revisions = list(script.walk_revisions())
    assert revisions[-1].down_revision is None
    assert all(not isinstance(r.down_revision, tuple) for r in revisions), "unexpected merge revision"


def test_every_model_table_is_created_by_a_migration():
    created = set()
    for path in (ROOT / "alembic" / "versions").glob("*.py"):
        created |= set(re.findall(r"op\.create_table\(\s*'(\w+)'", path.read_text()))
    assert set(Base.metadata.tables) <= created, set(Base.metadata.tables) - created


@pytest.mark.skipif(not os.getenv("MIGRATION_TEST_DATABASE_URL"), reason="set MIGRATION_TEST_DATABASE_URL to an empty disposable MySQL database")
def test_migrations_match_models_on_mysql(monkeypatch):
    from alembic import command
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine
    import app.database.database as database

    url = os.environ["MIGRATION_TEST_DATABASE_URL"]
    monkeypatch.setattr(database, "db_url", url)
    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")
    try:
        with create_engine(url).connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    finally:
        command.downgrade(config, "base")
