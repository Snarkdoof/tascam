from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import select, Session
from typing import List
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

@app.get("/api/clips", response_model=List[ClipRead])
def read_all_clips(session: Session = Depends(get_session)):
    # SQLModel default response might miss relationships.
    # To fix this quickly without creating new models, we can rely on Pydantic's "from_attributes" (orm_mode)
    # but we need to fetch the data.
    # Let's use a joining query for performance and ensure we return the data.
    from sqlalchemy.orm import selectinload
    clips = session.exec(
        select(Clip)
        .options(selectinload(Clip.source_file), selectinload(Clip.song))
        .join(SourceFile)
        .order_by(SourceFile.filename.asc(), Clip.start_seconds.asc())
    ).all()
    return clips

from pydantic import BaseModel
class ClipUpdate(BaseModel):
    title: str | None = None
    comment: str | None = None

class BatchDeleteRequest(BaseModel):
    clip_ids: List[int]

@app.patch("/api/clips/{clip_id}")
def update_clip(clip_id: int, clip_update: ClipUpdate, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    if clip_update.comment is not None:
        clip.comment = clip_update.comment
    
    if clip_update.title is not None and clip.song:
        clip.song.title = clip_update.title
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
