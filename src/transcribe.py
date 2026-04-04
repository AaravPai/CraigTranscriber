from __future__ import annotations

from pathlib import Path
from openai import OpenAI

from config import OPENAI_API_KEY, TRANSCRIPTION_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_file(audio_path: Path) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing from .env")

    with audio_path.open("rb") as f:
        result = client.audio.transcriptions.create(
            model=TRANSCRIPTION_MODEL,
            file=f,
        )

    text = getattr(result, "text", "") or ""
    return text.strip()