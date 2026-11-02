import os
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from datetime import datetime
from sqlmodel import select, Session
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from tascam_app.database import get_session, create_db_and_tables
from tascam_app.models import (
    Song, Clip, SourceFile, ClipRead, SongRead, User,
    Repertoire, RepertoireItem, RepertoireRead, RepertoireDetailRead,
    RepertoireItemRead, RepertoireCreate, RepertoireUpdate,
    RepertoireItemCreate, RepertoireItemUpdate, RepertoireBatchAddRequest,
    RepertoireReorderRequest
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Tascam Player", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "super-secret-key-change-in-prod"))

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get("CLIENT_ID"),
    client_secret=os.environ.get("CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Mount static files
app.mount("/static", StaticFiles(directory="tascam_app/static"), name="static")

templates = Jinja2Templates(directory="tascam_app/templates")

def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    user_email = request.session.get("user_email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    if not user.is_approved and not user.is_admin:
        raise HTTPException(status_code=403, detail="Account pending approval")
        
    return user

def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

@app.get("/manifest.json")
def get_manifest():
    return FileResponse("tascam_app/static/manifest.json", media_type="application/manifest+json")

@app.get("/sw.js")
def get_sw():
    return FileResponse("tascam_app/static/sw.js", media_type="application/javascript")

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    # If running behind an HTTPS proxy, ensure scheme is https
    if "njaal.net" in str(redirect_uri):
        redirect_uri = str(redirect_uri).replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request, session: Session = Depends(get_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        # First user is superuser
        is_first = session.exec(select(User)).first() is None
        user = User(
            email=email, 
            name=name, 
            picture=picture, 
            is_admin=is_first,
            is_approved=is_first
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
    request.session["user_email"] = user.email
    return RedirectResponse(url="/")

@app.get("/logout")
def logout(request: Request):
    request.session.pop("user_email", None)
    return RedirectResponse(url="/")

@app.get("/")
def read_root(request: Request, session: Session = Depends(get_session)):
    user_email = request.session.get("user_email")
    if not user_email:
        return templates.TemplateResponse("login.html", {"request": request})
        
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user or (not user.is_approved and not user.is_admin):
        return templates.TemplateResponse("pending.html", {"request": request, "user": user})
        
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/admin")
def admin_page(request: Request, user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "current_user": user})

@app.post("/api/admin/users/{user_id}/approve")
def approve_user(user_id: int, user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    target_user.is_approved = not target_user.is_approved
    session.add(target_user)
    session.commit()
    return {"ok": True, "is_approved": target_user.is_approved}

@app.get("/api/songs", response_model=List[Song])
def read_songs(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    query = select(Song).order_by(Song.created_at.desc())
    if not user.is_admin:
        query = query.where(Song.is_private == False)
    return session.exec(query).all()

@app.get("/api/songs/named", response_model=List[Song])
def read_named_songs(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    query = select(Song).where(Song.is_named == True).order_by(Song.created_at.desc())
    if not user.is_admin:
        query = query.where(Song.is_private == False)
    return session.exec(query).all()

@app.get("/api/clips", response_model=List[ClipRead])
def read_all_clips(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    query = select(Clip).options(selectinload(Clip.source_file), selectinload(Clip.song)).join(SourceFile)
    
    if not user.is_admin:
        query = query.where(Clip.is_private == False)
        
    query = query.order_by(SourceFile.filename.asc(), Clip.start_seconds.asc())
    
    clips = session.exec(query).all()
    
    # Filter out clips where the associated song is private
    if not user.is_admin:
        clips = [c for c in clips if not (c.song and c.song.is_private)]
        
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
    is_private: Optional[bool] = None
    tags: Optional[List[str]] = None
    markers: Optional[List[Dict[str, Any]]] = None

class ClipUpdate(BaseModel):
    title: str | None = None
    comment: str | None = None
    is_private: Optional[bool] = None

class BatchDeleteRequest(BaseModel):
    clip_ids: List[int]

@app.patch("/api/songs/{song_id}")
def update_song(song_id: int, song_update: SongUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
        
    # Only admins can change privacy
    if song_update.is_private is not None and user.is_admin:
        song.is_private = song_update.is_private
    
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
def trigger_backup(source_file_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
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
def update_clip(clip_id: int, clip_update: ClipUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    # Only admins can change privacy
    if clip_update.is_private is not None and user.is_admin:
        clip.is_private = clip_update.is_private
    
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
def delete_clip(clip_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
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
def batch_delete_clips(request: BatchDeleteRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
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
def read_song_clips(song_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    clips = session.exec(select(Clip).where(Clip.song_id == song_id)).all()
    return clips

# ==========================================
# Repertoire Endpoints
# ==========================================

@app.get("/api/repertoires", response_model=List[RepertoireRead])
def read_repertoires(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    query = select(Repertoire).options(selectinload(Repertoire.items).selectinload(RepertoireItem.clip))
    if not user.is_admin:
        query = query.where(Repertoire.is_private == False)
    query = query.order_by(Repertoire.created_at.desc())
    repertoires = session.exec(query).all()

    result = []
    for rep in repertoires:
        item_count = len(rep.items)
        total_duration = sum(item.clip.duration_seconds for item in rep.items if item.clip)
        result.append(RepertoireRead(
            id=rep.id,
            name=rep.name,
            description=rep.description,
            is_private=rep.is_private,
            created_at=rep.created_at,
            updated_at=rep.updated_at,
            item_count=item_count,
            total_duration_seconds=total_duration
        ))
    return result

@app.post("/api/repertoires", response_model=RepertoireRead)
def create_repertoire(repertoire_data: RepertoireCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = Repertoire(
        name=repertoire_data.name,
        description=repertoire_data.description,
        is_private=repertoire_data.is_private if user.is_admin else False
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return RepertoireRead(
        id=rep.id,
        name=rep.name,
        description=rep.description,
        is_private=rep.is_private,
        created_at=rep.created_at,
        updated_at=rep.updated_at,
        item_count=0,
        total_duration_seconds=0.0
    )

@app.get("/api/repertoires/{repertoire_id}", response_model=RepertoireDetailRead)
def read_repertoire(repertoire_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    query = select(Repertoire).where(Repertoire.id == repertoire_id).options(
        selectinload(Repertoire.items).selectinload(RepertoireItem.clip).selectinload(Clip.song),
        selectinload(Repertoire.items).selectinload(RepertoireItem.song)
    )
    rep = session.exec(query).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    sorted_items = sorted(rep.items, key=lambda x: x.position)
    total_duration = sum(item.clip.duration_seconds for item in sorted_items if item.clip)

    items_read = []
    for item in sorted_items:
        items_read.append(RepertoireItemRead(
            id=item.id,
            repertoire_id=item.repertoire_id,
            clip_id=item.clip_id,
            song_id=item.song_id,
            position=item.position,
            notes=item.notes,
            created_at=item.created_at,
            clip=ClipRead.model_validate(item.clip) if item.clip else None,
            song=SongRead.model_validate(item.song) if item.song else None
        ))

    return RepertoireDetailRead(
        id=rep.id,
        name=rep.name,
        description=rep.description,
        is_private=rep.is_private,
        created_at=rep.created_at,
        updated_at=rep.updated_at,
        item_count=len(sorted_items),
        total_duration_seconds=total_duration,
        items=items_read
    )

@app.patch("/api/repertoires/{repertoire_id}", response_model=RepertoireRead)
def update_repertoire(repertoire_id: int, rep_update: RepertoireUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = session.get(Repertoire, repertoire_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    if rep_update.name is not None:
        rep.name = rep_update.name
    if rep_update.description is not None:
        rep.description = rep_update.description
    if rep_update.is_private is not None and user.is_admin:
        rep.is_private = rep_update.is_private
    rep.updated_at = datetime.utcnow()

    session.add(rep)
    session.commit()
    session.refresh(rep)

    from sqlalchemy.orm import selectinload
    items = session.exec(select(RepertoireItem).where(RepertoireItem.repertoire_id == rep.id).options(selectinload(RepertoireItem.clip))).all()
    duration = sum(item.clip.duration_seconds for item in items if item.clip)
    return RepertoireRead(
        id=rep.id,
        name=rep.name,
        description=rep.description,
        is_private=rep.is_private,
        created_at=rep.created_at,
        updated_at=rep.updated_at,
        item_count=len(items),
        total_duration_seconds=duration
    )

@app.delete("/api/repertoires/{repertoire_id}")
def delete_repertoire(repertoire_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = session.get(Repertoire, repertoire_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    items = session.exec(select(RepertoireItem).where(RepertoireItem.repertoire_id == repertoire_id)).all()
    for item in items:
        session.delete(item)
    session.delete(rep)
    session.commit()
    return {"ok": True}

@app.post("/api/repertoires/{repertoire_id}/items", response_model=RepertoireItemRead)
def add_repertoire_item(repertoire_id: int, item_data: RepertoireItemCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = session.get(Repertoire, repertoire_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    clip = None
    if item_data.clip_id:
        clip = session.get(Clip, item_data.clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

    song_id = item_data.song_id or (clip.song_id if clip else None)

    if item_data.position is not None:
        pos = item_data.position
    else:
        existing_items = session.exec(select(RepertoireItem).where(RepertoireItem.repertoire_id == repertoire_id)).all()
        pos = max([i.position for i in existing_items], default=-1) + 1

    new_item = RepertoireItem(
        repertoire_id=repertoire_id,
        clip_id=item_data.clip_id,
        song_id=song_id,
        position=pos,
        notes=item_data.notes
    )
    rep.updated_at = datetime.utcnow()
    session.add(rep)
    session.add(new_item)
    session.commit()
    session.refresh(new_item)

    from sqlalchemy.orm import selectinload
    item_loaded = session.exec(
        select(RepertoireItem).where(RepertoireItem.id == new_item.id).options(
            selectinload(RepertoireItem.clip).selectinload(Clip.song),
            selectinload(RepertoireItem.song)
        )
    ).first()

    return RepertoireItemRead(
        id=item_loaded.id,
        repertoire_id=item_loaded.repertoire_id,
        clip_id=item_loaded.clip_id,
        song_id=item_loaded.song_id,
        position=item_loaded.position,
        notes=item_loaded.notes,
        created_at=item_loaded.created_at,
        clip=ClipRead.model_validate(item_loaded.clip) if item_loaded.clip else None,
        song=SongRead.model_validate(item_loaded.song) if item_loaded.song else None
    )

@app.post("/api/repertoires/{repertoire_id}/items/batch")
def batch_add_repertoire_items(repertoire_id: int, request: RepertoireBatchAddRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = session.get(Repertoire, repertoire_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    if not request.clip_ids:
        return {"ok": True, "added_count": 0}

    existing_items = session.exec(select(RepertoireItem).where(RepertoireItem.repertoire_id == repertoire_id)).all()
    curr_pos = max([i.position for i in existing_items], default=-1) + 1

    clips = session.exec(select(Clip).where(Clip.id.in_(request.clip_ids))).all()
    clips_by_id = {c.id: c for c in clips}

    added_count = 0
    for clip_id in request.clip_ids:
        clip = clips_by_id.get(clip_id)
        if not clip:
            continue
        new_item = RepertoireItem(
            repertoire_id=repertoire_id,
            clip_id=clip.id,
            song_id=clip.song_id,
            position=curr_pos + added_count
        )
        session.add(new_item)
        added_count += 1

    rep.updated_at = datetime.utcnow()
    session.add(rep)
    session.commit()
    return {"ok": True, "added_count": added_count}

@app.patch("/api/repertoires/{repertoire_id}/items/{item_id}", response_model=RepertoireItemRead)
def update_repertoire_item(repertoire_id: int, item_id: int, item_update: RepertoireItemUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    item = session.get(RepertoireItem, item_id)
    if not item or item.repertoire_id != repertoire_id:
        raise HTTPException(status_code=404, detail="Repertoire item not found")
    if item.repertoire and item.repertoire.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    if item_update.notes is not None:
        item.notes = item_update.notes
    if item_update.position is not None:
        item.position = item_update.position

    if item.repertoire:
        item.repertoire.updated_at = datetime.utcnow()
        session.add(item.repertoire)
    session.add(item)
    session.commit()
    session.refresh(item)

    from sqlalchemy.orm import selectinload
    item_loaded = session.exec(
        select(RepertoireItem).where(RepertoireItem.id == item.id).options(
            selectinload(RepertoireItem.clip).selectinload(Clip.song),
            selectinload(RepertoireItem.song)
        )
    ).first()

    return RepertoireItemRead(
        id=item_loaded.id,
        repertoire_id=item_loaded.repertoire_id,
        clip_id=item_loaded.clip_id,
        song_id=item_loaded.song_id,
        position=item_loaded.position,
        notes=item_loaded.notes,
        created_at=item_loaded.created_at,
        clip=ClipRead.model_validate(item_loaded.clip) if item_loaded.clip else None,
        song=SongRead.model_validate(item_loaded.song) if item_loaded.song else None
    )

@app.delete("/api/repertoires/{repertoire_id}/items/{item_id}")
def delete_repertoire_item(repertoire_id: int, item_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    item = session.get(RepertoireItem, item_id)
    if not item or item.repertoire_id != repertoire_id:
        raise HTTPException(status_code=404, detail="Repertoire item not found")
    if item.repertoire and item.repertoire.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    rep = item.repertoire
    session.delete(item)
    session.commit()

    remaining_items = session.exec(
        select(RepertoireItem).where(RepertoireItem.repertoire_id == repertoire_id).order_by(RepertoireItem.position.asc())
    ).all()
    for idx, rem_item in enumerate(remaining_items):
        rem_item.position = idx
        session.add(rem_item)
    if rep:
        rep.updated_at = datetime.utcnow()
        session.add(rep)
    session.commit()
    return {"ok": True}

@app.put("/api/repertoires/{repertoire_id}/reorder")
def reorder_repertoire_items(repertoire_id: int, request: RepertoireReorderRequest, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    rep = session.get(Repertoire, repertoire_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire not found")
    if rep.is_private and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    items = session.exec(select(RepertoireItem).where(RepertoireItem.repertoire_id == repertoire_id)).all()
    items_by_id = {i.id: i for i in items}

    for new_pos, item_id in enumerate(request.item_ids):
        item = items_by_id.get(item_id)
        if item:
            item.position = new_pos
            session.add(item)

    rep.updated_at = datetime.utcnow()
    session.add(rep)
    session.commit()
    return {"ok": True}

def get_local_clip_path(file_path: str) -> str:
    """Helper to ensure paths work regardless of the absolute path stored in the DB."""
    if not file_path:
        return ""
    # Always check the local data/clips folder first
    filename = os.path.basename(file_path)
    local_path = os.path.join("data", "clips", filename)
    if os.path.exists(local_path):
        return local_path
    # Fallback to the original path
    return file_path

@app.get("/api/clips/{clip_id}/stream")
def stream_clip(clip_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    local_path = get_local_clip_path(clip.file_path)
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")
    
    return FileResponse(local_path, media_type="audio/mpeg")

@app.get("/api/clips/{clip_id}/download")
def download_clip(clip_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    clip = session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
        
    local_path = get_local_clip_path(clip.file_path)
    if not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Clip file not found on disk")
    
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
        local_path, 
        media_type="audio/mpeg", 
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
