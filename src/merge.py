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

    def to_dict(self) -> dict[str, str | float]:
        return {
            "speaker_name": self.speaker_name,
            "source_audio_file": self.source_audio_file,
            "chunk_audio_file": self.chunk_audio_file,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ChunkTranscript":
        return cls(
            speaker_name=str(payload["speaker_name"]),
            source_audio_file=str(payload["source_audio_file"]),
            chunk_audio_file=str(payload["chunk_audio_file"]),
            start_seconds=float(payload["start_seconds"]),
            end_seconds=float(payload["end_seconds"]),
            text=str(payload["text"]),
        )


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"


def write_json(transcripts: list[ChunkTranscript], output_path: Path) -> None:
    ordered = sorted(transcripts, key=lambda item: (item.start_seconds, item.speaker_name))
    payload = [item.to_dict() for item in ordered]

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
