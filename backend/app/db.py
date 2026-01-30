"""
Database engine and session management.
"""
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

from app.config import settings
from sqlalchemy import inspect, text

# Create SQLite engine with check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False}
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
)


def init_db() -> None:
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)

    # Lightweight migration for existing SQLite DBs: add new columns if missing.
    try:
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("sessions")}
        if "learning_objectives" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN learning_objectives TEXT"))
    except Exception:
        # Avoid blocking startup if migration introspection fails; table creation covers fresh DBs.
        pass


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Yields a session and ensures it's closed after use.
    """
    with Session(engine) as session:
        yield session

