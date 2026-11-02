from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class SourceFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True, unique=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # New fields for Cloud Backup
    backup_url: Optional[str] = Field(default=None)
    backup_status: Optional[str] = Field(default=None)
    
    clips: List["Clip"] = Relationship(back_populates="source_file")

class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default="Unknown Song")
    artist: Optional[str] = Field(default="Unknown Artist")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # New fields for Song Identification, Tags, and Markers
    is_named: bool = Field(default=False)
    is_private: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    markers: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    clips: List["Clip"] = Relationship(back_populates="song")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    picture: Optional[str] = None
    is_approved: bool = Field(default=False)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_file_id: Optional[int] = Field(default=None, foreign_key="sourcefile.id")
    song_id: Optional[int] = Field(default=None, foreign_key="song.id")
    
    file_path: str 
    start_seconds: float
    duration_seconds: float
    
    comment: Optional[str] = Field(default=None)
    tempo: Optional[float] = Field(default=None)
    is_private: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    source_file: Optional[SourceFile] = Relationship(back_populates="clips")
    song: Optional[Song] = Relationship(back_populates="clips")

class Repertoire(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    is_private: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    items: List["RepertoireItem"] = Relationship(
        back_populates="repertoire",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class RepertoireItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repertoire_id: int = Field(foreign_key="repertoire.id", index=True)
    clip_id: Optional[int] = Field(default=None, foreign_key="clip.id")
    song_id: Optional[int] = Field(default=None, foreign_key="song.id")
    position: int = Field(default=0, index=True)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    repertoire: Optional[Repertoire] = Relationship(back_populates="items")
    clip: Optional[Clip] = Relationship()
    song: Optional[Song] = Relationship()

# Extract Base models if needed, but for now just Read models that include what we need
class SongRead(SQLModel):
    id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    is_named: bool = False
    is_private: bool = False
    tags: List[str] = []
    markers: List[Dict[str, Any]] = []
    created_at: datetime

class ClipRead(SQLModel):
    id: int
    source_file_id: Optional[int]
    song_id: Optional[int]
    file_path: str 
    start_seconds: float
    duration_seconds: float
    comment: Optional[str] = None
    tempo: Optional[float] = None
    is_private: bool = False
    created_at: datetime
    
    # Include Relationships
    song: Optional[SongRead] = None
    # We could include source_file too if needed

class RepertoireItemRead(SQLModel):
    id: int
    repertoire_id: int
    clip_id: Optional[int] = None
    song_id: Optional[int] = None
    position: int
    notes: Optional[str] = None
    created_at: datetime
    clip: Optional[ClipRead] = None
    song: Optional[SongRead] = None

class RepertoireRead(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool = False
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    total_duration_seconds: float = 0.0

class RepertoireDetailRead(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool = False
    created_at: datetime
    updated_at: datetime
    item_count: int = 0
    total_duration_seconds: float = 0.0
    items: List[RepertoireItemRead] = []

class RepertoireCreate(SQLModel):
    name: str
    description: Optional[str] = None
    is_private: Optional[bool] = False

class RepertoireUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None

class RepertoireItemCreate(SQLModel):
    clip_id: Optional[int] = None
    song_id: Optional[int] = None
    position: Optional[int] = None
    notes: Optional[str] = None

class RepertoireItemUpdate(SQLModel):
    notes: Optional[str] = None
    position: Optional[int] = None

class RepertoireBatchAddRequest(SQLModel):
    clip_ids: List[int]

class RepertoireReorderRequest(SQLModel):
    item_ids: List[int]
