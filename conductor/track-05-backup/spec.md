# Track 05: Cloud Backup

## Objective
Implement automated backup of large original audio files to Google Cloud/Drive.

## Requirements
1. **Google API Integration:**
   - Authenticate with Google Drive or Google Cloud Storage API.
   - Handle large file uploads (resumable uploads).
2. **Trigger Mechanism:**
   - Allow triggering the backup manually via the UI or automatically after audio extraction.
3. **Status Tracking:**
   - Update the `SourceFile` model with the backup status and cloud file ID.
   - Provide feedback to the user on the backup progress or status.

## Architecture
- Add a new module `tascam_app/backup.py` for cloud interaction logic.
- Use `google-api-python-client` or `google-cloud-storage`.
- Ensure credentials are read securely from environment variables or a local config file.
