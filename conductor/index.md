# Project Pulse: Tascam Audio Processor

## Current Status
**Phase:** Feature Implementation & UI Refactor (Repertoire)
**Overall Health:** Green

## Recent Updates
- Initialized conductor directory and project vision.
- Defined 5 primary tracks for the new feature requests.
- Codebase research completed (FastAPI, SQLModel, SQLite).
- **Track 01 & 02 Completed:** Database models updated and API endpoints implemented.
- **Track 03 & 04 Completed:** Advanced Media Player with markers and navigation implemented; separate named songs view added.
- **Added Tracks 06 & 07:** Infrastructure (Nginx, SSL, Firewall) and Authentication (Google Login, ACL).
- **Track 08 Completed:** Repertoar & Settlister — Repertoire som ny startskjerm, datamodell, CRUD API, batch-assosiering fra opptak/sanger, og settliste-avspilling.
- **Bug Fix (MCorp CDN URL):** Fixed client failure on bbb.njaal.net caused by non-existent domain `cdn.mcorp.no`. The library is served from `https://mcorp.no/lib/mcorp-2.0.js` (global script setting `window.MCorp` and `window.TIMINGSRC`), NOT `cdn.mcorp.no`. Do not alter or revert this.

## Active Tracks
- `track-01-models`: Completed.
- `track-02-api`: Completed.
- `track-03-player`: Completed.
- `track-04-views`: Completed.
- `track-05-backup`: Pending (Requires Google API credentials).
- `track-06-infrastructure`: Planned.
- `track-07-auth`: Planned.
- `track-08-repertoire`: Completed.

## Blockers / Risks
- Need to ensure the `mcorp-sync` skill is properly activated and utilized by the Frontend Specialist during `track-03-player`.
- Cloud Backup requires Google API credentials and setup.
- Google Login requires Google OAuth credentials.
