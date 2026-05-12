# Track 02: Backend API

## Objective
Implement the necessary FastAPI endpoints to support the new frontend features and cloud backup triggers.

## Requirements
1. **Markers API:**
   - Endpoint to add/update/delete markers for a specific clip.
   - Could be part of the existing `PATCH /api/clips/{clip_id}` or a dedicated endpoint.
2. **Tags API:**
   - Endpoint to update tags for a song.
   - `PATCH /api/songs/{song_id}`.
3. **Filtered Songs API:**
   - Endpoint to get "named" songs (where title != "Unknown Song" and doesn't start with "Song ").
   - Support filtering by tags.
   - Support sorting by date.
4. **Cloud Backup API:**
   - Endpoint to trigger backup for a specific `SourceFile`.
   - Endpoint to check backup status.

## Architecture
- Modify `tascam_app/web.py`.
- Add new Pydantic models for request validation.
