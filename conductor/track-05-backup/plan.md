# Plan: Track 05 - Cloud Backup

## Steps
1. **Dependencies:**
   - Add necessary Google API libraries to `pyproject.toml` or `requirements.txt`.
2. **Authentication Setup:**
   - Create a mechanism to load Google credentials (e.g., `credentials.json`).
3. **Upload Logic:**
   - Implement a function in `tascam_app/backup.py` to upload a file to Google Drive/GCS using resumable uploads.
4. **Integration with Processing:**
   - Modify `process.py` or the relevant ingestion script to trigger the backup function after successful extraction.
5. **API Integration:**
   - Ensure the `POST /api/source-files/{id}/backup` endpoint calls the upload logic.
6. **Testing:**
   - Mock the Google API to test the upload flow and status updates without actually uploading large files during unit tests.
