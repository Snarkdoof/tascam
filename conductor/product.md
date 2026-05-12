# Tascam Audio Processor - Product Vision

## Core Mandate
The Tascam Audio Processor is a tool for managing, splitting, and playing back audio recordings (e.g., from a Tascam recorder). It provides an intuitive web interface for musicians and audio engineers to organize their recordings, mark important sections, and back up their original files.

## Key Features
1. **Audio Ingestion & Splitting:** Automatically process and split large audio recordings into individual songs/clips.
2. **Advanced Playback:** A sophisticated media player supporting synchronized playback, looping, and precise navigation using `mcorp-sync` and `timingsrc`.
3. **Song Markers:** Ability to annotate specific sections of audio (e.g., "A", "B", bar numbers) with precise timing, stored as metadata.
4. **Organization & Filtering:** A dedicated view for named songs, supporting tags and chronological sorting.
5. **Cloud Backup:** Automated backup of large original audio files to Google Cloud/Drive after processing.

## Engineering Standards
- **Architecture:** FastAPI backend with SQLModel (SQLite), serving a web frontend.
- **Quality:** All features must be empirically verified. Bug fixes require reproduction test cases.
- **Documentation:** Maintain up-to-date documentation in the `conductor/` directory.
- **Skills:** Utilize available skills (e.g., `mcorp-sync`) for specialized implementations.
