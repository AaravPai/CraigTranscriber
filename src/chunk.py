from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
FFMPEG_DIR = str(Path(FFMPEG_EXE).parent)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from config import (
    KEEP_SILENCE_MS,
    MAX_CHUNK_MS,
    MIN_CHUNK_MS,
    MIN_SILENCE_LEN_MS,
    SILENCE_THRESH_OFFSET_DB,
)

AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffmpeg = FFMPEG_EXE


@dataclass
class AudioChunk:
    speaker_name: str
    source_audio_path: Path
    start_ms: int
    end_ms: int
    audio: AudioSegment

    @property
    def start_seconds(self) -> float:
        return self.start_ms / 1000.0

    @property
    def end_seconds(self) -> float:
        return self.end_ms / 1000.0


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _split_long_region(start_ms: int, end_ms: int, max_chunk_ms: int) -> list[tuple[int, int]]:
    length = end_ms - start_ms
    if length <= max_chunk_ms:
        return [(start_ms, end_ms)]

    pieces = []
    chunk_count = math.ceil(length / max_chunk_ms)
    piece_size = math.ceil(length / chunk_count)

    cur = start_ms
    while cur < end_ms:
        nxt = min(cur + piece_size, end_ms)
        pieces.append((cur, nxt))
        cur = nxt

    return pieces


def make_chunks_for_track(speaker_name: str, audio_path: Path) -> list[AudioChunk]:
    full_audio = AudioSegment.from_file(audio_path)
    if len(full_audio) == 0:
        return []

    silence_thresh = full_audio.dBFS - SILENCE_THRESH_OFFSET_DB
    nonsilent_regions = detect_nonsilent(
        full_audio,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=silence_thresh,
    )

    chunks: list[AudioChunk] = []

    for raw_start, raw_end in nonsilent_regions:
        start_ms = _clamp(raw_start - KEEP_SILENCE_MS, 0, len(full_audio))
        end_ms = _clamp(raw_end + KEEP_SILENCE_MS, 0, len(full_audio))

        if end_ms - start_ms < MIN_CHUNK_MS:
            continue

        for piece_start, piece_end in _split_long_region(start_ms, end_ms, MAX_CHUNK_MS):
            if piece_end - piece_start < MIN_CHUNK_MS:
                continue

            piece_audio = full_audio[piece_start:piece_end]
            chunks.append(
                AudioChunk(
                    speaker_name=speaker_name,
                    source_audio_path=audio_path,
                    start_ms=piece_start,
                    end_ms=piece_end,
                    audio=piece_audio,
                )
            )

    return chunks