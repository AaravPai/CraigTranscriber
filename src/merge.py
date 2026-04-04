from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChunkTranscript:
    speaker_name: str
    source_audio_file: str
    chunk_audio_file: str
    start_seconds: float
    end_seconds: float
    text: str


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"


def write_json(transcripts: list[ChunkTranscript], output_path: Path) -> None:
    payload = [
        {
            "speaker_name": item.speaker_name,
            "source_audio_file": item.source_audio_file,
            "chunk_audio_file": item.chunk_audio_file,
            "start_seconds": item.start_seconds,
            "end_seconds": item.end_seconds,
            "text": item.text,
        }
        for item in transcripts
    ]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def write_txt(transcripts: list[ChunkTranscript], output_path: Path) -> None:
    ordered = sorted(transcripts, key=lambda x: x.start_seconds)

    with output_path.open("w", encoding="utf-8") as f:
        for item in ordered:
            timestamp = format_timestamp(item.start_seconds)
            f.write(f"[{timestamp}] {item.speaker_name}: {item.text.strip()}\n")


def write_debug_txt(transcripts: list[ChunkTranscript], output_path: Path) -> None:
    ordered = sorted(transcripts, key=lambda x: x.start_seconds)

    with output_path.open("w", encoding="utf-8") as f:
        for item in ordered:
            start_ts = format_timestamp(item.start_seconds)
            end_ts = format_timestamp(item.end_seconds)
            f.write(
                f"[{start_ts} - {end_ts}] {item.speaker_name} "
                f"({item.chunk_audio_file}): {item.text.strip()}\n"
            )