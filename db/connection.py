"""
WorkSphere HR - Database Connection Layer
Agnostic database connection supporting SQLite and PostgreSQL.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

# SQLite requires specific connect_args for multithreading in Streamlit
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_engine():
    """Return the configured SQLAlchemy engine."""
    return engine


def init_db():
    """Create all tables defined in models if they do not exist."""
    # Import models so they are registered with Base metadata
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """
    Context manager providing a transactional database session.
    Automatically commits if block succeeds, rolls back on exception, and always closes.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
