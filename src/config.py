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


def _positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, received {raw_value!r}") from exc

    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _nonnegative_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, received {raw_value!r}") from exc

    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


MAX_CONCURRENT_TRANSCRIPTIONS = _positive_int_env("MAX_CONCURRENT_TRANSCRIPTIONS", 4)
MAX_TRANSCRIPTION_ATTEMPTS = _positive_int_env("MAX_TRANSCRIPTION_ATTEMPTS", 4)
RETRY_BASE_DELAY_SECONDS = _nonnegative_float_env("RETRY_BASE_DELAY_SECONDS", 1.0)

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
