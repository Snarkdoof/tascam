#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse, subprocess, sys
from pathlib import Path
from pydantic import BaseModel, Field

try:
    import argcomplete
except ImportError:
    argcomplete = None

class Silence(BaseModel):
    start: float = Field(..., ge=0)
    end: float = Field(..., ge=0)
    duration: float = Field(..., gt=0)

class Track(BaseModel):
    num: int
    start: float
    end: float
    duration: float
    merged_clips: int

def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def get_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def find_silences(file_path: str, noise_db: int, dur: float) -> list[Silence]:
    cmd = ["ffmpeg", "-i", file_path, "-af", f"silencedetect=noise={noise_db}dB:d={dur}", "-f", "null", "-"]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
    silences = []
    for line in res.stderr.splitlines():
        if "silence_start" in line:
            start = float(line.split("silence_start:")[1].strip())
        elif "silence_end" in line:
            parts = line.split("|")
            silences.append(Silence(
                start=start, end=float(parts[0].split("silence_end:")[1].strip()),
                duration=float(parts[1].split("silence_duration:")[1].strip())
            ))
    return silences

def auto_detect(file_path: str, expected: int, start_db: int, dur: float, min_s: float) -> list[Track]:
    current_db, total_dur = start_db, get_duration(file_path)
    best_tracks, best_diff = [], float('inf')
    
    for attempt in range(10):
        print(f"Attempt {attempt+1}: Threshold {current_db}dB...")
        splits = [max(0.0, s.end - 0.2) for s in find_silences(file_path, current_db, dur)]
        valid, merges = [0.0] + splits + [total_dur], [0] * (len(splits) + 1)
        
        while True:
            merged = False
            for i in range(len(valid) - 1):
                if valid[i+1] - valid[i] < min_s:
                    idx_to_merge = i if i > 0 else 1
                    valid.pop(idx_to_merge)
                    merges[i-1 if i > 0 else 0] += 1 + merges.pop(idx_to_merge)
                    merged = True
                    break
            if not merged: break
            
        tracks = [Track(num=i+1, start=valid[i], end=valid[i+1], duration=valid[i+1]-valid[i], merged_clips=merges[i])
                  for i in range(len(valid)-1)]
        
        diff = abs(len(tracks) - expected)
        if diff < best_diff:
            best_diff, best_tracks = diff, tracks
            
        if len(tracks) == expected:
            print(f"Success! Found {expected} songs.\n")
            return tracks
        elif len(tracks) > expected:
            current_db -= 2
        else:
            current_db += 2
            
    print(f"Max attempts reached. Best match gave {len(best_tracks)} tracks.\n")
    return best_tracks

def split_file(file_path: str, tracks: list[Track], out_dir: str):
    path, out = Path(file_path), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    for t in tracks:
        out_file = out / f"{path.stem}_track_{t.num:02d}{path.suffix}"
        cmd = ["ffmpeg", "-y", "-i", file_path, "-ss", str(t.start), "-to", str(t.end), "-c", "copy", str(out_file)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Created: {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Target-based silence splitter with review step.")
    parser.add_argument("file", help="Input audio file")
    parser.add_argument("-t", "--tracks", type=int, required=True, help="Expected number of tracks")
    parser.add_argument("-n", "--noise", type=int, default=-40, help="Starting dB threshold")
    parser.add_argument("-d", "--duration", type=float, default=2.0, help="Min silence duration")
    parser.add_argument("--min", type=float, default=120.0, help="Min track length in seconds")
    parser.add_argument("-o", "--outdir", default=".", help="Output directory")
    
    if argcomplete: argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    tracks = auto_detect(args.file, args.tracks, args.noise, args.duration, args.min)
    
    print(f"{'Trk':<4} | {'Start':<8} | {'End':<8} | {'Duration':<8} | {'Merged Intros/Applause'}")
    print("-" * 60)
    for t in tracks:
        merges = f"{t.merged_clips} short clip(s) appended" if t.merged_clips else "-"
        print(f"{t.num:<4} | {format_time(t.start):<8} | {format_time(t.end):<8} | {format_time(t.duration):<8} | {merges}")
        
    print("-" * 60)
    if input("\nDo you want to proceed with splitting? [y/N]: ").strip().lower() not in ['y', 'yes']:
        sys.exit("Aborted by user.")
        
    split_file(args.file, tracks, args.outdir)

if __name__ == "__main__":
    main()
