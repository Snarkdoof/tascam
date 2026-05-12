# Track 01: Database & Models

## Objective
Update the existing SQLModel schemas to support the new feature requirements: Song Markers, Tags, and Cloud Backup status.

## Requirements
1. **Song Markers:**
   - Add a field to store marker data.
   - Markers should be stored as a JSON dictionary with `start`, `end`, and `value` fields.
   - Since markers are specific to a segment of audio, this should likely be added to the `Clip` model.
2. **Tags:**
   - Support adding tags to songs.
   - This could be a simple JSON list of strings on the `Song` model, or a separate `Tag` model with a many-to-many relationship. Given the simplicity, a JSON list on `Song` might suffice, but a separate model is more robust. Let's use a JSON column for simplicity unless complex querying is needed.
3. **Cloud Backup:**
   - Add fields to track the backup status of original audio files.
   - Add `backup_status` (e.g., 'pending', 'uploaded', 'failed') and `backup_url` or `cloud_id` to the `SourceFile` model.

## Architecture
- Modify `tascam_app/models.py`.
- Ensure database migrations or schema updates are handled (SQLite might require dropping/recreating tables or using Alembic if we introduce it, but for now, we can just alter the models and handle the DB update).
