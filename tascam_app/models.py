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
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    markers: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    
    clips: List["Clip"] = Relationship(back_populates="song")

class Clip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_file_id: Optional[int] = Field(default=None, foreign_key="sourcefile.id")
    song_id: Optional[int] = Field(default=None, foreign_key="song.id")
    
    file_path: str 
    start_seconds: float
    duration_seconds: float
    
    comment: Optional[str] = Field(default=None)
    tempo: Optional[float] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    source_file: Optional[SourceFile] = Relationship(back_populates="clips")
    song: Optional[Song] = Relationship(back_populates="clips")

# Extract Base models if needed, but for now just Read models that include what we need
class SongRead(SQLModel):
    id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    is_named: bool = False
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
    created_at: datetime
    
    # Include Relationships
    song: Optional[SongRead] = None
    # We could include source_file too if needed
