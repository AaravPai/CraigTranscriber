from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_ZIPS_DIR = BASE_DIR / "input_zips"
EXTRACTED_DIR = BASE_DIR / "extracted"
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMP_CHUNKS_DIR = BASE_DIR / "temp_chunks"

INPUT_ZIPS_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-transcribe").strip()

SUPPORTED_AUDIO_EXTENSIONS = {
    ".flac",
    ".wav",
    ".ogg",
    ".mp3",
    ".aac",
    ".m4a",
    ".mp4",
    ".webm",
    ".opus",
}

MIN_SILENCE_LEN_MS = 1200
SILENCE_THRESH_OFFSET_DB = 16
KEEP_SILENCE_MS = 250
MAX_CHUNK_MS = 30000
MIN_CHUNK_MS = 800