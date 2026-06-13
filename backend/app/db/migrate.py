"""Apply idempotent schema migrations on startup."""

from pathlib import Path

from sqlalchemy import text

from .session import async_session, is_db_available

_MIGRATION_FILES = (
    Path(__file__).resolve().parents[3] / "infra" / "postgres" / "migrations" / "002_pine_scripts_backtests.sql",
)


async def ensure_schema() -> None:
    if not is_db_available() or async_session is None:
        return

    for path in _MIGRATION_FILES:
        if not path.exists():
            continue
        sql = path.read_text(encoding="utf-8")
        async with async_session() as session:
            await session.execute(text(sql))
            await session.commit()
