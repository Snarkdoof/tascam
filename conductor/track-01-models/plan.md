# Plan: Track 01 - Database & Models

## Steps
1. **Update `SourceFile` Model:**
   - Add `backup_status: str = Field(default="pending")`
   - Add `cloud_file_id: Optional[str] = Field(default=None)`
2. **Update `Song` Model:**
   - Add `tags: str = Field(default="[]")` (Store as JSON string for SQLite compatibility, or use SQLAlchemy JSON type).
3. **Update `Clip` Model:**
   - Add `markers: str = Field(default="[]")` (Store as JSON string representing a list of dicts: `[{"start": float, "end": float, "value": str}]`).
4. **Update Read Models:**
   - Ensure `SongRead` and `ClipRead` include the new fields.
5. **Database Migration:**
   - Since we are using SQLite without Alembic currently, provide a script or instructions to migrate existing data or recreate the database if acceptable.
6. **Testing:**
   - Write unit tests to verify the new fields can be written and read correctly.
