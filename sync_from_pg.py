import os
import shutil
from datetime import datetime
from sqlmodel import create_engine, Session, select, SQLModel
from tqdm.auto import tqdm
from tascam_app.models import SourceFile, Song, Clip, User, Repertoire, RepertoireItem

def sync_pg_to_sqlite(sqlite_path="tascam.db", pg_url=None):
    if not pg_url:
        pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # 1. Non-destructive backup of local sqlite db if it exists
    if os.path.exists(sqlite_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{sqlite_path}.bak_{timestamp}"
        shutil.copy2(sqlite_path, backup_path)
        print(f"Created backup of SQLite database at {backup_path}")

    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    pg_engine = create_engine(pg_url)

    # Ensure tables exist in SQLite
    SQLModel.metadata.create_all(sqlite_engine)

    with Session(pg_engine) as pg_session, Session(sqlite_engine) as sqlite_session:
        # Table 1: Users
        pg_users = pg_session.exec(select(User)).all()
        sqlite_users = {u.id: u for u in sqlite_session.exec(select(User)).all()}
        for u in tqdm(pg_users, desc="Syncing users"):
            if u.id not in sqlite_users:
                sqlite_session.add(User(**u.model_dump()))
            else:
                existing = sqlite_users[u.id]
                for k, v in u.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

        # Table 2: SourceFiles
        pg_files = pg_session.exec(select(SourceFile)).all()
        sqlite_files = {f.id: f for f in sqlite_session.exec(select(SourceFile)).all()}
        for f in tqdm(pg_files, desc="Syncing source files"):
            if f.id not in sqlite_files:
                sqlite_session.add(SourceFile(**f.model_dump()))
            else:
                existing = sqlite_files[f.id]
                for k, v in f.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

        # Table 3: Songs
        pg_songs = pg_session.exec(select(Song)).all()
        sqlite_songs = {s.id: s for s in sqlite_session.exec(select(Song)).all()}
        for s in tqdm(pg_songs, desc="Syncing songs"):
            if s.id not in sqlite_songs:
                sqlite_session.add(Song(**s.model_dump()))
            else:
                existing = sqlite_songs[s.id]
                for k, v in s.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

        # Table 4: Clips
        pg_clips = pg_session.exec(select(Clip)).all()
        sqlite_clips = {c.id: c for c in sqlite_session.exec(select(Clip)).all()}
        for c in tqdm(pg_clips, desc="Syncing clips"):
            if c.id not in sqlite_clips:
                sqlite_session.add(Clip(**c.model_dump()))
            else:
                existing = sqlite_clips[c.id]
                for k, v in c.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

        # Table 5: Repertoires
        pg_reps = pg_session.exec(select(Repertoire)).all()
        sqlite_reps = {r.id: r for r in sqlite_session.exec(select(Repertoire)).all()}
        for r in tqdm(pg_reps, desc="Syncing repertoires"):
            if r.id not in sqlite_reps:
                sqlite_session.add(Repertoire(**r.model_dump()))
            else:
                existing = sqlite_reps[r.id]
                for k, v in r.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

        # Table 6: RepertoireItems
        pg_items = pg_session.exec(select(RepertoireItem)).all()
        sqlite_items = {item.id: item for item in sqlite_session.exec(select(RepertoireItem)).all()}
        for item in tqdm(pg_items, desc="Syncing repertoire items"):
            if item.id not in sqlite_items:
                sqlite_session.add(RepertoireItem(**item.model_dump()))
            else:
                existing = sqlite_items[item.id]
                for k, v in item.model_dump().items():
                    setattr(existing, k, v)
        sqlite_session.commit()

    print("Sync from PostgreSQL to SQLite completed successfully!")

if __name__ == "__main__":
    sync_pg_to_sqlite()
