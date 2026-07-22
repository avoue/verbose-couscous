from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """Create the global async engine and session factory. Call once at startup.

    Connecting through a pgbouncer-style transaction pooler (e.g. Supabase's
    Transaction Pooler / Supavisor on port 6543) needs three things to avoid
    "prepared statement already/does not exist" errors, since each statement
    may be routed to a different backend connection:
      - poolclass=NullPool: SQLAlchemy does NOT keep its own persistent
        connection pool on top of the external pooler. Each checkout opens a
        fresh asyncpg connection and closes it cleanly afterwards, so no
        prepared-statement state leaks between logical requests.
      - statement_cache_size=0: disables asyncpg's own prepared-statement cache.
      - prepared_statement_cache_size=0: disables SQLAlchemy's *own* asyncpg
        prepared-statement cache, a separate setting on top of asyncpg's.
    All three are harmless no-ops against a direct connection or session
    pooler, so it's safe to always set them.
    """
    global _engine, _session_factory
    _engine = create_async_engine(
        database_url,
        poolclass=NullPool,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables() -> None:
    """Create all tables that don't exist yet. Import models first so they
    are registered on Base.metadata."""
    from . import models  # noqa: F401

    assert _engine is not None, "init_db() must be called before create_tables()"
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    assert _session_factory is not None, "init_db() must be called before use"
    return _session_factory
