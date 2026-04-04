from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import SUPPORTED_AUDIO_EXTENSIONS


@dataclass
class SpeakerTrack:
    speaker_name: str
    audio_path: Path


def clean_speaker_name(path: Path) -> str:
    return path.stem.strip()


def discover_tracks(extracted_dir: Path) -> list[SpeakerTrack]:
    tracks: list[SpeakerTrack] = []

    for path in extracted_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            continue

        speaker_name = clean_speaker_name(path)
        tracks.append(SpeakerTrack(speaker_name=speaker_name, audio_path=path))

    tracks.sort(key=lambda t: t.speaker_name.lower())
    return tracks


def find_info_file(extracted_dir: Path) -> Path | None:
    for path in extracted_dir.rglob("*"):
        if path.is_file() and path.name.lower() == "info.txt":
            return path
    return None