from __future__ import annotations

import json
import os
from pathlib import Path

from merge import ChunkTranscript


class CheckpointStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, checkpoint_key: str) -> Path:
        return self.directory / f"{checkpoint_key}.json"

    def load(self, checkpoint_key: str) -> ChunkTranscript | None:
        checkpoint_path = self._path_for(checkpoint_key)
        if not checkpoint_path.exists():
            return None

        with checkpoint_path.open("r", encoding="utf-8") as checkpoint_file:
            payload = json.load(checkpoint_file)
        return ChunkTranscript.from_dict(payload)

    def save(self, checkpoint_key: str, transcript: ChunkTranscript) -> None:
        checkpoint_path = self._path_for(checkpoint_key)
        temporary_path = checkpoint_path.with_suffix(".json.tmp")

        with temporary_path.open("w", encoding="utf-8") as checkpoint_file:
            json.dump(transcript.to_dict(), checkpoint_file, indent=2, ensure_ascii=False)
            checkpoint_file.flush()
            os.fsync(checkpoint_file.fileno())

        os.replace(temporary_path, checkpoint_path)
