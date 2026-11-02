import os
from sqlmodel import SQLModel, create_engine, Session
from tascam_app.models import SourceFile, Song, Clip, User, Repertoire, RepertoireItem

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    db_url = "sqlite:///tascam.db"

# SQLAlchemy 1.4+ expects postgresql:// instead of postgres://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
