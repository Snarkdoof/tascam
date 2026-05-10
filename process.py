#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argparse
import argcomplete
import os
import shutil
import logging
from datetime import datetime, timezone
from sqlmodel import select, Session
from tascam_app.database import create_db_and_tables, engine, get_session
from tascam_app.models import SourceFile, Song, Clip
from tascam_app.audio_processor import AudioProcessor, normalize_wav

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from pydub import AudioSegment

def ingest_files(file_paths: list[str], overwrite: bool = False, pre_roll: int = 3000, preserve_metadata: bool = False):
    # Validate all files exist
    valid_paths = []
    for f in file_paths:
        abs_path = os.path.abspath(f)
        if not os.path.exists(abs_path):
            logger.error(f"File not found: {abs_path}")
            return
        valid_paths.append(abs_path)
    
    if not valid_paths:
        return

    # Use the first file as the primary source identifier
    primary_path = valid_paths[0]

    create_db_and_tables()
    
    with Session(engine) as session:
        old_data = []
        # Check if already processed (based on first file)
        statement = select(SourceFile).where(SourceFile.filename == primary_path)
        existing = session.exec(statement).first()
        if existing:
            if overwrite:
                logger.info(f"File {primary_path} already processed (ID: {existing.id}). Overwriting...")
                clips_stmt = select(Clip).where(Clip.source_file_id == existing.id)
                clips = session.exec(clips_stmt).all()
                for c in clips:
                    if preserve_metadata and c.song:
                        old_data.append({
                            'start_seconds': c.start_seconds,
                            'title': c.song.title,
                            'comment': c.comment
                        })
                    if os.path.exists(c.file_path):
                        os.remove(c.file_path)
                    if c.song_id:
                        song = session.get(Song, c.song_id)
                        if song:
                            session.delete(song)
                    session.delete(c)
                session.delete(existing)
                session.commit()
            else:
                logger.warning(f"File {primary_path} already processed (ID: {existing.id}). Skipping.")
                return
            
        logger.info(f"Processing {len(valid_paths)} files as one recording...")
        source_file = SourceFile(filename=primary_path)
        session.add(source_file)
        session.commit()
        session.refresh(source_file)
        
        # Load and merge audio
        combined_audio = AudioSegment.empty()
        for i, path in enumerate(valid_paths):
            logger.info(f"Loading part {i+1}/{len(valid_paths)}: {path}")
            try:
                # Normalize the file to fix any float32 clipping before loading with pydub
                normalize_wav(path)
                segment = AudioSegment.from_wav(path)
                combined_audio += segment
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                return

        processor = AudioProcessor()
        songs, audio_obj = processor.process_audio(combined_audio)
        
        # Parse date from filename: YYMMDD_xxxx
        basename = os.path.basename(primary_path)
        created_at = datetime.now(timezone.utc)
        try:
            # Check for YYMMDD at start
            # e.g. 260204_0004.wav -> 260204
            parts = basename.split("_")
            if len(parts) > 0 and len(parts[0]) == 6 and parts[0].isdigit():
                date_str = parts[0] # YYMMDD
                # Assuming 20xx
                created_at = datetime.strptime("20" + date_str, "%Y%m%d")
        except ValueError:
            logger.warning(f"Could not parse date from {basename}, using current time.")

        for i, (start, end) in enumerate(songs):
            start_sec = start / 1000.0
            
            # Find closest metadata if preserve_metadata is True
            matched_title = "Processing..."
            matched_comment = None
            if old_data:
                # Find closest by start_seconds
                closest = min(old_data, key=lambda x: abs(x['start_seconds'] - start_sec))
                # If it's within 10 seconds, we consider it a match
                if abs(closest['start_seconds'] - start_sec) < 10.0:
                    matched_title = closest['title']
                    matched_comment = closest['comment']
                    old_data.remove(closest) # Prevent applying to multiple clips
            
            # Create a new Song for each clip initially (grouping later)
            song = Song(title=matched_title, created_at=created_at)
            session.add(song)
            session.commit()
            
            # Update title with real ID if it was just "Processing..."
            if song.title == "Processing...":
                song.title = f"Song {song.id}"
                session.add(song)
                session.commit()
            
            clip_filename = f"clip_{source_file.id}_{i}.mp3"
            clip_path = os.path.join("data/clips", clip_filename)
            abs_clip_path = os.path.abspath(clip_path)
            
            duration = processor.export_clip(audio_obj, start, end, abs_clip_path, pre_roll=pre_roll)
            
            features = processor.get_features(abs_clip_path)
            
            clip = Clip(
                source_file_id=source_file.id,
                song_id=song.id,
                file_path=abs_clip_path,
                start_seconds=start_sec,
                duration_seconds=duration,
                comment=matched_comment,
                tempo=features.get("tempo"),
                created_at=created_at
            )
            session.add(clip)
            session.commit()
            logger.info(f"Saved clip {i}: {clip_filename} ({duration:.2f}s, {features.get('tempo'):.1f} BPM)")
            
    logger.info("Ingest complete.")

def cleanup_orphans(dry_run: bool = True):
    from tascam_app.models import Clip
    
    data_dir = os.path.abspath("data/clips")
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory {data_dir} does not exist.")
        return

    # Get all files on disk
    disk_files = set()
    for f in os.listdir(data_dir):
        if f.endswith(".mp3"): # filter?
            disk_files.add(os.path.join(data_dir, f))
            
    # Get all files in DB
    with Session(engine) as session:
        db_clips = session.exec(select(Clip)).all()
        db_files = set(c.file_path for c in db_clips)
        
    # Find orphans
    orphans = disk_files - db_files
    
    if not orphans:
        logger.info("No orphaned files found.")
        return
        
    logger.info(f"Found {len(orphans)} orphaned files.")
    
    for orphan in orphans:
        if dry_run:
            logger.info(f"[DRY RUN] Would delete: {orphan}")
        else:
            try:
                os.remove(orphan)
                logger.info(f"Deleted: {orphan}")
            except OSError as e:
                logger.error(f"Failed to delete {orphan}: {e}")
                
    if dry_run:
        logger.info("Dry run complete. Run without --dry-run (or use --yes) to actually delete.")
    else:
        logger.info("Cleanup complete.")

def export_clips():
    from tascam_app.models import Clip
    
    export_base = os.path.abspath("exports")
    if not os.path.exists(export_base):
        os.makedirs(export_base)
        
    with Session(engine) as session:
        clips = session.exec(select(Clip)).all()
        count = 0
        
        for clip in clips:
            if not clip.file_path or not os.path.exists(clip.file_path):
                logger.warning(f"File missing for Clip {clip.id}: {clip.file_path}")
                continue
                
            # Date folder: YYYY-MM-DD
            date_str = clip.created_at.strftime("%Y-%m-%d")
            date_dir = os.path.join(export_base, date_str)
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
                
            # Filename: {id}.mp3 or {id}_{song_name}.mp3
            dest_filename = f"{clip.id}.mp3"
            if clip.song and clip.song.title and not clip.song.title.startswith("Song"):
                safe_title = "".join(c for c in clip.song.title if c.isalnum() or c in " _-").strip()
                safe_title = safe_title.replace(" ", "_")
                if safe_title:
                    dest_filename = f"{clip.id}_{safe_title}.mp3"
                    
            dest_path = os.path.join(date_dir, dest_filename)
            
            try:
                shutil.copy2(clip.file_path, dest_path)
                count += 1
            except OSError as e:
                logger.error(f"Failed to export Clip {clip.id}: {e}")
                
        logger.info(f"Exported {count} clips to {export_base}")


def import_directory(source_dir: str, overwrite: bool = False, pre_roll: int = 3000):
    valid_paths = []
    # Recursively find .wav files
    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith(".wav"):
                valid_paths.append(os.path.join(root, f))
    
    if not valid_paths:
        logger.info(f"No .wav files found in {source_dir}")
        return
    
    # Group by date prefix: YYMMDD_xxxx.wav
    groups = {}
    for path in valid_paths:
        basename = os.path.basename(path)
        parts = basename.split("_")
        if len(parts) > 0 and len(parts[0]) >= 6 and parts[0][:6].isdigit():
            date_prefix = parts[0][:6]
        else:
            date_prefix = "unknown"
        
        groups.setdefault(date_prefix, []).append(path)
    
    dest_dir = os.path.abspath("data/original")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    for date_prefix, files in groups.items():
        files.sort()
        logger.info(f"Processing group {date_prefix} with {len(files)} files.")
        
        copied_paths = []
        for file_path in files:
            dest_path = os.path.join(dest_dir, os.path.basename(file_path))
            try:
                shutil.copy2(file_path, dest_path)
                copied_paths.append(dest_path)
                logger.info(f"Copied {file_path} to {dest_path}")
            except OSError as e:
                logger.error(f"Failed to copy {file_path}: {e}")
        
        if copied_paths:
            logger.info(f"Ingesting {len(copied_paths)} copied files for date {date_prefix}...")
            # ingest_files handles saving to database and clips
            ingest_files(copied_paths, overwrite=overwrite, pre_roll=pre_roll)
            
            # Since ingest_files skips processing if primary file is already in DB,
            # we consider it "safe" to delete originals either way.
            # However, if ingestion crashed, python would have stopped, so we wouldn't reach here.
            # Assuming ingestion was successful:
            for file_path in files:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted original file from SD card: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to delete {file_path}: {e}")


def reprocess_all(pre_roll: int = 3000):
    with Session(engine) as session:
        source_files = session.exec(select(SourceFile)).all()
        if not source_files:
            logger.info("No files to reprocess.")
            return

        # For each source file, find the matching original files based on the date prefix
        for sf in source_files:
            basename = os.path.basename(sf.filename)
            parts = basename.split("_")
            if len(parts) > 0 and len(parts[0]) >= 6 and parts[0][:6].isdigit():
                date_prefix = parts[0][:6]
            else:
                logger.warning(f"Could not determine date prefix for {sf.filename}, skipping.")
                continue

            dir_path = os.path.dirname(sf.filename)
            valid_paths = []
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    if f.startswith(date_prefix) and f.lower().endswith(".wav"):
                        valid_paths.append(os.path.join(dir_path, f))
            
            if valid_paths:
                valid_paths.sort()
                logger.info(f"Reprocessing {len(valid_paths)} files for prefix {date_prefix}...")
                ingest_files(valid_paths, overwrite=True, pre_roll=pre_roll, preserve_metadata=True)
            else:
                logger.warning(f"No WAV files found for prefix {date_prefix} in {dir_path}")

def main():
    parser = argparse.ArgumentParser(description="Tascam Recording Processor")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ingest Dir
    parser_import_dir = subparsers.add_parser("import-dir", help="Import all WAV files from directory")
    parser_import_dir.add_argument("dir", nargs="?", default="/run/media/njaal/DR-05XP/MUSIC", help="Source directory")
    parser_import_dir.add_argument("--overwrite", action="store_true", help="Overwrite existing files in database")
    parser_import_dir.add_argument("--no-pre-roll", action="store_true", help="Disable the 3-second pre-roll on clips")
    
    # Ingest
    parser_ingest = subparsers.add_parser("ingest", help="Ingest WAV file(s)")
    parser_ingest.add_argument("files", nargs='+', help="Path to WAV file(s)")
    parser_ingest.add_argument("--overwrite", action="store_true", help="Overwrite existing files in database")
    parser_ingest.add_argument("--no-pre-roll", action="store_true", help="Disable the 3-second pre-roll on clips")

    # Reprocess
    parser_reprocess = subparsers.add_parser("reprocess", help="Reprocess all existing source files and apply float32 normalization, keeping metadata")
    parser_reprocess.add_argument("--no-pre-roll", action="store_true", help="Disable the 3-second pre-roll on clips")

    # Cleanup
    parser_cleanup = subparsers.add_parser("cleanup", help="Remove orphaned clip files")
    parser_cleanup.add_argument("--yes", action="store_true", help="Actually delete files (default is dry-run)")
    parser_cleanup.add_argument("--dry-run", action="store_true", help="Force dry-run (default)")

    # Export
    parser_export = subparsers.add_parser("export", help="Export clips to exports/YYYY-MM-DD/{id}.mp3")
    
    # Identify (Placeholder)
    parser_identify = subparsers.add_parser("identify", help="Identify songs (TODO)")
    
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    if args.command == "import-dir":
        import_directory(args.dir, overwrite=args.overwrite, pre_roll=0 if args.no_pre_roll else 3000)
    elif args.command == "ingest":
        ingest_files(args.files, overwrite=args.overwrite, pre_roll=0 if args.no_pre_roll else 3000)
    elif args.command == "reprocess":
        reprocess_all(pre_roll=0 if args.no_pre_roll else 3000)
    elif args.command == "cleanup":
        # dry_run is True unless --yes is specified (and --dry-run is NOT specified)
        dry_run = not args.yes or args.dry_run
        cleanup_orphans(dry_run=dry_run)
    elif args.command == "export":
        export_clips()
    elif args.command == "identify":
        print("Identification not implemented yet.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
