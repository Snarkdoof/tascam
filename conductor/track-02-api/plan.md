# Plan: Track 02 - Backend API

## Steps
1. **Update Clip Update Endpoint:**
   - Modify `PATCH /api/clips/{clip_id}` to accept `markers` data.
   - Validate JSON structure of markers.
2. **Create Song Update Endpoint:**
   - Implement `PATCH /api/songs/{song_id}` to allow updating `title`, `artist`, and `tags`.
3. **Create Filtered Songs Endpoint:**
   - Implement `GET /api/songs/named`.
   - Add query parameters for `tag` and `sort_by`.
   - Filter out default names in the SQL query.
4. **Create Backup Endpoints:**
   - Implement `POST /api/source-files/{id}/backup` to trigger the backup process (can be synchronous for now, or kick off a background task).
   - Implement `GET /api/source-files` to list files and their backup status.
5. **Testing:**
   - Write unit tests for all new endpoints using `TestClient`.
