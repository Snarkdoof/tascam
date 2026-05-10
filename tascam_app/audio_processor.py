import os
import logging
import scipy.io.wavfile as wavfile
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import librosa
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_wav(file_path: str):
    """
    Reads a WAV file, checks for float32 clipping (max amplitude > 1.0),
    and normalizes it to 0.99 to prevent clipping before pydub processing.
    Overwrites the original file if normalized.
    """
    try:
        fs, data = wavfile.read(file_path)
        # scipy.io.wavfile can return different dtypes based on the wav file format.
        # Float32 WAV files might have values > 1.0 or < -1.0 which indicates clipping.
        # Since we only want to normalize float arrays that exceed 1.0:
        if np.issubdtype(data.dtype, np.floating):
            max_amp = np.max(np.abs(data))
            if max_amp > 1.0:
                logger.info(f"File {file_path} is clipping. Max amplitude: {max_amp:.4f}. Normalizing...")
                normalized_data = (data / max_amp) * 0.99
                # Overwrite the original file with the normalized data
                wavfile.write(file_path, fs, normalized_data.astype(np.float32))
                logger.info(f"Normalized file saved to: {file_path}")
            else:
                logger.debug(f"File {file_path} is not clipping (max amp: {max_amp:.4f}).")
    except Exception as e:
        logger.error(f"Failed to normalize {file_path}: {e}")

class AudioProcessor:
    def __init__(self, silence_thresh=-35, min_silence_len=5000, keep_silence=500):
        """
        :param silence_thresh: dBFS threshold for silence (default -40)
        :param min_silence_len: minimum length of silence to be considered a split (ms)
        :param keep_silence: amount of silence to keep at start/end of clip (ms)
        """
        self.silence_thresh = silence_thresh
        self.min_silence_len = min_silence_len
        self.keep_silence = keep_silence
    
    def find_songs(self, file_path: str):
        """
        Scans a large audio file and identifies song segments.
        Wrapper around process_audio for single file.
        """
        logger.info(f"Loading {file_path}... this might take a moment.")
        try:
            audio = AudioSegment.from_wav(file_path)
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
            
        return self.process_audio(audio)

    def process_audio(self, audio: AudioSegment):
        """
        Scans an AudioSegment and identifies song segments.
        Returns a list of (start_ms, end_ms) tuples and the audio object.
        """
        logger.info(f"Audio loaded. Duration: {len(audio)/1000:.2f}s. Detecting songs...")
        
        # detect_nonsilent is better than split_on_silence as we want the ranges first
        nonsilence_ranges = detect_nonsilent(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=100
        )
        
        # Merge ranges that are close together (if detect_nonsilence didn't already)
        # detect_nonsilence does merge if silence < min_silence_len.
        
        # Filter out very short "songs" (e.g. just a cough or chair scrape that was loud)
        min_song_len = 30000 # 30 seconds
        songs = [
            (start, end) for start, end in nonsilence_ranges 
            if (end - start) > min_song_len
        ]
        
        logger.info(f"Found {len(songs)} potential songs.")
        return songs, audio

    def export_clip(self, audio: AudioSegment, start, end, output_path, pre_roll=3000):
        """
        Exports a segment to MP3.
        """
        # Add padding (3 seconds pre-amble before the estimated start)
        start = max(0, start - pre_roll)
        end = min(len(audio), end + self.keep_silence)
        
        clip = audio[start:end]
        
        logger.info(f"Exporting clip to {output_path}")
        clip.export(output_path, format="mp3", bitrate="192k")
        return (end - start) / 1000.0

    def extract_pre_roll(self, audio: AudioSegment, song_start, duration_sec=45):
        """
        Extracts audio BEFORE the song starts to catch announcements.
        """
        start = max(0, song_start - (duration_sec * 1000))
        end = song_start
        if start >= end:
            return None
        return audio[start:end]

    def get_features(self, clip_path):
        """
        Extract simple features for grouping.
        """
        try:
            # Load start of clip for speed
            y, sr = librosa.load(clip_path, duration=30) 
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            # tempo is usually a scalar, but can be an array in newer librosa?
            # beat_track returns: (tempo, beats)
            if np.ndim(tempo) > 0:
                tempo = tempo[0]
            
            return {
                "tempo": float(tempo)
            }
        except Exception as e:
            logger.error(f"Error extracting features for {clip_path}: {e}")
            return {"tempo": 0.0}
