# Tascam Audio Processor API & Utility Documentation (SKILLS)

This document provides reference information for using the Tascam Audio Processor APIs, command-line interfaces (CLIs), and deployment tools.

## Command-Line Interfaces (CLIs)

### 1. Ingestion and Processing (`process.py`)
Used to ingest, split, reprocess, and clean up audio files.
* **Usage**: `uv run python process.py <command> [options]`
* **Commands**:
  * `import-dir [<dir>] [--overwrite] [--no-pre-roll]`: Recursively search for `.wav` files in `<dir>` (defaults to `/run/media/njaal/DR-05XP/MUSIC`), group by date prefixes, copy them to `data/original`, split them into clips, insert metadata into the database, and delete the original files.
  * `ingest <files...> [--overwrite] [--no-pre-roll]`: Ingest specific `.wav` files.
  * `reprocess [--no-pre-roll]`: Reprocess all existing source files to re-apply normalization and keep metadata.
  * `cleanup [--yes] [--dry-run]`: Remove orphaned MP3 clip files from `data/clips` that are not tracked in the database.
  * `export`: Copy clips to `exports/YYYY-MM-DD/{id}_{title}.mp3` for distribution.

### 2. Live Audio Normalization (`normalize.py`)
Performs timestamp-locked normalization and MP3 encoding.
* **Usage**: `uv run python normalize.py <file1> <file2> -o <output_file> [options]`
* **Arguments**:
  * `files`: Two WAV files to concatenate.
  * `-s, --start`: Start time (default: `00:30:30`).
  * `-t, --duration`: Duration (default: `01:07:00`).
  * `-o, --output`: Output path for the generated MP3.

### 3. Concert Splitting (`split_concert.py`)
Splits a long concert recording based on target track count and silences.
* **Usage**: `uv run python split_concert.py <file> -t <expected_tracks> [options]`
* **Arguments**:
  * `file`: Input audio file path.
  * `-t, --tracks`: Expected number of tracks to produce.
  * `-n, --noise`: Noise threshold in dB (default: `-40`).
  * `-d, --duration`: Minimum silence duration in seconds (default: `2.0`).
  * `--min`: Minimum track length in seconds (default: `120.0`).
  * `-o, --outdir`: Output directory.

---

## Deployment & Infrastructure

The application runs behind an Nginx reverse proxy with SSL enabled and is deployed to a remote server.

### Host and Domains
* **Server IP**: `134.98.147.52`
* **Production Domain**: `https://bbb.njaal.net`
* **Alternate Domain**: `https://music.njaal.net` (redirects to `bbb.njaal.net`)

### Deployment Commands (`Makefile`)
* Run application locally:
  ```bash
  make run
  ```
* Deploy application code to remote server:
  ```bash
  make deploy
  ```
* Import remote PG database (establishes an SSH tunnel and runs ingestion):
  ```bash
  make import DIR=<path_to_directory>
  ```
* Set up remote PostgreSQL database and run migrations:
  ```bash
  make remote-db-setup
  ```
* Setup system packages and Python environment on remote server:
  ```bash
  make remote-install
  ```
* Configure Nginx proxy, SSL certificates via Certbot, and Firewall on remote:
  ```bash
  make remote-infra
  ```
* Start the application on the remote server in the background:
  ```bash
  make remote-run
  ```
