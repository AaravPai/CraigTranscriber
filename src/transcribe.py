from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

from config import (
    MAX_TRANSCRIPTION_ATTEMPTS,
    OPENAI_API_KEY,
    RETRY_BASE_DELAY_SECONDS,
    TRANSCRIPTION_MODEL,
)

_client: Any | None = None


def _get_client() -> Any:
    global _client

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing from .env")

    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


def _is_retryable(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        return True
    return status_code in {408, 409, 429} or status_code >= 500


async def transcribe_file(
    audio_path: Path,
    *,
    client: Any | None = None,
    max_attempts: int = MAX_TRANSCRIPTION_ATTEMPTS,
    base_delay_seconds: float = RETRY_BASE_DELAY_SECONDS,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> str:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    transcription_client = client or _get_client()

    for attempt in range(1, max_attempts + 1):
        try:
            with audio_path.open("rb") as audio_file:
                result = await transcription_client.audio.transcriptions.create(
                    model=TRANSCRIPTION_MODEL,
                    file=audio_file,
                )

            text = getattr(result, "text", "") or ""
            return text.strip()
        except Exception as exc:
            if attempt == max_attempts or not _is_retryable(exc):
                raise

            delay = base_delay_seconds * (2 ** (attempt - 1))
            print(
                f"  Transcription attempt {attempt}/{max_attempts} failed for "
                f"{audio_path.name}; retrying in {delay:.1f}s"
            )
            await sleep(delay)
