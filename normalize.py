#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import subprocess
from pydantic import BaseModel, Field

try:
    import argcomplete
except ImportError:
    argcomplete = None

class Config(BaseModel):
    files: list[str] = Field(..., min_length=2, max_length=2)
    start: str
    duration: str
    output: str

def run_normalization(cfg: Config):
    # Added async=1 to perfectly lock the timestamps and prevent stretching
    filt = (
        "[0:a]aresample=48000:async=1[a0];"
        "[1:a]aresample=48000:async=1[a1];"
        "[a0][a1]concat=n=2:v=0:a=1[c];"
        "[c]loudnorm=I=-16:TP=-1.5:LRA=18[out]"
    )
    cmd = [
        "ffmpeg", "-i", cfg.files[0], "-i", cfg.files[1],
        "-filter_complex", filt, "-map", "[out]",
        "-ss", cfg.start, "-t", cfg.duration,
        # Switched to CBR 320kbps to prevent VBR playback anomalies
        "-acodec", "libmp3lame", "-b:a", "320k", cfg.output
    ]
    print(f"Running timestamp-locked normalization and encoding to {cfg.output}...")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Normalize live audio (Timestamp Locked).")
    parser.add_argument("files", nargs=2, help="Two WAV files to concatenate")
    parser.add_argument("-s", "--start", default="00:30:30", help="Start time")
    parser.add_argument("-t", "--duration", default="01:07:00", help="Duration")
    parser.add_argument("-o", "--output", required=True, help="Output MP3 file")
    
    if argcomplete:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    cfg = Config(files=args.files, start=args.start, duration=args.duration, output=args.output)
    run_normalization(cfg)
    print("Done!")

if __name__ == "__main__":
    main()
