import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from tinydb import TinyDB

# ---------------------------------------------------------------------------
# TinyDB — únicamente para la funcionalidad heredada de "suppliers"
# ---------------------------------------------------------------------------

DATABASE_PATH = Path(
    os.getenv("TINYDB_PATH", Path(__file__).parent / "data" / "db.json")
)
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

tinydb_instance = TinyDB(DATABASE_PATH)
suppliers = tinydb_instance.table("suppliers")
audit_logs = tinydb_instance.table("audit_logs")
password_reset_tokens = tinydb_instance.table("password_reset_tokens")
profiles = tinydb_instance.table("profiles")
users = tinydb_instance.table("users")

# Alias de compatibilidad hacia atrás — los módulos legacy hacen "from database import db"
db = tinydb_instance

# ---------------------------------------------------------------------------
# SQLAlchemy — motor relacional para "incidents" y nuevos modelos
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent / 'data' / 'incidents.db'}",
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {},
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Dependency generator que provee una sesión SQLAlchemy y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
