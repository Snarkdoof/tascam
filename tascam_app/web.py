from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import select, Session
from typing import List, Optional
import os

from tascam_app.database import get_session
from tascam_app.models import Song, Clip, SourceFile, ClipRead, SongRead

app = FastAPI(title="Tascam Player")

# Mount static files
app.mount("/static", StaticFiles(directory="tascam_app/static"), name="static")

templates = Jinja2Templates(directory="tascam_app/templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/songs", response_model=List[Song])
def read_songs(session: Session = Depends(get_session)):
    songs = session.exec(select(Song).order_by(Song.created_at.desc())).all()
    return songs

@app.get("/api/songs/named", response_model=List[Song])
def read_named_songs(session: Session = Depends(get_session)):
    songs = session.exec(
        select(Song)
        .where(Song.is_named == True)
        .order_by(Song.created_at.desc())
    ).all()
    return songs

@app.get("/api/clips", response_model=List[ClipRead])
def read_all_clips(session: Session = Depends(get_session)):
    # SQLModel default response might miss relationships.
    # To fix this quickly without creating new models, we can rely on Pydantic's "from_attributes" (orm_mode)
    # but we need to fetch the data.
    # Let' let's use a joining query for performance and ensure we return the data.
    from sqlalchemy.orm import selectinload
    clips = session.exec(
        select(Clip)
        .options(selectinload(Clip.source_file), selectinload(Clip.song))
        .join(SourceFile)
        .order_by(SourceFile.filename.asc(), Clip.start_seconds.asc())
    ).all()
    return clips

from pydantic import BaseModel, Field as PydanticField
from typing import Dict, Any

class Marker(BaseModel):
    start: float
    end: float
    value: str

class SongUpdate(BaseModel):
    title: Optional[str] = None
    is_named: Optional[bool] = None
    tags: Optional[List[str]] = None
    markers: Optional[List[Dict[str, Any]]] = None

class ClipUpdate(BaseModel):
    title: str | None = None
    comment: str | None = None

class BatchDeleteRequest(BaseModel):
    clip_ids: List[int]

@app.patch("/api/songs/{song_id}")
def update_song(song_id: int, song_update: SongUpdate, session: Session = Depends(get_session)):
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    if song_update.title is not None:
        song.title = song_update.title
        song.is_named = True # Assume if we set a title, it's named
    
    if song_update.is_named is not None:
        song.is_named = song_update.is_named
        
    if song_update.tags is not None:
        song.tags = song_update.tags
        
    if song_update.markers is not None:
        song.markers = song_update.markers
        
    session.add(song)
    session.commit()
    session.refresh(song)
    return song

@app.post("/api/source_files/{source_file_id}/backup")
def trigger_backup(source_file_id: int, session: Session = Depends(get_session)):
    source_file = session.get(SourceFile, source_file_id)
    if not source_file:
        raise HTTPException(status_code=404, detail="Source file not found")
    
    # Stub for background upload task
    source_file.backup_status = "pending"
    session.add(source_file)
    session.commit()
    session.refresh(source_file)
    
    # In a real app, we would trigger an async task here
    return {"ok": True, "status": source_file.backup_status}

@app.patch("/api/clips/{clip_id}")
def update_clip(clip_id: int, clip_update: ClipUpdate, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if clip_update.comment is not None:
        clip.comment = clip_update.comment
    
    if clip_update.title is not None and clip.song:
        clip.song.title = clip_update.title
        clip.song.is_named = True
        session.add(clip.song)
        
    session.add(clip)
    session.commit()
    session.refresh(clip)
    return clip

@app.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Delete file from disk
    if clip.file_path and os.path.exists(clip.file_path):
        try:
            os.remove(clip.file_path)
        except OSError as e:
            print(f"Error deleting file {clip.file_path}: {e}")

    session.delete(clip)
    session.commit()
    return {"ok": True}

@app.post("/api/clips/batch-delete")
def batch_delete_clips(request: BatchDeleteRequest, session: Session = Depends(get_session)):
    if not request.clip_ids:
        return {"ok": True, "count": 0}
        
    statement = select(Clip).where(Clip.id.in_(request.clip_ids))
    clips = session.exec(statement).all()
    
    count = 0
    for clip in clips:
        # Delete file from disk
        if clip.file_path and os.path.exists(clip.file_path):
            try:
                os.remove(clip.file_path)
            except OSError as e:
                print(f"Error deleting file {clip.file_path}: {e}")
                
        session.delete(clip)
        count += 1
        
    session.commit()
    return {"ok": True, "count": count}


@app.get("/api/songs/{song_id}/clips")
def read_song_clips(song_id: int, session: Session = Depends(get_session)):
    clips = session.exec(select(Clip).where(Clip.song_id == song_id)).all()
    return clips

@app.get("/api/clips/{clip_id}/stream")
def stream_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip or not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return FileResponse(clip.file_path, media_type="audio/mpeg")

@app.get("/api/clips/{clip_id}/download")
def download_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip or not os.path.exists(clip.file_path):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Construct filename: YYYY-MM-DD_{id}.mp3 or YYYY-MM-DD_{id}_{song_name}.mp3
    date_str = clip.created_at.strftime("%Y-%m-%d")
    
    filename_base = f"{date_str}_{clip.id}"
    if clip.song and clip.song.title and not clip.song.title.startswith("Song"):
        safe_title = "".join(c for c in clip.song.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(" ", "_")
        if safe_title:
            filename_base = f"{filename_base}_{safe_title}"
            
    filename = f"{filename_base}.mp3"
    
    return FileResponse(
        clip.file_path, 
        media_type="audio/mpeg", 
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
